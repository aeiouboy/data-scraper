#!/usr/bin/env python3
"""
Create product matches for refrigerators and TVs with proper structure
"""

import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_product_matches():
    """Create matches for refrigerators and TVs"""
    supabase = SupabaseService()
    
    logger.info("🚀 Creating product matches for multiple categories...")
    
    # First, let's create some refrigerator matches
    logger.info("\n📦 Creating refrigerator matches...")
    
    # Get refrigerator products
    twd_fridge = await supabase.search_products(
        query="ตู้เย็น",
        filters={"retailer_code": "TWD"},
        limit=10
    )
    
    if twd_fridge and twd_fridge.get('products'):
        twd_fridges = twd_fridge['products']
        logger.info(f"Found {len(twd_fridges)} TWD refrigerators")
        
        # Create some sample matches within TWD (since HP doesn't have fridges)
        for i in range(0, min(3, len(twd_fridges) - 1)):
            product1 = twd_fridges[i]
            product2 = twd_fridges[i + 1]
            
            price1 = float(product1.get('current_price', 0))
            price2 = float(product2.get('current_price', 0))
            
            if price1 and price2:
                min_price = min(price1, price2)
                max_price = max(price1, price2)
                variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                
                match_data = {
                    'master_product_id': product1['id'],
                    'matched_product_ids': [product2['id']],
                    'match_confidence': 0.75,
                    'match_criteria': {
                        'algorithm_version': '1.0',
                        'confidence_scores': [0.75],
                        'matched_retailers': ['TWD'],
                        'matching_features': ['category', 'type']
                    },
                    'normalized_name': product1['name'].lower(),
                    'normalized_brand': (product1.get('brand', '') or '').upper(),
                    'unified_category': 'refrigerator',
                    'key_specifications': {
                        'type': 'refrigerator'
                    },
                    'price_range_min': min_price,
                    'price_range_max': max_price,
                    'best_price_retailer': 'TWD',
                    'price_variance_percentage': round(variance, 2)
                }
                
                try:
                    result = supabase.client.table('product_matches')\
                        .insert(match_data)\
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ Created refrigerator match: {product1['name'][:40]}...")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
    
    # Now create TV matches between TWD and HP
    logger.info("\n📺 Creating TV matches...")
    
    twd_tv = await supabase.search_products(
        query="tv",
        filters={"retailer_code": "TWD"},
        limit=10
    )
    
    hp_tv = await supabase.search_products(
        query="tv", 
        filters={"retailer_code": "HP"},
        limit=10
    )
    
    if twd_tv and hp_tv:
        twd_tvs = twd_tv.get('products', [])
        hp_tvs = hp_tv.get('products', [])
        
        logger.info(f"Found {len(twd_tvs)} TWD TVs and {len(hp_tvs)} HP TVs")
        
        matches_created = 0
        for twd_product in twd_tvs[:5]:
            twd_brand = (twd_product.get('brand', '') or '').lower()
            
            for hp_product in hp_tvs:
                hp_brand = (hp_product.get('brand', '') or '').lower()
                
                # Simple brand matching
                if twd_brand and hp_brand and twd_brand == hp_brand:
                    price1 = float(twd_product.get('current_price', 0))
                    price2 = float(hp_product.get('current_price', 0))
                    
                    if price1 and price2:
                        min_price = min(price1, price2)
                        max_price = max(price1, price2)
                        variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                        
                        match_data = {
                            'master_product_id': twd_product['id'],
                            'matched_product_ids': [hp_product['id']],
                            'match_confidence': 0.65,
                            'match_criteria': {
                                'algorithm_version': '1.0',
                                'confidence_scores': [0.65],
                                'matched_retailers': ['TWD', 'HP'],
                                'matching_features': ['brand', 'category']
                            },
                            'normalized_name': twd_product['name'].lower(),
                            'normalized_brand': twd_brand.upper(),
                            'unified_category': 'television',
                            'key_specifications': {
                                'type': 'tv',
                                'brand': twd_brand.upper()
                            },
                            'price_range_min': min_price,
                            'price_range_max': max_price,
                            'best_price_retailer': 'TWD' if price1 < price2 else 'HP',
                            'price_variance_percentage': round(variance, 2)
                        }
                        
                        try:
                            result = supabase.client.table('product_matches')\
                                .insert(match_data)\
                                .execute()
                            
                            if result.data:
                                matches_created += 1
                                logger.info(f"✅ Created TV match: {twd_brand.upper()}")
                                logger.info(f"   TWD: ฿{price1:,.0f} vs HP: ฿{price2:,.0f} (variance: {variance:.1f}%)")
                                break
                        except Exception as e:
                            logger.error(f"Error: {str(e)}")
        
        logger.info(f"\nCreated {matches_created} TV matches")
    
    # Also create some more variety - washing machines
    logger.info("\n🌀 Creating washing machine category...")
    
    # Search for washing machines (even if we don't have many)
    search_terms = ["washing", "washer", "ซักผ้า"]
    for term in search_terms:
        hp_wash = await supabase.search_products(
            query=term,
            filters={"retailer_code": "HP"},
            limit=5
        )
        
        if hp_wash and hp_wash.get('products'):
            products = hp_wash['products']
            logger.info(f"Found {len(products)} HP products with term '{term}'")
            
            # Create a sample match
            if len(products) >= 2:
                p1 = products[0]
                p2 = products[1]
                
                price1 = float(p1.get('current_price', 0))
                price2 = float(p2.get('current_price', 0))
                
                if price1 and price2:
                    match_data = {
                        'master_product_id': p1['id'],
                        'matched_product_ids': [p2['id']],
                        'match_confidence': 0.60,
                        'match_criteria': {
                            'algorithm_version': '1.0',
                            'confidence_scores': [0.60],
                            'matched_retailers': ['HP'],
                            'matching_features': ['category']
                        },
                        'normalized_name': p1['name'].lower(),
                        'normalized_brand': (p1.get('brand', '') or '').upper(),
                        'unified_category': 'washing_machine',
                        'key_specifications': {},
                        'price_range_min': min(price1, price2),
                        'price_range_max': max(price1, price2),
                        'best_price_retailer': 'HP',
                        'price_variance_percentage': abs(price1 - price2) / min(price1, price2) * 100
                    }
                    
                    try:
                        result = supabase.client.table('product_matches')\
                            .insert(match_data)\
                            .execute()
                        
                        if result.data:
                            logger.info(f"✅ Created washing machine match")
                            break
                    except Exception as e:
                        logger.error(f"Error: {str(e)}")
    
    # Final check
    logger.info("\n📊 Final Status:")
    
    all_matches = supabase.client.table('product_matches')\
        .select('unified_category')\
        .execute()
    
    if all_matches.data:
        category_counts = {}
        for match in all_matches.data:
            cat = match.get('unified_category', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        logger.info("Categories in product_matches:")
        for cat, count in sorted(category_counts.items()):
            logger.info(f"  {cat}: {count} matches")

async def main():
    await create_product_matches()

if __name__ == "__main__":
    asyncio.run(main())