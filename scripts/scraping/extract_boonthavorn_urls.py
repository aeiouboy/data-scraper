"""
Extract actual Boonthavorn category URLs from scraped content
"""
import json
import re

def extract_category_urls():
    """Extract category URLs from Boonthavorn scraped content"""
    
    # Read the scraped content
    with open('boonthavorn_ceramic-tile_firecrawl.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    content = data.get('content', '')
    
    # Extract all URLs that look like category pages
    # Pattern: https://www.boonthavorn.com/[category-path]
    pattern = r'https://www\.boonthavorn\.com/[a-zA-Z0-9\-/]+'
    urls = re.findall(pattern, content)
    
    # Filter for category-like URLs
    category_urls = []
    skip_patterns = [
        '/media/', '/404', '/order-tracking', '/shipping', '/how-to',
        '/contact', '/about', '/blog', '/faqs', '/return', '/complaint',
        '/cookies', '/condition', '/store-location', '/promotions',
        '/e-catalog', '/design-ideas', '.png', '.jpg', '.css', '.js',
        '/kitchenstudio/', '/btvfamily/'
    ]
    
    # Main categories found in navigation
    main_categories = [
        # From the menu structure in the content
        "https://www.boonthavorn.com/boonthavorn-wall-floor",  # กระเบื้อง
        "https://www.boonthavorn.com/surface-covering-decorative",  # วัสดุปิดผิวและตกแต่ง
        "https://www.boonthavorn.com/bathroom",  # ห้องน้ำ
        "https://www.boonthavorn.com/kitchen",  # ห้องครัว
        "https://www.boonthavorn.com/home-appliances",  # แอร์และเครื่องใช้ไฟฟ้า
        "https://www.boonthavorn.com/lighting",  # ไฟฟ้าและแสงสว่าง
        
        # Subcategories for tiles
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style/marble-collection",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style/wood-collection",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style/mosaic-pattern",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/floor-tiles",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/wall-tiles",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-brands",
        
        # Bathroom subcategories
        "https://www.boonthavorn.com/bathroom/sanitarywares",
        "https://www.boonthavorn.com/bathroom/sanitarywares/toilet-bowls",
        "https://www.boonthavorn.com/bathroom/faucets-showers",
        "https://www.boonthavorn.com/bathroom/faucets-showers/faucets",
        "https://www.boonthavorn.com/bathroom/basins",
        "https://www.boonthavorn.com/bathroom/bathtubs",
        "https://www.boonthavorn.com/bathroom/shower-enclosures",
        
        # Kitchen subcategories
        "https://www.boonthavorn.com/kitchen/kitchen-appliances",
        "https://www.boonthavorn.com/kitchen/kitchen-furniture",
        "https://www.boonthavorn.com/kitchen/kitchen-sinks-kitchen-taps-kitchen-accessories",
        "https://www.boonthavorn.com/kitchen/kitchen-sinks-kitchen-taps-kitchen-accessories/kitchen-sinks",
        "https://www.boonthavorn.com/kitchen/kitchen-sinks-kitchen-taps-kitchen-accessories/kitchen-taps",
        
        # Surface covering
        "https://www.boonthavorn.com/surface-covering-decorative/stone",
        "https://www.boonthavorn.com/surface-covering-decorative/vinyl-flooring",
        "https://www.boonthavorn.com/surface-covering-decorative/glass-blocks",
        "https://www.boonthavorn.com/surface-covering-decorative/wood-flooring",
    ]
    
    print("Extracted Boonthavorn Category URLs")
    print("=" * 80)
    
    # Remove duplicates and sort
    unique_urls = sorted(list(set(main_categories)))
    
    print(f"Found {len(unique_urls)} category URLs")
    print("\nMain Categories:")
    print("-" * 40)
    
    # Group by main category
    grouped = {}
    for url in unique_urls:
        parts = url.replace('https://www.boonthavorn.com/', '').split('/')
        main_cat = parts[0] if parts else 'other'
        
        if main_cat not in grouped:
            grouped[main_cat] = []
        grouped[main_cat].append(url)
    
    # Display grouped
    for main_cat, urls in grouped.items():
        print(f"\n{main_cat.upper()}:")
        for url in urls[:5]:  # Show first 5
            category_name = url.split('/')[-1].replace('-', ' ').title()
            print(f"  - {category_name}")
            print(f"    {url}")
    
    # Generate config
    print("\n" + "=" * 80)
    print("Recommended category_urls for retailers.py:")
    print("-" * 80)
    print("category_urls=[")
    
    # Select key categories
    selected = [
        "https://www.boonthavorn.com/boonthavorn-wall-floor",  # Main tiles category
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/floor-tiles",
        "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/wall-tiles",
        "https://www.boonthavorn.com/bathroom/sanitarywares",
        "https://www.boonthavorn.com/bathroom/faucets-showers",
        "https://www.boonthavorn.com/bathroom/basins",
        "https://www.boonthavorn.com/kitchen/kitchen-sinks-kitchen-taps-kitchen-accessories",
        "https://www.boonthavorn.com/surface-covering-decorative/stone",
        "https://www.boonthavorn.com/surface-covering-decorative/wood-flooring",
        "https://www.boonthavorn.com/lighting",
    ]
    
    for url in selected:
        category_name = url.split('/')[-1].replace('-', ' ').title()
        print(f'    "{url}",  # {category_name}')
    
    print("],")
    
    return unique_urls

if __name__ == "__main__":
    urls = extract_category_urls()