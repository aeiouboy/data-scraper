#!/usr/bin/env python3
"""
Test script to diagnose and fix Thai Watsadu category scraping issue
Following the project's file organization best practices
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Set up logging
from src.core.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Import required modules
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.firecrawl_client import FirecrawlClient
from src.services.supabase_service import SupabaseService


async def diagnose_category_issue(category_url: str) -> Dict[str, Any]:
    """
    Diagnose why Thai Watsadu category scraping only finds 1 product
    
    Args:
        category_url: The category URL to test
        
    Returns:
        Diagnostic results
    """
    logger.info(f"Starting diagnostic for URL: {category_url}")
    
    results = {
        'category_url': category_url,
        'diagnostics': {},
        'recommendations': []
    }
    
    scraper = ThaiWatsaduScraper()
    
    # Step 1: Test URL discovery
    logger.info("Step 1: Testing URL discovery...")
    try:
        discovered_urls = await scraper._discover_product_urls(category_url, max_pages=1)
        results['diagnostics']['urls_discovered'] = len(discovered_urls)
        results['diagnostics']['sample_urls'] = discovered_urls[:5] if discovered_urls else []
        
        logger.info(f"Discovered {len(discovered_urls)} product URLs")
        
        if len(discovered_urls) == 0:
            results['recommendations'].append("No URLs discovered - check if category page structure changed")
        elif len(discovered_urls) == 1:
            results['recommendations'].append("Only 1 URL discovered - check pagination or URL pattern matching")
            
    except Exception as e:
        logger.error(f"URL discovery failed: {str(e)}")
        results['diagnostics']['discovery_error'] = str(e)
        results['recommendations'].append(f"Fix URL discovery error: {str(e)}")
    
    # Step 2: Test individual product scraping
    if discovered_urls:
        logger.info("Step 2: Testing individual product scraping...")
        test_url = discovered_urls[0]
        
        try:
            product = await scraper.scrape_product(test_url)
            if product:
                results['diagnostics']['product_scraping'] = 'success'
                results['diagnostics']['sample_product'] = {
                    'name': product.name,
                    'sku': product.sku,
                    'price': float(product.current_price) if product.current_price else None
                }
                logger.info("Product scraping successful")
            else:
                results['diagnostics']['product_scraping'] = 'failed'
                results['recommendations'].append("Product extraction failed - check data extraction logic")
                
        except Exception as e:
            logger.error(f"Product scraping error: {str(e)}")
            results['diagnostics']['product_error'] = str(e)
            results['recommendations'].append(f"Fix product scraping error: {str(e)}")
    
    # Step 3: Test category scraping with minimal settings
    logger.info("Step 3: Testing category scraping...")
    try:
        category_result = await scraper.scrape_category(
            category_url=category_url,
            max_pages=1,
            max_concurrent=1
        )
        
        results['diagnostics']['category_scraping'] = category_result
        
        if category_result.get('discovered', 0) == 1:
            results['recommendations'].append("Category scraping only processes 1 URL - check batch processing logic")
            
    except Exception as e:
        logger.error(f"Category scraping error: {str(e)}")
        results['diagnostics']['category_error'] = str(e)
        results['recommendations'].append(f"Fix category scraping error: {str(e)}")
    
    # Step 4: Check Firecrawl response structure
    logger.info("Step 4: Analyzing Firecrawl response...")
    firecrawl = FirecrawlClient()
    try:
        response = await firecrawl.scrape(category_url)
        if response:
            links = response.get('linksOnPage', response.get('links', []))
            product_links = [
                link for link in links 
                if isinstance(link, (str, dict)) and '/product/' in str(link)
            ]
            results['diagnostics']['firecrawl_total_links'] = len(links)
            results['diagnostics']['firecrawl_product_links'] = len(product_links)
            
    except Exception as e:
        logger.error(f"Firecrawl test error: {str(e)}")
        results['diagnostics']['firecrawl_error'] = str(e)
    
    return results


async def test_fixed_scraping(category_url: str) -> Dict[str, Any]:
    """
    Test a potential fix for the scraping issue
    
    Args:
        category_url: The category URL to test
        
    Returns:
        Test results
    """
    logger.info("Testing fixed scraping approach...")
    
    scraper = ThaiWatsaduScraper()
    results = {
        'test_url': category_url,
        'results': {}
    }
    
    # Direct test of discovery + individual scraping
    try:
        # Discover URLs
        urls = await scraper._discover_product_urls(category_url, max_pages=1)
        results['results']['discovered'] = len(urls)
        
        # Test scraping first 3 products individually
        success_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls[:3], 1):
            logger.info(f"Testing product {i}/3: {url}")
            try:
                product = await scraper.scrape_product(url)
                if product:
                    success_count += 1
                    logger.info(f"✓ Successfully scraped: {product.name}")
                else:
                    failed_count += 1
                    logger.warning(f"✗ Failed to scrape product from: {url}")
                    
                # Add delay between products
                await asyncio.sleep(2)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Error scraping {url}: {str(e)}")
        
        results['results']['test_success'] = success_count
        results['results']['test_failed'] = failed_count
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        results['error'] = str(e)
    
    return results


async def main():
    """Main diagnostic function"""
    category_url = "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201"
    
    print("\n" + "="*60)
    print("Thai Watsadu Category Scraping Diagnostic")
    print("="*60)
    print(f"URL: {category_url}\n")
    
    # Run diagnostics
    print("Running diagnostics...")
    diagnostic_results = await diagnose_category_issue(category_url)
    
    # Print results
    print("\nDiagnostic Results:")
    print("-" * 40)
    for key, value in diagnostic_results['diagnostics'].items():
        print(f"{key}: {value}")
    
    print("\nRecommendations:")
    print("-" * 40)
    if diagnostic_results['recommendations']:
        for i, rec in enumerate(diagnostic_results['recommendations'], 1):
            print(f"{i}. {rec}")
    else:
        print("No issues found")
    
    # Test the fix
    print("\n" + "="*60)
    print("Testing Fixed Approach")
    print("="*60)
    
    fix_results = await test_fixed_scraping(category_url)
    print("\nFixed Approach Results:")
    print("-" * 40)
    print(json.dumps(fix_results, indent=2))
    
    # Save results
    output_dir = Path("data/analysis_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = asyncio.get_event_loop().time()
    output_file = output_dir / f"twd_category_diagnostic_{int(timestamp)}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'diagnostics': diagnostic_results,
            'fix_test': fix_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())