#!/usr/bin/env python3
"""
Enhanced Price Comparisons API v3 with Advanced Product Matching

This API endpoint uses the new enhanced product matcher with BTU validation,
model series validation, and category-specific rules to eliminate false positives.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime, timedelta

# Import our enhanced matching system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.btu_validator import BTUValidator
from utils.model_validator import ModelValidator
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/price-comparisons-v3", tags=["Enhanced Price Comparisons"])

class EnhancedPriceComparisonService:
    """Service for enhanced price comparisons with advanced validation."""
    
    def __init__(self):
        self.btu_validator = BTUValidator(tolerance=0.05)  # 5% BTU tolerance
        self.model_validator = ModelValidator(strict_series_matching=True)
        
    def get_enhanced_comparisons(self, supabase: SupabaseService, 
                               limit: int = 50, offset: int = 0,
                               min_savings: float = 0.0, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get price comparisons with enhanced validation to prevent false positives.
        
        Args:
            supabase: Supabase service instance
            limit: Number of comparisons to return
            offset: Pagination offset
            min_savings: Minimum savings amount filter
            category: Optional category filter
            
        Returns:
            Enhanced price comparison data with validation details
        """
        logger.info(f"Getting enhanced price comparisons: limit={limit}, offset={offset}, "
                   f"min_savings={min_savings}, category={category}")
        
        try:
            # Get product matches with their associated products
            query = supabase.client.table('product_matches').select(
                'id, normalized_name, match_confidence, unified_category, '
                'master_product_id, matched_product_ids, '
                'price_range_min, price_range_max, '
                'updated_at'
            )
            
            if category:
                query = query.eq('unified_category', category)
                
            # Get matches ordered by potential savings
            matches_result = query.order('price_range_max', desc=True).execute()
            matches = matches_result.data if matches_result.data else []
            
            # Get all unique product IDs
            all_product_ids = []
            for match in matches:
                if match.get('master_product_id'):
                    all_product_ids.append(match['master_product_id'])
                if match.get('matched_product_ids'):
                    all_product_ids.extend(match['matched_product_ids'])
            
            # Fetch all products in one query for efficiency
            products_dict = {}
            if all_product_ids:
                products_query = supabase.client.table('products').select('*').in_('id', all_product_ids)
                products_result = products_query.execute()
                if products_result.data:
                    products_dict = {p['id']: p for p in products_result.data}
            
            enhanced_comparisons = []
            validation_stats = {
                'total_matches_processed': 0,
                'valid_matches': 0,
                'rejected_btu_mismatch': 0,
                'rejected_model_series_mismatch': 0,
                'rejected_category_mismatch': 0,
                'rejected_low_confidence': 0
            }
            
            for match in matches:
                validation_stats['total_matches_processed'] += 1
                
                # Get products for this match
                retailer_prices = []
                match_products = []
                
                # Add master product
                if match.get('master_product_id') and match['master_product_id'] in products_dict:
                    product = products_dict[match['master_product_id']]
                    match_products.append(product)
                    retailer_prices.append(self._format_retailer_price(product))
                
                # Add matched products
                if match.get('matched_product_ids'):
                    for product_id in match['matched_product_ids']:
                        if product_id in products_dict:
                            product = products_dict[product_id]
                            match_products.append(product)
                            retailer_prices.append(self._format_retailer_price(product))
                
                # Skip if insufficient products
                if len(match_products) < 2:
                    continue
                
                # Enhanced validation
                validation_result = self._validate_match_enhanced(match_products, match)
                
                if not validation_result['is_valid']:
                    # Track rejection reasons
                    rejection_reason = validation_result['rejection_reason']
                    if 'btu' in rejection_reason.lower():
                        validation_stats['rejected_btu_mismatch'] += 1
                    elif 'model series' in rejection_reason.lower():
                        validation_stats['rejected_model_series_mismatch'] += 1
                    elif 'category' in rejection_reason.lower():
                        validation_stats['rejected_category_mismatch'] += 1
                    else:
                        validation_stats['rejected_low_confidence'] += 1
                    
                    logger.debug(f"Rejected match {match['id']}: {rejection_reason}")
                    continue
                
                # Calculate real-time prices and analysis
                current_prices = [float(rp['price']) for rp in retailer_prices if rp['price'] > 0]
                if len(current_prices) < 2:
                    continue
                    
                min_price = min(current_prices)
                max_price = max(current_prices)
                savings_amount = max_price - min_price
                
                # Apply savings filter
                if savings_amount < min_savings:
                    continue
                
                validation_stats['valid_matches'] += 1
                
                # Create enhanced comparison record
                enhanced_comparison = {
                    'matchId': match['id'],
                    'productName': match['normalized_name'],
                    'brand': match_products[0].get('brand', 'Unknown'),
                    'category': match.get('unified_category', 'Unknown'),
                    'matchConfidence': validation_result['enhanced_confidence'],
                    'originalConfidence': match.get('match_confidence', 0.0),
                    'validationStatus': validation_result['validation_status'],
                    'specifications': validation_result['specifications'],
                    'retailerPrices': sorted(retailer_prices, key=lambda x: x['price']),
                    'priceAnalysis': {
                        'minPrice': min_price,
                        'maxPrice': max_price,
                        'savingsAmount': savings_amount,
                        'savingsPercentage': (savings_amount / min_price * 100) if min_price > 0 else 0,
                        'bestRetailer': next((rp['retailerCode'] for rp in retailer_prices if rp['price'] == min_price), None),
                        'priceRange': f"฿{min_price:,.0f} - ฿{max_price:,.0f}"
                    },
                    'validationDetails': validation_result['validation_details'],
                    'lastUpdated': match.get('updated_at', datetime.now().isoformat())
                }
                
                enhanced_comparisons.append(enhanced_comparison)
                
                # Apply pagination
                if len(enhanced_comparisons) >= offset + limit:
                    break
            
            # Apply pagination
            paginated_comparisons = enhanced_comparisons[offset:offset + limit]
            
            result = {
                'comparisons': paginated_comparisons,
                'total': len(enhanced_comparisons),
                'page': (offset // limit) + 1 if limit > 0 else 1,
                'pageSize': limit,
                'totalPages': (len(enhanced_comparisons) + limit - 1) // limit if limit > 0 else 1,
                'validationStats': validation_stats,
                'filters': {
                    'limit': limit,
                    'offset': offset,
                    'minSavings': min_savings,
                    'category': category,
                    'enhancedValidation': True
                }
            }
            
            logger.info(f"Enhanced comparisons: {len(paginated_comparisons)} returned, "
                       f"{validation_stats['valid_matches']} valid out of "
                       f"{validation_stats['total_matches_processed']} processed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting enhanced comparisons: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get enhanced comparisons: {str(e)}")
    
    def _validate_match_enhanced(self, products: List[Dict[str, Any]], match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply enhanced validation to a product match.
        
        Args:
            products: List of product dictionaries
            match: Match record from database
            
        Returns:
            Validation result with enhanced confidence and details
        """
        validation_result = {
            'is_valid': True,
            'rejection_reason': '',
            'enhanced_confidence': match.get('match_confidence', 0.0),
            'validation_status': 'passed',
            'specifications': {},
            'validation_details': {}
        }
        
        if len(products) < 2:
            validation_result['is_valid'] = False
            validation_result['rejection_reason'] = "Insufficient products for comparison"
            return validation_result
        
        category = match.get('unified_category', '').lower()
        
        # Air conditioner specific validations
        if 'air_conditioner' in category or 'air-conditioner' in category:
            # BTU validation
            btu_validation = self._validate_btu_compatibility(products)
            validation_result['validation_details']['btu_validation'] = btu_validation
            
            if not btu_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['rejection_reason'] = f"BTU validation failed: {btu_validation['reason']}"
                validation_result['validation_status'] = 'rejected_btu_mismatch'
                return validation_result
            
            # Model series validation
            model_validation = self._validate_model_compatibility(products)
            validation_result['validation_details']['model_validation'] = model_validation
            
            if not model_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['rejection_reason'] = f"Model validation failed: {model_validation['reason']}"
                validation_result['validation_status'] = 'rejected_model_series_mismatch'
                return validation_result
            
            # Extract air conditioner specifications
            validation_result['specifications'] = self._extract_air_conditioner_specs(products)
            
            # Boost confidence for air conditioners with perfect BTU and model matches
            if (btu_validation.get('variance_percentage', 100) < 2 and 
                model_validation.get('match_type') == 'exact_match'):
                validation_result['enhanced_confidence'] = min(1.0, validation_result['enhanced_confidence'] + 0.1)
                validation_result['validation_status'] = 'enhanced_match'
        
        # Category validation
        categories = [p.get('category', '').lower() for p in products]
        unique_categories = set(categories)
        
        if len(unique_categories) > 1:
            # Check for misclassified air conditioners
            air_conditioner_indicators = ['แอร์', 'air conditioner', 'btu', 'บีทียู', 'inverter', 'carrier', 'daikin', 'haier']
            product_names = [p.get('name', '').lower() for p in products]
            
            has_ac_indicators = any(
                any(indicator in name for indicator in air_conditioner_indicators)
                for name in product_names
            )
            
            if 'television' in unique_categories and has_ac_indicators:
                logger.warning(f"Detected misclassified air conditioner in match {match.get('id')}")
                validation_result['validation_details']['category_correction'] = {
                    'original_categories': list(unique_categories),
                    'corrected_category': 'air_conditioner',
                    'reason': 'Detected air conditioner misclassified as television'
                }
            else:
                validation_result['is_valid'] = False
                validation_result['rejection_reason'] = f"Category mismatch: {list(unique_categories)}"
                validation_result['validation_status'] = 'rejected_category_mismatch'
                return validation_result
        
        # Confidence threshold check
        min_confidence = 0.7  # Base threshold
        if 'air_conditioner' in category:
            min_confidence = 0.85  # Stricter for air conditioners
        
        if validation_result['enhanced_confidence'] < min_confidence:
            validation_result['is_valid'] = False
            validation_result['rejection_reason'] = f"Confidence {validation_result['enhanced_confidence']:.3f} below threshold {min_confidence}"
            validation_result['validation_status'] = 'rejected_low_confidence'
            return validation_result
        
        return validation_result
    
    def _validate_btu_compatibility(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate BTU compatibility for air conditioners."""
        if len(products) < 2:
            return {'is_valid': True, 'reason': 'Insufficient products for BTU validation'}
        
        # Use our BTU validator
        product1 = {'name': products[0].get('name', '')}
        product2 = {'name': products[1].get('name', '')}
        
        is_valid, reason, details = self.btu_validator.validate_btu_match(product1, product2)
        
        return {
            'is_valid': is_valid,
            'reason': reason,
            'btu_values': [details.get('btu1'), details.get('btu2')],
            'variance_percentage': details.get('variance_percentage', 0)
        }
    
    def _validate_model_compatibility(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate model compatibility."""
        if len(products) < 2:
            return {'is_valid': True, 'reason': 'Insufficient products for model validation'}
        
        # Use our model validator
        product1 = {
            'name': products[0].get('name', ''),
            'brand': products[0].get('brand', '')
        }
        product2 = {
            'name': products[1].get('name', ''),
            'brand': products[1].get('brand', '')
        }
        
        is_valid, reason, details = self.model_validator.validate_model_match(product1, product2)
        
        match_type = 'different_models'
        if 'exact model match' in reason.lower():
            match_type = 'exact_match'
        elif 'same series' in reason.lower():
            match_type = 'same_series'
        
        return {
            'is_valid': is_valid,
            'reason': reason,
            'model_info': {
                'model1': details['model1'],
                'model2': details['model2']
            },
            'match_type': match_type
        }
    
    def _extract_air_conditioner_specs(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract air conditioner specifications."""
        specs = {}
        
        for product in products:
            name = product.get('name', '')
            
            # Extract BTU
            btu = self.btu_validator.extract_btu(name)
            if btu:
                specs['btu'] = str(btu)
                break
        
        # Extract other features
        combined_names = ' '.join([p.get('name', '') for p in products]).lower()
        
        if 'inverter' in combined_names:
            specs['inverter'] = True
        if 'wifi' in combined_names or 'wi-fi' in combined_names:
            specs['wifi'] = True
        if 'smart' in combined_names:
            specs['smart'] = True
        
        return specs
    
    def _format_retailer_price(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Format product as retailer price entry."""
        return {
            'retailerCode': product.get('retailer_code', 'Unknown'),
            'retailerName': self._get_retailer_name(product.get('retailer_code', '')),
            'productId': product.get('id'),
            'productName': product.get('name', ''),
            'price': float(product.get('current_price', 0)),
            'originalPrice': float(product.get('original_price', 0)) if product.get('original_price') else None,
            'discount': product.get('discount_percentage'),
            'url': product.get('url', ''),
            'image': product.get('image_url'),
            'inStock': product.get('in_stock', True),
            'lastUpdated': product.get('updated_at', datetime.now().isoformat())
        }
    
    def _get_retailer_name(self, retailer_code: str) -> str:
        """Get full retailer name from code."""
        retailer_names = {
            'HP': 'HomePro',
            'TWD': 'Thai Watsadu',
            'GH': 'Global House',
            'DH': 'DoHome',
            'BT': 'Boonthavorn',
            'MH': 'MegaHome'
        }
        return retailer_names.get(retailer_code, retailer_code)


# Initialize service
enhanced_service = EnhancedPriceComparisonService()

@router.get("/detailed-comparisons-enhanced")
async def get_detailed_comparisons_enhanced(
    limit: int = Query(50, ge=1, le=100, description="Number of comparisons to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    min_savings: float = Query(0.0, ge=0, description="Minimum savings amount filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    supabase: SupabaseService = Depends(lambda: SupabaseService())
):
    """
    Get detailed price comparisons with enhanced validation.
    
    This endpoint uses advanced product matching with:
    - BTU validation for air conditioners (5% tolerance)
    - Model series validation to prevent false positives
    - Category-specific rules and thresholds
    - Real-time price calculations
    
    Returns only validated matches that pass all quality checks.
    """
    try:
        result = enhanced_service.get_enhanced_comparisons(
            supabase=supabase,
            limit=limit,
            offset=offset,
            min_savings=min_savings,
            category=category
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced comparisons endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validation-stats")
async def get_validation_statistics(
    supabase: SupabaseService = Depends(lambda: SupabaseService())
):
    """
    Get validation statistics showing the impact of enhanced matching.
    """
    try:
        # Get a sample of comparisons to analyze
        result = enhanced_service.get_enhanced_comparisons(
            supabase=supabase,
            limit=100,
            offset=0
        )
        
        validation_stats = result.get('validationStats', {})
        
        # Calculate improvement metrics
        total_processed = validation_stats.get('total_matches_processed', 0)
        valid_matches = validation_stats.get('valid_matches', 0)
        
        improvement_stats = {
            'total_matches_analyzed': total_processed,
            'valid_matches_after_enhancement': valid_matches,
            'false_positive_prevention_rate': (total_processed - valid_matches) / total_processed if total_processed > 0 else 0,
            'quality_improvement': {
                'btu_mismatches_prevented': validation_stats.get('rejected_btu_mismatch', 0),
                'model_series_mismatches_prevented': validation_stats.get('rejected_model_series_mismatch', 0),
                'category_mismatches_prevented': validation_stats.get('rejected_category_mismatch', 0),
                'low_confidence_matches_filtered': validation_stats.get('rejected_low_confidence', 0)
            },
            'match_quality_score': valid_matches / total_processed if total_processed > 0 else 0
        }
        
        return improvement_stats
        
    except Exception as e:
        logger.error(f"Error getting validation statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for enhanced matching system."""
    return {
        'status': 'healthy',
        'version': '3.0.0',
        'features': [
            'BTU validation (5% tolerance)',
            'Model series validation',
            'Category-specific rules',
            'Real-time price calculations',
            'Enhanced confidence scoring'
        ],
        'timestamp': datetime.now().isoformat()
    }