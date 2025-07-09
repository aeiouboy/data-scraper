#!/usr/bin/env python3
"""
Migrate existing product data to fix category and availability fields
"""
import asyncio
import sys
import re
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

class ProductDataMigrator:
    """Migrate and fix product data"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        
        # Category mapping from URL patterns
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
    
    def extract_category_from_url(self, url: str) -> Optional[str]:
        """Extract category from URL pattern"""
        if not url:
            return None
        
        # Look for category code in URL (e.g., /c/LIG)
        match = re.search(r'/c/([A-Z]{3})', url)
        if match:
            category_code = match.group(1)
            return self.category_mapping.get(category_code, category_code)
        
        return None
    
    def infer_availability(self, product_data: dict) -> str:
        """Infer availability status from product data"""
        # If product has a current price, assume it's available
        if product_data.get('current_price'):
            return "in_stock"
        
        # If it has an original price but no current price, might be out of stock
        if product_data.get('original_price') and not product_data.get('current_price'):
            return "out_of_stock"
        
        return "unknown"
    
    async def migrate_products(self):
        """Migrate all products to fix category and availability"""
        print("🔄 Starting product data migration...")
        
        # Get all products
        try:
            result = self.supabase.client.table('products').select('*').execute()
            products = result.data
            
            if not products:
                print("No products found to migrate")
                return
            
            print(f"Found {len(products)} products to migrate")
            
            updated_count = 0
            
            for product in products:
                updates = {}
                
                # Fix category if missing or empty
                if not product.get('category') or product.get('category').strip() == '':
                    category = self.extract_category_from_url(product.get('url', ''))
                    if category:
                        updates['category'] = category
                
                # Fix availability if missing or unknown
                if not product.get('availability') or product.get('availability') == 'unknown':
                    availability = self.infer_availability(product)
                    updates['availability'] = availability
                
                # Update if we have changes
                if updates:
                    try:
                        self.supabase.client.table('products').update(updates).eq('id', product['id']).execute()
                        updated_count += 1
                        
                        print(f"✅ Updated product {product['sku']}: {updates}")
                    except Exception as e:
                        print(f"❌ Failed to update product {product['sku']}: {str(e)}")
            
            print(f"\n🎉 Migration completed! Updated {updated_count} products")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")

async def main():
    """Main migration function"""
    migrator = ProductDataMigrator()
    await migrator.migrate_products()

if __name__ == "__main__":
    asyncio.run(main())