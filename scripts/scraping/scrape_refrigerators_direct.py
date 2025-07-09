#!/usr/bin/env python3
"""
Direct refrigerator category scraping without job creation
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.homepro_scraper import HomeProScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def scrape_twd_refrigerators():
    """Scrape Thai Watsadu refrigerators"""
    logger.info("\n" + "="*60)
    logger.info("Scraping Thai Watsadu Refrigerators")
    logger.info("="*60)
    
    url = "https://www.thaiwatsadu.com/en/category/%E0%B8%95%E0%B8%B9%E0%B9%89%E0%B9%80%E0%B8%A2%E0%B9%87%E0%B8%99-630301"
    
    try:
        scraper = ThaiWatsaduScraper()
        logger.info(f"Scraping URL: {url}")
        
        # Scrape category
        result = await scraper.scrape_category(url, max_pages=2)
        products = result.get('products', [])
        
        logger.info(f"✅ Found {len(products)} products")
        
        if products:
            # Analyze the products
            brands = {}
            price_ranges = {"min": float('inf'), "max": 0}
            
            for product in products:
                # Count brands
                if product.brand:
                    brands[product.brand] = brands.get(product.brand, 0) + 1
                
                # Track price range
                if product.current_price:
                    price_ranges["min"] = min(price_ranges["min"], product.current_price)
                    price_ranges["max"] = max(price_ranges["max"], product.current_price)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"twd_refrigerators_{timestamp}.json"
            
            results = {
                "retailer": "Thai Watsadu",
                "retailer_code": "TWD",
                "category": "Refrigerators (ตู้เย็น)",
                "url": url,
                "scraped_at": timestamp,
                "summary": {
                    "total_products": len(products),
                    "brands_found": len(brands),
                    "price_range": {
                        "min": price_ranges["min"] if price_ranges["min"] != float('inf') else 0,
                        "max": price_ranges["max"]
                    }
                },
                "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
                "sample_products": [
                    {
                        "name": p.name,
                        "sku": p.sku,
                        "brand": p.brand,
                        "model": p.specifications.get("model", "") if p.specifications else "",
                        "current_price": p.current_price,
                        "original_price": p.original_price,
                        "discount": f"{((p.original_price - p.current_price) / p.original_price * 100):.0f}%" if p.original_price and p.current_price and p.original_price > p.current_price else None,
                        "availability": p.availability,
                        "url": p.url
                    } for p in products[:10]  # First 10 products as sample
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 Saved results to {filename}")
            logger.info(f"🏷️  Top brands: {', '.join(list(brands.keys())[:5])}")
            logger.info(f"💰 Price range: ฿{price_ranges['min']:,.0f} - ฿{price_ranges['max']:,.0f}")
            
            return results
            
    except Exception as e:
        logger.error(f"❌ Error scraping TWD: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def scrape_homepro_refrigerators():
    """Scrape HomePro refrigerators"""
    logger.info("\n" + "="*60)
    logger.info("Scraping HomePro Refrigerators")
    logger.info("="*60)
    
    url = "https://www.homepro.co.th/c/APP09"
    
    try:
        scraper = HomeProScraper()
        logger.info(f"Scraping URL: {url}")
        
        # Scrape category
        result = await scraper.scrape_category(url, max_pages=2)
        products = result.get('products', [])
        
        logger.info(f"✅ Found {len(products)} products")
        
        if products:
            # Analyze the products
            brands = {}
            price_ranges = {"min": float('inf'), "max": 0}
            
            for product in products:
                # Count brands
                if product.brand:
                    brands[product.brand] = brands.get(product.brand, 0) + 1
                
                # Track price range
                if product.current_price:
                    price_ranges["min"] = min(price_ranges["min"], product.current_price)
                    price_ranges["max"] = max(price_ranges["max"], product.current_price)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"homepro_refrigerators_{timestamp}.json"
            
            results = {
                "retailer": "HomePro",
                "retailer_code": "HP",
                "category": "Refrigerators (ตู้เย็น)",
                "url": url,
                "scraped_at": timestamp,
                "summary": {
                    "total_products": len(products),
                    "brands_found": len(brands),
                    "price_range": {
                        "min": price_ranges["min"] if price_ranges["min"] != float('inf') else 0,
                        "max": price_ranges["max"]
                    }
                },
                "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
                "sample_products": [
                    {
                        "name": p.name,
                        "sku": p.sku,
                        "brand": p.brand,
                        "model": p.specifications.get("model", "") if p.specifications else "",
                        "current_price": p.current_price,
                        "original_price": p.original_price,
                        "discount": f"{((p.original_price - p.current_price) / p.original_price * 100):.0f}%" if p.original_price and p.current_price and p.original_price > p.current_price else None,
                        "availability": p.availability,
                        "url": p.url
                    } for p in products[:10]  # First 10 products as sample
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 Saved results to {filename}")
            logger.info(f"🏷️  Top brands: {', '.join(list(brands.keys())[:5])}")
            logger.info(f"💰 Price range: ฿{price_ranges['min']:,.0f} - ฿{price_ranges['max']:,.0f}")
            
            return results
            
    except Exception as e:
        logger.error(f"❌ Error scraping HomePro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def compare_results(twd_results, hp_results):
    """Compare refrigerator offerings between retailers"""
    logger.info("\n" + "="*60)
    logger.info("Comparison Summary")
    logger.info("="*60)
    
    if twd_results and hp_results:
        # Common brands
        twd_brands = set(twd_results["brands"].keys())
        hp_brands = set(hp_results["brands"].keys())
        common_brands = twd_brands & hp_brands
        
        logger.info(f"🏪 Thai Watsadu: {twd_results['summary']['total_products']} products, {len(twd_brands)} brands")
        logger.info(f"🏪 HomePro: {hp_results['summary']['total_products']} products, {len(hp_brands)} brands")
        logger.info(f"🤝 Common brands: {', '.join(sorted(common_brands))}")
        logger.info(f"📊 TWD exclusive brands: {', '.join(sorted(twd_brands - hp_brands))}")
        logger.info(f"📊 HP exclusive brands: {', '.join(sorted(hp_brands - twd_brands))}")
        
        # Price comparison
        logger.info(f"\n💰 Price Ranges:")
        logger.info(f"   TWD: ฿{twd_results['summary']['price_range']['min']:,.0f} - ฿{twd_results['summary']['price_range']['max']:,.0f}")
        logger.info(f"   HP:  ฿{hp_results['summary']['price_range']['min']:,.0f} - ฿{hp_results['summary']['price_range']['max']:,.0f}")
        
        # Save comparison
        comparison = {
            "comparison_date": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "category": "Refrigerators",
            "retailers": {
                "TWD": {
                    "products": twd_results['summary']['total_products'],
                    "brands": len(twd_brands),
                    "price_range": twd_results['summary']['price_range']
                },
                "HP": {
                    "products": hp_results['summary']['total_products'],
                    "brands": len(hp_brands),
                    "price_range": hp_results['summary']['price_range']
                }
            },
            "common_brands": sorted(list(common_brands)),
            "exclusive_brands": {
                "TWD": sorted(list(twd_brands - hp_brands)),
                "HP": sorted(list(hp_brands - twd_brands))
            }
        }
        
        filename = f"refrigerator_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📊 Saved comparison to {filename}")

async def main():
    """Main function"""
    logger.info("🚀 Starting refrigerator category scraping")
    
    # Scrape both retailers
    twd_results = await scrape_twd_refrigerators()
    await asyncio.sleep(3)  # Pause between retailers
    
    hp_results = await scrape_homepro_refrigerators()
    
    # Compare results
    await compare_results(twd_results, hp_results)
    
    logger.info("\n✅ Scraping completed! Check the generated JSON files.")

if __name__ == "__main__":
    asyncio.run(main())