"""
Ultra-strict product matching API endpoints
Provides maximum accuracy matching with strict validation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from src.utils.product_matcher_ultra_strict import UltraStrictProductMatcher, MatchResult
from src.services.supabase_service import SupabaseService
from src.models.product import Product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/matching-ultra-strict", tags=["Ultra-Strict Matching"])

# Initialize services
ultra_strict_matcher = UltraStrictProductMatcher()
db_service = SupabaseService()

# Pydantic models for request/response
class UltraStrictMatchRequest(BaseModel):
    """Request model for ultra-strict matching"""
    product_id: str = Field(..., description="Product ID to find matches for")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence threshold")
    category_filter: Optional[str] = Field(None, description="Filter by category")
    retailer_exclusions: Optional[List[str]] = Field(None, description="Retailers to exclude")

class TestMatchRequest(BaseModel):
    """Request model for testing a match between two products"""
    product1_id: str = Field(..., description="First product ID")
    product2_id: str = Field(..., description="Second product ID")
    category: Optional[str] = Field(None, description="Product category for matching")

class UltraStrictMatchDetails(BaseModel):
    """Ultra-strict specific match details"""
    model_exact_match: bool = Field(description="Whether models match exactly")
    brand_exact_match: bool = Field(description="Whether brands match exactly")
    specification_validation: bool = Field(description="Whether specs passed validation")
    rejection_reason: Optional[str] = Field(None, description="Primary rejection reason")
    validation_score: float = Field(description="Overall validation score")
    model_similarity: float = Field(description="Model similarity score")
    brand_similarity: float = Field(description="Brand similarity score")
    early_rejection: bool = Field(description="Whether rejected in early validation")

class UltraStrictMatchResult(BaseModel):
    """Ultra-strict match result model"""
    matched_product: Dict[str, Any] = Field(description="Matched product details")
    confidence: float = Field(description="Match confidence score")
    match_type: str = Field(description="Type of match (exact, high, medium, low, none)")
    matched_fields: List[str] = Field(description="Fields that contributed to the match")
    warnings: List[str] = Field(description="Match warnings")
    rejection_reasons: List[str] = Field(description="Reasons for rejection")
    ultra_strict_details: UltraStrictMatchDetails = Field(description="Ultra-strict specific details")
    score_breakdown: Dict[str, float] = Field(description="Detailed score breakdown")
    price_comparison: Optional[Dict[str, Any]] = Field(None, description="Price comparison details")

class UltraStrictMatchResponse(BaseModel):
    """Response model for ultra-strict matching"""
    query_product: Dict[str, Any] = Field(description="Original product details")
    matches: List[UltraStrictMatchResult] = Field(description="List of matches")
    total_candidates: int = Field(description="Total candidates evaluated")
    matches_found: int = Field(description="Number of matches found")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    matcher_config: Dict[str, Any] = Field(description="Matcher configuration used")

@router.post("/find-matches", response_model=UltraStrictMatchResponse)
async def find_ultra_strict_matches(
    request: UltraStrictMatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Find ultra-strict matches for a product with maximum accuracy
    
    This endpoint uses the ultra-strict matcher to find product matches with:
    - Strict model number validation
    - Enhanced brand matching
    - Tight specification tolerances
    - High confidence thresholds
    """
    start_time = datetime.now()
    
    try:
        # Get the target product
        target_product = await db_service.get_product_by_id(request.product_id)
        if not target_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get potential matches from database
        potential_matches = await _get_potential_matches(
            target_product, 
            request.category_filter,
            request.retailer_exclusions
        )
        
        if not potential_matches:
            return UltraStrictMatchResponse(
                query_product=_product_to_dict(target_product),
                matches=[],
                total_candidates=0,
                matches_found=0,
                processing_time_ms=0,
                matcher_config=_get_matcher_config()
            )
        
        # Convert target product to dict for matching
        target_product_dict = _product_to_dict(target_product)
        
        # Find matches using ultra-strict matcher
        matches = []
        for candidate in potential_matches:
            candidate_dict = _product_to_dict(candidate)
            
            # Perform ultra-strict matching
            match_result = ultra_strict_matcher.match_products(
                target_product_dict,
                candidate_dict,
                target_product.unified_category or target_product.category or 'default'
            )
            
            # Only include matches above threshold
            if match_result.confidence >= request.confidence_threshold:
                ultra_strict_result = _create_ultra_strict_result(
                    candidate, match_result, target_product
                )
                matches.append(ultra_strict_result)
        
        # Sort by confidence descending
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Limit results
        matches = matches[:request.max_results]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log the matching operation
        logger.info(f"Ultra-strict matching completed: {len(matches)} matches found from {len(potential_matches)} candidates")
        
        # Background task for analytics
        background_tasks.add_task(
            _log_matching_analytics,
            target_product.id,
            len(potential_matches),
            len(matches),
            processing_time
        )
        
        return UltraStrictMatchResponse(
            query_product=target_product_dict,
            matches=matches,
            total_candidates=len(potential_matches),
            matches_found=len(matches),
            processing_time_ms=int(processing_time),
            matcher_config=_get_matcher_config()
        )
        
    except Exception as e:
        logger.error(f"Error in ultra-strict matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@router.post("/test-match", response_model=UltraStrictMatchResult)
async def test_ultra_strict_match(request: TestMatchRequest):
    """
    Test ultra-strict matching between two specific products
    
    This endpoint allows testing the ultra-strict matcher with two specific products
    to understand why they match or don't match.
    """
    try:
        # Get both products
        product1 = await db_service.get_product_by_id(request.product1_id)
        product2 = await db_service.get_product_by_id(request.product2_id)
        
        if not product1 or not product2:
            raise HTTPException(status_code=404, detail="One or both products not found")
        
        # Convert to dicts for matching
        product1_dict = _product_to_dict(product1)
        product2_dict = _product_to_dict(product2)
        
        # Perform ultra-strict matching
        category = request.category or product1.unified_category or product1.category or 'default'
        match_result = ultra_strict_matcher.match_products(
            product1_dict,
            product2_dict,
            category
        )
        
        # Create detailed result
        result = _create_ultra_strict_result(product2, match_result, product1)
        
        logger.info(f"Ultra-strict test match: {product1.id} vs {product2.id} = {match_result.confidence:.3f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in ultra-strict test match: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test match failed: {str(e)}")

@router.get("/config")
async def get_ultra_strict_config():
    """Get ultra-strict matcher configuration"""
    return {
        "matcher_type": "ultra-strict",
        "version": "1.0.0",
        "thresholds": {
            "exact": 0.99,
            "high": 0.90,
            "medium": 0.80,
            "low": 0.70,
            "minimum": 0.60
        },
        "weights": {
            "sku": 0.45,
            "brand": 0.20,
            "name": 0.10,
            "specs": 0.20,
            "category": 0.05
        },
        "tolerances": {
            "air-conditioner": {"btu": 0.02, "power": 0.03, "capacity": 0.02},
            "refrigerator": {"capacity": 0.05, "volume": 0.05},
            "default": {"size": 0.08, "capacity": 0.08, "power": 0.10}
        },
        "features": [
            "strict_model_validation",
            "enhanced_brand_matching",
            "early_rejection_checks",
            "specification_validation",
            "price_consistency_checks"
        ]
    }

# Helper functions
async def _get_potential_matches(
    target_product: Product,
    category_filter: Optional[str] = None,
    retailer_exclusions: Optional[List[str]] = None
) -> List[Product]:
    """Get potential matches from database"""
    # Build query filters
    filters = {}
    
    # Same category
    if category_filter:
        filters['unified_category'] = category_filter
    elif target_product.unified_category:
        filters['unified_category'] = target_product.unified_category
    
    # Exclude same retailer
    if target_product.retailer_code:
        filters['retailer_code__ne'] = target_product.retailer_code
    
    # Exclude specific retailers
    if retailer_exclusions:
        filters['retailer_code__not_in'] = retailer_exclusions
    
    # Get potential matches
    try:
        results = await db_service.get_products_by_filters(filters, limit=500)
        return results
    except Exception as e:
        logger.error(f"Error getting potential matches: {str(e)}")
        return []

def _product_to_dict(product: Product) -> Dict[str, Any]:
    """Convert Product model to dictionary for matching"""
    return {
        'id': product.id,
        'name': product.name,
        'brand': product.brand,
        'sku': product.sku,
        'specs': product.specifications or {},
        'category': product.unified_category or product.category,
        'price': float(product.current_price) if product.current_price else None,
        'retailer_code': product.retailer_code,
        'url': product.url
    }

def _create_ultra_strict_result(
    candidate: Product,
    match_result: MatchResult,
    target_product: Product
) -> UltraStrictMatchResult:
    """Create ultra-strict match result from match result"""
    
    # Create ultra-strict specific details
    ultra_strict_details = UltraStrictMatchDetails(
        model_exact_match=(match_result.details.get('sku_score', 0) >= 0.99),
        brand_exact_match=(match_result.details.get('brand_score', 0) >= 0.99),
        specification_validation=match_result.details.get('spec_validation', {}).get('valid', False),
        rejection_reason=match_result.rejection_reasons[0] if match_result.rejection_reasons else None,
        validation_score=match_result.confidence,
        model_similarity=match_result.details.get('sku_score', 0),
        brand_similarity=match_result.details.get('brand_score', 0),
        early_rejection=match_result.details.get('early_rejection', False)
    )
    
    # Create price comparison
    price_comparison = None
    if candidate.current_price and target_product.current_price:
        candidate_price = float(candidate.current_price)
        target_price = float(target_product.current_price)
        price_diff = candidate_price - target_price
        price_variance = abs(price_diff) / max(candidate_price, target_price)
        
        price_comparison = {
            'target_price': target_price,
            'candidate_price': candidate_price,
            'price_difference': price_diff,
            'price_variance': price_variance,
            'savings': max(0, -price_diff),
            'is_better_deal': price_diff < 0
        }
    
    return UltraStrictMatchResult(
        matched_product=_product_to_dict(candidate),
        confidence=match_result.confidence,
        match_type=match_result.match_type,
        matched_fields=match_result.matched_fields,
        warnings=match_result.warnings,
        rejection_reasons=match_result.rejection_reasons,
        ultra_strict_details=ultra_strict_details,
        score_breakdown={
            'sku_score': match_result.details.get('sku_score', 0),
            'brand_score': match_result.details.get('brand_score', 0),
            'name_score': match_result.details.get('name_score', 0),
            'spec_score': match_result.details.get('spec_score', 0),
            'category_score': match_result.details.get('category_score', 0),
            'weighted_confidence': match_result.details.get('weighted_confidence', 0),
            'model_penalty': match_result.details.get('model_penalty', 0)
        },
        price_comparison=price_comparison
    )

def _get_matcher_config() -> Dict[str, Any]:
    """Get matcher configuration"""
    return {
        "type": "ultra-strict",
        "version": "1.0.0",
        "accuracy_focus": "maximum",
        "false_positive_prevention": "strict",
        "model_validation": "enhanced",
        "brand_matching": "strict",
        "specification_tolerance": "tight"
    }

async def _log_matching_analytics(
    product_id: str,
    candidates_count: int,
    matches_count: int,
    processing_time: float
):
    """Log matching analytics for monitoring"""
    try:
        analytics_data = {
            'matcher_type': 'ultra-strict',
            'product_id': product_id,
            'candidates_evaluated': candidates_count,
            'matches_found': matches_count,
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat(),
            'match_rate': matches_count / candidates_count if candidates_count > 0 else 0
        }
        
        # Log to database or analytics service
        logger.info(f"Ultra-strict matching analytics: {analytics_data}")
        
    except Exception as e:
        logger.error(f"Error logging matching analytics: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for ultra-strict matching service"""
    return {
        "status": "healthy",
        "matcher_type": "ultra-strict",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }