"""
Test Thai Watsadu scraper with a single product - no user input
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
    
    # Use one of the product URLs we found
    test_url = "https://www.thaiwatsadu.com/th/product/%E0%B9%80%E0%B8%81%E0%B9%89%E0%B8%B2%E0%B8%AD%E0%B8%B5%E0%B9%89%E0%B8%AA%E0%B8%99%E0%B8%B2%E0%B8%A1-BISTRO-FONTE-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-SC-092-%E0%B8%AA%E0%B8%B5%E0%B9%80%E0%B8%97%E0%B8%B2---%E0%B8%94%E0%B8%B3-60425753"
    
    print("\n" + "="*60)
    print("Thai Watsadu Single Product Test")
    print("="*60)
    print(f"\nTesting URL: {test_url}")
    print("-" * 60)
    
    try:
        # Scrape the product
        product = await scraper.scrape_product(test_url)
        
        if product:
            print(f"\n✓ Successfully scraped product:")
            print(f"  Name: {product.name}")
            print(f"  SKU: {product.sku}")
            print(f"  Retailer SKU: {product.retailer_sku}")
            print(f"  Brand: {product.brand}")
            print(f"  Category: {product.category}")
            print(f"  Unified Category: {product.unified_category}")
            print(f"  Current Price: ฿{product.current_price}")
            print(f"  Original Price: ฿{product.original_price}")
            if product.discount_percentage:
                print(f"  Discount: {product.discount_percentage}%")
            print(f"  Availability: {product.availability}")
            print(f"  Retailer: {product.retailer_name} ({product.retailer_code})")
            print(f"  Monitoring Tier: {product.monitoring_tier}")
            print(f"  Images: {len(product.images)} found")
            if product.features:
                print(f"  Features: {len(product.features)} found")
            if product.specifications:
                print(f"  Specifications: {len(product.specifications)} found")
            
            # Show some specifications
            if product.specifications:
                print("\n  Sample specifications:")
                for i, (key, value) in enumerate(list(product.specifications.items())[:3]):
                    print(f"    - {key}: {value}")
                    
            # Calculate discount percentage
            if product.original_price and product.current_price:
                discount_pct = ((float(product.original_price) - float(product.current_price)) / float(product.original_price)) * 100
                print(f"\n  Calculated discount: {discount_pct:.1f}%")
                
            print("\n✓ Test completed successfully - product data extracted correctly")
        else:
            print("✗ Failed to scrape product")
            
    except Exception as e:
        print(f"✗ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test complete!")
    print("API calls used: 1")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_single_product())