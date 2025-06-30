#!/usr/bin/env python3
"""Test URL patterns on HomePro"""
import asyncio
from app.services.firecrawl_client import FirecrawlClient

async def test_scrape_page():
    client = FirecrawlClient()
    
    # Scrape a category page to see actual links
    result = await client.scrape("https://www.homepro.co.th/c/electrical")
    
    if result:
        print("=== Page scraped successfully ===")
        
        # Check what keys we have
        print(f"Result keys: {list(result.keys())}")
        
        # Check for linksOnPage
        if "linksOnPage" in result:
            links = result["linksOnPage"]
            print(f"\nTotal links found: {len(links)}")
            
            # Filter for product-like links
            product_patterns = []
            for link in links:
                if isinstance(link, str):
                    # Check various patterns
                    if any(p in link for p in ['/p/', '/product/', 'sku=', 'item=']):
                        product_patterns.append(link)
                    # Also check for links with numbers that might be products
                    elif 'homepro.co.th' in link and any(c.isdigit() for c in link):
                        if link not in product_patterns:
                            product_patterns.append(link)
            
            print(f"\nPotential product links: {len(product_patterns)}")
            for i, link in enumerate(product_patterns[:10]):
                print(f"  {i+1}. {link}")
        
        # Check markdown content for patterns
        if "markdown" in result:
            content = result["markdown"]
            print(f"\nMarkdown length: {len(content)} chars")
            
            # Look for product links in markdown
            import re
            
            # Try different patterns
            patterns = [
                r'href=["\']([^"\']*?/p/[^"\']*?)["\']',  # href="/p/something"
                r'\[.*?\]\(([^)]*?/p/[^)]*?)\)',  # [text](/p/something)
                r'homepro\.co\.th/p/\d+',  # homepro.co.th/p/12345
                r'/p/\d{5,}',  # /p/12345 (5+ digits)
            ]
            
            all_product_links = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                all_product_links.update(matches)
            
            if all_product_links:
                print(f"\nProduct links found in markdown: {len(all_product_links)}")
                for i, link in enumerate(list(all_product_links)[:10]):
                    print(f"  {i+1}. {link}")
            else:
                # Show a sample of the markdown to understand the structure
                print("\nNo product links found. Sample of markdown:")
                print(content[:2000])
                
                # Also check if there are any links at all
                all_links = re.findall(r'href=["\']([^"\']+)["\']', content)
                print(f"\nTotal href links in markdown: {len(all_links)}")
                if all_links:
                    print("Sample links:")
                    for i, link in enumerate(all_links[:10]):
                        print(f"  {i+1}. {link}")

        # Also check HTML content if available
        if "html" in result:
            html = result["html"]
            print(f"\nHTML length: {len(html)} chars")
            
            # Look for product links in HTML
            html_links = re.findall(r'href=["\']([^"\']*?/p/[^"\']*?)["\']', html, re.IGNORECASE)
            if html_links:
                print(f"\nProduct links found in HTML: {len(html_links)}")
                for i, link in enumerate(html_links[:10]):
                    print(f"  {i+1}. {link}")

if __name__ == "__main__":
    asyncio.run(test_scrape_page())