"""
Discover ALL Thai Watsadu categories systematically
"""
import asyncio
import aiohttp
import json
from urllib.parse import quote

async def check_category_exists(session, base_url, category_name, category_id):
    """Check if a category URL exists"""
    url = f"{base_url}/th/category/{quote(category_name)}-{category_id}"
    try:
        async with session.head(url, timeout=5, allow_redirects=True) as response:
            if response.status == 200:
                return {
                    'name': category_name,
                    'id': category_id,
                    'url': str(response.url),
                    'original_url': url
                }
    except:
        pass
    return None

async def discover_all_twd_categories():
    """Discover all Thai Watsadu categories"""
    print("Discovering ALL Thai Watsadu Categories")
    print("=" * 80)
    
    base_url = "https://www.thaiwatsadu.com"
    all_categories = []
    
    async with aiohttp.ClientSession() as session:
        # 1. Check main category IDs (1-999)
        print("\n1. Checking main category IDs (1-999)...")
        tasks = []
        for i in range(1, 1000):
            # Try with generic name first
            task = check_category_exists(session, base_url, str(i), str(i))
            tasks.append(task)
            
            # Batch requests
            if len(tasks) >= 20:
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result:
                        all_categories.append(result)
                        print(f"✓ Found: ID {result['id']}")
                tasks = []
                await asyncio.sleep(0.5)
        
        # Process remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)
            for result in results:
                if result:
                    all_categories.append(result)
                    print(f"✓ Found: ID {result['id']}")
        
        print(f"\nFound {len(all_categories)} main categories")
        
        # 2. Check subcategory patterns (XXYY where XX is main category)
        print("\n2. Checking subcategory patterns...")
        
        # Known main category IDs from previous discovery
        known_main_ids = [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]
        
        for main_id in known_main_ids:
            print(f"\nChecking subcategories for main category {main_id}...")
            tasks = []
            
            # Check patterns: 5101-5199, 5201-5299, etc.
            for sub in range(1, 100):
                sub_id = f"{main_id}{sub:02d}"
                task = check_category_exists(session, base_url, sub_id, sub_id)
                tasks.append(task)
                
                if len(tasks) >= 10:
                    results = await asyncio.gather(*tasks)
                    for result in results:
                        if result:
                            all_categories.append(result)
                            print(f"  ✓ Found subcategory: {result['id']}")
                    tasks = []
                    await asyncio.sleep(0.3)
            
            if tasks:
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result:
                        all_categories.append(result)
                        print(f"  ✓ Found subcategory: {result['id']}")
        
        # 3. Check special patterns (4-digit and 6-digit IDs)
        print("\n3. Checking special ID patterns...")
        special_ids = [
            # Known special IDs
            6010, 6110, 719900,
            # Check some ranges
            *range(1000, 1100, 10),
            *range(6000, 6200, 10),
            *range(7000, 7200, 100),
            *range(700000, 720000, 1000)
        ]
        
        tasks = []
        for special_id in special_ids:
            task = check_category_exists(session, base_url, str(special_id), str(special_id))
            tasks.append(task)
            
            if len(tasks) >= 10:
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result:
                        all_categories.append(result)
                        print(f"✓ Found special category: {result['id']}")
                tasks = []
                await asyncio.sleep(0.3)
        
        if tasks:
            results = await asyncio.gather(*tasks)
            for result in results:
                if result:
                    all_categories.append(result)
                    print(f"✓ Found special category: {result['id']}")
    
    # Remove duplicates based on URL
    unique_categories = {}
    for cat in all_categories:
        unique_categories[cat['url']] = cat
    
    final_categories = list(unique_categories.values())
    
    # Sort by ID
    final_categories.sort(key=lambda x: (len(str(x['id'])), x['id']))
    
    # Save results
    with open('twd_all_categories.json', 'w', encoding='utf-8') as f:
        json.dump(final_categories, f, ensure_ascii=False, indent=2)
    
    # Generate category_urls list
    print("\n" + "=" * 80)
    print(f"TOTAL THAI WATSADU CATEGORIES FOUND: {len(final_categories)}")
    print("=" * 80)
    
    print("\nCategory URLs for retailers.py:")
    print("-" * 80)
    print("category_urls=[")
    for cat in final_categories:
        print(f'    "{cat["url"]}",  # ID: {cat["id"]}')
    print("],")
    
    # Also save just the URLs
    urls_only = [cat['url'] for cat in final_categories]
    with open('twd_category_urls.txt', 'w', encoding='utf-8') as f:
        f.write("category_urls=[\n")
        for url in urls_only:
            f.write(f'    "{url}",\n')
        f.write("]\n")
    
    print(f"\nResults saved to:")
    print("- twd_all_categories.json (full details)")
    print("- twd_category_urls.txt (URLs only for easy copying)")
    
    return final_categories

async def main():
    await discover_all_twd_categories()

if __name__ == "__main__":
    asyncio.run(main())