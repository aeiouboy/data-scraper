#!/usr/bin/env python3
"""
Fix category data for existing products by analyzing their URLs and patterns
"""
import asyncio
import sys
import re
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

class CategoryFixer:
    """Fix category information for products"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        
        # Enhanced category mapping
        self.category_mapping = {
            'LIG': 'โคมไฟและหลอดไฟ',
            'PAI': 'สีและอุปกรณ์ทาสี', 
            'BAT': 'ห้องน้ำ',
            'PLU': 'งานระบบประปา',
            'KIT': 'ห้องครัวและอุปกรณ์',
            'SMA': 'เครื่องใช้ไฟฟ้าขนาดเล็ก',
            'HHP': 'จัดเก็บและของใช้ในบ้าน',
            'TVA': 'ทีวี เครื่องเสียง เกม',
            'FLO': 'วัสดุปูพื้นและผนัง',
            'FUR': 'เฟอร์นิเจอร์และของแต่งบ้าน',
            'APP': 'เครื่องใช้ไฟฟ้า',
            'CON': 'วัสดุก่อสร้าง',
            'ELT': 'ระบบไฟฟ้าและความปลอดภัย',
            'DOW': 'ประตูและหน้าต่าง',
            'TOO': 'เครื่องมือและฮาร์ดแวร์',
            'OUT': 'เฟอร์นิเจอร์นอกบ้านและสวน',
            'BED': 'ห้องนอนและเครื่องนอน',
            'SPO': 'กีฬาและการเดินทาง',
            'BEA': 'ความงามและดูแลตัว',
            'MOM': 'แม่และเด็ก',
            'HEA': 'สุขภาพ',
            'PET': 'อุปกรณ์สัตว์เลี้ยง',
            'ATM': 'ยานยนต์'
        }
        
        # Brand to category mapping for additional inference
        self.brand_category_hints = {
            'ECOFLOW': 'เครื่องใช้ไฟฟ้า',
            'HOMEPRO': 'เครื่องใช้ไฟฟ้า',  # Default for HomePro brand
            'PETUS': 'วัสดุก่อสร้าง',
            'LOVER HANDS': 'จัดเก็บและของใช้ในบ้าน',
            'lifree': 'จัดเก็บและของใช้ในบ้าน',
            'coleman': 'เฟอร์นิเจอร์และของแต่งบ้าน'
        }
        
        # Product name keywords to category mapping
        self.keyword_category_mapping = {
            'โคมไฟ': 'โคมไฟและหลอดไฟ',
            'หลอดไฟ': 'โคมไฟและหลอดไฟ',
            'สี': 'สีและอุปกรณ์ทาสี',
            'ห้องน้ำ': 'ห้องน้ำ',
            'ห้องครัว': 'ห้องครัวและอุปกรณ์',
            'เครื่องใช้ไฟฟ้า': 'เครื่องใช้ไฟฟ้า',
            'ทีวี': 'ทีวี เครื่องเสียง เกม',
            'เฟอร์นิเจอร์': 'เฟอร์นิเจอร์และของแต่งบ้าน',
            'เก้าอี้': 'เฟอร์นิเจอร์และของแต่งบ้าน',
            'โซฟา': 'เฟอร์นิเจอร์และของแต่งบ้าน',
            'กรรมพับ': 'จัดเก็บและของใช้ในบ้าน',
            'กล่อง': 'จัดเก็บและของใช้ในบ้าน',
            'ถุง': 'จัดเก็บและของใช้ในบ้าน',
            'POWER BOX': 'เครื่องใช้ไฟฟ้า',
            'CANVAS SLING': 'เฟอร์นิเจอร์และของแต่งบ้าน',
            'COMFORT SOFA': 'เฟอร์นิเจอร์และของแต่งบ้าน'
        }
    
    def extract_category_from_url(self, url: str) -> Optional[str]:
        """Extract category from URL pattern"""
        if not url:
            return None
        
        # Look for category code in URL (e.g., /c/LIG)
        match = re.search(r'/c/([A-Z]{3})', url)
        if match:
            category_code = match.group(1)
            return self.category_mapping.get(category_code)
        
        return None
    
    def infer_category_from_brand(self, brand: str) -> Optional[str]:
        """Infer category from brand"""
        if not brand:
            return None
        
        brand = brand.strip().upper()
        for brand_hint, category in self.brand_category_hints.items():
            if brand_hint.upper() in brand:
                return category
        
        return None
    
    def infer_category_from_name(self, name: str) -> Optional[str]:
        """Infer category from product name keywords"""
        if not name:
            return None
        
        name_upper = name.upper()
        for keyword, category in self.keyword_category_mapping.items():
            if keyword.upper() in name_upper:
                return category
        
        return None
    
    def determine_category(self, product: dict) -> Optional[str]:
        """Determine category using multiple methods"""
        # Method 1: URL-based extraction
        category = self.extract_category_from_url(product.get('url', ''))
        if category:
            return category
        
        # Method 2: Brand-based inference
        category = self.infer_category_from_brand(product.get('brand', ''))
        if category:
            return category
        
        # Method 3: Name-based inference
        category = self.infer_category_from_name(product.get('name', ''))
        if category:
            return category
        
        return None
    
    async def fix_categories(self):
        """Fix categories for all products"""
        print("🔧 Starting category fixing process...")
        
        try:
            # Get all products without category or with empty category
            result = self.supabase.client.table('products').select('*').or_('category.is.null,category.eq.').execute()
            products = result.data
            
            if not products:
                print("No products need category fixing")
                return
            
            print(f"Found {len(products)} products without categories")
            
            fixed_count = 0
            
            for product in products:
                category = self.determine_category(product)
                
                if category:
                    try:
                        self.supabase.client.table('products').update({
                            'category': category
                        }).eq('id', product['id']).execute()
                        
                        fixed_count += 1
                        print(f"✅ Fixed category for {product['sku']}: {category}")
                    except Exception as e:
                        print(f"❌ Failed to update category for {product['sku']}: {str(e)}")
                else:
                    print(f"⚠️  Could not determine category for {product['sku']} - {product.get('name', '')[:50]}...")
            
            print(f"\n🎉 Category fixing completed! Fixed {fixed_count} out of {len(products)} products")
            
        except Exception as e:
            print(f"❌ Category fixing failed: {str(e)}")

async def main():
    """Main function"""
    fixer = CategoryFixer()
    await fixer.fix_categories()

if __name__ == "__main__":
    asyncio.run(main())