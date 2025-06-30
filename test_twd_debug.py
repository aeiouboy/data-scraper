"""
Debug test for Thai Watsadu scraper
Shows what content we're getting from the page
"""
import asyncio
import logging
from app.services.firecrawl_client import FirecrawlClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_scrape():
    """Debug what we're getting from Thai Watsadu"""
    client = FirecrawlClient()
    
    # Test URL
    test_url = "https://www.thaiwatsadu.com/th"
    
    print(f"\nScraping: {test_url}")
    print("="*60)
    
    try:
        result = await client.scrape(test_url)
        
        if result:
            print("\n✓ Successfully scraped page")
            
            # Show what keys we got
            print(f"\nData keys: {list(result.keys())}")
            
            # Show links if any
            links = []
            if 'linksOnPage' in result:
                links = result['linksOnPage']
                print(f"\nFound {len(links)} links")
                print(f"Type of links: {type(links)}")
                if links:
                    print(f"Type of first link: {type(links[0])}")
                
            # Show first few links to understand structure
            print("\nFirst 10 links:")
            for i, link in enumerate(links[:10]):
                print(f"  {i+1}. Type: {type(link)}, Value: {link}")
                
                # Filter for potential product links
                product_links = []
                category_links = []
                
                for link in links:
                    if '/product/' in link or '/p/' in link:
                        product_links.append(link)
                    elif '/category/' in link or '/c/' in link:
                        category_links.append(link)
                
                print(f"\nPotential product links: {len(product_links)}")
                for link in product_links[:5]:
                    print(f"  - {link}")
                    
                print(f"\nCategory links: {len(category_links)}")
                for link in category_links[:5]:
                    print(f"  - {link}")
            
            # Show markdown snippet
            if 'markdown' in result:
                markdown = result['markdown']
                print(f"\nMarkdown length: {len(markdown)} chars")
                print("\nFirst 500 chars of markdown:")
                print("-"*40)
                print(markdown[:500])
                print("-"*40)
                
                # Look for Thai Watsadu specific patterns
                if 'สินค้า' in markdown:
                    print("✓ Found Thai word for 'product'")
                if 'ราคา' in markdown:
                    print("✓ Found Thai word for 'price'")
                if 'บาท' in markdown:
                    print("✓ Found Thai currency (Baht)")
                    
        else:
            print("✗ Failed to scrape page")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scrape())