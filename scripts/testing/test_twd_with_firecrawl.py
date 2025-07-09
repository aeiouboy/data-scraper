"""
Test Thai Watsadu scraping with Firecrawl API
"""
import asyncio
import os
from dotenv import load_dotenv
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.config.retailers import RETAILER_CONFIGS, RetailerType

# Load environment variables
load_dotenv()

async def test_category_discovery():
    """Test discovering products from Thai Watsadu categories"""
    # Initialize scraper
    scraper = ThaiWatsaduScraper()
    
    # Get a few test categories
    twd_config = RETAILER_CONFIGS[RetailerType.TWD]
    test_categories = twd_config.category_urls[:3]  # Test first 3 categories
    
    print("Testing Thai Watsadu Category Discovery with Firecrawl")
    print("=" * 80)
    print(f"FIRECRAWL_API_KEY present: {'FIRECRAWL_API_KEY' in os.environ}")
    print()
    
    total_products_found = 0
    
    for category_url in test_categories:
        print(f"\nTesting category: {category_url}")
        print("-" * 80)
        
        try:
            # Discover product URLs (just 1 page for testing)
            product_urls = await scraper._discover_product_urls(category_url, max_pages=1)
            
            print(f"✓ Found {len(product_urls)} product URLs")
            
            if product_urls:
                # Show sample URLs
                print("\nSample product URLs:")
                for i, url in enumerate(product_urls[:5]):
                    print(f"  {i+1}. {url}")
                
                total_products_found += len(product_urls)
                
                # Test scraping one product
                if product_urls:
                    print(f"\nTesting product scrape: {product_urls[0]}")
                    product = await scraper.scrape_product(product_urls[0])
                    
                    if product:
                        print("✓ Successfully scraped product:")
                        print(f"  Name: {product.name}")
                        print(f"  SKU: {product.sku}")
                        print(f"  Price: ฿{product.current_price}")
                        print(f"  Category: {product.category}")
                        print(f"  Availability: {product.availability}")
                    else:
                        print("✗ Failed to scrape product")
            else:
                print("✗ No product URLs found")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            if "API key" in str(e):
                print("\n⚠️  FIRECRAWL_API_KEY not set or invalid!")
                print("Please ensure FIRECRAWL_API_KEY is set in your .env file")
                return
    
    print("\n" + "=" * 80)
    print(f"Total products discovered: {total_products_found}")
    
    if total_products_found > 0:
        print("✓ Thai Watsadu scraper is working correctly!")
    else:
        print("✗ No products found. Check if:")
        print("  1. FIRECRAWL_API_KEY is valid")
        print("  2. Thai Watsadu website structure hasn't changed")
        print("  3. Network connection is working")

async def test_specific_product():
    """Test scraping a specific product if URL is known"""
    # You can add a specific product URL here if you have one
    product_url = "https://www.thaiwatsadu.com/th/product/EXAMPLE"  # Replace with actual URL
    
    print("\n" + "=" * 80)
    print("Testing specific product scrape")
    print("=" * 80)
    print("⚠️  Update product_url with an actual Thai Watsadu product URL to test")

async def main():
    """Run tests"""
    # Check for API key
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found in environment!")
        print("Please add it to your .env file")
        return
    
    # Run category discovery test
    await test_category_discovery()
    
    # Run specific product test (if URL is provided)
    # await test_specific_product()

if __name__ == "__main__":
    asyncio.run(main())