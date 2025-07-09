#!/usr/bin/env python3
"""
Improved matching algorithm that prevents same-retailer matches
and enhances confidence scoring
"""
import os
import sys
import asyncio
from datetime import datetime
import logging
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.services.supabase_service import SupabaseService
from src.models.matching_models import MatchingAlgorithmConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_existing_matches():
    """Update existing matches to remove same-retailer matches"""
    try:
        # Initialize Supabase
        supabase = SupabaseService()
        
        # Get all product matches
        logger.info("Fetching existing product matches...")
        matches_result = supabase.client.table('product_matches').select('*').execute()
        matches = matches_result.data if matches_result.data else []
        
        removed_count = 0
        updated_count = 0
        
        for match in matches:
            # Check if this is a same-retailer match
            master_id = match.get('master_product_id')
            matched_ids = match.get('matched_product_ids', [])
            
            if not master_id or not matched_ids:
                continue
            
            # Get all products
            all_product_ids = [master_id] + matched_ids
            products_result = supabase.client.table('products').select('id, retailer_code').in_('id', all_product_ids).execute()
            products = products_result.data if products_result.data else []
            
            # Create a map of product ID to retailer code
            product_retailers = {p['id']: p['retailer_code'] for p in products}
            
            # Check if all products are from the same retailer
            retailer_codes = set(product_retailers.values())
            
            if len(retailer_codes) == 1:
                # Same retailer match - remove it
                logger.info(f"Removing same-retailer match {match['id']} (all products from {list(retailer_codes)[0]})")
                supabase.client.table('product_matches').delete().eq('id', match['id']).execute()
                removed_count += 1
            else:
                # Valid cross-retailer match - ensure confidence is set
                if not match.get('match_confidence'):
                    # Update with default confidence
                    update_data = {
                        'match_confidence': 0.85,
                        'updated_at': datetime.now().isoformat()
                    }
                    supabase.client.table('product_matches').update(update_data).eq('id', match['id']).execute()
                    updated_count += 1
        
        logger.info(f"Removed {removed_count} same-retailer matches")
        logger.info(f"Updated {updated_count} matches with confidence scores")
        
    except Exception as e:
        logger.error(f"Error updating existing matches: {str(e)}")
        raise


async def run_enhanced_matching(category: Optional[str] = None, limit: int = 100):
    """Run enhanced matching algorithm on unmatched products"""
    try:
        # Initialize services
        supabase = SupabaseService()
        
        # Configure advanced matcher
        config = MatchingAlgorithmConfig(
            min_confidence_threshold=0.6,
            require_same_category=True,
            price_variance_threshold=0.5,  # 50% price variance allowed
            use_ml_matching=False,  # Can enable if sentence-transformers is installed
            min_name_similarity=0.6,
            min_brand_similarity=0.8
        )
        
        matcher = AdvancedProductMatcher(supabase, config)
        
        # Get unmatched products
        logger.info(f"Fetching unmatched products{f' in category {category}' if category else ''}...")
        
        # First, get products that aren't already in matches
        existing_matches = supabase.client.table('product_matches').select('master_product_id, matched_product_ids').execute()
        matched_product_ids = set()
        
        for match in (existing_matches.data or []):
            if match.get('master_product_id'):
                matched_product_ids.add(match['master_product_id'])
            for pid in match.get('matched_product_ids', []):
                matched_product_ids.add(pid)
        
        # Get products not in matches
        query = supabase.client.table('products').select('*')
        
        if category:
            query = query.eq('category', category)
        
        query = query.limit(limit * 2)  # Get extra to account for already matched products
        products_result = query.execute()
        
        # Filter out already matched products
        products = [p for p in (products_result.data or []) if p['id'] not in matched_product_ids][:limit]
        
        if not products:
            logger.info("No unmatched products found")
            return
        
        logger.info(f"Processing {len(products)} unmatched products...")
        
        # Run matching algorithm
        match_groups = await matcher.match_products(products)
        
        logger.info(f"Found {len(match_groups)} potential match groups")
        
        # Save match groups to database
        saved_count = 0
        for group in match_groups:
            try:
                # Prepare match data
                match_data = {
                    'master_product_id': group.matched_products[0].product_id,
                    'matched_product_ids': [p.product_id for p in group.matched_products[1:]],
                    'normalized_name': group.canonical_product.normalized_name,
                    'normalized_brand': group.canonical_product.brand,
                    'unified_category': group.canonical_product.category,
                    'match_confidence': group.confidence.overall,
                    'match_details': {
                        'name_match': group.confidence.name_match,
                        'brand_match': group.confidence.brand_match,
                        'spec_match': group.confidence.spec_match,
                        'price_consistency': group.confidence.price_consistency,
                        'algorithm_version': group.match_metadata.algorithm_version,
                        'created_at': group.created_at.isoformat()
                    },
                    'key_specifications': group.canonical_product.specifications.dict() if group.canonical_product.specifications else {},
                    'price_range_min': group.price_analysis.current_best_price if group.price_analysis else 0,
                    'price_range_max': max([p.current_price for p in group.matched_products]),
                    'price_variance_percentage': group.price_analysis.savings_opportunity.percentage if group.price_analysis and group.price_analysis.savings_opportunity else 0,
                    'best_price_retailer': group.price_analysis.current_best_retailer if group.price_analysis else None,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Insert into database
                result = supabase.client.table('product_matches').insert(match_data).execute()
                if result.data:
                    saved_count += 1
                    logger.info(f"Saved match group: {group.canonical_product.normalized_name} ({len(group.matched_products)} products)")
                
            except Exception as e:
                logger.error(f"Error saving match group: {str(e)}")
                continue
        
        logger.info(f"Successfully saved {saved_count} match groups to database")
        
    except Exception as e:
        logger.error(f"Error running enhanced matching: {str(e)}")
        raise


async def main():
    """Main execution function"""
    logger.info("Starting improved matching algorithm...")
    
    # First, clean up existing same-retailer matches
    logger.info("\n1. Cleaning up same-retailer matches...")
    await update_existing_matches()
    
    # Run enhanced matching on new products
    logger.info("\n2. Running enhanced matching algorithm...")
    await run_enhanced_matching(limit=200)
    
    logger.info("\nMatching algorithm improvements complete!")


if __name__ == "__main__":
    asyncio.run(main())