"""
Check Thai Watsadu product specifications in detail
"""
import asyncio
import logging
from app.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_product_details():
    """Test to see all specifications"""
    scraper = ThaiWatsaduScraper()
    
    test_url = "https://www.thaiwatsadu.com/th/product/%E0%B9%80%E0%B8%81%E0%B9%89%E0%B8%B2%E0%B8%AD%E0%B8%B5%E0%B9%89%E0%B8%AA%E0%B8%99%E0%B8%B2%E0%B8%A1-BISTRO-FONTE-%E0%B8%A3%E0%B8%B8%E0%B9%88%E0%B8%99-SC-092-%E0%B8%AA%E0%B8%B5%E0%B9%80%E0%B8%97%E0%B8%B2---%E0%B8%94%E0%B8%B3-60425753"
    
    print("\n" + "="*60)
    print("Thai Watsadu Product Details Check")
    print("="*60)
    
    try:
        product = await scraper.scrape_product(test_url)
        
        if product:
            print(f"\nProduct: {product.name}")
            print(f"Category extracted: {product.category}")
            
            print(f"\nAll {len(product.specifications)} specifications:")
            for key, value in product.specifications.items():
                print(f"  {key}: {value}")
                
            if product.features:
                print(f"\nAll {len(product.features)} features:")
                for feature in product.features:
                    print(f"  - {feature}")
                    
            print(f"\nDescription: {product.description}")
        else:
            print("Failed to scrape product")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_product_details())