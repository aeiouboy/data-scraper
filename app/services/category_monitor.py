"""
Category Monitor Service - Monitors category changes and website structure updates
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import hashlib
import json

from app.services.supabase_service import SupabaseService
from app.core.category_explorer import CategoryExplorer
from app.config.retailers import retailer_manager
from app.services.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)


class CategoryChange:
    """Represents a detected category change"""
    
    def __init__(self, 
                 retailer_code: str,
                 change_type: str,
                 category_id: Optional[str] = None,
                 old_value: Optional[Dict] = None,
                 new_value: Optional[Dict] = None,
                 severity: str = 'info'):
        self.retailer_code = retailer_code
        self.change_type = change_type  # new_category, removed, url_changed, etc.
        self.category_id = category_id
        self.old_value = old_value or {}
        self.new_value = new_value or {}
        self.severity = severity
        self.detected_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'retailer_code': self.retailer_code,
            'change_type': self.change_type,
            'category_id': self.category_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'detected_at': self.detected_at.isoformat(),
            'severity': self.severity
        }


class CategoryMonitor:
    """
    Monitors retailer categories for changes and updates
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.explorer = CategoryExplorer()
        self.changes_detected: List[CategoryChange] = []
        
    async def monitor_all_retailers(self) -> Dict[str, Any]:
        """
        Monitor all active retailers for category changes
        
        Returns:
            Summary of monitoring results
        """
        logger.info("Starting category monitoring for all retailers")
        
        results = {
            'start_time': datetime.now(),
            'retailers_checked': 0,
            'total_changes': 0,
            'changes_by_type': {},
            'retailers': {}
        }
        
        # Get all active retailers
        retailers = retailer_manager.get_all_retailers()
        
        for retailer in retailers:
            try:
                retailer_changes = await self.monitor_retailer(retailer.code)
                results['retailers'][retailer.code] = retailer_changes
                results['retailers_checked'] += 1
                results['total_changes'] += retailer_changes['change_count']
                
                # Aggregate changes by type
                for change_type, count in retailer_changes['changes_by_type'].items():
                    results['changes_by_type'][change_type] = \
                        results['changes_by_type'].get(change_type, 0) + count
                        
                # Rate limiting between retailers
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error monitoring {retailer.code}: {str(e)}")
                results['retailers'][retailer.code] = {
                    'error': str(e),
                    'change_count': 0
                }
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        # Save monitoring results
        await self._save_monitoring_results(results)
        
        return results
    
    async def monitor_retailer(self, retailer_code: str) -> Dict[str, Any]:
        """
        Monitor a single retailer for category changes
        
        Args:
            retailer_code: Retailer identifier
            
        Returns:
            Monitoring results for the retailer
        """
        logger.info(f"Monitoring categories for {retailer_code}")
        
        self.changes_detected = []
        
        # Get current categories from database
        current_categories = await self._get_current_categories(retailer_code)
        
        # Quick check: verify sample of categories
        sample_size = min(10, len(current_categories))
        sample_categories = current_categories[:sample_size] if current_categories else []
        
        # Verify each sample category
        for category in sample_categories:
            await self._verify_category(category)
            await asyncio.sleep(1)  # Rate limiting
        
        # Check for new categories on homepage
        await self._check_for_new_categories(retailer_code)
        
        # Analyze detected changes
        critical_changes = [c for c in self.changes_detected if c.severity == 'critical']
        warning_changes = [c for c in self.changes_detected if c.severity == 'warning']
        
        # Create alerts for critical changes
        if critical_changes:
            await self._create_alerts(critical_changes)
        
        # Save all changes
        saved_count = await self._save_changes()
        
        # Prepare summary
        changes_by_type = {}
        for change in self.changes_detected:
            changes_by_type[change.change_type] = \
                changes_by_type.get(change.change_type, 0) + 1
        
        return {
            'retailer_code': retailer_code,
            'categories_checked': len(sample_categories),
            'change_count': len(self.changes_detected),
            'critical_changes': len(critical_changes),
            'warning_changes': len(warning_changes),
            'changes_by_type': changes_by_type,
            'saved_changes': saved_count,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_current_categories(self, retailer_code: str) -> List[Dict[str, Any]]:
        """Get current categories from database"""
        try:
            result = self.supabase.client.table('retailer_categories')\
                .select('*')\
                .eq('retailer_code', retailer_code)\
                .eq('is_active', True)\
                .order('level', desc=False)\
                .order('product_count', desc=True)\
                .execute()
                
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
    
    async def _verify_category(self, category: Dict[str, Any]):
        """Verify a single category is still valid"""
        try:
            async with FirecrawlClient() as client:
                # Quick HEAD request to check if URL is accessible
                page_data = await client.scrape(category['category_url'])
                
                if not page_data:
                    # Category URL not accessible
                    self.changes_detected.append(CategoryChange(
                        retailer_code=category['retailer_code'],
                        change_type='category_unavailable',
                        category_id=category['id'],
                        old_value={'url': category['category_url']},
                        severity='warning'
                    ))
                    return
                
                # Check if it's still a category page
                html = page_data.get('html', '')
                
                # Look for signs it's been removed or changed
                if any(pattern in html.lower() for pattern in [
                    '404', 'not found', 'page not found', 
                    'removed', 'discontinued'
                ]):
                    self.changes_detected.append(CategoryChange(
                        retailer_code=category['retailer_code'],
                        change_type='category_removed',
                        category_id=category['id'],
                        old_value={'name': category['category_name']},
                        severity='critical'
                    ))
                    return
                
                # Check if redirected to different URL
                final_url = page_data.get('url', category['category_url'])
                if final_url != category['category_url']:
                    self.changes_detected.append(CategoryChange(
                        retailer_code=category['retailer_code'],
                        change_type='url_changed',
                        category_id=category['id'],
                        old_value={'url': category['category_url']},
                        new_value={'url': final_url},
                        severity='warning'
                    ))
                
                # Update last verified timestamp
                self.supabase.client.table('retailer_categories')\
                    .update({'last_verified': datetime.now().isoformat()})\
                    .eq('id', category['id'])\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error verifying category {category['category_name']}: {str(e)}")
            
            # Mark as verification failed
            self.changes_detected.append(CategoryChange(
                retailer_code=category['retailer_code'],
                change_type='verification_failed',
                category_id=category['id'],
                old_value={'error': str(e)},
                severity='warning'
            ))
    
    async def _check_for_new_categories(self, retailer_code: str):
        """Check homepage for new categories"""
        try:
            # Use explorer to discover categories from homepage only
            discovery_result = await self.explorer.discover_all_categories(
                retailer_code=retailer_code,
                max_depth=1,  # Only check root level
                max_categories=50
            )
            
            # Get existing category codes
            existing = await self._get_current_categories(retailer_code)
            existing_codes = {cat['category_code'] for cat in existing}
            
            # Check for new categories
            discovered_codes = set(discovery_result['category_tree'][0]['code'] 
                                 for tree in discovery_result['category_tree'])
            
            new_codes = discovered_codes - existing_codes
            
            for code in new_codes:
                # Find the category info
                for tree in discovery_result['category_tree']:
                    if tree['code'] == code:
                        self.changes_detected.append(CategoryChange(
                            retailer_code=retailer_code,
                            change_type='new_category',
                            new_value={
                                'code': code,
                                'name': tree['name'],
                                'url': tree['url']
                            },
                            severity='info'
                        ))
                        break
                        
        except Exception as e:
            logger.error(f"Error checking for new categories: {str(e)}")
    
    async def _save_changes(self) -> int:
        """Save detected changes to database"""
        saved_count = 0
        
        for change in self.changes_detected:
            try:
                change_data = change.to_dict()
                
                result = self.supabase.client.table('category_changes')\
                    .insert(change_data)\
                    .execute()
                    
                if result.data:
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving change: {str(e)}")
                
        return saved_count
    
    async def _create_alerts(self, critical_changes: List[CategoryChange]):
        """Create alerts for critical changes"""
        for change in critical_changes:
            try:
                alert_data = {
                    'alert_type': 'category_change',
                    'severity': change.severity,
                    'retailer_code': change.retailer_code,
                    'title': f"Critical category change: {change.change_type}",
                    'message': self._format_change_message(change),
                    'details': {
                        'change_type': change.change_type,
                        'category_id': change.category_id,
                        'old_value': change.old_value,
                        'new_value': change.new_value
                    }
                }
                
                self.supabase.client.table('scraper_alerts')\
                    .insert(alert_data)\
                    .execute()
                    
            except Exception as e:
                logger.error(f"Error creating alert: {str(e)}")
    
    def _format_change_message(self, change: CategoryChange) -> str:
        """Format a human-readable change message"""
        if change.change_type == 'category_removed':
            return f"Category '{change.old_value.get('name', 'Unknown')}' appears to be removed"
        elif change.change_type == 'url_changed':
            return f"Category URL changed from {change.old_value.get('url')} to {change.new_value.get('url')}"
        elif change.change_type == 'new_category':
            return f"New category discovered: {change.new_value.get('name')} ({change.new_value.get('code')})"
        elif change.change_type == 'category_unavailable':
            return f"Category URL not accessible: {change.old_value.get('url')}"
        else:
            return f"Category change detected: {change.change_type}"
    
    async def _save_monitoring_results(self, results: Dict[str, Any]):
        """Save monitoring run results"""
        try:
            # Save to a monitoring history table if needed
            logger.info(f"Monitoring completed: {results['total_changes']} changes detected")
            
            # Could save to a monitoring_runs table for history
            
        except Exception as e:
            logger.error(f"Error saving monitoring results: {str(e)}")
    
    async def get_recent_changes(
        self, 
        retailer_code: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent category changes"""
        try:
            query = self.supabase.client.table('category_changes')\
                .select('*')\
                .gte('detected_at', (datetime.now() - timedelta(days=days)).isoformat())
                
            if retailer_code:
                query = query.eq('retailer_code', retailer_code)
                
            result = query.order('detected_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching recent changes: {str(e)}")
            return []
    
    async def get_category_health(self, retailer_code: str) -> Dict[str, Any]:
        """Get category health metrics for a retailer"""
        try:
            # Get all categories
            categories = await self._get_current_categories(retailer_code)
            
            # Calculate metrics
            total_categories = len(categories)
            
            # Categories not verified in last 7 days
            stale_date = (datetime.now() - timedelta(days=7)).isoformat()
            stale_categories = [
                cat for cat in categories 
                if cat.get('last_verified', '') < stale_date
            ]
            
            # Categories with low success rate
            low_success_categories = [
                cat for cat in categories
                if cat.get('avg_success_rate', 100) < 80
            ]
            
            # Recent changes
            recent_changes = await self.get_recent_changes(retailer_code, days=7)
            
            return {
                'retailer_code': retailer_code,
                'total_categories': total_categories,
                'active_categories': len([c for c in categories if c.get('is_active')]),
                'stale_categories': len(stale_categories),
                'low_success_categories': len(low_success_categories),
                'recent_changes': len(recent_changes),
                'health_score': self._calculate_health_score(
                    total_categories,
                    len(stale_categories),
                    len(low_success_categories),
                    len(recent_changes)
                ),
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating category health: {str(e)}")
            return {
                'retailer_code': retailer_code,
                'error': str(e)
            }
    
    def _calculate_health_score(
        self,
        total: int,
        stale: int,
        low_success: int,
        changes: int
    ) -> float:
        """Calculate overall health score (0-100)"""
        if total == 0:
            return 0.0
            
        # Start with 100
        score = 100.0
        
        # Deduct for stale categories
        stale_penalty = (stale / total) * 30  # Max 30 point penalty
        score -= stale_penalty
        
        # Deduct for low success categories  
        success_penalty = (low_success / total) * 20  # Max 20 point penalty
        score -= success_penalty
        
        # Deduct for many recent changes (instability)
        if changes > total * 0.1:  # More than 10% changed
            score -= 10
            
        return max(0.0, round(score, 1))