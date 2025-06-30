"""
Quick test for Adaptive Scraping System
"""
import asyncio
import logging
from datetime import datetime

from app.core.scraper_config_manager import ScraperConfigManager
from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def quick_test():
    """Quick test to verify system is working"""
    print("\n🚀 ADAPTIVE SCRAPING QUICK TEST")
    print("="*40)
    
    # 1. Test Database
    print("\n1️⃣ Testing Database Connection...")
    try:
        db = SupabaseService()
        
        # Check tables
        tables = ['retailer_categories', 'scraper_selectors']
        for table in tables:
            result = db.client.table(table).select('id').limit(1).execute()
            print(f"   ✅ Table '{table}' exists")
            
    except Exception as e:
        print(f"   ❌ Database error: {str(e)}")
        return
    
    # 2. Test Configuration Manager
    print("\n2️⃣ Testing Configuration Manager...")
    try:
        config_manager = ScraperConfigManager()
        
        # Get existing selectors
        selectors = await config_manager.get_selectors(
            retailer_code='HP',
            page_type='product',
            element_type='product_name'
        )
        print(f"   ✅ Found {len(selectors)} product name selectors")
        
        # Show configuration
        config = await config_manager.get_retailer_config('HP')
        print(f"   ✅ Total HP selectors: {config['total_selectors']}")
        
    except Exception as e:
        print(f"   ❌ Config manager error: {str(e)}")
    
    # 3. Test Category Stats
    print("\n3️⃣ Checking Category Statistics...")
    try:
        # Get category count
        result = db.client.table('retailer_categories')\
            .select('id', count='exact')\
            .eq('retailer_code', 'HP')\
            .execute()
            
        category_count = result.count or 0
        print(f"   ✅ HomePro categories in database: {category_count}")
        
        if category_count > 0:
            # Get sample categories
            sample = db.client.table('retailer_categories')\
                .select('category_name, category_code, level')\
                .eq('retailer_code', 'HP')\
                .limit(5)\
                .execute()
                
            print("   📂 Sample categories:")
            for cat in sample.data:
                print(f"      - {cat['category_name']} ({cat['category_code']}) - Level {cat['level']}")
    
    except Exception as e:
        print(f"   ❌ Category stats error: {str(e)}")
    
    # 4. Test Alerts
    print("\n4️⃣ Checking Recent Alerts...")
    try:
        alerts = db.client.table('scraper_alerts')\
            .select('alert_type, severity, title')\
            .eq('is_resolved', False)\
            .limit(5)\
            .order('created_at', desc=True)\
            .execute()
            
        if alerts.data:
            print(f"   ⚠️  Found {len(alerts.data)} unresolved alerts:")
            for alert in alerts.data:
                print(f"      - [{alert['severity']}] {alert['title']}")
        else:
            print("   ✅ No unresolved alerts")
            
    except Exception as e:
        print(f"   ❌ Alerts error: {str(e)}")
    
    print("\n" + "="*40)
    print("✅ Quick test completed!")
    print("\nNext steps:")
    print("1. Run category discovery: POST /api/categories/discover?retailer_code=HP")
    print("2. Configure selectors for your retailers")
    print("3. Start monitoring: POST /api/categories/monitor")
    print("4. Use adaptive scrapers with the mixin class")


if __name__ == "__main__":
    asyncio.run(quick_test())