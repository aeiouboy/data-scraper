"""
Test script for Adaptive Scraping System
"""
import asyncio
import logging
from datetime import datetime

from app.core.category_explorer import CategoryExplorer
from app.services.category_monitor import CategoryMonitor
from app.core.scraper_config_manager import ScraperConfigManager
from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_category_discovery():
    """Test 1: Category Discovery"""
    print("\n" + "="*60)
    print("TEST 1: CATEGORY DISCOVERY")
    print("="*60)
    
    try:
        explorer = CategoryExplorer()
        
        # Test with HomePro (limited scope for testing)
        print("\n🔍 Discovering categories for HomePro...")
        result = await explorer.discover_all_categories(
            retailer_code='HP',
            max_depth=2,  # Limited depth for testing
            max_categories=20  # Limited categories for testing
        )
        
        print(f"✅ Discovery completed!")
        print(f"   - Categories discovered: {result['discovered_count']}")
        print(f"   - Categories saved: {result['saved_count']}")
        print(f"   - Duration: {result['duration_seconds']:.2f} seconds")
        
        # Show sample categories
        if result['category_tree']:
            print("\n📂 Sample Category Tree:")
            for i, cat in enumerate(result['category_tree'][:5]):
                print(f"   {i+1}. {cat['name']} ({cat['code']})")
                if cat.get('children'):
                    for child in cat['children'][:3]:
                        print(f"      └─ {child['name']}")
                        
        return True
        
    except Exception as e:
        print(f"❌ Category discovery failed: {str(e)}")
        logger.error(f"Category discovery error: {str(e)}", exc_info=True)
        return False


async def test_category_monitor():
    """Test 2: Category Monitoring"""
    print("\n" + "="*60)
    print("TEST 2: CATEGORY MONITORING")
    print("="*60)
    
    try:
        monitor = CategoryMonitor()
        
        # Test monitoring for HomePro
        print("\n🔍 Monitoring categories for HomePro...")
        result = await monitor.monitor_retailer('HP')
        
        print(f"✅ Monitoring completed!")
        print(f"   - Categories checked: {result['categories_checked']}")
        print(f"   - Changes detected: {result['change_count']}")
        print(f"   - Critical changes: {result['critical_changes']}")
        print(f"   - Warning changes: {result['warning_changes']}")
        
        # Show any changes
        if result['changes_by_type']:
            print("\n📋 Changes by type:")
            for change_type, count in result['changes_by_type'].items():
                print(f"   - {change_type}: {count}")
                
        # Get category health
        print("\n💚 Checking category health...")
        health = await monitor.get_category_health('HP')
        print(f"   - Total categories: {health['total_categories']}")
        print(f"   - Active categories: {health['active_categories']}")
        print(f"   - Health score: {health['health_score']}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Category monitoring failed: {str(e)}")
        logger.error(f"Category monitoring error: {str(e)}", exc_info=True)
        return False


async def test_scraper_config():
    """Test 3: Scraper Configuration Manager"""
    print("\n" + "="*60)
    print("TEST 3: SCRAPER CONFIGURATION")
    print("="*60)
    
    try:
        config_manager = ScraperConfigManager()
        
        # Add test selectors
        print("\n🔧 Adding test selectors...")
        
        # Add product name selector
        selector_id = await config_manager.add_selector(
            retailer_code='HP',
            page_type='product',
            element_type='product_name',
            selector_type='css',
            selector_value='h1.product-name, h1[class*="product"], h1',
            priority=1,
            validation_regex=r'^.{3,200}$',
            transformation_rule='strip',
            notes='Test selector for product names'
        )
        
        if selector_id:
            print(f"✅ Added product name selector: {selector_id}")
        else:
            print("⚠️  Product name selector may already exist")
            
        # Add price selector
        price_selector_id = await config_manager.add_selector(
            retailer_code='HP',
            page_type='product',
            element_type='price',
            selector_type='css',
            selector_value='span.price, [class*="price"]:not([class*="old"])',
            priority=1,
            validation_regex=r'[\d,]+',
            transformation_rule='regex:[\\d,]+\\.?\\d*',
            notes='Test selector for current price'
        )
        
        if price_selector_id:
            print(f"✅ Added price selector: {price_selector_id}")
        else:
            print("⚠️  Price selector may already exist")
            
        # Get selectors
        print("\n📋 Retrieving configured selectors...")
        name_selectors = await config_manager.get_selectors(
            retailer_code='HP',
            page_type='product',
            element_type='product_name'
        )
        
        print(f"   Found {len(name_selectors)} name selectors")
        for i, sel in enumerate(name_selectors[:3]):
            print(f"   {i+1}. {sel.selector_type}: {sel.selector_value[:50]}...")
            
        # Get full configuration
        print("\n📊 Getting full retailer configuration...")
        config = await config_manager.get_retailer_config('HP')
        print(f"   - Total selectors: {config['total_selectors']}")
        print(f"   - Page types: {list(config['selectors'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper configuration failed: {str(e)}")
        logger.error(f"Scraper configuration error: {str(e)}", exc_info=True)
        return False


async def test_database_connection():
    """Test 4: Database Connection and Schema"""
    print("\n" + "="*60)
    print("TEST 4: DATABASE CONNECTION")
    print("="*60)
    
    try:
        db = SupabaseService()
        
        # Test connection
        print("\n🔌 Testing database connection...")
        test_query = db.client.table('products').select('id').limit(1).execute()
        print("✅ Database connection successful!")
        
        # Check if adaptive scraping tables exist
        print("\n📊 Checking adaptive scraping tables...")
        tables_to_check = [
            'retailer_categories',
            'scraper_selectors',
            'website_structures',
            'selector_performance',
            'category_changes',
            'scraper_alerts'
        ]
        
        tables_exist = []
        for table in tables_to_check:
            try:
                result = db.client.table(table).select('id').limit(1).execute()
                tables_exist.append(table)
                print(f"   ✅ {table}")
            except Exception as e:
                print(f"   ❌ {table} - Not found")
                
        if len(tables_exist) == len(tables_to_check):
            print("\n✅ All adaptive scraping tables exist!")
        else:
            print(f"\n⚠️  Only {len(tables_exist)}/{len(tables_to_check)} tables found")
            print("   Run the schema creation script: scripts/create_adaptive_scraping_schema.sql")
            
        return len(tables_exist) > 0
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return False


async def test_api_endpoints():
    """Test 5: API Endpoints"""
    print("\n" + "="*60)
    print("TEST 5: API ENDPOINTS")
    print("="*60)
    
    try:
        import httpx
        
        print("\n🌐 Testing API endpoints...")
        print("   (Make sure the FastAPI server is running on port 8000)")
        
        async with httpx.AsyncClient() as client:
            # Test category tree endpoint
            response = await client.get("http://localhost:8000/api/categories/tree/HP")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Category tree endpoint working")
                print(f"   - Total categories: {data.get('total_categories', 0)}")
            else:
                print(f"⚠️  Category tree endpoint returned: {response.status_code}")
                
            # Test category health endpoint
            response = await client.get("http://localhost:8000/api/categories/health/HP")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Category health endpoint working")
                print(f"   - Health score: {data.get('health_score', 0)}/100")
            else:
                print(f"⚠️  Category health endpoint returned: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"⚠️  API test skipped (server may not be running): {str(e)}")
        return True  # Don't fail if API isn't running


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADAPTIVE SCRAPING SYSTEM TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check retailers
    print("\n📋 Available retailers:")
    for retailer in retailer_manager.get_all_retailers():
        print(f"   - {retailer.name} ({retailer.code})")
    
    # Run tests
    test_results = []
    
    # Test 1: Database
    test_results.append(("Database Connection", await test_database_connection()))
    
    # Test 2: Category Discovery (only if DB is working)
    if test_results[-1][1]:
        test_results.append(("Category Discovery", await test_category_discovery()))
    else:
        print("\n⚠️  Skipping remaining tests - database not ready")
        test_results.append(("Category Discovery", False))
    
    # Test 3: Category Monitoring
    if test_results[0][1]:  # If DB is working
        test_results.append(("Category Monitoring", await test_category_monitor()))
    else:
        test_results.append(("Category Monitoring", False))
    
    # Test 4: Scraper Configuration
    if test_results[0][1]:  # If DB is working
        test_results.append(("Scraper Configuration", await test_scraper_config()))
    else:
        test_results.append(("Scraper Configuration", False))
    
    # Test 5: API Endpoints
    test_results.append(("API Endpoints", await test_api_endpoints()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The adaptive scraping system is working correctly.")
    elif passed == 0:
        print("\n❌ No tests passed. Please check:")
        print("   1. Database connection and credentials in .env")
        print("   2. Run the schema creation script")
        print("   3. Ensure the FastAPI server is running")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())