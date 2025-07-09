"""
Enhanced price comparison API endpoints with detailed retailer data
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["price-comparisons-v2"])


def get_supabase(request: Request) -> SupabaseService:
    """Get Supabase service from request"""
    return request.app.state.supabase


@router.get("/detailed-comparisons")
async def get_detailed_comparisons(
    supabase: SupabaseService = Depends(get_supabase),
    limit: int = Query(default=50, ge=1, le=200, description="Number of results"),
    min_savings: float = Query(default=0, ge=0, description="Minimum savings amount"),
    min_savings_percent: float = Query(default=0, ge=0, le=100, description="Minimum savings percentage"),
    min_confidence: float = Query(default=0.5, ge=0, le=1, description="Minimum match confidence"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get detailed price comparisons with individual retailer prices
    """
    try:
        # Get product matches
        query = supabase.client.table('product_matches').select('*')
        
        if category:
            query = query.eq('unified_category', category)
        
        # Filter by match confidence
        if min_confidence > 0.5:
            query = query.gte('match_confidence', min_confidence)
        
        # Filter by minimum savings percentage if specified
        if min_savings_percent > 0:
            query = query.gte('price_variance_percentage', min_savings_percent)
            
        query = query.order('price_variance_percentage', desc=True)
        query = query.limit(limit)
        
        matches_result = query.execute()
        matches = matches_result.data if matches_result.data else []
        
        detailed_comparisons = []
        
        for match in matches:
            if not match.get('master_product_id'):
                continue
                
            # Get master product details
            master_result = supabase.client.table('products')\
                .select('*')\
                .eq('id', match['master_product_id'])\
                .single()\
                .execute()
            
            if not master_result.data:
                continue
                
            master_product = master_result.data
            
            # Get matched products details
            retailer_prices = [{
                'retailerCode': master_product['retailer_code'],
                'retailerName': master_product['retailer_name'],
                'productId': master_product['id'],
                'productName': master_product['name'],
                'price': float(master_product['current_price']) if master_product.get('current_price') else 0,
                'originalPrice': float(master_product['original_price']) if master_product.get('original_price') else None,
                'discount': master_product.get('discount_percentage', 0),
                'url': master_product.get('url'),
                'image': master_product['images'][0] if master_product.get('images') else None,
                'inStock': master_product.get('availability') == 'in_stock',
                'lastUpdated': master_product.get('updated_at')
            }]
            
            # Get matched products
            for matched_id in match.get('matched_product_ids', []):
                matched_result = supabase.client.table('products')\
                    .select('*')\
                    .eq('id', matched_id)\
                    .single()\
                    .execute()
                
                if matched_result.data:
                    matched_product = matched_result.data
                    retailer_prices.append({
                        'retailerCode': matched_product['retailer_code'],
                        'retailerName': matched_product['retailer_name'],
                        'productId': matched_product['id'],
                        'productName': matched_product['name'],
                        'price': float(matched_product['current_price']) if matched_product.get('current_price') else 0,
                        'originalPrice': float(matched_product['original_price']) if matched_product.get('original_price') else None,
                        'discount': matched_product.get('discount_percentage', 0),
                        'url': matched_product.get('url'),
                        'image': matched_product['images'][0] if matched_product.get('images') else None,
                        'inStock': matched_product.get('availability') == 'in_stock',
                        'lastUpdated': matched_product.get('updated_at')
                    })
            
            # Calculate savings
            prices = [r['price'] for r in retailer_prices if r['price'] > 0]
            if len(prices) < 2:
                continue
                
            min_price = min(prices)
            max_price = max(prices)
            savings_amount = max_price - min_price
            
            if min_savings > 0 and savings_amount < min_savings:
                continue
            
            detailed_comparisons.append({
                'matchId': match['id'],
                'productName': match['normalized_name'],
                'brand': match.get('normalized_brand', 'Unknown'),
                'category': match.get('unified_category', 'Unknown'),
                'matchConfidence': match.get('match_confidence', 0.85),
                'specifications': match.get('key_specifications', {}),
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
            'total': len(detailed_comparisons),
            'filters': {
                'limit': limit,
                'minSavings': min_savings,
                'category': category
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed comparisons: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get detailed comparisons")


@router.get("/categories-with-savings")
async def get_categories_with_savings(supabase: SupabaseService = Depends(get_supabase)):
    """
    Get categories with their total savings potential
    """
    try:
        # Get all matches grouped by category
        matches_result = supabase.client.table('product_matches')\
            .select('unified_category, price_range_min, price_range_max')\
            .execute()
        
        matches = matches_result.data if matches_result.data else []
        
        category_savings = {}
        
        for match in matches:
            category = match.get('unified_category', 'Unknown')
            if category not in category_savings:
                category_savings[category] = {
                    'category': category,
                    'totalProducts': 0,
                    'totalSavings': 0,
                    'avgSavingsPercentage': 0,
                    'savingsAmounts': []
                }
            
            if match.get('price_range_min') and match.get('price_range_max'):
                savings = float(match['price_range_max']) - float(match['price_range_min'])
                category_savings[category]['totalProducts'] += 1
                category_savings[category]['totalSavings'] += savings
                category_savings[category]['savingsAmounts'].append(savings)
        
        # Calculate averages
        result = []
        for category_data in category_savings.values():
            if category_data['totalProducts'] > 0:
                category_data['avgSavingsPercentage'] = (
                    sum(category_data['savingsAmounts']) / 
                    len(category_data['savingsAmounts']) / 1000 * 100  # Rough percentage
                )
                del category_data['savingsAmounts']  # Remove raw data
                result.append(category_data)
        
        # Sort by total savings
        result.sort(key=lambda x: x['totalSavings'], reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting categories with savings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get categories")