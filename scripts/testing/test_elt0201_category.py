#!/usr/bin/env python3
"""
Test scraping HomePro ELT0201 category and validate specific fields
"""

import asyncio
import sys
import os
import logging
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.homepro_scraper import HomeProScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_elt0201_category():
    """Test scraping ELT0201 category and validate results"""
    
    category_url = "https://www.homepro.co.th/c/ELT0201"
    
    logger.info(f"🔄 Testing category: {category_url}")
    
    try:
        # Initialize scraper with native strategy
        scraper = HomeProScraper(use_native=True)
        
        # Step 1: Discover products from the category
        logger.info("📍 Step 1: Discovering products from category...")
        product_urls = await scraper.discover_product_urls(category_url, max_pages=3)
        
        logger.info(f"🔍 Discovered {len(product_urls)} product URLs")
        if not product_urls:
            logger.error("❌ No products found in category")
            return
        
        # Show first 5 URLs
        logger.info("📋 Sample URLs discovered:")
        for i, url in enumerate(product_urls[:5], 1):
            logger.info(f"   {i}. {url}")
        
        # Step 2: Scrape first 5 products to validate data extraction
        logger.info(f"\n📍 Step 2: Scraping first 5 products for validation...")
        
        results = []
        for i, url in enumerate(product_urls[:5], 1):
            logger.info(f"\n🔄 [{i}/5] Scraping: {url}")
            
            try:
                # Scrape single product
                product_data = await scraper.scrape_single_product(url)
                
                if product_data:
                    # Extract the expected fields
                    result = {
                        'sku': product_data.get('sku', 'N/A'),
                        'product_name': product_data.get('name', 'N/A'),
                        'brand': product_data.get('brand', 'N/A'),
                        'category': product_data.get('category', 'N/A'),
                        'original_price': product_data.get('original_price', 'N/A'),
                        'sale_price': product_data.get('current_price', 'N/A'),
                        'discount': product_data.get('discount_percentage', 'N/A'),
                        'status': product_data.get('availability', 'N/A'),
                        'url': product_data.get('url', url)  # Use saved URL from product data
                    }
                    
                    results.append(result)
                    
                    # Log the result
                    logger.info(f"✅ Product {i} extracted:")
                    logger.info(f"   SKU: {result['sku']}")
                    logger.info(f"   Product Name: {result['product_name'][:50]}...")
                    logger.info(f"   Brand: {result['brand']}")
                    logger.info(f"   Category: {result['category']}")
                    logger.info(f"   Original Price: ฿{result['original_price']}")
                    logger.info(f"   Sale Price: ฿{result['sale_price']}")
                    logger.info(f"   Discount: {result['discount']}%")
                    logger.info(f"   Status: {result['status']}")
                    logger.info(f"   URL: {result['url']}")
                    
                else:
                    logger.warning(f"❌ Failed to scrape product {i}")
                    results.append({
                        'sku': 'FAILED',
                        'product_name': 'FAILED',
                        'brand': 'FAILED',
                        'category': 'FAILED',
                        'original_price': 'FAILED',
                        'sale_price': 'FAILED',
                        'discount': 'FAILED',
                        'status': 'FAILED',
                        'url': url
                    })
                    
            except Exception as e:
                logger.error(f"❌ Error scraping product {i}: {str(e)}")
        
        # Step 3: Validation Summary
        logger.info("\n" + "="*60)
        logger.info("📊 VALIDATION RESULTS")
        logger.info("="*60)
        
        logger.info(f"🔍 Category: ELT0201 (Electronics/Electrical)")
        logger.info(f"📋 Total URLs discovered: {len(product_urls)}")
        logger.info(f"🧪 Products tested: {len(results)}")
        
        # Count field completeness
        field_stats = {
            'sku': 0,
            'product_name': 0,
            'brand': 0,
            'category': 0,
            'original_price': 0,
            'sale_price': 0,
            'discount': 0,
            'status': 0,
            'url': 0
        }
        
        for result in results:
            for field in field_stats:
                if field == 'url' and result[field] not in ['FAILED', None, '']:
                    field_stats[field] += 1
                elif field != 'url' and result[field] not in ['N/A', 'FAILED', None, '']:
                    field_stats[field] += 1
        
        logger.info(f"\n📈 Field Extraction Success Rates:")
        total_tested = len(results)
        for field, count in field_stats.items():
            percentage = (count / total_tested * 100) if total_tested > 0 else 0
            logger.info(f"   {field}: {count}/{total_tested} ({percentage:.1f}%)")
        
        # Display results table
        logger.info(f"\n📋 Detailed Results Table:")
        logger.info("-" * 120)
        logger.info(f"{'SKU':<12} {'Name':<25} {'Brand':<12} {'Category':<18} {'Orig':<8} {'Sale':<8} {'Disc':<6} {'Status':<10} {'URL':<30}")
        logger.info("-" * 140)
        
        for result in results:
            name = str(result['product_name'])[:23] + ".." if len(str(result['product_name'])) > 25 else str(result['product_name'])
            brand = str(result['brand'])[:13] + ".." if len(str(result['brand'])) > 15 else str(result['brand'])
            category = str(result['category'])[:18] + ".." if len(str(result['category'])) > 20 else str(result['category'])
            
            url_display = result['url'].replace('https://www.homepro.co.th/', '') if result['url'] != 'FAILED' else 'FAILED'
            logger.info(f"{str(result['sku']):<12} {name:<25} {brand:<12} {category:<18} {str(result['original_price']):<8} {str(result['sale_price']):<8} {str(result['discount']):<6} {str(result['status']):<10} {url_display:<30}")
        
        # Save results to JSON for further analysis
        with open('elt0201_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'category_url': category_url,
                'total_discovered': len(product_urls),
                'tested_products': len(results),
                'field_stats': field_stats,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Results saved to: elt0201_validation_results.json")
        
        # Overall assessment
        avg_success = sum(field_stats.values()) / (len(field_stats) * total_tested) * 100 if total_tested > 0 else 0
        logger.info(f"\n🎯 Overall Data Extraction Success: {avg_success:.1f}%")
        
        if avg_success >= 80:
            logger.info("🎉 EXCELLENT - Data extraction working very well!")
        elif avg_success >= 60:
            logger.info("👍 GOOD - Data extraction working well with minor issues")
        elif avg_success >= 40:
            logger.info("⚠️ FAIR - Data extraction needs improvement")
        else:
            logger.info("❌ POOR - Data extraction has significant issues")
            
    except Exception as e:
        logger.error(f"💥 Fatal error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_elt0201_category())