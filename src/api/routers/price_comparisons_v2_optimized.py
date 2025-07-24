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
import re

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
        # Build optimized query with server-side filtering and minimal data fetch
        # Use SELECT with specific fields to reduce data transfer
        query = supabase.client.table('product_matches').select(
            'id, normalized_name, normalized_brand, unified_category, '
            'price_range_min, price_range_max, price_variance_percentage, '
            'best_price_retailer, match_confidence, key_specifications, '
            'updated_at, master_product_id, matched_product_ids'
        )
        
        # Apply filters at database level for better performance
        if category:
            query = query.eq('unified_category', category)
        
        # Pre-filter by price range to reduce dataset size
        if min_savings > 0:
            # Use price_range_max - price_range_min >= min_savings
            query = query.gte('price_range_max', min_savings)
        
        # Filter by minimum savings percentage if specified
        if min_savings_percent > 0:
            query = query.gte('price_variance_percentage', min_savings_percent)
        
        # Apply confidence filter
        if min_confidence > 0.5:
            query = query.gte('match_confidence', min_confidence)
        
        # Add sorting (only available fields)
        if sort_by == 'savings_amount':
            # Sort by price range max since savings_amount doesn't exist in DB
            query = query.order('price_range_max', desc=(sort_order == 'desc'))
        elif sort_by == 'savings_percentage':
            query = query.order('price_variance_percentage', desc=(sort_order == 'desc'))
        elif sort_by == 'confidence':
            query = query.order('match_confidence', desc=(sort_order == 'desc'))
        else:
            query = query.order('updated_at', desc=True)
        
        # Get count with optimized query using count='exact' on main query
        count_query = supabase.client.table('product_matches').select('id', count='exact')
        if category:
            count_query = count_query.eq('unified_category', category)
        if min_savings > 0:
            count_query = count_query.gte('price_range_max', min_savings)
        if min_savings_percent > 0:
            count_query = count_query.gte('price_variance_percentage', min_savings_percent)
        if min_confidence > 0.5:
            count_query = count_query.gte('match_confidence', min_confidence)
        
        # Execute count query separately but efficiently
        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data or [])
        
        # Apply pagination and execute main query
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        matches = result.data if result.data else []
        
        # Process results efficiently
        detailed_comparisons = []
        
        # Batch load all products for all matches with minimal fields
        all_product_ids = []
        for match in matches:
            if match.get('master_product_id'):
                all_product_ids.append(match['master_product_id'])
            if match.get('matched_product_ids'):
                all_product_ids.extend(match['matched_product_ids'])
        
        # Get all products in one query with only needed fields
        products_dict = {}
        if all_product_ids:
            # Only select essential fields to reduce data transfer
            products_query = supabase.client.table('products').select(
                'id, name, retailer_code, retailer_name, current_price, '
                'original_price, discount_percentage, url, images, '
                'availability, updated_at'
            ).in_('id', all_product_ids)
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
                
            # Calculate real-time prices from actual product data
            current_prices = [float(rp['price']) for rp in retailer_prices if rp['price'] > 0]
            min_price = min(current_prices) if current_prices else 0
            max_price = max(current_prices) if current_prices else 0
            savings_amount = max_price - min_price if min_price and max_price else 0
            
            # Skip if no price variance
            if len(retailer_prices) < 2 or savings_amount <= 0:
                continue
            
            # Skip false positive matches for air conditioners with significant BTU differences
            # Optimize BTU validation to run only when necessary
            if match.get('unified_category') == 'air_conditioner' and len(retailer_prices) >= 2:
                btu_values = []
                for rp in retailer_prices:
                    product_name = rp.get('productName', '')
                    # Extract BTU from product names using optimized regex
                    btu_match = re.search(r'(\d{1,2}[,.]?\d{3})\s*(?:บีทียู|BTU)', product_name, re.IGNORECASE)
                    if btu_match:
                        btu_str = btu_match.group(1).replace(',', '').replace('.', '')
                        try:
                            btu_values.append(int(btu_str))
                        except ValueError:
                            pass
                
                # If we have BTU values and they differ significantly, skip this match
                if len(btu_values) >= 2:
                    min_btu = min(btu_values)
                    max_btu = max(btu_values)
                    btu_variance = (max_btu - min_btu) / min_btu * 100 if min_btu > 0 else 0
                    # Skip matches with more than 30% BTU difference
                    if btu_variance > 30:
                        continue
            
            # Apply min_savings filter (after calculation)
            if min_savings > 0 and savings_amount < min_savings:
                continue
            
            detailed_comparisons.append({
                'matchId': match['id'],
                'productName': match['normalized_name'],
                'brand': match.get('normalized_brand', 'Unknown'),
                'category': match.get('unified_category', 'Unknown'),
                'matchConfidence': match.get('match_confidence', 0.85),
                'specifications': match.get('key_specifications') if isinstance(match.get('key_specifications'), dict) else (json.loads(match.get('key_specifications', '{}')) if match.get('key_specifications') else {}),
                'retailerPrices': sorted(retailer_prices, key=lambda x: x['price']),
                'priceAnalysis': {
                    'minPrice': min_price,
                    'maxPrice': max_price,
                    'savingsAmount': savings_amount,
                    'savingsPercentage': (savings_amount / min_price * 100) if min_price > 0 else 0,
                    'bestRetailer': next((rp['retailerCode'] for rp in retailer_prices if rp['price'] == min_price), None),
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
    """Calculate stats from pre-computed price ranges for performance"""
    try:
        # Use price_range_min and price_range_max from product_matches for faster calculation
        query = supabase.client.table('product_matches').select(
            'id, price_range_min, price_range_max, price_variance_percentage, unified_category'
        )
        
        if category:
            query = query.eq('unified_category', category)
        
        # Add basic filters to reduce dataset size
        query = query.gt('price_range_max', 0)  # Only matches with valid price ranges
        query = query.gte('price_variance_percentage', 1)  # Only matches with meaningful variance
        
        result = query.execute()
        matches = result.data if result.data else []
        
        total_savings = 0
        total_variance = 0
        count_with_savings = len(matches)
        
        # Calculate stats from pre-computed values
        for match in matches:
            savings = (match.get('price_range_max', 0) or 0) - (match.get('price_range_min', 0) or 0)
            total_savings += savings
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