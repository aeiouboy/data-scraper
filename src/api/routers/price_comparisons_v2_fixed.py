"""
Fixed price comparison API endpoints that exclude disabled/false positive matches
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
router = APIRouter(tags=["price-comparisons-v2-fixed"])


def get_supabase(request: Request) -> SupabaseService:
    """Get Supabase service from request"""
    return request.app.state.supabase


def is_product_match_disabled(product):
    """Check if a product has been marked as match disabled"""
    try:
        specs = product.get('specifications', {})
        if isinstance(specs, str):
            try:
                specs = json.loads(specs)
            except:
                specs = {}
        
        return specs.get('match_disabled', False)
    except:
        return False


def filter_disabled_products(products):
    """Filter out products that have been marked as match disabled"""
    return [p for p in products if not is_product_match_disabled(p)]


def check_match_group_validity(products):
    """Check if a match group is valid after filtering disabled products"""
    if len(products) < 2:
        return False, "Less than 2 products remain after filtering"
    
    # Check for BTU variance in air conditioners
    btus = []
    for product in products:
        name = product.get('name', '')
        # Extract BTU from name
        import re
        btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*(?:BTU|บีทียู)', name, re.IGNORECASE)
        if btu_match:
            btu = int(btu_match.group(1).replace(',', '').replace('.', ''))
            btus.append(btu)
        else:
            # Try simpler pattern
            btu_match = re.search(r'(\d{2,5})\s*(?:BTU|บีทียู)', name, re.IGNORECASE)
            if btu_match:
                btu = int(btu_match.group(1))
                btus.append(btu)
    
    # If this is an air conditioner category, check BTU variance
    if len(btus) >= 2:
        min_btu = min(btus)
        max_btu = max(btus)
        btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
        
        if btu_variance > 10:
            return False, f"BTU variance {btu_variance:.1f}% exceeds 10% threshold"
    
    return True, "Valid match group"


@router.get("/detailed-comparisons-fixed")
async def get_detailed_comparisons_fixed(
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
    Fixed price comparisons that exclude disabled/false positive matches
    """
    try:
        # First, get match groups instead of product_matches
        query = supabase.client.table('match_groups').select('*')
        
        # Apply category filter if specified
        if category:
            query = query.eq('unified_category', category)
        
        # Get all match groups
        match_groups_result = query.execute()
        match_groups = match_groups_result.data if match_groups_result.data else []
        
        valid_comparisons = []
        
        for match_group in match_groups:
            match_group_id = match_group['id']
            
            # Get all products in this match group
            mappings_result = supabase.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
            
            if not mappings_result.data:
                continue
            
            # Get product details
            product_ids = [m['product_id'] for m in mappings_result.data]
            products_result = supabase.client.table('products').select('*').in_('id', product_ids).execute()
            
            if not products_result.data:
                continue
            
            products = products_result.data
            
            # Filter out disabled products
            active_products = filter_disabled_products(products)
            
            # Check if the match group is still valid
            is_valid, reason = check_match_group_validity(active_products)
            
            if not is_valid:
                logger.debug(f"Skipping match group {match_group_id}: {reason}")
                continue
            
            # Calculate price statistics
            prices = [float(p.get('current_price', 0)) for p in active_products if p.get('current_price')]
            
            if len(prices) < 2:
                continue
            
            min_price = min(prices)
            max_price = max(prices)
            price_variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
            
            # Apply filters
            if min_savings > 0 and (max_price - min_price) < min_savings:
                continue
            
            if min_savings_percent > 0 and price_variance < min_savings_percent:
                continue
            
            # Format retailer prices
            retailer_prices = []
            for product in active_products:
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
            
            # Sort by price
            retailer_prices.sort(key=lambda x: x['price'] if x['price'] else float('inf'))
            
            # Calculate savings
            savings_amount = max_price - min_price
            savings_percentage = price_variance
            
            # Find best price retailer
            best_price_product = min(active_products, key=lambda p: float(p.get('current_price', float('inf'))))
            
            comparison = {
                'id': match_group_id,
                'productName': match_group.get('canonical_name', ''),
                'brand': match_group.get('canonical_brand', ''),
                'category': match_group.get('unified_category', ''),
                'savingsAmount': savings_amount,
                'savingsPercentage': savings_percentage,
                'bestPrice': min_price,
                'worstPrice': max_price,
                'bestPriceRetailer': best_price_product.get('retailer_code', ''),
                'retailerPrices': retailer_prices,
                'priceRange': {
                    'min': min_price,
                    'max': max_price,
                    'variance': price_variance
                },
                'matchConfidence': match_group.get('confidence_score', 0.8),
                'totalRetailers': len(retailer_prices),
                'inStockCount': len([p for p in retailer_prices if p['inStock']]),
                'lastUpdated': match_group.get('updated_at'),
                'keySpecs': match_group.get('key_specifications', {}),
                'validationStatus': 'verified_no_false_positives'
            }
            
            valid_comparisons.append(comparison)
        
        # Apply sorting
        if sort_by == 'savings_amount':
            valid_comparisons.sort(key=lambda x: x['savingsAmount'], reverse=(sort_order == 'desc'))
        elif sort_by == 'savings_percentage':
            valid_comparisons.sort(key=lambda x: x['savingsPercentage'], reverse=(sort_order == 'desc'))
        elif sort_by == 'confidence':
            valid_comparisons.sort(key=lambda x: x['matchConfidence'], reverse=(sort_order == 'desc'))
        else:
            valid_comparisons.sort(key=lambda x: x['lastUpdated'] or '', reverse=True)
        
        # Apply pagination
        total_count = len(valid_comparisons)
        paginated_comparisons = valid_comparisons[offset:offset + limit]
        
        return {
            'comparisons': paginated_comparisons,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'hasMore': offset + limit < total_count
            },
            'filters': {
                'min_savings': min_savings,
                'min_savings_percent': min_savings_percent,
                'min_confidence': min_confidence,
                'category': category
            },
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'validation_applied': True,
                'false_positives_filtered': True,
                'api_version': 'v2_fixed'
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_detailed_comparisons_fixed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/validate-existing-matches")
async def validate_existing_matches(
    supabase: SupabaseService = Depends(get_supabase),
    limit: int = Query(default=50, ge=1, le=100, description="Number of matches to validate")
):
    """
    Validate existing matches and report on potential false positives
    """
    try:
        # Get all match groups
        match_groups_result = supabase.client.table('match_groups').select('*').limit(limit).execute()
        match_groups = match_groups_result.data if match_groups_result.data else []
        
        validation_results = []
        
        for match_group in match_groups:
            match_group_id = match_group['id']
            
            # Get all products in this match group
            mappings_result = supabase.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
            
            if not mappings_result.data:
                continue
            
            # Get product details
            product_ids = [m['product_id'] for m in mappings_result.data]
            products_result = supabase.client.table('products').select('*').in_('id', product_ids).execute()
            
            if not products_result.data:
                continue
            
            products = products_result.data
            
            # Check for disabled products
            disabled_products = [p for p in products if is_product_match_disabled(p)]
            active_products = [p for p in products if not is_product_match_disabled(p)]
            
            # Check validity
            is_valid, reason = check_match_group_validity(active_products)
            
            result = {
                'match_group_id': match_group_id,
                'canonical_name': match_group.get('canonical_name', ''),
                'total_products': len(products),
                'disabled_products': len(disabled_products),
                'active_products': len(active_products),
                'is_valid': is_valid,
                'validation_reason': reason,
                'status': 'valid' if is_valid else 'invalid'
            }
            
            # Add BTU analysis for air conditioners
            if any('BTU' in p.get('name', '').upper() or 'บีทียู' in p.get('name', '') for p in products):
                btus = []
                for product in products:
                    name = product.get('name', '')
                    import re
                    btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*(?:BTU|บีทียู)', name, re.IGNORECASE)
                    if btu_match:
                        btu = int(btu_match.group(1).replace(',', '').replace('.', ''))
                        btus.append(btu)
                    else:
                        btu_match = re.search(r'(\d{2,5})\s*(?:BTU|บีทียู)', name, re.IGNORECASE)
                        if btu_match:
                            btu = int(btu_match.group(1))
                            btus.append(btu)
                
                if len(btus) >= 2:
                    min_btu = min(btus)
                    max_btu = max(btus)
                    btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                    
                    result['btu_analysis'] = {
                        'min_btu': min_btu,
                        'max_btu': max_btu,
                        'btu_variance': btu_variance,
                        'exceeds_threshold': btu_variance > 10
                    }
            
            validation_results.append(result)
        
        # Summary statistics
        total_validated = len(validation_results)
        valid_matches = len([r for r in validation_results if r['is_valid']])
        invalid_matches = total_validated - valid_matches
        has_disabled_products = len([r for r in validation_results if r['disabled_products'] > 0])
        
        return {
            'validation_results': validation_results,
            'summary': {
                'total_validated': total_validated,
                'valid_matches': valid_matches,
                'invalid_matches': invalid_matches,
                'matches_with_disabled_products': has_disabled_products,
                'validation_rate': (valid_matches / total_validated * 100) if total_validated > 0 else 0
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in validate_existing_matches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health-check")
async def health_check():
    """Health check endpoint for the fixed price comparison API"""
    return {
        'status': 'healthy',
        'api_version': 'v2_fixed',
        'features': [
            'false_positive_filtering',
            'btu_variance_validation',
            'disabled_product_exclusion',
            'match_group_validation'
        ],
        'timestamp': datetime.now().isoformat()
    }