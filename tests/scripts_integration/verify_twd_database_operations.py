#!/usr/bin/env python3
"""
Verify Thai Watsadu database operations
"""
import asyncio
import logging
from datetime import datetime
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.services.supabase_service import SupabaseService
from src.models.product import Product
from decimal import Decimal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_operations():
    """Test database operations step by step"""
    
    supabase = SupabaseService()
    
    print("\n=== Testing Thai Watsadu Database Operations ===\n")
    
    # 1. Check current TWD product count
    print("1. Checking current TWD products in database...")
    response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    print(f"   Current TWD products: {response.count}")
    
    # 2. Create a test product
    print("\n2. Creating test product...")
    test_product = Product(
        sku="TWD-TEST-001",
        name="Test Thai Watsadu Product",
        brand="Test Brand",
        category="Test Category",
        current_price=Decimal("99.99"),
        original_price=Decimal("199.99"),
        description="Test product for database verification",
        features=["Feature 1", "Feature 2"],
        specifications={"spec1": "value1"},
        availability="in_stock",
        images=["https://example.com/image.jpg"],
        url="https://www.thaiwatsadu.com/test-product",
        retailer_code="TWD",
        retailer_name="Thai Watsadu",
        retailer_sku="TEST-001"
    )
    
    # 3. Try to save the product
    print("3. Attempting to save test product...")
    try:
        saved = await supabase.upsert_product(test_product)
        if saved:
            print(f"   ✅ Successfully saved! Product ID: {saved.get('id')}")
            print(f"   Product data: {saved}")
        else:
            print("   ❌ Failed to save - returned None")
    except Exception as e:
        print(f"   ❌ Error saving product: {str(e)}")
        logger.error(f"Save error details: {e}", exc_info=True)
    
    # 4. Check if product exists
    print("\n4. Checking if test product exists in database...")
    check_response = supabase.client.table('products').select('*').eq('sku', 'TWD-TEST-001').execute()
    if check_response.data:
        print(f"   ✅ Found test product: {check_response.data[0]['name']}")
    else:
        print("   ❌ Test product not found in database")
    
    # 5. Test actual scraping and saving
    print("\n5. Testing actual product scraping...")
    scraper = ThaiWatsaduScraper()
    test_url = "https://www.thaiwatsadu.com/th/product/chaffcutter-smf2300-170451"
    
    print(f"   Scraping: {test_url}")
    product = await scraper.scrape_product(test_url)
    
    if product:
        print(f"   ✅ Successfully scraped: {product.name}")
        print(f"      SKU: {product.sku}")
        print(f"      Price: {product.current_price}")
        
        # Try to save
        print("\n   Attempting to save scraped product...")
        try:
            saved = await supabase.upsert_product(product)
            if saved:
                print(f"   ✅ Successfully saved scraped product!")
            else:
                print("   ❌ Failed to save scraped product - returned None")
        except Exception as e:
            print(f"   ❌ Error saving scraped product: {str(e)}")
            logger.error(f"Save error details: {e}", exc_info=True)
    else:
        print("   ❌ Failed to scrape product")
    
    # 6. Final count
    print("\n6. Final TWD product count...")
    final_response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    print(f"   Final TWD products: {final_response.count}")
    
    # 7. Clean up test product
    print("\n7. Cleaning up test product...")
    cleanup = supabase.client.table('products').delete().eq('sku', 'TWD-TEST-001').execute()
    print("   Test product removed")

if __name__ == "__main__":
    asyncio.run(test_database_operations())