"""
Product matching API endpoints for testing and managing cross-retailer matches
"""
from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
import hashlib

from src.services.product_matcher import ProductMatcher, ProductMatchAnalyzer
from src.services.supabase_service import SupabaseService
from src.utils.text_normalizer import TextNormalizer
from src.utils.product_matcher_improved import ImprovedProductMatcher

logger = logging.getLogger(__name__)
router = APIRouter(tags=["matching"])


from pydantic import BaseModel

class TestMatchRequest(BaseModel):
    product1_name: str
    product2_name: str
    brand1: Optional[str] = None
    brand2: Optional[str] = None

@router.post("/test-match")
async def test_product_match(
    request: Request,
    match_request: TestMatchRequest
):
    """
    Test the product matching algorithm with two product names
    
    This endpoint demonstrates the enhanced matching capabilities including:
    - Thai/English text normalization
    - SKU extraction
    - Specification matching
    - Brand alias resolution
    """
    try:
        # Initialize matcher
        improved_matcher = ImprovedProductMatcher()
        
        # Prepare product data for improved matcher
        product1_data = {
            'name': match_request.product1_name,
            'brand': match_request.brand1,
            'sku': '',  # Extract from name if available
            'specs': {},
            'category': 'default'
        }
        
        product2_data = {
            'name': match_request.product2_name,
            'brand': match_request.brand2,
            'sku': '',  # Extract from name if available
            'specs': {},
            'category': 'default'
        }
        
        # Perform matching
        match_result_obj = improved_matcher.match_products(
            product1_data,
            product2_data,
            'default'
        )
        
        # Convert to expected format
        match_result = {
            'overall_confidence': match_result_obj.confidence,
            'name_similarity': match_result_obj.details.get('name_score', 0),
            'sku_match': match_result_obj.details.get('sku_score', 0) > 0.8,
            'brand_match': match_result_obj.details.get('brand_score', 0),
            'spec_match': match_result_obj.details.get('spec_score', 0),
            'details': match_result_obj.details,
            'warnings': match_result_obj.warnings,
            'rejection_reasons': match_result_obj.rejection_reasons
        }
        
        # Add normalized text for debugging
        normalizer = TextNormalizer()
        match_result['normalized_name1'] = normalizer.normalize(match_request.product1_name)
        match_result['normalized_name2'] = normalizer.normalize(match_request.product2_name)
        
        # Determine match status
        confidence = match_result['overall_confidence']
        if confidence >= 0.90:
            status = "EXACT_MATCH"
        elif confidence >= 0.70:
            status = "LIKELY_MATCH"
        elif confidence >= 0.50:
            status = "POSSIBLE_MATCH"
        else:
            status = "NO_MATCH"
        
        return {
            "match_status": status,
            "confidence_score": round(confidence, 3),
            "details": match_result,
            "recommendation": _get_match_recommendation(confidence)
        }
        
    except Exception as e:
        logger.error(f"Error testing product match: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test product match")


@router.post("/process-new-products")
async def process_new_products(
    request: Request,
    background_tasks: BackgroundTasks,
    retailer_codes: Optional[List[str]] = Query(None, description="Filter by specific retailers"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of products to process")
):
    """
    Process recently added products to find cross-retailer matches
    
    This runs the matching algorithm on products that haven't been matched yet
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Get unmatched products
        query = supabase.client.table('products').select('*')
        
        # Filter products without matches
        query = query.is_('product_hash', None)
        
        if retailer_codes:
            query = query.in_('retailer_code', retailer_codes)
        
        query = query.limit(limit)
        result = query.execute()
        
        products_to_process = result.data if result.data else []
        
        if not products_to_process:
            return {
                "message": "No unmatched products found",
                "processed": 0
            }
        
        # Process in background
        background_tasks.add_task(
            _process_products_batch,
            products_to_process,
            supabase
        )
        
        return {
            "message": f"Started processing {len(products_to_process)} products",
            "job_id": f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "products_queued": len(products_to_process)
        }
        
    except Exception as e:
        logger.error(f"Error processing new products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process products")


@router.get("/match-suggestions/{product_id}")
async def get_match_suggestions(
    request: Request,
    product_id: str,
    min_confidence: float = Query(default=0.5, ge=0, le=1, description="Minimum confidence threshold")
):
    """
    Get match suggestions for a specific product
    
    Returns potential matches with confidence scores
    """
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid product ID format: '{product_id}'. Expected UUID format."
            )
            
        supabase: SupabaseService = request.app.state.supabase
        
        # Get the product
        product_result = supabase.client.table('products').select('*').eq('id', product_id).single().execute()
        
        if not product_result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = product_result.data
        
        # Initialize matcher
        matcher = ProductMatcher()
        improved_matcher = ImprovedProductMatcher()
        
        # Get potential matches from other retailers
        query = supabase.client.table('products').select('*')
        query = query.neq('retailer_code', product['retailer_code'])
        
        # Filter by category if available
        if product.get('unified_category'):
            query = query.eq('unified_category', product['unified_category'])
        
        query = query.limit(100)
        candidates_result = query.execute()
        candidates = candidates_result.data if candidates_result.data else []
        
        # Score each candidate
        suggestions = []
        for candidate in candidates:
            # Prepare product data for improved matcher
            product_data = {
                'name': product['name'],
                'brand': product.get('brand', ''),
                'sku': product.get('sku', ''),
                'specs': product.get('specifications', {}),
                'category': product.get('unified_category', 'default')
            }
            
            candidate_data = {
                'name': candidate['name'],
                'brand': candidate.get('brand', ''),
                'sku': candidate.get('sku', ''),
                'specs': candidate.get('specifications', {}),
                'category': candidate.get('unified_category', 'default')
            }
            
            match_result_obj = improved_matcher.match_products(
                product_data,
                candidate_data,
                product.get('unified_category', 'default')
            )
            
            # Convert to expected format
            match_result = {
                'overall_confidence': match_result_obj.confidence,
                'name_similarity': match_result_obj.details.get('name_score', 0),
                'sku_match': match_result_obj.details.get('sku_score', 0) > 0.8,
                'brand_match': match_result_obj.details.get('brand_score', 0),
                'spec_match': match_result_obj.details.get('spec_score', 0)
            }
            
            if match_result['overall_confidence'] >= min_confidence:
                suggestions.append({
                    'product': {
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'brand': candidate.get('brand'),
                        'retailer': candidate['retailer_name'],
                        'price': candidate.get('current_price'),
                        'url': candidate['url']
                    },
                    'match_confidence': round(match_result['overall_confidence'], 3),
                    'match_details': {
                        'name_similarity': round(match_result['name_similarity'], 3),
                        'sku_match': match_result['sku_match'],
                        'brand_match': round(match_result['brand_match'], 3),
                        'spec_match': round(match_result['spec_match'], 3)
                    }
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['match_confidence'], reverse=True)
        
        return {
            'base_product': {
                'id': product['id'],
                'name': product['name'],
                'brand': product.get('brand'),
                'retailer': product['retailer_name']
            },
            'suggestions': suggestions[:20],  # Top 20 matches
            'total_candidates_checked': len(candidates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get match suggestions")


class ConfirmMatchRequest(BaseModel):
    product1_id: str
    product2_id: str
    is_match: bool
    confidence_override: Optional[float] = None

@router.post("/confirm-match")
async def confirm_product_match(
    request: Request,
    match_data: ConfirmMatchRequest
):
    """
    Manually confirm or reject a product match
    
    This helps improve the matching algorithm by learning from manual corrections
    """
    try:
        supabase: SupabaseService = request.app.state.supabase
        
        # Record the match decision in match_history
        match_history = {
            'product1_id': match_data.product1_id,
            'product2_id': match_data.product2_id,
            'match_score': match_data.confidence_override or (0.95 if match_data.is_match else 0.05),
            'match_status': 'confirmed' if match_data.is_match else 'rejected',
            'match_details': {
                'manual_review': True,
                'reviewed_at': datetime.now().isoformat()
            },
            'reviewed_by': 'user',
            'reviewed_at': datetime.now().isoformat()
        }
        
        result = supabase.client.table('match_history').insert(match_history).execute()
        
        if match_data.is_match:
            # Create or update product_match record
            # This would be implemented based on your specific needs
            pass
        
        return {
            'message': f"Match {'confirmed' if match_data.is_match else 'rejected'} successfully",
            'match_history_id': result.data[0]['id'] if result.data else None
        }
        
    except Exception as e:
        logger.error(f"Error confirming match: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm match")


@router.get("/analytics")
async def get_matching_analytics(request: Request):
    """
    Get analytics on product matching performance
    
    Returns statistics on match rates, confidence distribution, and retailer coverage
    """
    try:
        analyzer = ProductMatchAnalyzer()
        
        # Get comprehensive analytics
        price_comparison = await analyzer.generate_price_comparison_report()
        competitiveness = await analyzer.get_retailer_competitiveness_analysis()
        
        # Get match history stats
        supabase: SupabaseService = request.app.state.supabase
        
        history_result = supabase.client.table('match_history').select('*').execute()
        history_data = history_result.data if history_result.data else []
        
        # Calculate match statistics
        total_reviews = len(history_data)
        confirmed_matches = len([h for h in history_data if h.get('match_status') == 'confirmed'])
        rejected_matches = len([h for h in history_data if h.get('match_status') == 'rejected'])
        
        # Get confidence distribution
        confidence_distribution = {
            'high_confidence': len([h for h in history_data if h.get('match_score', 0) >= 0.8]),
            'medium_confidence': len([h for h in history_data if 0.5 <= h.get('match_score', 0) < 0.8]),
            'low_confidence': len([h for h in history_data if h.get('match_score', 0) < 0.5])
        }
        
        return {
            'match_statistics': {
                'total_products_matched': price_comparison['total_matches'],
                'retailer_coverage': price_comparison['retailer_coverage'],
                'average_price_variance': price_comparison['price_variance_stats']['average_variance'],
                'max_price_variance': price_comparison['price_variance_stats']['max_variance']
            },
            'manual_review_stats': {
                'total_reviews': total_reviews,
                'confirmed_matches': confirmed_matches,
                'rejected_matches': rejected_matches,
                'accuracy_rate': (confirmed_matches / total_reviews * 100) if total_reviews > 0 else 0
            },
            'confidence_distribution': confidence_distribution,
            'top_savings_opportunities': price_comparison['savings_opportunities'][:10],
            'retailer_competitiveness': competitiveness,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting matching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


def _get_match_recommendation(confidence: float) -> str:
    """Get recommendation based on confidence score"""
    if confidence >= 0.90:
        return "These products are almost certainly the same. Recommend automatic matching."
    elif confidence >= 0.70:
        return "These products are likely the same. Recommend manual review before matching."
    elif confidence >= 0.50:
        return "These products might be the same. Requires careful manual review."
    else:
        return "These products are likely different. Not recommended for matching."


async def _process_products_batch(products: List[Dict], supabase: SupabaseService):
    """Process a batch of products for matching (background task)"""
    try:
        matcher = ProductMatcher()
        processed = 0
        
        for product in products:
            try:
                # Generate product hash
                normalizer = TextNormalizer()
                normalized_name = normalizer.normalize(product['name'])
                normalized_brand = normalizer.normalize(product.get('brand', ''))
                
                product_hash = hashlib.md5(
                    f"{normalized_name}_{normalized_brand}_{product.get('unified_category', '')}".encode()
                ).hexdigest()
                
                # Update product with hash
                supabase.client.table('products').update({
                    'product_hash': product_hash,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', product['id']).execute()
                
                processed += 1
                
                # Add small delay to avoid overwhelming the system
                if processed % 10 == 0:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error processing product {product['id']}: {str(e)}")
                continue
        
        logger.info(f"Batch processing completed: {processed}/{len(products)} products processed")
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")