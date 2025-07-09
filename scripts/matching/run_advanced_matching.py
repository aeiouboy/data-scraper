#!/usr/bin/env python3
"""
Run advanced matching to create match groups across retailers
"""
import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.models.matching_models import MatchingAlgorithmConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def save_match_group_to_db(group, supabase):
    """Save a match group to the database"""
    # Save match group
    group_data = {
        'canonical_name': group.canonical_product.normalized_name,
        'canonical_brand': group.canonical_product.brand,
        'category': group.canonical_product.category,
        'product_type': group.canonical_product.product_type,
        'key_features': group.canonical_product.key_features,
        'created_at': datetime.now().isoformat()
    }
    
    result = supabase.client.table('match_groups')\
        .insert(group_data)\
        .execute()
    
    if result.data:
        group_id = result.data[0]['id']
        
        # Save confidence
        confidence_data = {
            'match_group_id': group_id,
            'overall_score': group.confidence.overall,
            'name_match_score': group.confidence.name_match,
            'brand_match_score': group.confidence.brand_match,
            'spec_match_score': group.confidence.spec_match,
            'price_consistency_score': group.confidence.price_consistency,
            'confidence_level': group.confidence_level.value
        }
        
        supabase.client.table('match_confidence')\
            .insert(confidence_data)\
            .execute()
        
        # Map products
        for product in group.matched_products:
            mapping_data = {
                'product_id': product.product_id,
                'match_group_id': group_id,
                'retailer_code': product.retailer_code
            }
            
            supabase.client.table('product_match_mapping')\
                .insert(mapping_data)\
                .execute()


async def run_matching_for_category(category_name: str, search_terms: list):
    """Run matching for a specific category across retailers"""
    supabase = SupabaseService()
    
    # Configure matcher with relaxed settings for demo
    config = MatchingAlgorithmConfig(
        min_name_similarity=0.6,  # Lower threshold for demo
        min_brand_similarity=0.7,
        use_ml_matching=False,  # Disable ML for now
        price_variance_threshold=0.7,  # Allow 70% price difference
        require_same_category=False  # Relax category requirement
    )
    
    matcher = AdvancedProductMatcher(supabase, config)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing category: {category_name}")
    logger.info(f"{'='*60}")
    
    # Collect products from all retailers
    all_products = []
    
    for term in search_terms:
        # Get products from each retailer
        for retailer in ['HP', 'TWD']:
            result = await supabase.search_products(
                query=term,
                filters={'retailer_code': retailer},
                limit=50
            )
            
            if result and 'products' in result:
                products = result['products']
                logger.info(f"Found {len(products)} {retailer} products for '{term}'")
                all_products.extend(products)
    
    # Remove duplicates
    unique_products = {p['id']: p for p in all_products}.values()
    products = list(unique_products)
    
    logger.info(f"\nTotal unique products: {len(products)}")
    
    # Group by retailer
    by_retailer = {}
    for p in products:
        retailer = p.get('retailer_code', 'Unknown')
        if retailer not in by_retailer:
            by_retailer[retailer] = []
        by_retailer[retailer].append(p)
    
    for retailer, prods in by_retailer.items():
        logger.info(f"  {retailer}: {len(prods)} products")
    
    # Run matching
    logger.info("\nRunning advanced matching algorithm...")
    match_groups = await matcher.match_products(products)
    
    logger.info(f"Created {len(match_groups)} match groups")
    
    # Save to database
    saved_count = 0
    for group in match_groups:
        try:
            # Save match group directly
            await save_match_group_to_db(group, supabase)
            saved_count += 1
            
            logger.info(f"\n✅ Saved match group:")
            logger.info(f"   Product: {group.canonical_product.normalized_name[:60]}...")
            logger.info(f"   Brand: {group.canonical_product.brand}")
            logger.info(f"   Confidence: {group.confidence.overall:.2f}")
            logger.info(f"   Retailers: {[p.retailer_code for p in group.matched_products]}")
            if group.price_analysis.savings_opportunity:
                logger.info(f"   💰 Savings: ฿{group.price_analysis.savings_opportunity.amount:,.0f}")
            
        except Exception as e:
            logger.error(f"Error saving match group: {str(e)}")
    
    logger.info(f"\nSaved {saved_count} match groups to database")
    
    return saved_count


async def create_manual_matches():
    """Create some manual matches for demonstration"""
    supabase = SupabaseService()
    
    logger.info("\n" + "="*60)
    logger.info("Creating manual matches for demonstration")
    logger.info("="*60)
    
    # Example: Match similar air conditioners
    # Get HP air conditioners
    hp_result = await supabase.search_products(
        query="แอร์",
        filters={'retailer_code': 'HP'},
        limit=10
    )
    
    # Get TWD air conditioners
    twd_result = await supabase.search_products(
        query="แอร์",
        filters={'retailer_code': 'TWD'},
        limit=10
    )
    
    if hp_result and twd_result:
        hp_products = hp_result.get('products', [])
        twd_products = twd_result.get('products', [])
        
        logger.info(f"Found {len(hp_products)} HP and {len(twd_products)} TWD air conditioners")
        
        # Create matches based on brand
        matches_created = 0
        
        for hp_product in hp_products[:5]:  # Limit to first 5
            hp_brand = (hp_product.get('brand', '') or '').lower().strip()
            if not hp_brand:
                continue
            
            for twd_product in twd_products:
                twd_brand = (twd_product.get('brand', '') or '').lower().strip()
                
                # Simple brand matching
                if hp_brand and twd_brand and (
                    hp_brand == twd_brand or 
                    hp_brand in twd_brand or 
                    twd_brand in hp_brand
                ):
                    # Create match group
                    try:
                        # Insert match group
                        match_group_data = {
                            'canonical_name': f"{hp_brand} Air Conditioner",
                            'canonical_brand': hp_brand.upper(),
                            'category': 'air_conditioner',
                            'product_type': 'air_conditioner',
                            'key_features': ['แอร์', 'เครื่องปรับอากาศ'],
                            'created_at': datetime.now().isoformat()
                        }
                        
                        group_result = supabase.client.table('match_groups')\
                            .insert(match_group_data)\
                            .execute()
                        
                        if group_result.data:
                            group_id = group_result.data[0]['id']
                            
                            # Create confidence
                            confidence_data = {
                                'match_group_id': group_id,
                                'overall_score': 0.75,
                                'name_match_score': 0.7,
                                'brand_match_score': 0.9,
                                'spec_match_score': 0.6,
                                'price_consistency_score': 0.8,
                                'confidence_level': 'high'
                            }
                            
                            supabase.client.table('match_confidence')\
                                .insert(confidence_data)\
                                .execute()
                            
                            # Map products
                            for product, retailer in [(hp_product, 'HP'), (twd_product, 'TWD')]:
                                mapping_data = {
                                    'product_id': product['id'],
                                    'match_group_id': group_id,
                                    'retailer_code': retailer,
                                    'is_primary': retailer == 'HP'
                                }
                                
                                supabase.client.table('product_match_mapping')\
                                    .insert(mapping_data)\
                                    .execute()
                            
                            matches_created += 1
                            logger.info(f"✅ Created match: {hp_brand} - HP vs TWD")
                            break  # Only one match per HP product
                            
                    except Exception as e:
                        logger.error(f"Error creating match: {str(e)}")
        
        logger.info(f"\nCreated {matches_created} manual matches")


async def main():
    """Run matching for all categories"""
    logger.info("Advanced Product Matching Runner")
    logger.info("="*60)
    
    # Categories to process
    categories = [
        {
            'name': 'Air Conditioners',
            'terms': ['แอร์', 'เครื่องปรับอากาศ', 'air']
        },
        {
            'name': 'Refrigerators',
            'terms': ['ตู้เย็น', 'refrigerator', 'ตู้แช่']
        },
        {
            'name': 'Televisions',
            'terms': ['ทีวี', 'โทรทัศน์', 'tv', 'television']
        }
    ]
    
    total_matches = 0
    
    # Run automated matching
    for category in categories:
        count = await run_matching_for_category(category['name'], category['terms'])
        total_matches += count
    
    # If no automated matches, create manual ones
    if total_matches == 0:
        logger.info("\nNo automated matches found. Creating manual matches...")
        await create_manual_matches()
    
    # Verify results
    logger.info("\n" + "="*60)
    logger.info("Verification")
    logger.info("="*60)
    
    # Create supabase instance for verification
    supabase = SupabaseService()
    
    # Check match groups
    result = supabase.client.table('match_groups')\
        .select('id', count='exact')\
        .execute()
    
    logger.info(f"Total match groups in database: {result.count}")
    
    # Show sample matches
    sample_result = supabase.client.table('match_group_details')\
        .select('*')\
        .limit(5)\
        .execute()
    
    if sample_result.data:
        logger.info("\nSample match groups:")
        for group in sample_result.data:
            logger.info(f"\n  {group['canonical_name']}")
            logger.info(f"    Brand: {group['canonical_brand']}")
            logger.info(f"    Retailers: {group['retailer_count']}")
            logger.info(f"    Price range: ฿{group['min_price']:,.0f} - ฿{group['max_price']:,.0f}")
            logger.info(f"    Confidence: {group['confidence_score']:.2f}")
            if group['savings_amount']:
                logger.info(f"    💰 Savings: ฿{group['savings_amount']:,.0f}")


if __name__ == "__main__":
    asyncio.run(main())