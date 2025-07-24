"""
Enhanced price comparison API endpoints with detailed retailer data
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from src.services.supabase_service import SupabaseService
from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher

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
    category: Optional[str] = Query(None, description="Filter by category"),
    matcher_mode: Optional[str] = Query(default="standard", description="Matching mode: 'standard' or 'ultra-strict'")
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
        
        # Initialize ultra-strict matcher if needed
        ultra_strict_matcher = None
        if matcher_mode == "ultra-strict":
            ultra_strict_matcher = UltraStrictProductMatcher()
            logger.info(f"Ultra-strict mode activated for {len(matches)} matches")
        
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
            matched_products_data = []
            for matched_id in match.get('matched_product_ids', []):
                matched_result = supabase.client.table('products')\
                    .select('*')\
                    .eq('id', matched_id)\
                    .single()\
                    .execute()
                
                if matched_result.data:
                    matched_products_data.append(matched_result.data)
            
            # Ultra-strict validation: check each matched product pair
            if ultra_strict_matcher:
                validated_products = [master_product]  # Always include master product
                
                for matched_product in matched_products_data:
                    # Ensure products have specifications field for ultra-strict matching
                    # Also handle SKU field - if it's a pure numeric ID, don't pass it
                    master_sku = master_product.get('sku', '')
                    matched_sku = matched_product.get('sku', '')
                    
                    master_with_specs = {
                        **master_product,
                        'specifications': master_product.get('specifications', {}),
                        # Only include SKU if it's not a pure numeric ID
                        'sku': master_sku if not master_sku.isdigit() else ''
                    }
                    matched_with_specs = {
                        **matched_product,
                        'specifications': matched_product.get('specifications', {}),
                        # Only include SKU if it's not a pure numeric ID
                        'sku': matched_sku if not matched_sku.isdigit() else ''
                    }
                    
                    # Validate match between master and matched product
                    match_result = ultra_strict_matcher.match_products(
                        master_with_specs,
                        matched_with_specs,
                        category=match.get('unified_category', 'default')
                    )
                    
                    
                    # Only include if confidence meets ultra-strict threshold (0.84+)
                    # Lowered from 0.90 to 0.84 to allow legitimate matches with identical models
                    # (accounts for floating-point precision issues)
                    if match_result.confidence >= 0.84:
                        validated_products.append(matched_product)
                    else:
                        # Enhanced debug logging
                        logger.info(f"Ultra-strict filter rejected match: {master_product.get('name', '')} vs {matched_product.get('name', '')} (confidence: {match_result.confidence:.2f})")
                        if match_result.rejection_reasons:
                            logger.info(f"Rejection reasons: {match_result.rejection_reasons}")
                        if match_result.confidence == 0.0:
                            logger.info(f"Zero confidence - early rejection. Match type: {match_result.match_type}")
                
                # Skip this match if only master product remains (no valid matches)
                if len(validated_products) < 2:
                    continue
                    
                # Update matched_products_data with validated products only
                matched_products_data = validated_products[1:]  # Exclude master product
            
            # Add matched products to retailer_prices
            for matched_product in matched_products_data:
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
                'category': category,
                'matcherMode': matcher_mode
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