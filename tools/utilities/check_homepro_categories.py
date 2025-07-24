#!/usr/bin/env python3
"""
Check existing HomePro categories in the database and show their details
"""
import sys
from pathlib import Path
import json
from collections import defaultdict, Counter

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.supabase_service import SupabaseService

# Known HomePro categories from scrape_all_categories.py
KNOWN_HOMEPRO_CATEGORIES = {
    "LIG": {
        "name": "โคมไฟและหลอดไฟ (Lighting)",
        "url": "https://www.homepro.co.th/c/LIG",
        "priority": 1,
        "estimated_products": 500
    },
    "PAI": {
        "name": "สีและอุปกรณ์ทาสี (Paint)",
        "url": "https://www.homepro.co.th/c/PAI", 
        "priority": 2,
        "estimated_products": 800
    },
    "BAT": {
        "name": "ห้องน้ำ (Bathroom)",
        "url": "https://www.homepro.co.th/c/BAT",
        "priority": 3,
        "estimated_products": 1200
    },
    "PLU": {
        "name": "งานระบบประปา (Plumbing)",
        "url": "https://www.homepro.co.th/c/PLU",
        "priority": 4,
        "estimated_products": 1500
    },
    "KIT": {
        "name": "ห้องครัวและอุปกรณ์ (Kitchen)",
        "url": "https://www.homepro.co.th/c/KIT",
        "priority": 5,
        "estimated_products": 2000
    },
    "SMA": {
        "name": "เครื่องใช้ไฟฟ้าขนาดเล็ก (Small Appliances)",
        "url": "https://www.homepro.co.th/c/SMA",
        "priority": 6,
        "estimated_products": 3000
    },
    "HHP": {
        "name": "จัดเก็บและของใช้ในบ้าน (Storage & Household)",
        "url": "https://www.homepro.co.th/c/HHP",
        "priority": 7,
        "estimated_products": 4000
    },
    "TVA": {
        "name": "ทีวี เครื่องเสียง เกม (TV, Audio, Gaming)",
        "url": "https://www.homepro.co.th/c/TVA",
        "priority": 8,
        "estimated_products": 5000
    },
    "FLO": {
        "name": "วัสดุปูพื้นและผนัง (Floor & Wall)",
        "url": "https://www.homepro.co.th/c/FLO",
        "priority": 9,
        "estimated_products": 6000
    },
    "FUR": {
        "name": "เฟอร์นิเจอร์และของแต่งบ้าน (Furniture & Decor)",
        "url": "https://www.homepro.co.th/c/FUR",
        "priority": 10,
        "estimated_products": 8000
    },
    "APP": {
        "name": "เครื่องใช้ไฟฟ้า (Appliances)",
        "url": "https://www.homepro.co.th/c/APP",
        "priority": 11,
        "estimated_products": 10000
    },
    "CON": {
        "name": "วัสดุก่อสร้าง (Construction Materials)",
        "url": "https://www.homepro.co.th/c/CON",
        "priority": 12,
        "estimated_products": 3500
    },
    "ELT": {
        "name": "ระบบไฟฟ้าและความปลอดภัย (Electrical & Safety)",
        "url": "https://www.homepro.co.th/c/ELT",
        "priority": 13,
        "estimated_products": 2500
    },
    "DOW": {
        "name": "ประตูและหน้าต่าง (Doors & Windows)",
        "url": "https://www.homepro.co.th/c/DOW",
        "priority": 14,
        "estimated_products": 2000
    },
    "TOO": {
        "name": "เครื่องมือและฮาร์ดแวร์ (Tools & Hardware)",
        "url": "https://www.homepro.co.th/c/TOO",
        "priority": 15,
        "estimated_products": 4000
    },
    "OUT": {
        "name": "เฟอร์นิเจอร์นอกบ้านและสวน (Outdoor & Garden)",
        "url": "https://www.homepro.co.th/c/OUT",
        "priority": 16,
        "estimated_products": 2500
    },
    "BED": {
        "name": "ห้องนอนและเครื่องนอน (Bedroom & Bedding)",
        "url": "https://www.homepro.co.th/c/BED",
        "priority": 17,
        "estimated_products": 3000
    },
    "SPO": {
        "name": "กีฬาและการเดินทาง (Sports & Travel)",
        "url": "https://www.homepro.co.th/c/SPO",
        "priority": 18,
        "estimated_products": 1500
    },
    "BEA": {
        "name": "ความงามและดูแลตัว (Beauty & Personal Care)",
        "url": "https://www.homepro.co.th/c/BEA",
        "priority": 19,
        "estimated_products": 2000
    },
    "MOM": {
        "name": "แม่และเด็ก (Mother & Baby)",
        "url": "https://www.homepro.co.th/c/MOM",
        "priority": 20,
        "estimated_products": 1800
    },
    "HEA": {
        "name": "สุขภาพ (Health)",
        "url": "https://www.homepro.co.th/c/HEA",
        "priority": 21,
        "estimated_products": 1200
    },
    "PET": {
        "name": "อุปกรณ์สัตว์เลี้ยง (Pet Supplies)",
        "url": "https://www.homepro.co.th/c/PET",
        "priority": 22,
        "estimated_products": 1000
    },
    "ATM": {
        "name": "ยานยนต์ (Automotive)",
        "url": "https://www.homepro.co.th/c/ATM",
        "priority": 23,
        "estimated_products": 1500
    }
}

def extract_category_code_from_url(url):
    """Extract category code from HomePro URL"""
    if not url:
        return None
    
    # Pattern: https://www.homepro.co.th/c/XXX
    import re
    match = re.search(r'/c/([A-Z]{3})', url)
    if match:
        return match.group(1)
    
    # Pattern: https://www.homepro.co.th/XXX/...
    match = re.search(r'homepro\.co\.th/([A-Z]{3})/', url)
    if match:
        return match.group(1)
    
    return None

def check_homepro_categories():
    """Check what HomePro categories are in the database"""
    print("🔍 Checking HomePro Categories in Database")
    print("=" * 80)
    
    db = SupabaseService()
    
    try:
        # Get all HomePro products with their categories and URLs
        response = db.client.table('products').select(
            'category, url, name, current_price, created_at, updated_at'
        ).eq('retailer_code', 'HP').execute()
        
        if not response.data:
            print("❌ No HomePro products found in database")
            return
        
        products = response.data
        total_products = len(products)
        
        print(f"📦 Total HomePro products: {total_products:,}")
        
        # Analyze categories
        categories_from_db = Counter()
        categories_from_urls = Counter()
        category_to_urls = defaultdict(set)
        category_to_products = defaultdict(list)
        
        for product in products:
            # Category from database field
            db_category = product.get('category')
            if db_category:
                categories_from_db[db_category] += 1
            
            # Category from URL
            url = product.get('url', '')
            url_category = extract_category_code_from_url(url)
            if url_category:
                categories_from_urls[url_category] += 1
                category_to_urls[url_category].add(url)
                category_to_products[url_category].append(product)
        
        print(f"\n📂 Categories found in database 'category' field: {len(categories_from_db)}")
        print(f"🔗 Categories found in product URLs: {len(categories_from_urls)}")
        
        # Show categories by URL (most reliable)
        print(f"\n📋 Categories by URL Analysis:")
        print("-" * 80)
        sorted_url_categories = sorted(categories_from_urls.items(), key=lambda x: x[1], reverse=True)
        
        for category_code, count in sorted_url_categories:
            known_info = KNOWN_HOMEPRO_CATEGORIES.get(category_code, {})
            category_name = known_info.get('name', 'Unknown')
            category_url = known_info.get('url', f'https://www.homepro.co.th/c/{category_code}')
            
            print(f"  {category_code}: {count:,} products - {category_name}")
            print(f"      URL: {category_url}")
            
            # Show sample URLs for this category
            sample_urls = list(category_to_urls[category_code])[:3]
            for url in sample_urls:
                print(f"      Sample: {url}")
        
        # Show database categories that don't match URL pattern
        print(f"\n📂 Categories in 'category' field (top 20):")
        print("-" * 80)
        sorted_db_categories = sorted(categories_from_db.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_db_categories[:20]:
            print(f"  {category}: {count:,} products")
        
        # Show missing categories
        print(f"\n🔍 Missing Categories (from known list):")
        print("-" * 80)
        found_codes = set(categories_from_urls.keys())
        missing_codes = set(KNOWN_HOMEPRO_CATEGORIES.keys()) - found_codes
        
        if missing_codes:
            for code in sorted(missing_codes):
                info = KNOWN_HOMEPRO_CATEGORIES[code]
                print(f"  {code}: {info['name']} - {info['url']}")
        else:
            print("  ✅ All known categories found!")
        
        # Generate re-scraping commands
        print(f"\n🚀 Re-scraping Commands:")
        print("-" * 80)
        print("# Re-scrape all found categories:")
        for category_code, count in sorted_url_categories:
            info = KNOWN_HOMEPRO_CATEGORIES.get(category_code, {})
            url = info.get('url', f'https://www.homepro.co.th/c/{category_code}')
            print(f"python scripts/scraping/scrape.py --retailer HP --category-url '{url}' --limit 1000")
        
        print("\n# Or use the comprehensive scraper:")
        print("python scripts/scraping/scrape_all_categories.py all --max-pages 100")
        
        # Generate category URLs for retailers.py
        print(f"\n📝 Category URLs for retailers.py:")
        print("-" * 80)
        print("category_urls = [")
        for category_code, count in sorted_url_categories:
            info = KNOWN_HOMEPRO_CATEGORIES.get(category_code, {})
            url = info.get('url', f'https://www.homepro.co.th/c/{category_code}')
            name = info.get('name', 'Unknown')
            print(f'    "{url}",  # {category_code} - {name} ({count:,} products)')
        print("]")
        
    except Exception as e:
        print(f"❌ Error checking categories: {str(e)}")

if __name__ == "__main__":
    check_homepro_categories()