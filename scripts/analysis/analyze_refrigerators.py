#!/usr/bin/env python3
"""
Analyze refrigerator products from the database
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def analyze_retailer_refrigerators(supabase: SupabaseService, retailer_code: str):
    """Analyze refrigerator products for a specific retailer"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Analyzing {retailer_code} Refrigerators")
    logger.info(f"{'='*60}")
    
    try:
        # Search for refrigerator products
        search_terms = ["refrigerator", "ตู้เย็น", "fridge"]
        all_products = []
        
        for term in search_terms:
            result = await supabase.search_products(
                query=term,
                filters={"retailer_code": retailer_code},
                limit=100
            )
            if result and 'products' in result:
                all_products.extend(result['products'])
        
        # Remove duplicates
        unique_products = {p['sku']: p for p in all_products}.values()
        products = list(unique_products)
        
        logger.info(f"Found {len(products)} refrigerator products")
        
        if products:
            # Analyze brands
            brands = defaultdict(int)
            price_ranges = {"min": float('inf'), "max": 0}
            by_type = defaultdict(int)
            discounts = []
            
            for product in products:
                # Count brands
                if product.get('brand'):
                    brands[product['brand']] += 1
                
                # Track price range
                if product.get('current_price'):
                    price = float(product['current_price'])
                    price_ranges["min"] = min(price_ranges["min"], price)
                    price_ranges["max"] = max(price_ranges["max"], price)
                
                # Track discounts
                if product.get('original_price') and product.get('current_price'):
                    orig = float(product['original_price'])
                    curr = float(product['current_price'])
                    if orig > curr:
                        discount_pct = (orig - curr) / orig * 100
                        discounts.append({
                            'name': product['name'],
                            'sku': product['sku'],
                            'discount': discount_pct,
                            'savings': orig - curr
                        })
                
                # Categorize by type
                name_lower = product['name'].lower()
                if 'side by side' in name_lower or 'sbs' in name_lower:
                    by_type['Side by Side'] += 1
                elif '4 door' in name_lower or '4 ประตู' in name_lower:
                    by_type['4 Door'] += 1
                elif '2 door' in name_lower or '2 ประตู' in name_lower:
                    by_type['2 Door'] += 1
                elif '1 door' in name_lower or '1 ประตู' in name_lower:
                    by_type['1 Door'] += 1
                else:
                    by_type['Other'] += 1
            
            # Sort discounts by percentage
            discounts.sort(key=lambda x: x['discount'], reverse=True)
            
            # Create analysis results
            results = {
                "retailer": retailer_code,
                "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_products": len(products),
                    "brands_found": len(brands),
                    "price_range": {
                        "min": price_ranges["min"] if price_ranges["min"] != float('inf') else 0,
                        "max": price_ranges["max"]
                    },
                    "products_on_sale": len(discounts)
                },
                "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
                "product_types": dict(by_type),
                "top_discounts": discounts[:10],
                "sample_products": [
                    {
                        "name": p['name'],
                        "sku": p['sku'],
                        "brand": p.get('brand'),
                        "current_price": p.get('current_price'),
                        "original_price": p.get('original_price'),
                        "url": p.get('url')
                    } for p in list(products)[:5]
                ]
            }
            
            # Save results
            filename = f"{retailer_code.lower()}_refrigerator_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 Saved analysis to {filename}")
            logger.info(f"🏷️  Top brands: {', '.join(list(brands.keys())[:5])}")
            logger.info(f"💰 Price range: ฿{price_ranges['min']:,.0f} - ฿{price_ranges['max']:,.0f}")
            logger.info(f"🏷️  Products on sale: {len(discounts)}")
            
            return results
            
    except Exception as e:
        logger.error(f"Error analyzing {retailer_code}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def compare_retailers(twd_results, hp_results):
    """Compare refrigerator offerings between retailers"""
    logger.info("\n" + "="*60)
    logger.info("Retailer Comparison")
    logger.info("="*60)
    
    if twd_results and hp_results:
        # Brand comparison
        twd_brands = set(twd_results['brands'].keys())
        hp_brands = set(hp_results['brands'].keys())
        common_brands = twd_brands & hp_brands
        
        logger.info(f"\n📊 Product Count:")
        logger.info(f"   Thai Watsadu: {twd_results['summary']['total_products']} products")
        logger.info(f"   HomePro: {hp_results['summary']['total_products']} products")
        
        logger.info(f"\n🏷️  Brand Analysis:")
        logger.info(f"   Common brands ({len(common_brands)}): {', '.join(sorted(common_brands))}")
        logger.info(f"   TWD exclusive ({len(twd_brands - hp_brands)}): {', '.join(sorted(twd_brands - hp_brands))}")
        logger.info(f"   HP exclusive ({len(hp_brands - twd_brands)}): {', '.join(sorted(hp_brands - twd_brands))}")
        
        logger.info(f"\n💰 Price Comparison:")
        logger.info(f"   TWD: ฿{twd_results['summary']['price_range']['min']:,.0f} - ฿{twd_results['summary']['price_range']['max']:,.0f}")
        logger.info(f"   HP: ฿{hp_results['summary']['price_range']['min']:,.0f} - ฿{hp_results['summary']['price_range']['max']:,.0f}")
        
        logger.info(f"\n🎯 Sales & Discounts:")
        logger.info(f"   TWD: {twd_results['summary']['products_on_sale']} products on sale")
        logger.info(f"   HP: {hp_results['summary']['products_on_sale']} products on sale")
        
        # Save comparison
        comparison = {
            "comparison_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": "Refrigerators",
            "summary": {
                "TWD": twd_results['summary'],
                "HP": hp_results['summary']
            },
            "brand_analysis": {
                "common_brands": sorted(list(common_brands)),
                "twd_exclusive": sorted(list(twd_brands - hp_brands)),
                "hp_exclusive": sorted(list(hp_brands - twd_brands))
            },
            "product_types": {
                "TWD": twd_results['product_types'],
                "HP": hp_results['product_types']
            }
        }
        
        filename = f"refrigerator_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📊 Saved comparison to {filename}")

async def main():
    """Main function"""
    logger.info("🚀 Starting refrigerator product analysis from database")
    
    supabase = SupabaseService()
    
    # Analyze both retailers
    twd_results = await analyze_retailer_refrigerators(supabase, "TWD")
    hp_results = await analyze_retailer_refrigerators(supabase, "HP")
    
    # Compare results
    await compare_retailers(twd_results, hp_results)
    
    logger.info("\n✅ Analysis completed! Check the generated JSON files.")

if __name__ == "__main__":
    asyncio.run(main())