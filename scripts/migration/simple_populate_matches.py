#!/usr/bin/env python3
"""
Simple script to populate product_matches table from matching_results
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def populate_product_matches():
    """Simple population script"""
    db = SupabaseService()
    
    logger.info("Getting confirmed matches...")
    
    # Get a sample of confirmed matches from our imported data
    matches = db.client.table('matching_results')\
        .select('*')\
        .eq('status', 'confirmed')\
        .eq('matching_method', 'hybrid')\
        .limit(50)\
        .execute()
    
    logger.info(f"Found {len(matches.data)} confirmed matches")
    
    product_matches_to_create = []
    processed_products = set()
    
    for match in matches.data:
        try:
            # Get source and matched product details
            source_product = db.client.table('products')\
                .select('*')\
                .eq('id', match['source_product_id'])\
                .single()\
                .execute()
                
            matched_product = db.client.table('products')\
                .select('*')\
                .eq('id', match['matched_product_id'])\
                .single()\
                .execute()
            
            if not source_product.data or not matched_product.data:
                continue
                
            source = source_product.data
            matched = matched_product.data
            
            # Create a unique key for this product comparison
            product_key = f"{source['name'][:50]}_{source['category']}"
            
            if product_key in processed_products:
                continue
            
            processed_products.add(product_key)
            
            # Calculate price comparison
            prices = [source['current_price'], matched['current_price']]
            min_price = min(prices)
            max_price = max(prices)
            
            if min_price <= 0:
                continue
                
            # Find best price retailer
            if source['current_price'] <= matched['current_price']:
                best_retailer = source['retailer_code']
            else:
                best_retailer = matched['retailer_code']
            
            # Calculate variance
            price_variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
            
            # Skip if no significant price difference
            if price_variance < 1:
                continue
                
            # Create product_matches entry
            product_match = {
                'id': str(uuid4()),
                'master_product_id': source['id'],
                'matched_product_ids': [matched['id']],
                'match_confidence': float(match['confidence_score']),
                'match_criteria': {
                    'algorithm_version': '2.0',
                    'source': 'imported_matching_results',
                    'confidence_scores': {'overall': float(match['confidence_score'])}
                },
                'normalized_name': source['name'][:150],
                'normalized_brand': source.get('brand', 'UNKNOWN')[:30],
                'unified_category': source['category'],
                'key_specifications': {},
                'price_range_min': float(min_price),
                'price_range_max': float(max_price), 
                'best_price_retailer': best_retailer,
                'price_variance_percentage': float(price_variance),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            product_matches_to_create.append(product_match)
            
            logger.info(f"Created match for: {source['name'][:60]}... ({source['retailer_code']} vs {matched['retailer_code']}) - {price_variance:.1f}% variance")
            
            if len(product_matches_to_create) >= 20:  # Limit to 20 for testing
                break
                
        except Exception as e:
            logger.error(f"Error processing match {match['id']}: {e}")
            continue
    
    if product_matches_to_create:
        logger.info(f"Inserting {len(product_matches_to_create)} product_matches...")
        
        try:
            result = db.client.table('product_matches')\
                .insert(product_matches_to_create)\
                .execute()
            
            created_count = len(result.data) if result.data else 0
            logger.info(f"✅ Created {created_count} product_matches entries")
            
        except Exception as e:
            logger.error(f"❌ Error inserting: {e}")
            # Try individual inserts
            created_count = 0
            for product_match in product_matches_to_create:
                try:
                    result = db.client.table('product_matches')\
                        .insert([product_match])\
                        .execute()
                    if result.data:
                        created_count += 1
                except Exception as e2:
                    logger.warning(f"Failed to insert individual match: {e2}")
            
            logger.info(f"✅ Created {created_count} product_matches entries individually")
    
    return len(product_matches_to_create) > 0


async def main():
    print("🔄 Populating product_matches from imported data...")
    
    try:
        success = await populate_product_matches()
        
        if success:
            print("✅ Success! Check http://localhost:3000/price-comparisons")
            return 0
        else:
            print("❌ No data was added")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))