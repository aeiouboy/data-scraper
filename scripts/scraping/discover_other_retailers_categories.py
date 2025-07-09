"""
Discover categories for Global House, DoHome, and MegaHome
"""
import asyncio
from src.services.firecrawl_client import FirecrawlClient
from dotenv import load_dotenv
import json
import re

load_dotenv()

async def discover_globalhouse_categories():
    """Discover Global House categories"""
    print("\n" + "="*80)
    print("DISCOVERING GLOBAL HOUSE CATEGORIES")
    print("="*80)
    
    firecrawl = FirecrawlClient()
    base_url = "https://www.globalhouse.co.th"
    categories = set()
    
    try:
        result = await firecrawl.scrape(base_url)
        if result:
            # Extract links
            links = result.get('linksOnPage', result.get('links', []))
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                # Global House category patterns
                if 'globalhouse.co.th' in href:
                    # Look for category-like URLs
                    category_patterns = [
                        r'/([a-z-]+)/?$',  # Simple category pattern
                        r'/category/([a-z-]+)',
                        r'/c/([a-z-]+)',
                        r'/products/([a-z-]+)'
                    ]
                    
                    for pattern in category_patterns:
                        match = re.search(pattern, href)
                        if match:
                            category = match.group(1)
                            # Filter out non-category pages
                            skip = ['about', 'contact', 'privacy', 'terms', 'cart', 'checkout', 
                                   'account', 'login', 'register', 'search', 'blog', 'news',
                                   'promotion', 'help', 'faq', 'shipping', 'return', 'payment']
                            if category not in skip and len(category) > 2:
                                categories.add(href)
                                break
    except Exception as e:
        print(f"Error: {e}")
    
    # Add known categories
    known_categories = [
        'furniture', 'home-decor', 'lighting', 'kitchen-dining', 'bathroom',
        'bedroom', 'living-room', 'outdoor', 'office', 'storage', 'garden',
        'tools', 'electrical', 'plumbing', 'paint', 'flooring', 'tiles',
        'doors-windows', 'construction', 'hardware', 'appliances', 'cleaning',
        'automotive', 'sports', 'toys', 'pet-supplies', 'textiles', 'curtains',
        'rugs', 'bedding', 'kitchen-appliances', 'small-appliances', 'furniture-parts',
        'wood-materials', 'metal-materials', 'safety-equipment', 'power-tools',
        'hand-tools', 'measuring-tools', 'fasteners', 'adhesives', 'sealants',
        'insulation', 'roofing', 'ceiling', 'wall-materials', 'decorative-items'
    ]
    
    for cat in known_categories:
        categories.add(f"{base_url}/{cat}")
    
    return sorted(list(categories))

async def discover_dohome_categories():
    """Discover DoHome categories"""
    print("\n" + "="*80)
    print("DISCOVERING DOHOME CATEGORIES")
    print("="*80)
    
    firecrawl = FirecrawlClient()
    base_url = "https://www.dohome.co.th"
    categories = set()
    
    try:
        result = await firecrawl.scrape(base_url)
        if result:
            # Extract links
            links = result.get('linksOnPage', result.get('links', []))
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                if 'dohome.co.th' in href:
                    # DoHome patterns
                    patterns = [r'/category/', r'/c/', r'/-c-']
                    for pattern in patterns:
                        if pattern in href:
                            categories.add(href)
                            break
    except Exception as e:
        print(f"Error: {e}")
    
    # Add known categories
    known_categories = [
        'hardware-tools', 'electrical', 'plumbing', 'paint', 'building-materials',
        'garden', 'automotive', 'household', 'furniture', 'bathroom', 'kitchen',
        'lighting', 'flooring', 'tiles', 'doors-windows', 'safety', 'storage',
        'cleaning', 'appliances', 'outdoor-living', 'power-tools', 'hand-tools',
        'fasteners', 'adhesives', 'roofing', 'insulation', 'concrete', 'steel',
        'wood', 'cement', 'bricks', 'sand', 'stone', 'glass', 'plastic',
        'metal-sheets', 'pipes', 'fittings', 'valves', 'pumps', 'tanks',
        'filters', 'heaters', 'coolers', 'fans', 'air-conditioning', 'ventilation',
        'locks', 'hinges', 'handles', 'brackets', 'screws', 'nails', 'bolts'
    ]
    
    for cat in known_categories:
        categories.add(f"{base_url}/{cat}")
        categories.add(f"{base_url}/category/{cat}")
    
    return sorted(list(categories))

async def discover_megahome_categories():
    """Discover MegaHome categories"""
    print("\n" + "="*80)
    print("DISCOVERING MEGAHOME CATEGORIES")
    print("="*80)
    
    firecrawl = FirecrawlClient()
    base_url = "https://www.megahome.co.th"
    categories = set()
    
    try:
        result = await firecrawl.scrape(base_url)
        if result:
            # Extract links
            links = result.get('linksOnPage', result.get('links', []))
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                if 'megahome.co.th' in href:
                    # Category patterns
                    patterns = ['/category/', '/c/', '/product-category/']
                    for pattern in patterns:
                        if pattern in href:
                            categories.add(href)
                            break
    except Exception as e:
        print(f"Error: {e}")
    
    # Add known categories
    known_categories = [
        'building-materials', 'tools-hardware', 'electrical-plumbing',
        'paint-coating', 'roofing', 'flooring', 'garden-outdoor',
        'safety-equipment', 'concrete-cement', 'steel-metal', 'wood-lumber',
        'tiles-ceramic', 'doors-windows', 'insulation', 'adhesives-sealants',
        'fasteners', 'plumbing-fixtures', 'electrical-supplies', 'lighting',
        'hvac', 'power-tools', 'hand-tools', 'measuring-tools', 'safety-gear',
        'construction-equipment', 'industrial-supplies', 'automotive-supplies',
        'cleaning-supplies', 'packaging-materials', 'storage-solutions',
        'workshop-equipment', 'welding-supplies', 'painting-supplies',
        'concrete-tools', 'masonry-tools', 'drywall-tools', 'flooring-tools',
        'roofing-tools', 'plumbing-tools', 'electrical-tools', 'landscaping',
        'irrigation', 'fencing', 'decking', 'outdoor-furniture', 'grills-bbq',
        'generators', 'compressors', 'ladders', 'scaffolding', 'wheelbarrows'
    ]
    
    for cat in known_categories:
        categories.add(f"{base_url}/{cat}")
        categories.add(f"{base_url}/category/{cat}")
    
    return sorted(list(categories))

async def main():
    """Discover categories for all retailers"""
    all_results = {}
    
    # Global House
    gh_categories = await discover_globalhouse_categories()
    all_results['globalhouse'] = gh_categories
    print(f"\nFound {len(gh_categories)} Global House categories")
    
    # DoHome
    dh_categories = await discover_dohome_categories()
    all_results['dohome'] = dh_categories
    print(f"\nFound {len(dh_categories)} DoHome categories")
    
    # MegaHome
    mh_categories = await discover_megahome_categories()
    all_results['megahome'] = mh_categories
    print(f"\nFound {len(mh_categories)} MegaHome categories")
    
    # Save results
    with open('other_retailers_categories.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print formatted output
    print("\n" + "="*80)
    print("CATEGORY URLS FOR RETAILERS.PY")
    print("="*80)
    
    print("\n# Global House")
    print("category_urls=[")
    for url in gh_categories[:30]:  # Limit to 30 most relevant
        cat_name = url.split('/')[-1].replace('-', ' ').title()
        print(f'    "{url}",  # {cat_name}')
    print("],")
    
    print("\n# DoHome")
    print("category_urls=[")
    for url in dh_categories[:25]:  # Limit to 25 most relevant
        cat_name = url.split('/')[-1].replace('-', ' ').title()
        print(f'    "{url}",  # {cat_name}')
    print("],")
    
    print("\n# MegaHome")
    print("category_urls=[")
    for url in mh_categories[:25]:  # Limit to 25 most relevant
        cat_name = url.split('/')[-1].replace('-', ' ').title()
        print(f'    "{url}",  # {cat_name}')
    print("],")

if __name__ == "__main__":
    asyncio.run(main())