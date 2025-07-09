"""
Get verified HomePro categories from their sitemap or main navigation
"""
import asyncio
from src.services.firecrawl_client import FirecrawlClient
from dotenv import load_dotenv
import re

load_dotenv()

async def get_homepro_categories():
    """Get HomePro categories from main page"""
    print("Getting HomePro Categories from Main Page")
    print("=" * 80)
    
    firecrawl = FirecrawlClient()
    base_url = "https://www.homepro.co.th"
    
    categories = []
    
    try:
        # Get main page
        result = await firecrawl.scrape(base_url)
        if result:
            # Look for category links in the content
            content = result.get('markdown', '')
            
            # Find all /c/XXX patterns
            pattern = r'/c/([A-Z]{3})'
            matches = re.findall(pattern, content)
            
            # Remove duplicates and sort
            unique_codes = sorted(list(set(matches)))
            
            print(f"Found {len(unique_codes)} unique category codes")
            
            # Create full URLs
            for code in unique_codes:
                categories.append({
                    'code': code,
                    'url': f"{base_url}/c/{code}"
                })
            
            # Also check links
            links = result.get('linksOnPage', result.get('links', []))
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                if '/c/' in href and 'homepro.co.th' in href:
                    code_match = re.search(r'/c/([A-Z]{3})$', href)
                    if code_match:
                        code = code_match.group(1)
                        if not any(c['code'] == code for c in categories):
                            categories.append({
                                'code': code,
                                'url': href
                            })
            
            # Sort by code
            categories.sort(key=lambda x: x['code'])
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Add known working categories if not found
    known_working = [
        'LIG', 'PAI', 'FUR', 'APP', 'TVA', 'KIT', 'BAT', 'HHP', 'CON', 'ELT',
        'DOW', 'TOO', 'OUT', 'BED', 'SPO', 'BEA', 'MOM', 'HEA', 'PET', 'ATM',
        'GAR', 'OFF', 'CLO', 'STA', 'TEX', 'DEC', 'SAF', 'PLU', 'TIL', 'FLO',
        'CEI', 'WAL', 'ROO', 'INS', 'HVA', 'POW', 'NET', 'COM', 'DIY', 'STO'
    ]
    
    for code in known_working:
        if not any(c['code'] == code for c in categories):
            categories.append({
                'code': code,
                'url': f"{base_url}/c/{code}"
            })
    
    # Sort again
    categories.sort(key=lambda x: x['code'])
    
    print(f"\nTotal HomePro categories: {len(categories)}")
    
    # Generate category_urls
    print("\nCategory URLs for retailers.py:")
    print("-" * 80)
    print("category_urls=[")
    for cat in categories:
        print(f'    "{cat["url"]}",  # {cat["code"]}')
    print("],")
    
    return categories

async def main():
    await get_homepro_categories()

if __name__ == "__main__":
    asyncio.run(main())