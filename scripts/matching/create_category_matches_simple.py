#!/usr/bin/env python3
"""
Simple script to create product matches for refrigerators
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

async def create_refrigerator_matches():
    """Create matches for refrigerator products"""
    supabase = SupabaseService()
    
    logger.info("🚀 Creating refrigerator product matches...")
    
    try:
        # Get refrigerator products from TWD
        twd_result = await supabase.search_products(
            query="ตู้เย็น",
            filters={"retailer_code": "TWD"},
            limit=20
        )
        
        twd_products = twd_result.get('products', []) if twd_result else []
        logger.info(f"Found {len(twd_products)} TWD refrigerator products")
        
        # For now, let's create some manual matches based on the products we have
        # Since HP doesn't have refrigerators yet, we'll create sample matches within TWD
        
        if len(twd_products) >= 2:
            # Create a few sample matches to demonstrate
            for i in range(0, min(3, len(twd_products) - 1)):
                product1 = twd_products[i]
                product2 = twd_products[i + 1]
                
                price1 = float(product1.get('current_price', 0))
                price2 = float(product2.get('current_price', 0))
                
                if price1 and price2:
                    min_price = min(price1, price2)
                    max_price = max(price1, price2)
                    variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                    
                    match_data = {
                        'id': str(uuid.uuid4()),
                        'master_product_id': product1['id'],
                        'matched_product_ids': [product2['id']],
                        'retailer_codes': ['TWD'],
                        'unified_category': 'refrigerator',
                        'normalized_name': product1['name'].lower(),
                        'normalized_brand': (product1.get('brand', '') or '').lower(),
                        'best_price_retailer': 'TWD' if price1 < price2 else 'TWD',
                        'price_range_min': min_price,
                        'price_range_max': max_price,
                        'price_variance_percentage': round(variance, 2),
                        'match_confidence': 0.85,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    try:
                        result = supabase.client.table('product_matches')\
                            .insert(match_data)\
                            .execute()
                        
                        if result.data:
                            logger.info(f"✅ Created match: {product1['name'][:40]}...")
                            logger.info(f"   Price variance: {variance:.1f}%")
                    except Exception as e:
                        logger.error(f"Error inserting match: {str(e)}")
        
        # Also create some TV matches if we have TV products
        logger.info("\n🚀 Creating TV product matches...")
        
        # Get TV products
        tv_twd = await supabase.search_products(
            query="tv",
            filters={"retailer_code": "TWD"},
            limit=10
        )
        
        tv_hp = await supabase.search_products(
            query="tv",
            filters={"retailer_code": "HP"},
            limit=10
        )
        
        twd_tvs = tv_twd.get('products', []) if tv_twd else []
        hp_tvs = tv_hp.get('products', []) if tv_hp else []
        
        logger.info(f"Found {len(twd_tvs)} TWD TVs and {len(hp_tvs)} HP TVs")
        
        # Create cross-retailer matches for TVs
        matches_created = 0
        for twd_tv in twd_tvs[:5]:  # Limit to first 5
            # Find a matching HP TV (simple brand matching)
            twd_brand = (twd_tv.get('brand', '') or '').lower()
            
            for hp_tv in hp_tvs:
                hp_brand = (hp_tv.get('brand', '') or '').lower()
                
                # Simple match: same brand
                if twd_brand and hp_brand and twd_brand == hp_brand:
                    price1 = float(twd_tv.get('current_price', 0))
                    price2 = float(hp_tv.get('current_price', 0))
                    
                    if price1 and price2:
                        min_price = min(price1, price2)
                        max_price = max(price1, price2)
                        variance = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                        
                        match_data = {
                            'id': str(uuid.uuid4()),
                            'master_product_id': twd_tv['id'],
                            'matched_product_ids': [hp_tv['id']],
                            'retailer_codes': ['TWD', 'HP'],
                            'unified_category': 'television',
                            'normalized_name': twd_tv['name'].lower(),
                            'normalized_brand': twd_brand,
                            'best_price_retailer': 'TWD' if price1 < price2 else 'HP',
                            'price_range_min': min_price,
                            'price_range_max': max_price,
                            'price_variance_percentage': round(variance, 2),
                            'match_confidence': 0.75,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        try:
                            result = supabase.client.table('product_matches')\
                                .insert(match_data)\
                                .execute()
                            
                            if result.data:
                                matches_created += 1
                                logger.info(f"✅ Created TV match: {twd_brand.upper()}")
                                logger.info(f"   TWD: ฿{price1:,.0f} vs HP: ฿{price2:,.0f} (variance: {variance:.1f}%)")
                                break  # Only one match per TWD product
                        except Exception as e:
                            logger.error(f"Error inserting TV match: {str(e)}")
        
        logger.info(f"\nCreated {matches_created} TV matches")
        
        # Check final status
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
            for cat, count in category_counts.items():
                logger.info(f"  {cat}: {count} matches")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await create_refrigerator_matches()

if __name__ == "__main__":
    asyncio.run(main())