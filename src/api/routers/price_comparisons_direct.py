"""
Direct price comparison API that uses data from match_criteria without requiring actual product records
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["price-comparisons-direct"])


def get_supabase(request: Request) -> SupabaseService:
    """Get Supabase service from request"""
    return request.app.state.supabase


@router.get("/comparisons-direct")
async def get_direct_comparisons(
    supabase: SupabaseService = Depends(get_supabase),
    limit: int = Query(default=12, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    min_savings: float = Query(default=0, ge=0, description="Minimum savings amount"),
    min_savings_percent: float = Query(default=0, ge=0, le=100, description="Minimum savings percentage"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by product name"),
    sort_by: str = Query(default="savings_amount", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order")
):
    """
    Direct price comparisons using data stored in match_criteria
    """
    try:
        # Build query with filters
        query = supabase.client.table('product_matches').select(
            'id, normalized_name, normalized_brand, unified_category, '
            'price_range_min, price_range_max, price_variance_percentage, '
            'best_price_retailer, match_confidence, match_criteria, '
            'created_at, updated_at'
        )
        
        # Apply filters
        if category:
            query = query.eq('unified_category', category)
        
        if search:
            query = query.ilike('normalized_name', f'%{search}%')
        
        if min_savings > 0:
            # Calculate savings as price_range_max - price_range_min
            query = query.gte('price_range_max', min_savings)
        
        if min_savings_percent > 0:
            query = query.gte('price_variance_percentage', min_savings_percent)
        
        # Only get imported JSON data
        query = query.contains('match_criteria', {"source": "imported_json"})
        
        # Add sorting
        if sort_by == 'savings_amount':
            query = query.order('price_range_max', desc=(sort_order == 'desc'))
        elif sort_by == 'savings_percentage':
            query = query.order('price_variance_percentage', desc=(sort_order == 'desc'))
        elif sort_by == 'confidence':
            query = query.order('match_confidence', desc=(sort_order == 'desc'))
        else:
            query = query.order('created_at', desc=True)
        
        # Get count
        count_query = supabase.client.table('product_matches').select('id', count='exact')
        if category:
            count_query = count_query.eq('unified_category', category)
        if min_savings > 0:
            count_query = count_query.gte('price_range_max', min_savings)
        if min_savings_percent > 0:
            count_query = count_query.gte('price_variance_percentage', min_savings_percent)
        count_query = count_query.contains('match_criteria', {"source": "imported_json"})
        
        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data or [])
        
        # Apply pagination and execute
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        matches = result.data if result.data else []
        
        # Process results using data from match_criteria
        detailed_comparisons = []
        
        for match in matches:
            try:
                match_criteria = match.get('match_criteria', {})
                retailers = match_criteria.get('retailers', [])
                prices = match_criteria.get('prices', {})
                
                # Skip if no price data
                if not prices or len(prices) < 2:
                    continue
                
                # Calculate savings
                price_values = [float(p) for p in prices.values() if p and float(p) > 0]
                if not price_values or len(price_values) < 2:
                    continue
                
                min_price = min(price_values)
                max_price = max(price_values)
                savings_amount = max_price - min_price
                
                if savings_amount <= 0:
                    continue
                
                # Create retailer price list from stored data
                retailer_prices = []
                retailer_mapping = {
                    "Thai Watsadu": "TWD",
                    "HomePro": "HP",
                    "Do Home": "DH", 
                    "Globalhouse": "GH",
                    "Boonthavorn": "BT",
                    "Bnbhome": "BNB",
                    "MegaHome": "MH"
                }
                
                for retailer_name, price in prices.items():
                    if price and float(price) > 0:
                        retailer_code = retailer_mapping.get(retailer_name, retailer_name.upper()[:3])
                        retailer_prices.append({
                            'retailerCode': retailer_code,
                            'retailerName': retailer_name,
                            'productId': f"virtual-{match['id']}-{retailer_code}",
                            'productName': match['normalized_name'],
                            'price': float(price),
                            'originalPrice': None,
                            'discount': None,
                            'url': None,
                            'image': None,
                            'inStock': True,
                            'lastUpdated': match.get('updated_at', match.get('created_at'))
                        })
                
                if len(retailer_prices) < 2:
                    continue
                
                # Find best retailer
                best_retailer = min(retailer_prices, key=lambda x: x['price'])
                
                comparison = {
                    'matchId': match['id'],
                    'productName': match['normalized_name'],
                    'brand': match.get('normalized_brand', 'Unknown'),
                    'category': match.get('unified_category', 'unknown'),
                    'matchConfidence': match.get('match_confidence', 0.95),
                    'specifications': {},
                    'retailerPrices': retailer_prices,
                    'priceAnalysis': {
                        'minPrice': min_price,
                        'maxPrice': max_price, 
                        'savingsAmount': savings_amount,
                        'savingsPercentage': (savings_amount / min_price * 100) if min_price > 0 else 0,
                        'bestRetailer': best_retailer['retailerCode'],
                        'priceRange': f"฿{min_price:,.0f} - ฿{max_price:,.0f}"
                    },
                    'lastUpdated': match.get('updated_at', match.get('created_at'))
                }
                
                detailed_comparisons.append(comparison)
                
            except Exception as e:
                logger.error(f"Error processing match {match.get('id')}: {e}")
                continue
        
        return {
            'comparisons': detailed_comparisons,
            'total': total_count,
            'page': (offset // limit) + 1,
            'pageSize': limit,
            'totalPages': (total_count + limit - 1) // limit,
            'filters': {
                'limit': limit,
                'offset': offset,
                'minSavings': min_savings,
                'minSavingsPercent': min_savings_percent,
                'category': category,
                'sortBy': sort_by,
                'sortOrder': sort_order
            }
        }
    
    except Exception as e:
        logger.error(f"Error in get_direct_comparisons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_available_categories(
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get available categories from imported data"""
    try:
        result = supabase.client.table('product_matches')\
            .select('unified_category')\
            .contains('match_criteria', {"source": "imported_json"})\
            .execute()
        
        categories = {}
        for item in result.data or []:
            cat = item['unified_category'] 
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'categories': [{'name': cat, 'count': count} for cat, count in sorted(categories.items())],
            'total': len(categories)
        }
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_comparison_stats(
    supabase: SupabaseService = Depends(get_supabase)
):
    """Get basic comparison statistics"""
    try:
        # Get count first
        count_result = supabase.client.table('product_matches')\
            .select('id', count='exact')\
            .contains('match_criteria', {"source": "imported_json"})\
            .execute()
        
        total_matches = count_result.count if hasattr(count_result, 'count') else 0
        
        # Process categories in batches to handle all records
        categories = {}
        high_savings = 0
        batch_size = 1000
        offset = 0
        
        while True:
            batch_result = supabase.client.table('product_matches')\
                .select('unified_category, price_variance_percentage')\
                .contains('match_criteria', {"source": "imported_json"})\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not batch_result.data:
                break
                
            for item in batch_result.data:
                cat = item['unified_category']
                categories[cat] = categories.get(cat, 0) + 1
                
                variance = item.get('price_variance_percentage', 0)
                if variance > 20:  # More than 20% savings
                    high_savings += 1
            
            # Break if we got less than batch_size records (last batch)
            if len(batch_result.data) < batch_size:
                break
            
            offset += batch_size
        
        return {
            'totalMatches': total_matches,
            'categoriesCount': len(categories),
            'highSavingsOpportunities': high_savings,
            'categories': [{'category': cat, 'count': count} for cat, count in sorted(categories.items())]
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))