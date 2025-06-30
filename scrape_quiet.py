#!/usr/bin/env python3
"""
Quiet scraping with progress bars and CSV export
"""
import asyncio
import sys
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.core.scraper import HomeProScraper
from app.core.url_discovery import URLDiscovery
from app.utils.progress import ProgressBar

# Suppress verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("app.services").setLevel(logging.WARNING)
logging.getLogger("app.core").setLevel(logging.WARNING)


async def discover_urls_quiet(category_url: str, max_pages: int = 5) -> List[str]:
    """Discover URLs with progress bar"""
    print(f"🔍 Discovering products from: {category_url}")
    
    discovery = URLDiscovery()
    try:
        progress = ProgressBar(max_pages, "📄 Scanning pages")
        
        # Mock progress for discovery (actual discovery happens in one call)
        for i in range(max_pages):
            await asyncio.sleep(0.1)  # Small delay for visual effect
            progress.update(i + 1, f"Page {i + 1}/{max_pages}")
        
        urls = await discovery.discover_from_category(category_url, max_pages)
        print(f"\n✅ Found {len(urls)} products")
        return urls
    finally:
        await discovery.close()


async def scrape_products_quiet(urls: List[str], export_csv: bool = True) -> Dict[str, Any]:
    """Scrape products with progress bar and optional CSV export"""
    print(f"\n📦 Scraping {len(urls)} products...")
    
    scraper = HomeProScraper()
    progress = ProgressBar(len(urls), "🛒 Scraping")
    
    results = []
    success_count = 0
    failed_urls = []
    
    # Keep client open for all requests
    async with scraper.firecrawl as client:
        for i, url in enumerate(urls):
            try:
                # Scrape product
                raw_data = await client.scrape(url)
                
                if raw_data:
                    product = scraper.processor.process_product_data(raw_data, url)
                    if product:
                        # Save to database
                        saved = await scraper.supabase.upsert_product(product)
                        if saved:
                            success_count += 1
                            results.append({
                                'sku': product.sku,
                                'name': product.name,
                                'brand': product.brand or 'N/A',
                                'current_price': float(product.current_price) if product.current_price else 0,
                                'original_price': float(product.original_price) if product.original_price else 0,
                                'discount': f"{product.discount_percentage:.1f}%" if product.discount_percentage else "0%",
                                'url': url,
                                'status': 'success'
                            })
                        else:
                            failed_urls.append(url)
                            results.append({'url': url, 'status': 'failed - save error'})
                    else:
                        failed_urls.append(url)
                        results.append({'url': url, 'status': 'failed - processing error'})
                else:
                    failed_urls.append(url)
                    results.append({'url': url, 'status': 'failed - scrape error'})
                    
            except Exception as e:
                failed_urls.append(url)
                results.append({'url': url, 'status': f'failed - {str(e)}'})
            
            # Update progress
            progress.update(i + 1, f"✓ {success_count} ✗ {len(failed_urls)}")
    
    # Export to CSV if requested
    if export_csv and results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"scrape_results_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['sku', 'name', 'brand', 'current_price', 'original_price', 'discount', 'url', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Ensure all fields exist
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"\n📊 Results exported to: {csv_filename}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {len(failed_urls)}")
    print(f"   📊 Success rate: {(success_count/len(urls)*100):.1f}%")
    
    return {
        'total': len(urls),
        'success': success_count,
        'failed': len(failed_urls),
        'failed_urls': failed_urls,
        'results': results
    }


async def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scrape_quiet.py discover <category_url> [max_pages]")
        print("  python scrape_quiet.py scrape <urls_file> [limit]")
        print("  python scrape_quiet.py auto <category_url> [max_products]")
        print("\nExamples:")
        print("  python scrape_quiet.py discover https://www.homepro.co.th/c/electrical 3")
        print("  python scrape_quiet.py scrape discovered_urls.txt 10")
        print("  python scrape_quiet.py auto https://www.homepro.co.th/c/tools 20")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "discover":
        if len(sys.argv) < 3:
            print("Error: Please provide a category URL")
            sys.exit(1)
        
        category_url = sys.argv[2]
        max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        urls = await discover_urls_quiet(category_url, max_pages)
        
        # Save URLs
        with open("discovered_urls_quiet.txt", "w") as f:
            for url in urls:
                f.write(url + "\n")
        print(f"💾 URLs saved to: discovered_urls_quiet.txt")
    
    elif command == "scrape":
        if len(sys.argv) < 3:
            print("Error: Please provide a URLs file")
            sys.exit(1)
        
        urls_file = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        # Read URLs
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if limit:
            urls = urls[:limit]
        
        await scrape_products_quiet(urls)
    
    elif command == "auto":
        # Discover and scrape in one go
        if len(sys.argv) < 3:
            print("Error: Please provide a category URL")
            sys.exit(1)
        
        category_url = sys.argv[2]
        max_products = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        
        # Discover URLs
        urls = await discover_urls_quiet(category_url, max_pages=5)
        
        # Limit URLs
        urls = urls[:max_products]
        
        # Scrape products
        await scrape_products_quiet(urls)
    
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())