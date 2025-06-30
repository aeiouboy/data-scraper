#!/usr/bin/env python3
"""Debug scraping to see full content"""
import asyncio
from app.services.firecrawl_client import FirecrawlClient

async def debug_scrape():
    client = FirecrawlClient()
    
    # Scrape a product page
    result = await client.scrape("https://www.homepro.co.th/p/1243357")
    
    if result:
        # Save markdown to file
        with open("debug_markdown.md", "w") as f:
            f.write(result.get("markdown", ""))
        
        # Look for product info in markdown
        markdown = result.get("markdown", "")
        
        # Find price patterns
        import re
        prices = re.findall(r'฿\s*([\d,]+)', markdown)
        print(f"Found prices: {prices}")
        
        # Find product name - usually in title or h1
        titles = re.findall(r'#\s+(.+)', markdown)
        print(f"Found titles: {titles[:5]}")
        
        # Look for SKU patterns
        skus = re.findall(r'(?:SKU|รหัส|รหัสสินค้า)[\s:]*([A-Z0-9-]+)', markdown, re.IGNORECASE)
        print(f"Found SKUs: {skus[:5]}")
        
        # Check metadata
        metadata = result.get("metadata", {})
        print(f"\nMetadata title: {metadata.get('title', 'N/A')}")
        print(f"Metadata description: {metadata.get('description', 'N/A')}")
        
        print("\nMarkdown saved to debug_markdown.md")

if __name__ == "__main__":
    asyncio.run(debug_scrape())