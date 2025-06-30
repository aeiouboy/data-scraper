"""
Import all 23 HomePro categories from configuration
"""
import asyncio
from datetime import datetime
from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager, RetailerType

async def import_homepro_categories():
    """Import all configured HomePro categories"""
    print("📦 Importing HomePro Categories")
    print("="*50)
    
    # Get HomePro configuration
    hp_config = retailer_manager.get_retailer(RetailerType.HOMEPRO)
    
    print(f"Found {len(hp_config.category_urls)} categories in configuration")
    
    # Initialize database
    db = SupabaseService()
    
    imported = 0
    updated = 0
    
    for i, url in enumerate(hp_config.category_urls):
        # Extract category code from URL
        code = url.split('/')[-1]
        name = hp_config.category_mapping.get(code, f"Category {code}")
        
        print(f"\n{i+1}. Processing {code} - {name}")
        
        try:
            # Check if exists
            existing = db.client.table('retailer_categories')\
                .select('id')\
                .eq('retailer_code', 'HP')\
                .eq('category_code', code)\
                .execute()
            
            category_data = {
                'retailer_code': 'HP',
                'category_code': code,
                'category_name': name,
                'category_url': url,
                'level': 0,  # Root level
                'position': i,
                'is_active': True,
                'is_auto_discovered': False,
                'discovered_at': datetime.now().isoformat(),
                'last_verified': datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing
                result = db.client.table('retailer_categories')\
                    .update(category_data)\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
                print(f"   ✅ Updated existing category")
                updated += 1
            else:
                # Insert new
                result = db.client.table('retailer_categories')\
                    .insert(category_data)\
                    .execute()
                print(f"   ✅ Imported new category")
                imported += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print(f"✅ Import Complete!")
    print(f"   - New categories: {imported}")
    print(f"   - Updated categories: {updated}")
    print(f"   - Total: {imported + updated}/23")
    
    # Show all categories
    print("\n📂 All HomePro Categories:")
    all_cats = db.client.table('retailer_categories')\
        .select('category_code, category_name')\
        .eq('retailer_code', 'HP')\
        .order('position')\
        .execute()
    
    for cat in all_cats.data:
        print(f"   - {cat['category_code']}: {cat['category_name']}")
    
    return imported + updated

if __name__ == "__main__":
    asyncio.run(import_homepro_categories())