"""
Advanced price comparison API endpoints with improved matching and analysis
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from src.services.supabase_service import SupabaseService
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.services.price_analysis_engine import PriceAnalysisEngine
from src.models.matching_models import (
    MatchingRequest,
    MatchingResponse,
    ProductMatchGroup,
    MatchingAlgorithmConfig,
    PriceAnalysis
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/price-comparisons", tags=["price_comparisons_v2"])


@router.post("/analyze", response_model=MatchingResponse)
async def analyze_price_comparisons(
    request: MatchingRequest,
    background_tasks: BackgroundTasks
):
    """
    Advanced price comparison analysis with ML-powered matching
    
    - Matches products across retailers using semantic similarity
    - Calculates confidence scores with detailed breakdown
    - Provides price volatility analysis
    - Identifies savings opportunities
    """
    try:
        supabase = SupabaseService()
        matcher = AdvancedProductMatcher(supabase, request.algorithm_config)
        
        # Get products based on request criteria
        products = []
        
        if request.product_ids:
            # Get specific products
            for product_id in request.product_ids:
                result = await supabase.get_product(product_id)
                if result:
                    products.append(result)
        else:
            # Search for products
            filters = {}
            if request.retailer_codes:
                filters['retailer_codes'] = request.retailer_codes
            if request.category:
                filters['category'] = request.category
            
            search_result = await supabase.search_products(
                query="",
                filters=filters,
                limit=100
            )
            if search_result and 'products' in search_result:
                products = search_result['products']
        
        if not products:
            return MatchingResponse(
                match_groups=[],
                total_groups=0,
                total_products=0,
                processing_time_ms=0,
                algorithm_version="2.0"
            )
        
        # Perform matching
        start_time = datetime.now()
        match_groups = await matcher.match_products(products)
        
        # Filter by minimum confidence
        if request.min_confidence > 0:
            match_groups = [
                mg for mg in match_groups 
                if mg.confidence.overall >= request.min_confidence
            ]
        
        # Cache results in background
        background_tasks.add_task(
            cache_match_results,
            match_groups,
            None  # No user context for now
        )
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return MatchingResponse(
            match_groups=match_groups,
            total_groups=len(match_groups),
            total_products=len(products),
            processing_time_ms=processing_time,
            algorithm_version="2.0"
        )
        
    except Exception as e:
        logger.error(f"Error in price comparison analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match-groups/{group_id}")
async def get_match_group_details(
    group_id: str,
    include_history: bool = Query(False, description="Include price history"),
    history_days: int = Query(30, description="Days of history to include")
):
    """Get detailed information about a specific match group"""
    try:
        supabase = SupabaseService()
        
        # Get match group from database
        result = supabase.client.table('match_groups')\
            .select('*, match_confidence(*), match_group_stats(*)')\
            .eq('id', group_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Match group not found")
        
        match_group = result.data
        
        # Get matched products
        mapping_result = supabase.client.table('product_match_mapping')\
            .select('product_id, retailer_code, variant_type, variant_value')\
            .eq('match_group_id', group_id)\
            .execute()
        
        products = []
        if mapping_result.data:
            product_ids = [m['product_id'] for m in mapping_result.data]
            products_result = supabase.client.table('products')\
                .select('*')\
                .in_('id', product_ids)\
                .execute()
            
            if products_result.data:
                products = products_result.data
        
        # Get price analysis
        analysis_result = supabase.client.table('price_analysis_cache')\
            .select('*')\
            .eq('match_group_id', group_id)\
            .eq('analysis_type', 'current')\
            .gte('expires_at', datetime.now().isoformat())\
            .single()\
            .execute()
        
        price_analysis = analysis_result.data if analysis_result.data else None
        
        # Include price history if requested
        price_history = None
        if include_history:
            # This would fetch historical price data
            price_history = await get_price_history_for_group(
                group_id, 
                history_days,
                supabase
            )
        
        return {
            "match_group": match_group,
            "products": products,
            "price_analysis": price_analysis,
            "price_history": price_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match group details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-groups/{group_id}/validate")
async def validate_match_group(
    group_id: str,
    validation: Dict[str, Any]
):
    """Submit user validation for a match group"""
    try:
        supabase = SupabaseService()
        
        # Record user feedback
        feedback_data = {
            'match_group_id': group_id,
            'is_correct_match': validation.get('is_correct', True),
            'confidence_override': validation.get('confidence_override'),
            'feedback_reason': validation.get('reason'),
            'user_id': None,  # No user context for now
            'created_at': datetime.now().isoformat()
        }
        
        if 'product1_id' in validation and 'product2_id' in validation:
            feedback_data['product1_id'] = validation['product1_id']
            feedback_data['product2_id'] = validation['product2_id']
        
        result = supabase.client.table('user_match_feedback')\
            .insert(feedback_data)\
            .execute()
        
        # Update match confidence if needed
        if validation.get('update_confidence', False):
            await update_match_confidence(group_id, supabase)
        
        return {"status": "success", "feedback_id": result.data[0]['id']}
        
    except Exception as e:
        logger.error(f"Error validating match group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/savings-opportunities")
async def get_savings_opportunities(
    min_savings: float = Query(100, description="Minimum savings amount"),
    category: Optional[str] = Query(None, description="Filter by category"),
    confidence_threshold: float = Query(0.7, description="Minimum match confidence"),
    limit: int = Query(50, description="Maximum results"),
    offset: int = Query(0, description="Pagination offset")
):
    """Get top savings opportunities across all matched products"""
    try:
        supabase = SupabaseService()
        
        # Query match groups with savings
        query = supabase.client.table('match_group_details')\
            .select('*')\
            .gte('confidence_score', confidence_threshold)\
            .gte('savings_amount', min_savings)\
            .order('savings_amount', desc=True)\
            .range(offset, offset + limit - 1)
        
        if category:
            query = query.eq('category', category)
        
        result = query.execute()
        
        opportunities = []
        for group in result.data:
            opportunities.append({
                'match_group_id': group['id'],
                'product_name': group['canonical_name'],
                'brand': group['canonical_brand'],
                'category': group['category'],
                'savings_amount': group['savings_amount'],
                'savings_percentage': group['savings_percentage'],
                'best_price': group['current_best_price'],
                'best_retailer': group['current_best_retailer'],
                'price_range': {
                    'min': group['min_price'],
                    'max': group['max_price']
                },
                'retailer_count': group['retailer_count'],
                'confidence_score': group['confidence_score'],
                'confidence_level': group['confidence_level']
            })
        
        # Get total count
        count_result = supabase.client.table('match_group_details')\
            .select('id', count='exact')\
            .gte('confidence_score', confidence_threshold)\
            .gte('savings_amount', min_savings)\
            .execute()
        
        return {
            'opportunities': opportunities,
            'total': count_result.count,
            'offset': offset,
            'limit': limit
        }
        
    except Exception as e:
        logger.error(f"Error getting savings opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price-monitoring/subscribe")
async def subscribe_to_price_monitoring(
    subscription: Dict[str, Any]
):
    """Subscribe to price change notifications for a match group"""
    try:
        supabase = SupabaseService()
        
        # Validate match group exists
        group_result = supabase.client.table('match_groups')\
            .select('id')\
            .eq('id', subscription['match_group_id'])\
            .single()\
            .execute()
        
        if not group_result.data:
            raise HTTPException(status_code=404, detail="Match group not found")
        
        # Create subscription
        sub_data = {
            'match_group_id': subscription['match_group_id'],
            'user_id': None,  # No user context for now
            'email': subscription.get('email', None),
            'threshold_percentage': subscription.get('threshold_percentage', 5.0),
            'threshold_amount': subscription.get('threshold_amount'),
            'monitor_type': subscription.get('monitor_type', 'drop'),
            'notification_channels': subscription.get('channels', ['email']),
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
        
        if 'expires_in_days' in subscription:
            sub_data['expires_at'] = (
                datetime.now() + timedelta(days=subscription['expires_in_days'])
            ).isoformat()
        
        result = supabase.client.table('price_monitoring_subscriptions')\
            .insert(sub_data)\
            .execute()
        
        return {
            "status": "success",
            "subscription_id": result.data[0]['id'],
            "message": "Price monitoring subscription created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating price monitoring subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/price-volatility")
async def get_price_volatility_analytics(
    category: Optional[str] = Query(None),
    days: int = Query(30, description="Days to analyze")
):
    """Get price volatility analytics across categories and retailers"""
    try:
        supabase = SupabaseService()
        engine = PriceAnalysisEngine(supabase)
        
        # Get volatility data
        volatility_data = await engine.analyze_market_volatility(
            category=category,
            days=days
        )
        
        return volatility_data
        
    except Exception as e:
        logger.error(f"Error getting volatility analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve-matching")
async def trigger_matching_improvement(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None),
    force: bool = Query(False, description="Force re-matching of existing groups")
):
    """Trigger background job to improve product matching"""
    try:
        # Add background task to process matching improvements
        background_tasks.add_task(
            improve_product_matching,
            category=category,
            force=force
        )
        
        return {
            "status": "processing",
            "message": "Matching improvement job started",
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Error triggering matching improvement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def cache_match_results(match_groups: List[ProductMatchGroup], user_id: Optional[str]):
    """Cache match results in database"""
    try:
        supabase = SupabaseService()
        
        for group in match_groups:
            # Store match group
            group_data = {
                'canonical_name': group.canonical_product.normalized_name,
                'canonical_brand': group.canonical_product.brand,
                'category': group.canonical_product.category,
                'product_type': group.canonical_product.product_type,
                'key_features': group.canonical_product.key_features,
                'specifications': group.canonical_product.specifications.dict() if group.canonical_product.specifications else None
            }
            
            # Insert or update match group
            group_result = supabase.client.table('match_groups')\
                .upsert(group_data, on_conflict='canonical_name,canonical_brand,category')\
                .execute()
            
            if group_result.data:
                group_id = group_result.data[0]['id']
                
                # Store confidence
                confidence_data = {
                    'match_group_id': group_id,
                    'overall_score': group.confidence.overall,
                    'name_match_score': group.confidence.name_match,
                    'brand_match_score': group.confidence.brand_match,
                    'spec_match_score': group.confidence.spec_match,
                    'price_consistency_score': group.confidence.price_consistency,
                    'user_validation_score': group.confidence.user_validation,
                    'confidence_level': group.confidence_level.value,
                    'factors': [f.dict() for f in group.match_metadata.match_features]
                }
                
                supabase.client.table('match_confidence')\
                    .upsert(confidence_data, on_conflict='match_group_id')\
                    .execute()
                
                # Store price analysis
                if group.price_analysis:
                    analysis_data = {
                        'match_group_id': group_id,
                        'analysis_type': 'current',
                        'current_best_price': group.price_analysis.current_best_price,
                        'current_best_retailer': group.price_analysis.current_best_retailer,
                        'savings_amount': group.price_analysis.savings_opportunity.amount if group.price_analysis.savings_opportunity else None,
                        'savings_percentage': group.price_analysis.savings_opportunity.percentage if group.price_analysis.savings_opportunity else None,
                        'volatility_level': group.price_analysis.volatility.value,
                        'volatility_score': group.price_analysis.volatility_score,
                        'data': group.price_analysis.dict(),
                        'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
                    }
                    
                    supabase.client.table('price_analysis_cache')\
                        .upsert(analysis_data, on_conflict='match_group_id,analysis_type')\
                        .execute()
                
    except Exception as e:
        logger.error(f"Error caching match results: {str(e)}")


async def update_match_confidence(group_id: str, supabase: SupabaseService):
    """Update match confidence based on user feedback"""
    try:
        # Get all feedback for this group
        feedback_result = supabase.client.table('user_match_feedback')\
            .select('*')\
            .eq('match_group_id', group_id)\
            .execute()
        
        if feedback_result.data:
            # Calculate new confidence based on feedback
            positive_feedback = sum(1 for f in feedback_result.data if f['is_correct_match'])
            total_feedback = len(feedback_result.data)
            
            if total_feedback > 0:
                user_validation_score = positive_feedback / total_feedback
                
                # Update confidence
                supabase.client.table('match_confidence')\
                    .update({'user_validation_score': user_validation_score})\
                    .eq('match_group_id', group_id)\
                    .execute()
                
    except Exception as e:
        logger.error(f"Error updating match confidence: {str(e)}")


async def get_price_history_for_group(group_id: str, days: int, supabase: SupabaseService):
    """Get price history for all products in a match group"""
    try:
        # Get all products in the group
        mapping_result = supabase.client.table('product_match_mapping')\
            .select('product_id')\
            .eq('match_group_id', group_id)\
            .execute()
        
        if not mapping_result.data:
            return []
        
        product_ids = [m['product_id'] for m in mapping_result.data]
        
        # Get price history for each product
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        history_result = supabase.client.table('price_history')\
            .select('*')\
            .in_('product_id', product_ids)\
            .gte('timestamp', since_date)\
            .order('timestamp', desc=True)\
            .execute()
        
        return history_result.data if history_result.data else []
        
    except Exception as e:
        logger.error(f"Error getting price history: {str(e)}")
        return []


async def improve_product_matching(category: Optional[str], force: bool):
    """Background task to improve product matching"""
    try:
        logger.info(f"Starting matching improvement for category: {category}")
        supabase = SupabaseService()
        matcher = AdvancedProductMatcher(supabase)
        
        # Get products to match
        filters = {}
        if category:
            filters['category'] = category
        
        # Get unmatched or low-confidence products
        if not force:
            # Query products not in any match group or with low confidence
            pass  # Complex query implementation
        
        result = await supabase.search_products(
            query="",
            filters=filters,
            limit=500
        )
        
        if result and 'products' in result:
            products = result['products']
            
            # Run matching in batches
            batch_size = 50
            for i in range(0, len(products), batch_size):
                batch = products[i:i+batch_size]
                match_groups = await matcher.match_products(batch)
                
                # Cache results
                await cache_match_results(match_groups, None)
                
                logger.info(f"Processed batch {i//batch_size + 1}, found {len(match_groups)} matches")
        
        logger.info("Matching improvement completed")
        
    except Exception as e:
        logger.error(f"Error in matching improvement: {str(e)}")