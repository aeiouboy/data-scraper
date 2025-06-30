"""
Test Global House scraper with minimal API usage
"""
import asyncio
import logging
from app.scrapers.globalhouse_scraper import GlobalHouseScraper
from app.services.firecrawl_client import FirecrawlClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_discovery():
    """Test Global House homepage discovery"""
    client = FirecrawlClient()
    
    homepage = "https://www.globalhouse.co.th/"
    
    print("\n" + "="*60)
    print("Global House Homepage Discovery Test")
    print("="*60)
    print(f"\nFetching: {homepage}")
    
    try:
        result = await client.scrape(homepage)
        
        if result:
            print("✓ Successfully scraped homepage")
            
            # Extract links
            links = result.get('linksOnPage', result.get('links', []))
            print(f"\nTotal links found: {len(links)}")
            
            # Categorize links
            product_links = []
            category_links = []
            
            for link in links:
                if isinstance(link, dict):
                    url = link.get('url', link.get('href', ''))
                else:
                    url = str(link)
                
                # Skip if not a valid URL
                if not url or not url.startswith('http'):
                    continue
                
                # Product patterns
                if any(pattern in url for pattern in ['/product/', '/p/', '/item/']):
                    product_links.append(url)
                # Category patterns  
                elif any(pattern in url for pattern in ['/category/', '/c/', 'furniture', 'decor', 'lighting']):
                    category_links.append(url)
            
            print(f"\nProduct links found: {len(product_links)}")
            if product_links:
                print("Sample product URLs:")
                for url in product_links[:5]:
                    print(f"  - {url}")
            
            print(f"\nCategory links found: {len(category_links)}")
            if category_links:
                print("Sample category URLs:")
                for url in category_links[:5]:
                    print(f"  - {url}")
            
            # Check markdown content
            markdown = result.get('markdown', '')
            if markdown:
                print(f"\nMarkdown length: {len(markdown)} chars")
                # Look for Thai content
                if 'สินค้า' in markdown:
                    print("✓ Found Thai word for 'product'")
                if 'ราคา' in markdown:
                    print("✓ Found Thai word for 'price'")
                if 'เฟอร์นิเจอร์' in markdown:
                    print("✓ Found Thai word for 'furniture'")
                    
        else:
            print("✗ Failed to scrape homepage")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("API calls used: 1")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_discovery())