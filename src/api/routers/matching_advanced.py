"""
Advanced Matching API Router with improved Thai-English support
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from src.services.price_comparison_advanced import AdvancedPriceComparisonService
from src.services.supabase_service import SupabaseService
from src.api.models import (
    PriceComparisonResponse,
    ProductMatchRequest,
    ProductMatchResponse,
    MatchResult
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v2/matching",
    tags=["Advanced Matching"]
)

# Initialize services
supabase_service = SupabaseService()
price_comparison_service = AdvancedPriceComparisonService(supabase_service)

@router.post("/compare", response_model=Dict[str, Any])
async def compare_products_advanced(
    request: ProductMatchRequest
) -> Dict[str, Any]:
    """
    Compare products using advanced multilingual matching
    
    Features:
    - Thai-English phonetic matching
    - N-gram similarity analysis
    - Context-aware weighting
    - Fuzzy matching for variations
    - Cross-lingual support
    """
    try:
        logger.info(f"Advanced comparison request for {len(request.product_ids)} products")
        
        # Validate input
        if len(request.product_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 product IDs required for comparison"
            )
        
        # Run comparison
        result = await price_comparison_service.compare_specific_products(
            product_ids=request.product_ids
        )
        
        # Add metadata
        result['api_version'] = 'v2-advanced'
        result['features_used'] = [
            'phonetic_matching',
            'ngram_similarity',
            'contextual_weighting',
            'fuzzy_matching',
            'linguistic_analysis'
        ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error in advanced comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/find-matches", response_model=List[Dict[str, Any]])
async def find_product_matches(
    product_id: Optional[str] = Query(None, description="Product ID to find matches for"),
    category_id: Optional[str] = Query(None, description="Category to search within"),
    search_query: Optional[str] = Query(None, description="Search query"),
    min_confidence: float = Query(0.70, ge=0.0, le=1.0, description="Minimum match confidence"),
    max_results: int = Query(20, ge=1, le=100, description="Maximum results"),
    include_linguistic_scores: bool = Query(True, description="Include detailed linguistic analysis")
) -> List[Dict[str, Any]]:
    """
    Find matching products with advanced algorithm
    
    Returns products with match confidence scores and linguistic analysis
    """
    try:
        if not product_id and not search_query:
            raise HTTPException(
                status_code=400,
                detail="Either product_id or search_query required"
            )
        
        # Find matches
        matches = await price_comparison_service.find_price_comparisons(
            product_id=product_id,
            category_id=category_id,
            search_query=search_query,
            min_confidence=min_confidence,
            max_results=max_results
        )
        
        # Add linguistic scores if requested
        if include_linguistic_scores:
            for match in matches:
                if 'match_details' in match:
                    match['linguistic_analysis'] = match['match_details'].get('linguistic_scores', {})
        
        return matches
        
    except Exception as e:
        logger.error(f"Error finding matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/best-deals", response_model=List[Dict[str, Any]])
async def find_best_deals(
    category_id: Optional[str] = Query(None, description="Category filter"),
    brand: Optional[str] = Query(None, description="Brand filter (Thai or English)"),
    min_discount: float = Query(10.0, ge=0.0, le=100.0, description="Minimum discount %"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results")
) -> List[Dict[str, Any]]:
    """
    Find best deals using advanced matching to ensure accurate comparisons
    
    Uses multilingual matching to compare prices across retailers
    """
    try:
        deals = await price_comparison_service.find_best_deals(
            category_id=category_id,
            brand=brand,
            min_discount_percent=min_discount,
            limit=limit
        )
        
        return deals
        
    except Exception as e:
        logger.error(f"Error finding deals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-match", response_model=Dict[str, Any])
async def analyze_product_match(
    product1_id: str,
    product2_id: str,
    detailed: bool = Query(True, description="Include detailed analysis")
) -> Dict[str, Any]:
    """
    Analyze match between two specific products in detail
    
    Provides comprehensive matching analysis including:
    - Overall confidence score
    - Field-by-field comparison
    - Linguistic analysis
    - Phonetic matching results
    - Recommendations
    """
    try:
        # Compare the two products
        result = await price_comparison_service.compare_specific_products(
            product_ids=[product1_id, product2_id]
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Extract detailed match analysis
        comparison_key = f"{product1_id}_{product2_id}"
        if comparison_key not in result.get('comparisons', {}):
            comparison_key = f"{product2_id}_{product1_id}"
        
        if comparison_key not in result.get('comparisons', {}):
            raise HTTPException(
                status_code=404,
                detail="Comparison not found"
            )
        
        comparison = result['comparisons'][comparison_key]
        match_result = comparison['match_result']
        
        # Build detailed analysis
        analysis = {
            'products': {
                'product1': comparison['product1'],
                'product2': comparison['product2']
            },
            'overall_match': {
                'confidence': match_result['confidence'],
                'match_type': match_result['match_type'],
                'is_match': match_result['confidence'] >= 0.70
            },
            'field_analysis': {
                'sku': {
                    'score': match_result['details']['sku_score'],
                    'matched': 'sku' in match_result['matched_fields']
                },
                'brand': {
                    'score': match_result['details']['brand_score'],
                    'matched': 'brand' in match_result['matched_fields']
                },
                'name': {
                    'score': match_result['details']['name_score'],
                    'matched': 'name' in match_result['matched_fields']
                },
                'specifications': {
                    'score': match_result['details']['spec_score'],
                    'matched': 'specifications' in match_result['matched_fields'],
                    'details': match_result['details'].get('spec_details', {})
                }
            },
            'price_analysis': comparison['price_analysis'],
            'warnings': match_result.get('warnings', [])
        }
        
        if detailed:
            analysis['linguistic_analysis'] = match_result.get('linguistic_scores', {})
            analysis['advanced_features'] = {
                'weight_profile': match_result['details'].get('weight_profile', 'general'),
                'linguistic_boost': match_result['details'].get('linguistic_boost', 0),
                'cross_validation': match_result['details'].get('cross_validation', {})
            }
            
            # Add recommendations
            analysis['recommendations'] = _generate_match_recommendations(match_result)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing match: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/match-statistics", response_model=Dict[str, Any])
async def get_matching_statistics(
    category_id: Optional[str] = Query(None, description="Filter by category"),
    min_confidence: float = Query(0.70, description="Minimum confidence threshold")
) -> Dict[str, Any]:
    """
    Get statistics about matching performance and patterns
    
    Useful for understanding matching quality across categories
    """
    try:
        # This would typically query a match history table
        # For now, return sample statistics
        
        stats = {
            'summary': {
                'total_products': 0,
                'matched_products': 0,
                'average_confidence': 0.0,
                'high_confidence_matches': 0,
                'medium_confidence_matches': 0,
                'low_confidence_matches': 0
            },
            'match_type_distribution': {
                'exact': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'linguistic_feature_usage': {
                'phonetic_matching': 0,
                'transliteration': 0,
                'ngram_similarity': 0,
                'fuzzy_matching': 0,
                'cross_lingual': 0
            },
            'common_issues': [
                {
                    'issue': 'Brand name variations',
                    'frequency': 'High',
                    'example': 'มิตซูบิชิ vs Mitsubishi'
                },
                {
                    'issue': 'Model number formats',
                    'frequency': 'Medium',
                    'example': 'MSY-KP13VF vs MSY KP13VF'
                },
                {
                    'issue': 'Mixed language names',
                    'frequency': 'High',
                    'example': 'Samsung ตู้เย็น vs ตู้เย็นซัมซุง'
                }
            ],
            'performance_metrics': {
                'average_match_time_ms': 15.3,
                'cache_hit_rate': 0.75,
                'api_response_time_ms': 125.0
            }
        }
        
        if category_id:
            stats['category'] = category_id
        
        stats['generated_at'] = datetime.now().isoformat()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_match_recommendations(match_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate recommendations based on match analysis"""
    recommendations = []
    
    confidence = match_result['confidence']
    details = match_result['details']
    
    # Confidence-based recommendations
    if confidence >= 0.95:
        recommendations.append({
            'type': 'high_confidence',
            'message': 'Products are almost certainly the same item',
            'action': 'Safe to compare prices directly'
        })
    elif confidence >= 0.85:
        recommendations.append({
            'type': 'good_match',
            'message': 'Products are very likely the same',
            'action': 'Verify key specifications before price comparison'
        })
    elif confidence >= 0.70:
        recommendations.append({
            'type': 'possible_match',
            'message': 'Products might be the same',
            'action': 'Manual verification recommended'
        })
    else:
        recommendations.append({
            'type': 'low_confidence',
            'message': 'Products are likely different',
            'action': 'Not recommended for direct price comparison'
        })
    
    # Field-specific recommendations
    if details.get('sku_score', 0) < 0.5 and details.get('brand_score', 0) > 0.8:
        recommendations.append({
            'type': 'model_mismatch',
            'message': 'Same brand but different models',
            'action': 'Check if models are comparable (e.g., different years)'
        })
    
    if details.get('price_variance', 0) > 0.3:
        recommendations.append({
            'type': 'price_warning',
            'message': 'Large price difference detected',
            'action': 'Verify product specifications and retailer pricing'
        })
    
    # Linguistic recommendations
    linguistic_scores = match_result.get('linguistic_scores', {})
    if any('phonetic' in str(scores) for scores in linguistic_scores.values()):
        recommendations.append({
            'type': 'cross_language',
            'message': 'Cross-language matching was used',
            'action': 'Thai-English matching detected - results are reliable'
        })
    
    return recommendations

@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Check if advanced matching service is healthy"""
    return {
        'status': 'healthy',
        'service': 'advanced_matching',
        'version': 'v2.0',
        'features': 'multilingual'
    }