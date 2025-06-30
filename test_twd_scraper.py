"""
Test script for Thai Watsadu scraper
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

async def test_single_product():
    """Test scraping a single Thai Watsadu product"""
    scraper = ThaiWatsaduScraper()
    supabase = SupabaseService()
    
    # Example Thai Watsadu product URLs
    test_urls = [
        "https://www.thaiwatsadu.com/th/product/3012345",  # Replace with actual product URL
        # Add more test URLs here
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing URL: {url}")
        print('='*60)
        
        try:
            # Scrape product
            product = await scraper.scrape_product(url)
            
            if product:
                print(f"✓ Successfully scraped: {product.name}")
                print(f"  SKU: {product.sku}")
                print(f"  Brand: {product.brand}")
                print(f"  Category: {product.category}")
                print(f"  Price: ฿{product.current_price}")
                print(f"  Availability: {product.availability}")
                print(f"  Retailer: {product.retailer_name} ({product.retailer_code})")
                print(f"  Monitoring Tier: {product.monitoring_tier}")
                
                # Save to database
                saved = await supabase.upsert_product(product)
                if saved:
                    print(f"✓ Saved to database with ID: {saved['id']}")
                else:
                    print("✗ Failed to save to database")
            else:
                print("✗ Failed to scrape product")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")

async def test_category_scraping():
    """Test scraping a Thai Watsadu category"""
    scraper = ThaiWatsaduScraper()
    supabase = SupabaseService()
    
    # Example category URL
    category_url = "https://www.thaiwatsadu.com/th/c/construction-materials"
    
    print(f"\n{'='*60}")
    print(f"Testing category: {category_url}")
    print('='*60)
    
    try:
        # Scrape category (limit to 2 pages for testing)
        products = await scraper.scrape_category(category_url, max_pages=2)
        
        print(f"\n✓ Found {len(products)} products")
        
        # Save products
        saved_count = 0
        for product in products:
            saved = await supabase.upsert_product(product)
            if saved:
                saved_count += 1
        
        print(f"✓ Saved {saved_count}/{len(products)} products to database")
        
        # Show sample
        if products:
            print("\nSample products:")
            for product in products[:5]:
                print(f"  - {product.name[:50]}... | ฿{product.current_price}")
                
    except Exception as e:
        print(f"✗ Error: {str(e)}")

async def main():
    """Run tests"""
    print("Thai Watsadu Scraper Test")
    print("========================\n")
    
    # Test single product
    # await test_single_product()
    
    # Test category scraping
    # await test_category_scraping()
    
    print("\n⚠️  Please update the test URLs with actual Thai Watsadu product/category URLs")
    print("Visit https://www.thaiwatsadu.com/th to find test URLs")

if __name__ == "__main__":
    asyncio.run(main())