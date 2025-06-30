"""
Price comparison API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.services.supabase_service import SupabaseService
from app.api.models import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["price-comparisons"])


@router.get("/top-savings")
async def get_top_savings(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Number of results to return"),
    min_savings_percent: float = Query(default=5.0, ge=0, le=100, description="Minimum savings percentage"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get products with the highest savings opportunities across retailers
    
    Returns products where significant price differences exist between retailers
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Query for products with price variations
        # For now, we'll simulate with products that have discounts
        query = supabase.client.table('products').select(
            'id, sku, name, brand, category, current_price, original_price, '
            'discount_percentage, retailer_code, retailer_name, url, images'
        )
        
        # Filter by discount percentage as a proxy for savings
        query = query.gt('discount_percentage', min_savings_percent)
        
        if category:
            query = query.eq('category', category)
        
        # Order by discount percentage (highest first)
        query = query.order('discount_percentage', desc=True)
        query = query.limit(limit)
        
        result = query.execute()
        products = result.data if result.data else []
        
        # Format response with savings information
        savings_opportunities = []
        for product in products:
            if product.get('discount_percentage', 0) > 0:
                savings_amount = (product.get('original_price', 0) - product.get('current_price', 0)) if product.get('original_price') and product.get('current_price') else 0
                
                savings_opportunities.append({
                    'id': product['id'],
                    'name': product['name'],
                    'brand': product.get('brand'),
                    'category': product.get('category'),
                    'retailer': {
                        'code': product['retailer_code'],
                        'name': product['retailer_name']
                    },
                    'current_price': product.get('current_price', 0),
                    'original_price': product.get('original_price', 0),
                    'savings_amount': savings_amount,
                    'savings_percentage': product.get('discount_percentage', 0),
                    'url': product['url'],
                    'image': product['images'][0] if product.get('images') else None,
                    'availability': product.get('availability', 'unknown')
                })
        
        return {
            'savings': savings_opportunities,
            'total': len(savings_opportunities),
            'query': {
                'limit': limit,
                'min_savings_percent': min_savings_percent,
                'category': category
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting top savings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top savings")


@router.get("/retailer-competitiveness")
async def get_retailer_competitiveness(request: Request):
    """
    Analyze retailer competitiveness based on pricing
    
    Returns metrics showing which retailers offer the best prices
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Get retailer statistics
        retailers_response = supabase.client.table('retailers').select('*').execute()
        retailers = retailers_response.data if retailers_response.data else []
        
        competitiveness_data = []
        
        for retailer in retailers:
            # Get pricing statistics for this retailer
            stats_query = supabase.client.table('products').select(
                'current_price, discount_percentage'
            ).eq('retailer_code', retailer['code'])
            
            stats_result = stats_query.execute()
            products = stats_result.data if stats_result.data else []
            
            if products:
                prices = [p['current_price'] for p in products if p.get('current_price')]
                discounts = [p['discount_percentage'] for p in products if p.get('discount_percentage')]
                
                avg_price = sum(prices) / len(prices) if prices else 0
                avg_discount = sum(discounts) / len(discounts) if discounts else 0
                products_on_sale = len([d for d in discounts if d > 0])
                
                # Calculate competitiveness score (lower avg price + higher avg discount = better)
                competitiveness_score = (100 - (avg_price / 1000)) + (avg_discount * 2)
                
                competitiveness_data.append({
                    'retailer': {
                        'code': retailer['code'],
                        'name': retailer['name'],
                        'market_position': retailer.get('market_position', '')
                    },
                    'metrics': {
                        'average_price': round(avg_price, 2),
                        'average_discount': round(avg_discount, 2),
                        'products_on_sale': products_on_sale,
                        'total_products': len(products),
                        'sale_percentage': round((products_on_sale / len(products) * 100) if products else 0, 2)
                    },
                    'competitiveness_score': round(competitiveness_score, 2),
                    'price_index': round(avg_price / 10000 * 100, 2)  # Normalized price index
                })
        
        # Sort by competitiveness score
        competitiveness_data.sort(key=lambda x: x['competitiveness_score'], reverse=True)
        
        # Add ranking
        for idx, item in enumerate(competitiveness_data):
            item['rank'] = idx + 1
        
        return {
            'retailers': competitiveness_data,
            'summary': {
                'most_competitive': competitiveness_data[0]['retailer']['name'] if competitiveness_data else None,
                'least_competitive': competitiveness_data[-1]['retailer']['name'] if competitiveness_data else None,
                'average_discount_market': round(
                    sum(r['metrics']['average_discount'] for r in competitiveness_data) / len(competitiveness_data)
                    if competitiveness_data else 0, 2
                )
            },
            'updated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing retailer competitiveness: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze retailer competitiveness")


@router.get("/category/{category}")
async def get_category_comparisons(
    request: Request,
    category: str,
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    Get price comparisons for products in a specific category
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Get products in this category from all retailers
        query = supabase.client.table('products').select(
            'id, sku, name, brand, current_price, original_price, '
            'discount_percentage, retailer_code, retailer_name, url, availability'
        ).eq('category', category)
        
        query = query.order('current_price', desc=False)
        query = query.limit(limit)
        
        result = query.execute()
        products = result.data if result.data else []
        
        # Group by product name/brand for comparison
        product_groups = {}
        for product in products:
            # Create a key based on normalized name and brand
            key = f"{product.get('brand', '').lower()}_{product['name'].lower()[:30]}"
            
            if key not in product_groups:
                product_groups[key] = {
                    'name': product['name'],
                    'brand': product.get('brand'),
                    'retailers': []
                }
            
            product_groups[key]['retailers'].append({
                'code': product['retailer_code'],
                'name': product['retailer_name'],
                'price': product.get('current_price', 0),
                'original_price': product.get('original_price'),
                'discount': product.get('discount_percentage', 0),
                'availability': product.get('availability', 'unknown'),
                'url': product['url']
            })
        
        # Calculate price variations
        comparisons = []
        for key, group in product_groups.items():
            if len(group['retailers']) > 1:
                prices = [r['price'] for r in group['retailers'] if r['price']]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    price_variance = ((max_price - min_price) / min_price * 100) if min_price > 0 else 0
                    
                    comparisons.append({
                        'product': {
                            'name': group['name'],
                            'brand': group['brand']
                        },
                        'price_range': {
                            'min': min_price,
                            'max': max_price,
                            'variance_percentage': round(price_variance, 2)
                        },
                        'retailers': sorted(group['retailers'], key=lambda x: x['price'] or float('inf')),
                        'best_deal': min(group['retailers'], key=lambda x: x['price'] or float('inf'))
                    })
        
        # Sort by price variance (highest first)
        comparisons.sort(key=lambda x: x['price_range']['variance_percentage'], reverse=True)
        
        return {
            'category': category,
            'comparisons': comparisons,
            'total': len(comparisons),
            'summary': {
                'average_variance': round(
                    sum(c['price_range']['variance_percentage'] for c in comparisons) / len(comparisons)
                    if comparisons else 0, 2
                ),
                'products_compared': len(comparisons)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting category comparisons: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get category comparisons")


@router.get("/product/{product_id}")
async def get_product_match(request: Request, product_id: str):
    """
    Get cross-retailer matches for a specific product
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Get the product
        product_result = supabase.client.table('products').select('*').eq('id', product_id).single().execute()
        product = product_result.data
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Find similar products from other retailers
        # Simple matching based on name and brand similarity
        search_terms = product['name'].split()[:3]  # First 3 words
        search_query = ' '.join(search_terms)
        
        similar_query = supabase.client.table('products').select(
            'id, sku, name, brand, current_price, original_price, '
            'discount_percentage, retailer_code, retailer_name, url, availability, images'
        )
        
        # Search for similar names
        similar_query = similar_query.ilike('name', f'%{search_query}%')
        
        # Exclude same retailer
        similar_query = similar_query.neq('retailer_code', product['retailer_code'])
        
        similar_result = similar_query.execute()
        similar_products = similar_result.data if similar_result.data else []
        
        # Calculate match confidence based on name similarity
        matches = []
        for similar in similar_products:
            # Simple similarity check
            name_similarity = len(set(product['name'].lower().split()) & set(similar['name'].lower().split())) / len(set(product['name'].lower().split()))
            brand_match = product.get('brand', '').lower() == similar.get('brand', '').lower()
            
            confidence = (name_similarity * 0.7) + (0.3 if brand_match else 0)
            
            if confidence > 0.5:  # Only include good matches
                matches.append({
                    'product': {
                        'id': similar['id'],
                        'name': similar['name'],
                        'brand': similar.get('brand'),
                        'sku': similar['sku']
                    },
                    'retailer': {
                        'code': similar['retailer_code'],
                        'name': similar['retailer_name']
                    },
                    'pricing': {
                        'current_price': similar.get('current_price', 0),
                        'original_price': similar.get('original_price'),
                        'discount_percentage': similar.get('discount_percentage', 0)
                    },
                    'availability': similar.get('availability', 'unknown'),
                    'url': similar['url'],
                    'image': similar['images'][0] if similar.get('images') else None,
                    'match_confidence': round(confidence, 2)
                })
        
        # Sort by price (lowest first)
        matches.sort(key=lambda x: x['pricing']['current_price'] or float('inf'))
        
        # Calculate savings
        base_price = product.get('current_price', 0)
        for match in matches:
            match_price = match['pricing']['current_price']
            if base_price and match_price:
                savings = base_price - match_price
                match['savings'] = {
                    'amount': savings,
                    'percentage': round((savings / base_price * 100), 2) if savings > 0 else 0
                }
        
        return {
            'base_product': {
                'id': product['id'],
                'name': product['name'],
                'brand': product.get('brand'),
                'retailer': {
                    'code': product['retailer_code'],
                    'name': product['retailer_name']
                },
                'current_price': product.get('current_price', 0),
                'url': product['url']
            },
            'matches': matches,
            'total_matches': len(matches),
            'best_price': min(matches, key=lambda x: x['pricing']['current_price'] or float('inf')) if matches else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product matches: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get product matches")


@router.post("/matches")
async def create_match(
    request: Request,
    master_product_id: str,
    matched_product_ids: List[str]
):
    """
    Create a manual product match across retailers
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Verify all products exist
        all_product_ids = [master_product_id] + matched_product_ids
        products_result = supabase.client.table('products').select('id, name, brand, category').in_('id', all_product_ids).execute()
        products = {p['id']: p for p in products_result.data} if products_result.data else {}
        
        if len(products) != len(all_product_ids):
            raise HTTPException(status_code=400, detail="One or more products not found")
        
        master_product = products[master_product_id]
        
        # Create match record
        match_data = {
            'master_product_id': master_product_id,
            'matched_product_ids': matched_product_ids,
            'normalized_name': master_product['name'].lower(),
            'normalized_brand': master_product.get('brand', '').lower() if master_product.get('brand') else None,
            'unified_category': master_product.get('category', 'other'),
            'match_confidence': 1.0,  # Manual match = 100% confidence
            'match_criteria': {
                'method': 'manual',
                'created_by': 'user',
                'created_at': datetime.now().isoformat()
            }
        }
        
        result = supabase.client.table('product_matches').insert(match_data).execute()
        
        if result.data:
            return {
                'message': 'Product match created successfully',
                'match_id': result.data[0]['id']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create match")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product match: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create product match")


@router.post("/refresh")
async def refresh_matches(request: Request):
    """
    Refresh all product matches (placeholder for background job)
    """
    try:
        # In a real implementation, this would trigger a background job
        # to re-analyze and update all product matches
        
        return {
            'message': 'Match refresh job queued',
            'job_id': 'refresh_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
            'status': 'pending'
        }
        
    except Exception as e:
        logger.error(f"Error refreshing matches: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh matches")