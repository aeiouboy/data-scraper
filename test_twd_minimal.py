"""
Minimal test for Thai Watsadu scraper
Tests with just 1-2 products to minimize API usage
"""
import asyncio
import logging
from app.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from app.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_minimal():
    """Test with minimal API usage"""
    scraper = ThaiWatsaduScraper()
    supabase = SupabaseService()
    
    print("\n" + "="*60)
    print("Thai Watsadu Minimal Test")
    print("="*60)
    
    # Test 1: Scrape just the first category page to discover URLs
    test_category = "https://www.thaiwatsadu.com/th/c/tools-hardware"
    
    print(f"\nTest 1: Discovering product URLs from: {test_category}")
    print("-" * 60)
    
    try:
        # Use internal method to just discover URLs without scraping
        product_urls = await scraper._discover_product_urls(test_category, max_pages=1)
        
        print(f"✓ Found {len(product_urls)} product URLs on first page")
        
        if product_urls:
            # Show first 3 URLs
            print("\nSample URLs found:")
            for url in product_urls[:3]:
                print(f"  - {url}")
            
            # Test 2: Scrape just ONE product
            print(f"\nTest 2: Scraping ONE product for testing")
            print("-" * 60)
            
            test_url = product_urls[0]
            print(f"Testing URL: {test_url}")
            
            product = await scraper.scrape_product(test_url)
            
            if product:
                print(f"\n✓ Successfully scraped product:")
                print(f"  Name: {product.name}")
                print(f"  SKU: {product.sku}")
                print(f"  Brand: {product.brand}")
                print(f"  Category: {product.category}")
                print(f"  Unified Category: {product.unified_category}")
                print(f"  Current Price: ฿{product.current_price}")
                print(f"  Original Price: ฿{product.original_price}")
                print(f"  Discount: {product.discount_percentage}%")
                print(f"  Availability: {product.availability}")
                print(f"  Retailer: {product.retailer_name} ({product.retailer_code})")
                print(f"  Monitoring Tier: {product.monitoring_tier}")
                print(f"  Images: {len(product.images)} found")
                
                # Test 3: Save to database
                print(f"\nTest 3: Saving to database")
                print("-" * 60)
                
                saved = await supabase.upsert_product(product)
                if saved:
                    print(f"✓ Successfully saved to database")
                    print(f"  Product ID: {saved['id']}")
                else:
                    print("✗ Failed to save to database")
            else:
                print("✗ Failed to scrape product")
        else:
            print("✗ No product URLs found")
            
    except Exception as e:
        print(f"✗ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test Summary:")
    print("- API calls used: ~2 (1 for category page, 1 for product)")
    print("- Products scraped: 1")
    print("- Total time: Minimal")
    print("="*60)

async def test_scraper_only():
    """Test scraper without database saves"""
    scraper = ThaiWatsaduScraper()
    
    print("\n" + "="*60)
    print("Thai Watsadu Scraper Test (No Database)")
    print("="*60)
    
    # Direct product URL test (if you have one)
    # Replace with an actual Thai Watsadu product URL
    test_urls = [
        "https://www.thaiwatsadu.com/th/product/example-product-url",  # Replace this
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            product = await scraper.scrape_product(url)
            if product:
                print("✓ Scraping successful")
                print(f"  Product: {product.name}")
                print(f"  Price: ฿{product.current_price}")
            else:
                print("✗ Scraping failed")
        except Exception as e:
            print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    # Run minimal test
    asyncio.run(test_minimal())
    
    # Uncomment to test without database
    # asyncio.run(test_scraper_only())