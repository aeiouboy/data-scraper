"""
Optimized price comparison API endpoints with performance improvements
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio

from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["price-comparisons-v2"])


def get_supabase(request: Request) -> SupabaseService:
    """Get Supabase service from request"""
    return request.app.state.supabase


@router.get("/detailed-comparisons-optimized")
async def get_detailed_comparisons_optimized(
    supabase: SupabaseService = Depends(get_supabase),
    limit: int = Query(default=12, ge=1, le=50, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    min_savings: float = Query(default=0, ge=0, description="Minimum savings amount"),
    min_savings_percent: float = Query(default=0, ge=0, le=100, description="Minimum savings percentage"),
    min_confidence: float = Query(default=0.5, ge=0, le=1, description="Minimum match confidence"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query(default="savings_amount", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order")
):
    """
    Optimized price comparisons with proper pagination and efficient queries
    """
    try:
        # Build optimized query with server-side filtering
        # Use existing product_matches table until views are created
        query = supabase.client.table('product_matches').select(
            'id, normalized_name, normalized_brand, unified_category, '
            'price_range_min, price_range_max, price_variance_percentage, '
            'best_price_retailer, match_confidence, key_specifications, '
            'updated_at, master_product_id, matched_product_ids'
        )
        
        # Apply filters at database level
        if category:
            query = query.eq('unified_category', category)
        
        if min_savings > 0:
            query = query.gte('savings_amount', min_savings)
        
        # Filter by minimum savings percentage if specified
        if min_savings_percent > 0:
            query = query.gte('price_variance_percentage', min_savings_percent)
        
        # Apply confidence filter
        if min_confidence > 0.5:
            query = query.gte('match_confidence', min_confidence)
        
        # Add sorting
        if sort_by == 'savings_amount':
            query = query.order('savings_amount', desc=(sort_order == 'desc'))
        elif sort_by == 'savings_percentage':
            query = query.order('price_variance_percentage', desc=(sort_order == 'desc'))
        else:
            query = query.order('updated_at', desc=True)
        
        # Get count first (before pagination)
        # Note: Supabase doesn't support count() directly, we'll get total after query
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        matches = result.data if result.data else []
        
        # Get total count by doing a separate count query
        count_query = supabase.client.table('product_matches').select('id', count='exact')
        if category:
            count_query = count_query.eq('unified_category', category)
        if min_savings > 0:
            count_query = count_query.gte('savings_amount', min_savings)
        if min_savings_percent > 0:
            count_query = count_query.gte('price_variance_percentage', min_savings_percent)
        if min_confidence > 0.5:
            count_query = count_query.gte('match_confidence', min_confidence)
        
        count_result = count_query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Process results efficiently
        detailed_comparisons = []
        
        # Batch load all products for all matches
        all_product_ids = []
        for match in matches:
            if match.get('master_product_id'):
                all_product_ids.append(match['master_product_id'])
            if match.get('matched_product_ids'):
                all_product_ids.extend(match['matched_product_ids'])
        
        # Get all products in one query
        products_dict = {}
        if all_product_ids:
            # Use existing method from supabase service
            products_query = supabase.client.table('products').select('*').in_('id', all_product_ids)
            products_result = products_query.execute()
            if products_result.data:
                products_dict = {p['id']: p for p in products_result.data}
        
        for match in matches:
            # Get products for this match
            matched_products = []
            
            # Add master product
            if match.get('master_product_id') and match['master_product_id'] in products_dict:
                matched_products.append(products_dict[match['master_product_id']])
            
            # Add matched products
            if match.get('matched_product_ids'):
                for prod_id in match['matched_product_ids']:
                    if prod_id in products_dict:
                        matched_products.append(products_dict[prod_id])
            
            # Format retailer prices from products
            retailer_prices = []
            for product in matched_products:
                retailer_prices.append({
                    'retailerCode': product.get('retailer_code', ''),
                    'retailerName': product.get('retailer_name', ''),
                    'productId': product.get('id', ''),
                    'productName': product.get('name', ''),
                    'price': float(product.get('current_price', 0)) if product.get('current_price') else 0,
                    'originalPrice': float(product.get('original_price', 0)) if product.get('original_price') else None,
                    'discount': product.get('discount_percentage', 0),
                    'url': product.get('url'),
                    'image': product.get('images', [None])[0] if product.get('images') else None,
                    'inStock': product.get('availability') == 'in_stock',
                    'lastUpdated': product.get('updated_at')
                })
            
            # Skip if no products found
            if not retailer_prices:
                continue
                
            # Calculate savings efficiently
            min_price = float(match['price_range_min']) if match.get('price_range_min') else 0
            max_price = float(match['price_range_max']) if match.get('price_range_max') else 0
            savings_amount = max_price - min_price if min_price and max_price else 0
            
            # Skip if no price variance
            if len(retailer_prices) < 2 or savings_amount <= 0:
                continue
            
            detailed_comparisons.append({
                'matchId': match['id'],
                'productName': match['normalized_name'],
                'brand': match.get('normalized_brand', 'Unknown'),
                'category': match.get('unified_category', 'Unknown'),
                'matchConfidence': match.get('match_confidence', 0.85),
                'specifications': json.loads(match.get('key_specifications', '{}')) if match.get('key_specifications') else {},
                'retailerPrices': sorted(retailer_prices, key=lambda x: x['price']),
                'priceAnalysis': {
                    'minPrice': min_price,
                    'maxPrice': max_price,
                    'savingsAmount': savings_amount,
                    'savingsPercentage': match.get('price_variance_percentage', 0),
                    'bestRetailer': match.get('best_price_retailer'),
                    'priceRange': f"฿{min_price:,.0f} - ฿{max_price:,.0f}"
                },
                'lastUpdated': match.get('updated_at', datetime.now().isoformat())
            })
        
        return {
            'comparisons': detailed_comparisons,
            'total': total_count,
            'page': offset // limit + 1,
            'pageSize': limit,
            'totalPages': (total_count + limit - 1) // limit,
            'filters': {
                'limit': limit,
                'offset': offset,
                'minSavings': min_savings,
                'category': category,
                'sortBy': sort_by,
                'sortOrder': sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"Error in optimized comparisons: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get comparisons")


@router.get("/categories-summary")
async def get_categories_summary(
    supabase: SupabaseService = Depends(get_supabase)
):
    """
    Get categories with counts and savings summary - optimized with caching
    """
    try:
        # Use aggregated view for better performance
        result = supabase.client.table('category_savings_summary').select('*').execute()
        
        categories = []
        for row in result.data:
            categories.append({
                'category': row['category'],
                'productCount': row['product_count'],
                'avgSavings': float(row['avg_savings']),
                'maxSavings': float(row['max_savings']),
                'totalSavings': float(row['total_savings'])
            })
        
        return {
            'categories': sorted(categories, key=lambda x: x['totalSavings'], reverse=True),
            'total': len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting categories summary: {str(e)}")
        # Fallback to basic query if view doesn't exist
        return await get_categories_with_savings_fallback(supabase)


async def get_categories_with_savings_fallback(supabase: SupabaseService):
    """Fallback method if optimized view doesn't exist"""
    try:
        result = supabase.client.table('product_matches').select(
            'unified_category, price_range_min, price_range_max'
        ).execute()
        
        category_stats = {}
        for match in result.data:
            cat = match.get('unified_category', 'Unknown')
            if cat not in category_stats:
                category_stats[cat] = {
                    'count': 0,
                    'total_savings': 0,
                    'max_savings': 0
                }
            
            savings = (match.get('price_range_max', 0) or 0) - (match.get('price_range_min', 0) or 0)
            category_stats[cat]['count'] += 1
            category_stats[cat]['total_savings'] += savings
            category_stats[cat]['max_savings'] = max(category_stats[cat]['max_savings'], savings)
        
        categories = []
        for cat, stats in category_stats.items():
            categories.append({
                'category': cat,
                'productCount': stats['count'],
                'avgSavings': stats['total_savings'] / stats['count'] if stats['count'] > 0 else 0,
                'maxSavings': stats['max_savings'],
                'totalSavings': stats['total_savings']
            })
        
        return {
            'categories': sorted(categories, key=lambda x: x['totalSavings'], reverse=True),
            'total': len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error in fallback categories: {str(e)}")
        return {'categories': [], 'total': 0}


@router.get("/quick-stats")
async def get_quick_stats(
    supabase: SupabaseService = Depends(get_supabase),
    category: Optional[str] = Query(None)
):
    """
    Get quick statistics for the price comparisons page
    """
    try:
        # Use pre-aggregated stats table if available
        query = supabase.client.table('price_comparison_stats').select('*')
        
        if category:
            query = query.eq('category', category)
        else:
            query = query.is_('category', None)
        
        result = query.single().execute()
        
        if result.data:
            return {
                'totalSavingsAvailable': float(result.data.get('total_savings', 0)),
                'productsWithSavings': result.data.get('products_with_savings', 0),
                'avgPriceVariance': float(result.data.get('avg_price_variance', 0)),
                'lastUpdated': result.data.get('updated_at')
            }
        
        # Fallback to calculating stats
        return await calculate_quick_stats_fallback(supabase, category)
        
    except Exception as e:
        logger.error(f"Error getting quick stats: {str(e)}")
        return await calculate_quick_stats_fallback(supabase, category)


async def calculate_quick_stats_fallback(supabase: SupabaseService, category: Optional[str]):
    """Calculate stats if pre-aggregated table doesn't exist"""
    try:
        query = supabase.client.table('product_matches').select(
            'price_range_min, price_range_max, price_variance_percentage'
        )
        
        if category:
            query = query.eq('unified_category', category)
        
        result = query.execute()
        matches = result.data if result.data else []
        
        total_savings = 0
        total_variance = 0
        count_with_savings = 0
        
        for match in matches:
            min_price = match.get('price_range_min', 0) or 0
            max_price = match.get('price_range_max', 0) or 0
            savings = max_price - min_price
            
            if savings > 0:
                total_savings += savings
                count_with_savings += 1
                total_variance += match.get('price_variance_percentage', 0) or 0
        
        return {
            'totalSavingsAvailable': total_savings,
            'productsWithSavings': count_with_savings,
            'avgPriceVariance': total_variance / count_with_savings if count_with_savings > 0 else 0,
            'lastUpdated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating fallback stats: {str(e)}")
        return {
            'totalSavingsAvailable': 0,
            'productsWithSavings': 0,
            'avgPriceVariance': 0,
            'lastUpdated': datetime.now().isoformat()
        }