#!/usr/bin/env python3
"""
Create product matches for more categories (refrigerators, TVs, etc.)
"""

import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService
from src.services.product_matcher import ProductMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_matches_for_category(category_name: str, search_terms: list):
    """Create matches for a specific category"""
    supabase = SupabaseService()
    matcher = ProductMatcher(supabase)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Creating matches for {category_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Get products from both retailers for this category
        all_products = []
        
        for term in search_terms:
            result = await supabase.search_products(
                query=term,
                limit=100
            )
            if result and 'products' in result:
                all_products.extend(result['products'])
        
        # Remove duplicates
        unique_products = {p['id']: p for p in all_products}.values()
        products = list(unique_products)
        
        # Group by retailer
        retailers = {}
        for product in products:
            retailer = product.get('retailer_code')
            if retailer not in retailers:
                retailers[retailer] = []
            retailers[retailer].append(product)
        
        logger.info(f"Found products:")
        for retailer, prods in retailers.items():
            logger.info(f"  {retailer}: {len(prods)} products")
        
        # Create matches between retailers
        if len(retailers) >= 2:
            retailer_list = list(retailers.keys())
            
            for i in range(len(retailer_list)):
                for j in range(i + 1, len(retailer_list)):
                    retailer1 = retailer_list[i]
                    retailer2 = retailer_list[j]
                    
                    logger.info(f"\nMatching {retailer1} vs {retailer2}...")
                    
                    matches_created = 0
                    for product1 in retailers[retailer1]:
                        # Find potential matches in retailer2
                        best_match = None
                        best_score = 0
                        
                        for product2 in retailers[retailer2]:
                            # Simple matching based on brand and keywords
                            score = 0
                            
                            # Brand match
                            if product1.get('brand') and product2.get('brand'):
                                if product1['brand'].lower() == product2['brand'].lower():
                                    score += 50
                            
                            # Name similarity (simple keyword matching)
                            name1_words = set(product1['name'].lower().split())
                            name2_words = set(product2['name'].lower().split())
                            common_words = name1_words & name2_words
                            
                            if len(common_words) > 3:
                                score += len(common_words) * 10
                            
                            if score > best_score and score >= 60:
                                best_score = score
                                best_match = product2
                        
                        # Create match if found
                        if best_match:
                            try:
                                # Calculate price variance
                                price1 = float(product1.get('current_price', 0))
                                price2 = float(best_match.get('current_price', 0))
                                
                                if price1 and price2:
                                    min_price = min(price1, price2)
                                    max_price = max(price1, price2)
                                    variance = ((max_price - min_price) / min_price) * 100
                                    
                                    # Create match record
                                    match_data = {
                                        'master_product_id': product1['id'],
                                        'matched_product_ids': [best_match['id']],
                                        'retailer_codes': [retailer1, retailer2],
                                        'unified_category': category_name.lower().replace(' ', '_'),
                                        'unified_brand': product1.get('brand'),
                                        'unified_model': None,  # Could extract from name
                                        'min_price': min_price,
                                        'max_price': max_price,
                                        'price_variance_percentage': round(variance, 2),
                                        'match_confidence': best_score / 100.0,
                                        'created_at': datetime.now().isoformat()
                                    }
                                    
                                    # Insert match
                                    result = supabase.client.table('product_matches')\
                                        .insert(match_data)\
                                        .execute()
                                    
                                    if result.data:
                                        matches_created += 1
                                        logger.info(f"  Created match: {product1['name'][:50]}... <-> {best_match['name'][:50]}...")
                                        
                            except Exception as e:
                                logger.error(f"Error creating match: {str(e)}")
                    
                    logger.info(f"Created {matches_created} matches between {retailer1} and {retailer2}")
        else:
            logger.warning(f"Need at least 2 retailers with products to create matches")
            
    except Exception as e:
        logger.error(f"Error creating matches for {category_name}: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Create matches for multiple categories"""
    logger.info("🚀 Starting product matching for multiple categories")
    
    categories = [
        {
            "name": "Refrigerators",
            "terms": ["ตู้เย็น", "refrigerator", "fridge"]
        },
        {
            "name": "TVs",
            "terms": ["ทีวี", "television", "tv", "LED TV", "Smart TV"]
        },
        {
            "name": "Washing Machines",
            "terms": ["เครื่องซักผ้า", "washing machine", "washer"]
        }
    ]
    
    for category in categories:
        await create_matches_for_category(category['name'], category['terms'])
        await asyncio.sleep(2)  # Pause between categories
    
    logger.info("\n✅ Product matching completed!")

if __name__ == "__main__":
    asyncio.run(main())