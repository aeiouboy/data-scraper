#!/usr/bin/env python3
"""
Migrate existing product_matches to new match_groups structure
"""
import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_matches():
    """Migrate existing product_matches to new structure"""
    supabase = SupabaseService()
    
    logger.info("Starting migration of product_matches to match_groups...")
    
    try:
        # Get existing matches
        matches_result = supabase.client.table('product_matches')\
            .select('*')\
            .execute()
        
        if not matches_result.data:
            logger.info("No existing matches to migrate")
            return
        
        matches = matches_result.data
        logger.info(f"Found {len(matches)} matches to migrate")
        
        migrated_count = 0
        
        for match in matches:
            try:
                # Create match group
                match_group_data = {
                    'canonical_name': match.get('normalized_name', 'Unknown'),
                    'canonical_brand': match.get('normalized_brand', match.get('unified_brand', 'Unknown')),
                    'category': match.get('unified_category', 'Unknown'),
                    'product_type': match.get('unified_category', 'Unknown'),
                    'key_features': match.get('key_specifications', {}).get('features', []),
                    'specifications': match.get('key_specifications', {}),
                    'created_at': match.get('created_at'),
                    'updated_at': match.get('updated_at')
                }
                
                # Insert match group
                group_result = supabase.client.table('match_groups')\
                    .insert(match_group_data)\
                    .execute()
                
                if not group_result.data:
                    logger.error(f"Failed to create match group for {match['id']}")
                    continue
                
                match_group_id = group_result.data[0]['id']
                
                # Create confidence record
                confidence_data = {
                    'match_group_id': match_group_id,
                    'overall_score': match.get('match_confidence', 0.7),
                    'name_match_score': 0.8,  # Default values
                    'brand_match_score': 0.9,
                    'spec_match_score': 0.7,
                    'price_consistency_score': 0.8,
                    'user_validation_score': 0,
                    'confidence_level': 'high' if match.get('match_confidence', 0.7) > 0.8 else 'medium',
                    'factors': match.get('match_criteria', {})
                }
                
                supabase.client.table('match_confidence')\
                    .insert(confidence_data)\
                    .execute()
                
                # Map products to match group
                all_product_ids = [match['master_product_id']] + match.get('matched_product_ids', [])
                
                for product_id in all_product_ids:
                    # Get product details
                    product_result = supabase.client.table('products')\
                        .select('retailer_code')\
                        .eq('id', product_id)\
                        .single()\
                        .execute()
                    
                    if product_result.data:
                        mapping_data = {
                            'product_id': product_id,
                            'match_group_id': match_group_id,
                            'retailer_code': product_result.data['retailer_code'],
                            'is_primary': product_id == match['master_product_id']
                        }
                        
                        supabase.client.table('product_match_mapping')\
                            .insert(mapping_data)\
                            .execute()
                
                # Create price analysis cache
                if match.get('price_range_min') and match.get('price_range_max'):
                    analysis_data = {
                        'match_group_id': match_group_id,
                        'analysis_type': 'current',
                        'current_best_price': match.get('price_range_min'),
                        'current_best_retailer': match.get('best_price_retailer'),
                        'savings_amount': match.get('price_range_max', 0) - match.get('price_range_min', 0),
                        'savings_percentage': match.get('price_variance_percentage', 0),
                        'volatility_level': 'moderate',
                        'volatility_score': 0.5,
                        'data': {
                            'migrated': True,
                            'original_match_id': match['id']
                        },
                        'expires_at': (datetime.now().isoformat())
                    }
                    
                    supabase.client.table('price_analysis_cache')\
                        .insert(analysis_data)\
                        .execute()
                
                migrated_count += 1
                logger.info(f"Migrated match {match['id']} -> group {match_group_id}")
                
            except Exception as e:
                logger.error(f"Error migrating match {match['id']}: {str(e)}")
                continue
        
        logger.info(f"Migration completed! Migrated {migrated_count} out of {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


async def verify_migration():
    """Verify the migration was successful"""
    supabase = SupabaseService()
    
    logger.info("\nVerifying migration...")
    
    # Count records in new tables
    tables = [
        'match_groups',
        'match_confidence',
        'product_match_mapping',
        'price_analysis_cache'
    ]
    
    for table in tables:
        result = supabase.client.table(table)\
            .select('id', count='exact')\
            .execute()
        
        logger.info(f"{table}: {result.count} records")
    
    # Check a sample match group
    sample_result = supabase.client.table('match_group_details')\
        .select('*')\
        .limit(1)\
        .execute()
    
    if sample_result.data:
        logger.info("\nSample match group:")
        group = sample_result.data[0]
        logger.info(f"  Name: {group['canonical_name']}")
        logger.info(f"  Brand: {group['canonical_brand']}")
        logger.info(f"  Category: {group['category']}")
        logger.info(f"  Retailers: {group['retailer_count']}")
        logger.info(f"  Price range: ฿{group['min_price']} - ฿{group['max_price']}")
        logger.info(f"  Confidence: {group['confidence_score']} ({group['confidence_level']})")


async def main():
    """Main migration function"""
    logger.info("Match Groups Migration Tool")
    logger.info("=" * 50)
    
    # Run migration
    await migrate_matches()
    
    # Verify results
    await verify_migration()
    
    logger.info("\nMigration complete!")
    logger.info("You can now use the new /api/v2/price-comparisons endpoints")


if __name__ == "__main__":
    asyncio.run(main()