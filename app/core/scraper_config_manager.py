"""
Scraper Configuration Manager - Manages dynamic selectors and scraping configurations
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager

logger = logging.getLogger(__name__)


class SelectorType(Enum):
    """Types of selectors supported"""
    CSS = "css"
    XPATH = "xpath"
    REGEX = "regex"
    JSON_PATH = "json_path"


class ElementType(Enum):
    """Types of elements to extract"""
    PRODUCT_NAME = "product_name"
    PRICE = "price"
    ORIGINAL_PRICE = "original_price"
    DISCOUNT = "discount"
    IMAGE = "image"
    DESCRIPTION = "description"
    BRAND = "brand"
    SKU = "sku"
    AVAILABILITY = "availability"
    RATING = "rating"
    REVIEW_COUNT = "review_count"
    CATEGORY = "category"
    PRODUCT_LINK = "product_link"
    PAGINATION = "pagination"


class Selector:
    """Represents a single selector configuration"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.retailer_code = data.get('retailer_code')
        self.page_type = data.get('page_type')
        self.element_type = data.get('element_type')
        self.selector_type = data.get('selector_type')
        self.selector_value = data.get('selector_value')
        self.selector_context = data.get('selector_context')
        self.priority = data.get('priority', 1)
        self.confidence_score = data.get('confidence_score', 1.0)
        self.validation_regex = data.get('validation_regex')
        self.transformation_rule = data.get('transformation_rule')
        self.fallback_value = data.get('fallback_value')
        self.is_active = data.get('is_active', True)
        
    def validate_value(self, value: str) -> bool:
        """Validate extracted value against regex if configured"""
        if not self.validation_regex or not value:
            return True
            
        try:
            return bool(re.match(self.validation_regex, value))
        except Exception as e:
            logger.error(f"Validation regex error: {str(e)}")
            return True
            
    def transform_value(self, value: str) -> str:
        """Apply transformation rule if configured"""
        if not self.transformation_rule or not value:
            return value
            
        try:
            # Handle common transformations
            if self.transformation_rule == 'strip':
                return value.strip()
            elif self.transformation_rule.startswith('replace:'):
                parts = self.transformation_rule.split(':', 2)
                if len(parts) == 3:
                    return value.replace(parts[1], parts[2])
            elif self.transformation_rule == 'lowercase':
                return value.lower()
            elif self.transformation_rule == 'uppercase':
                return value.upper()
            elif self.transformation_rule.startswith('regex:'):
                pattern = self.transformation_rule[6:]
                match = re.search(pattern, value)
                return match.group(1) if match else value
                
        except Exception as e:
            logger.error(f"Transformation error: {str(e)}")
            
        return value


class ScraperConfigManager:
    """
    Manages dynamic scraper configurations and selectors
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        self._selector_cache: Dict[str, List[Selector]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 3600  # 1 hour cache
        
    async def get_selectors(
        self,
        retailer_code: str,
        page_type: str,
        element_type: str,
        force_refresh: bool = False
    ) -> List[Selector]:
        """
        Get active selectors for a specific element
        
        Args:
            retailer_code: Retailer identifier
            page_type: Type of page (product, category, search)
            element_type: Type of element to extract
            force_refresh: Force cache refresh
            
        Returns:
            List of selectors ordered by priority and confidence
        """
        cache_key = f"{retailer_code}:{page_type}:{element_type}"
        
        # Check cache
        if not force_refresh and self._is_cache_valid() and cache_key in self._selector_cache:
            return self._selector_cache[cache_key]
            
        try:
            # Query selectors
            result = self.supabase.client.table('scraper_selectors')\
                .select('*')\
                .in_('retailer_code', [retailer_code, 'DEFAULT'])\
                .eq('page_type', page_type)\
                .eq('element_type', element_type)\
                .eq('is_active', True)\
                .order('priority', desc=False)\
                .order('confidence_score', desc=True)\
                .execute()
                
            selectors = [Selector(data) for data in (result.data or [])]
            
            # Update cache
            self._selector_cache[cache_key] = selectors
            self._cache_timestamp = datetime.now()
            
            return selectors
            
        except Exception as e:
            logger.error(f"Error fetching selectors: {str(e)}")
            return []
    
    def _is_cache_valid(self) -> bool:
        """Check if selector cache is still valid"""
        if not self._cache_timestamp:
            return False
            
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl
    
    async def add_selector(
        self,
        retailer_code: str,
        page_type: str,
        element_type: str,
        selector_type: str,
        selector_value: str,
        **kwargs
    ) -> Optional[str]:
        """
        Add a new selector configuration
        
        Args:
            retailer_code: Retailer identifier
            page_type: Type of page
            element_type: Type of element
            selector_type: Type of selector (css, xpath, etc.)
            selector_value: The actual selector
            **kwargs: Additional selector properties
            
        Returns:
            Selector ID if successful
        """
        try:
            selector_data = {
                'retailer_code': retailer_code,
                'page_type': page_type,
                'element_type': element_type,
                'selector_type': selector_type,
                'selector_value': selector_value,
                'priority': kwargs.get('priority', 1),
                'selector_context': kwargs.get('selector_context'),
                'validation_regex': kwargs.get('validation_regex'),
                'transformation_rule': kwargs.get('transformation_rule'),
                'fallback_value': kwargs.get('fallback_value'),
                'notes': kwargs.get('notes'),
                'created_by': kwargs.get('created_by', 'system'),
                'is_auto_discovered': kwargs.get('is_auto_discovered', False),
                'discovered_method': kwargs.get('discovered_method')
            }
            
            result = self.supabase.client.table('scraper_selectors')\
                .insert(selector_data)\
                .execute()
                
            if result.data:
                # Invalidate cache
                self._cache_timestamp = None
                return result.data[0]['id']
                
        except Exception as e:
            logger.error(f"Error adding selector: {str(e)}")
            
        return None
    
    async def record_selector_performance(
        self,
        selector_id: str,
        url: str,
        success: bool,
        execution_time_ms: Optional[int] = None,
        extracted_value: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        """
        Record performance metrics for a selector
        
        Args:
            selector_id: Selector identifier
            url: URL where selector was used
            success: Whether extraction was successful
            execution_time_ms: Time taken to execute
            extracted_value: Value extracted (if successful)
            error_message: Error message (if failed)
            error_type: Type of error
        """
        try:
            performance_data = {
                'selector_id': selector_id,
                'url': url,
                'success': success,
                'execution_time_ms': execution_time_ms,
                'extracted_value': extracted_value[:500] if extracted_value else None,  # Limit length
                'error_message': error_message,
                'error_type': error_type
            }
            
            self.supabase.client.table('selector_performance')\
                .insert(performance_data)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error recording selector performance: {str(e)}")
    
    async def get_selector_stats(
        self,
        selector_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get performance statistics for a selector
        
        Args:
            selector_id: Selector identifier
            days: Number of days to analyze
            
        Returns:
            Performance statistics
        """
        try:
            # Get selector info
            selector_result = self.supabase.client.table('scraper_selectors')\
                .select('*')\
                .eq('id', selector_id)\
                .single()\
                .execute()
                
            if not selector_result.data:
                return {}
                
            selector = selector_result.data
            
            # Get performance data
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            perf_result = self.supabase.client.table('selector_performance')\
                .select('*')\
                .eq('selector_id', selector_id)\
                .gte('created_at', since_date)\
                .execute()
                
            performances = perf_result.data or []
            
            # Calculate statistics
            total_uses = len(performances)
            successes = sum(1 for p in performances if p['success'])
            failures = total_uses - successes
            
            avg_time = 0
            if performances:
                times = [p['execution_time_ms'] for p in performances 
                        if p['execution_time_ms'] is not None]
                avg_time = sum(times) / len(times) if times else 0
                
            # Group errors by type
            error_types = {}
            for p in performances:
                if not p['success'] and p['error_type']:
                    error_types[p['error_type']] = error_types.get(p['error_type'], 0) + 1
                    
            return {
                'selector': selector,
                'total_uses': total_uses,
                'successes': successes,
                'failures': failures,
                'success_rate': (successes / total_uses * 100) if total_uses > 0 else 0,
                'avg_execution_time_ms': avg_time,
                'error_types': error_types,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting selector stats: {str(e)}")
            return {}
    
    async def deactivate_failing_selectors(
        self,
        threshold: float = 0.3,
        min_uses: int = 10
    ):
        """
        Automatically deactivate selectors with poor performance
        
        Args:
            threshold: Minimum success rate (0-1)
            min_uses: Minimum uses before considering deactivation
        """
        try:
            # Get all active selectors
            result = self.supabase.client.table('scraper_selectors')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
                
            selectors = result.data or []
            
            for selector in selectors:
                # Skip if not enough data
                if selector['success_count'] + selector['failure_count'] < min_uses:
                    continue
                    
                # Check success rate
                total = selector['success_count'] + selector['failure_count']
                success_rate = selector['success_count'] / total
                
                if success_rate < threshold:
                    logger.warning(
                        f"Deactivating selector {selector['id']} "
                        f"({selector['retailer_code']}/{selector['element_type']}) "
                        f"due to low success rate: {success_rate:.2%}"
                    )
                    
                    # Deactivate selector
                    self.supabase.client.table('scraper_selectors')\
                        .update({'is_active': False})\
                        .eq('id', selector['id'])\
                        .execute()
                        
                    # Create alert
                    alert_data = {
                        'alert_type': 'selector_deactivated',
                        'severity': 'warning',
                        'retailer_code': selector['retailer_code'],
                        'title': f"Selector deactivated: {selector['element_type']}",
                        'message': f"Selector deactivated due to {success_rate:.1%} success rate",
                        'details': {
                            'selector_id': selector['id'],
                            'element_type': selector['element_type'],
                            'success_rate': success_rate,
                            'total_uses': total
                        }
                    }
                    
                    self.supabase.client.table('scraper_alerts')\
                        .insert(alert_data)\
                        .execute()
                        
        except Exception as e:
            logger.error(f"Error deactivating failing selectors: {str(e)}")
    
    async def get_retailer_config(
        self,
        retailer_code: str
    ) -> Dict[str, Any]:
        """
        Get complete scraper configuration for a retailer
        
        Args:
            retailer_code: Retailer identifier
            
        Returns:
            Complete configuration including selectors and rules
        """
        try:
            # Get all active selectors
            selectors_result = self.supabase.client.table('scraper_selectors')\
                .select('*')\
                .eq('retailer_code', retailer_code)\
                .eq('is_active', True)\
                .order('page_type')\
                .order('element_type')\
                .order('priority')\
                .execute()
                
            # Get scraper rules
            rules_result = self.supabase.client.table('scraper_rules')\
                .select('*')\
                .eq('retailer_code', retailer_code)\
                .eq('is_active', True)\
                .execute()
                
            # Organize selectors by page type and element
            selectors_by_page = {}
            for selector in (selectors_result.data or []):
                page_type = selector['page_type']
                element_type = selector['element_type']
                
                if page_type not in selectors_by_page:
                    selectors_by_page[page_type] = {}
                    
                if element_type not in selectors_by_page[page_type]:
                    selectors_by_page[page_type][element_type] = []
                    
                selectors_by_page[page_type][element_type].append(selector)
                
            # Organize rules by type
            rules_by_type = {}
            for rule in (rules_result.data or []):
                rule_type = rule['rule_type']
                if rule_type not in rules_by_type:
                    rules_by_type[rule_type] = []
                rules_by_type[rule_type].append(rule)
                
            return {
                'retailer_code': retailer_code,
                'selectors': selectors_by_page,
                'rules': rules_by_type,
                'total_selectors': len(selectors_result.data or []),
                'total_rules': len(rules_result.data or [])
            }
            
        except Exception as e:
            logger.error(f"Error getting retailer config: {str(e)}")
            return {}
    
    async def copy_selectors(
        self,
        from_retailer: str,
        to_retailer: str,
        page_type: Optional[str] = None,
        element_type: Optional[str] = None
    ) -> int:
        """
        Copy selectors from one retailer to another
        
        Args:
            from_retailer: Source retailer code
            to_retailer: Target retailer code
            page_type: Optional filter by page type
            element_type: Optional filter by element type
            
        Returns:
            Number of selectors copied
        """
        try:
            # Build query
            query = self.supabase.client.table('scraper_selectors')\
                .select('*')\
                .eq('retailer_code', from_retailer)\
                .eq('is_active', True)
                
            if page_type:
                query = query.eq('page_type', page_type)
            if element_type:
                query = query.eq('element_type', element_type)
                
            result = query.execute()
            selectors = result.data or []
            
            copied_count = 0
            for selector in selectors:
                # Remove ID and update retailer code
                selector.pop('id', None)
                selector['retailer_code'] = to_retailer
                selector['notes'] = f"Copied from {from_retailer}"
                selector['created_at'] = None
                selector['updated_at'] = None
                
                # Insert copy
                copy_result = self.supabase.client.table('scraper_selectors')\
                    .insert(selector)\
                    .execute()
                    
                if copy_result.data:
                    copied_count += 1
                    
            logger.info(f"Copied {copied_count} selectors from {from_retailer} to {to_retailer}")
            return copied_count
            
        except Exception as e:
            logger.error(f"Error copying selectors: {str(e)}")
            return 0