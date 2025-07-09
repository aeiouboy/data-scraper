"""
Discover ALL categories for each retailer website
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
import time
from src.services.firecrawl_client import FirecrawlClient
from src.config.retailers import RETAILER_CONFIGS, RetailerType
from dotenv import load_dotenv

load_dotenv()

class CategoryDiscoverer:
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.discovered_categories = {}
        
    async def discover_homepro_categories(self):
        """Discover all HomePro categories"""
        print("\n" + "="*80)
        print("DISCOVERING ALL HOMEPRO CATEGORIES")
        print("="*80)
        
        base_url = "https://www.homepro.co.th"
        categories = set()
        
        # HomePro uses /c/XXX pattern
        # First, get main page to find all category links
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(base_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text
                        soup = BeautifulSoup(text, 'html.parser')
                        
                        # Find all category links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if '/c/' in href:
                                full_url = urljoin(base_url, href)
                                if 'homepro.co.th/c/' in full_url:
                                    categories.add(full_url)
            except Exception as e:
                print(f"Error fetching main page: {e}")
        
        # Use Firecrawl for better discovery
        try:
            result = await self.firecrawl.scrape(base_url)
            if result:
                links = result.get('linksOnPage', result.get('links', []))
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    if '/c/' in href and 'homepro.co.th' in href:
                        categories.add(href)
        except Exception as e:
            print(f"Firecrawl error: {e}")
        
        # Known HomePro category codes (comprehensive list)
        known_codes = [
            'LIG', 'PAI', 'FUR', 'APP', 'TVA', 'KIT', 'BAT', 'HHP', 'CON', 'ELT',
            'DOW', 'TOO', 'OUT', 'BED', 'SPO', 'BEA', 'MOM', 'HEA', 'PET', 'ATM',
            'GAR', 'OFF', 'CLO', 'STA', 'TEX', 'DEC', 'SAF', 'PLU', 'TIL', 'FLO',
            'CEI', 'WAL', 'ROO', 'INS', 'HVA', 'POW', 'NET', 'PHO', 'COM', 'AUD',
            'CAM', 'GAM', 'TOY', 'BOO', 'MUS', 'SPT', 'FIT', 'BIK', 'CAR', 'MOT'
        ]
        
        for code in known_codes:
            categories.add(f"{base_url}/c/{code}")
        
        self.discovered_categories['homepro'] = sorted(list(categories))
        print(f"Found {len(categories)} HomePro categories")
        return categories
    
    async def discover_thaiwatsadu_all_categories(self):
        """Discover ALL Thai Watsadu categories"""
        print("\n" + "="*80)
        print("DISCOVERING ALL THAI WATSADU CATEGORIES")
        print("="*80)
        
        base_url = "https://www.thaiwatsadu.com"
        categories = set()
        
        # Use Firecrawl to get main page
        try:
            result = await self.firecrawl.scrape(f"{base_url}/th")
            if result:
                # Extract all category links
                links = result.get('linksOnPage', result.get('links', []))
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    if '/th/category/' in href and 'thaiwatsadu.com' in href:
                        categories.add(href)
                
                # Also check markdown content for category links
                markdown = result.get('markdown', '')
                category_pattern = r'https://www\.thaiwatsadu\.com/th/category/[^"\s]+'
                found_cats = re.findall(category_pattern, markdown)
                categories.update(found_cats)
        except Exception as e:
            print(f"Error with Firecrawl: {e}")
        
        # Systematically check category IDs
        print("Checking category ID ranges...")
        async with aiohttp.ClientSession() as session:
            # Main categories (1-100)
            for i in range(1, 101):
                url = f"{base_url}/th/category/{i}"
                try:
                    async with session.head(url, timeout=3, allow_redirects=True) as response:
                        if response.status == 200:
                            categories.add(response.url)
                            print(f"✓ Found category ID: {i}")
                    await asyncio.sleep(0.1)
                except:
                    pass
            
            # Subcategories (XX01-XX10 pattern)
            for main in range(51, 70):
                for sub in range(1, 11):
                    cat_id = f"{main}{sub:02d}"
                    url = f"{base_url}/th/category/{cat_id}"
                    try:
                        async with session.head(url, timeout=3, allow_redirects=True) as response:
                            if response.status == 200:
                                categories.add(response.url)
                                print(f"✓ Found subcategory ID: {cat_id}")
                        await asyncio.sleep(0.1)
                    except:
                        pass
        
        self.discovered_categories['thaiwatsadu'] = sorted(list(categories))
        print(f"Found {len(categories)} Thai Watsadu categories")
        return categories
    
    async def discover_globalhouse_categories(self):
        """Discover all Global House categories"""
        print("\n" + "="*80)
        print("DISCOVERING ALL GLOBAL HOUSE CATEGORIES")
        print("="*80)
        
        base_url = "https://www.globalhouse.co.th"
        categories = set()
        
        # Use Firecrawl
        try:
            result = await self.firecrawl.scrape(base_url)
            if result:
                links = result.get('linksOnPage', result.get('links', []))
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    # Global House patterns
                    category_patterns = ['/category/', '/c/', '/product-category/']
                    for pattern in category_patterns:
                        if pattern in href and 'globalhouse.co.th' in href:
                            categories.add(href)
        except Exception as e:
            print(f"Error: {e}")
        
        # Common Global House categories
        known_categories = [
            'furniture', 'home-decor', 'lighting', 'kitchen-dining', 'bathroom',
            'bedroom', 'living-room', 'outdoor', 'office', 'storage', 'garden',
            'tools', 'electrical', 'plumbing', 'paint', 'flooring', 'tiles',
            'doors-windows', 'construction', 'hardware', 'appliances', 'cleaning',
            'automotive', 'sports', 'toys', 'pet-supplies'
        ]
        
        for cat in known_categories:
            categories.add(f"{base_url}/{cat}")
            categories.add(f"{base_url}/category/{cat}")
            categories.add(f"{base_url}/c/{cat}")
        
        self.discovered_categories['globalhouse'] = sorted(list(categories))
        print(f"Found {len(categories)} Global House categories")
        return categories
    
    async def discover_dohome_categories(self):
        """Discover all DoHome categories"""
        print("\n" + "="*80)
        print("DISCOVERING ALL DOHOME CATEGORIES")
        print("="*80)
        
        base_url = "https://www.dohome.co.th"
        categories = set()
        
        # Use Firecrawl
        try:
            result = await self.firecrawl.scrape(base_url)
            if result:
                links = result.get('linksOnPage', result.get('links', []))
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    if 'dohome.co.th' in href:
                        # DoHome category patterns
                        if any(pattern in href for pattern in ['/category/', '/c/', '/-c-']):
                            categories.add(href)
        except Exception as e:
            print(f"Error: {e}")
        
        # Known DoHome categories
        known_categories = [
            'hardware-tools', 'electrical', 'plumbing', 'paint', 'building-materials',
            'garden', 'automotive', 'household', 'furniture', 'bathroom', 'kitchen',
            'lighting', 'flooring', 'tiles', 'doors-windows', 'safety', 'storage',
            'cleaning', 'appliances', 'outdoor-living', 'power-tools', 'hand-tools',
            'fasteners', 'adhesives', 'roofing', 'insulation', 'concrete', 'steel'
        ]
        
        for cat in known_categories:
            categories.add(f"{base_url}/{cat}")
            categories.add(f"{base_url}/category/{cat}")
        
        self.discovered_categories['dohome'] = sorted(list(categories))
        print(f"Found {len(categories)} DoHome categories")
        return categories
    
    async def discover_boonthavorn_all_categories(self):
        """Discover ALL Boonthavorn categories using Firecrawl"""
        print("\n" + "="*80)
        print("DISCOVERING ALL BOONTHAVORN CATEGORIES")
        print("="*80)
        
        base_url = "https://www.boonthavorn.com"
        categories = set()
        
        # Start with main categories we found
        main_categories = [
            f"{base_url}/boonthavorn-wall-floor",
            f"{base_url}/surface-covering-decorative",
            f"{base_url}/bathroom",
            f"{base_url}/kitchen",
            f"{base_url}/home-appliances",
            f"{base_url}/lighting",
        ]
        
        categories.update(main_categories)
        
        # Crawl each main category to find subcategories
        for main_cat in main_categories:
            try:
                print(f"Crawling: {main_cat}")
                result = await self.firecrawl.scrape(main_cat)
                if result:
                    links = result.get('linksOnPage', result.get('links', []))
                    for link in links:
                        if isinstance(link, dict):
                            href = link.get('url', link.get('href', ''))
                        else:
                            href = str(link)
                        
                        # Check if it's a subcategory of the main category
                        if main_cat in href and href != main_cat and 'boonthavorn.com' in href:
                            # Filter out non-category URLs
                            skip_patterns = [
                                '/media/', '/static/', '.jpg', '.png', '.pdf',
                                '/customer/', '/cart/', '/checkout/', '/account/',
                                '#', 'javascript:', 'tel:', 'mailto:', '/blog/'
                            ]
                            if not any(skip in href.lower() for skip in skip_patterns):
                                categories.add(href)
                
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error crawling {main_cat}: {e}")
        
        self.discovered_categories['boonthavorn'] = sorted(list(categories))
        print(f"Found {len(categories)} Boonthavorn categories")
        return categories
    
    async def discover_megahome_categories(self):
        """Discover all MegaHome categories"""
        print("\n" + "="*80)
        print("DISCOVERING ALL MEGAHOME CATEGORIES")
        print("="*80)
        
        base_url = "https://www.megahome.co.th"
        categories = set()
        
        # Use Firecrawl
        try:
            result = await self.firecrawl.scrape(base_url)
            if result:
                links = result.get('linksOnPage', result.get('links', []))
                for link in links:
                    if isinstance(link, dict):
                        href = link.get('url', link.get('href', ''))
                    else:
                        href = str(link)
                    
                    if 'megahome.co.th' in href:
                        # Category patterns
                        if any(pattern in href for pattern in ['/category/', '/c/', '/product-category/']):
                            categories.add(href)
        except Exception as e:
            print(f"Error: {e}")
        
        # Known MegaHome categories
        known_categories = [
            'building-materials', 'tools-hardware', 'electrical-plumbing',
            'paint-coating', 'roofing', 'flooring', 'garden-outdoor',
            'safety-equipment', 'concrete-cement', 'steel-metal', 'wood-lumber',
            'tiles-ceramic', 'doors-windows', 'insulation', 'adhesives-sealants',
            'fasteners', 'plumbing-fixtures', 'electrical-supplies', 'lighting',
            'hvac', 'power-tools', 'hand-tools', 'measuring-tools', 'safety-gear',
            'construction-equipment', 'industrial-supplies'
        ]
        
        for cat in known_categories:
            categories.add(f"{base_url}/{cat}")
            categories.add(f"{base_url}/category/{cat}")
        
        self.discovered_categories['megahome'] = sorted(list(categories))
        print(f"Found {len(categories)} MegaHome categories")
        return categories
    
    async def discover_all(self):
        """Discover categories for all retailers"""
        # Run discovery for each retailer
        await self.discover_homepro_categories()
        await self.discover_thaiwatsadu_all_categories()
        await self.discover_globalhouse_categories()
        await self.discover_dohome_categories()
        await self.discover_boonthavorn_all_categories()
        await self.discover_megahome_categories()
        
        # Save results
        with open('all_retailer_categories.json', 'w', encoding='utf-8') as f:
            json.dump(self.discovered_categories, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print("SUMMARY OF ALL DISCOVERED CATEGORIES")
        print("="*80)
        
        total = 0
        for retailer, cats in self.discovered_categories.items():
            count = len(cats)
            total += count
            print(f"{retailer.upper()}: {count} categories")
        
        print(f"\nTOTAL CATEGORIES ACROSS ALL RETAILERS: {total}")
        print("\nFull results saved to: all_retailer_categories.json")
        
        return self.discovered_categories

async def main():
    discoverer = CategoryDiscoverer()
    await discoverer.discover_all()

if __name__ == "__main__":
    asyncio.run(main())