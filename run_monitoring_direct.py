"""
Run category monitoring directly
"""
import asyncio
from datetime import datetime
from app.services.category_monitor import CategoryMonitor

async def run_monitoring():
    """Run category monitoring for all retailers or specific one"""
    
    print("🔍 CATEGORY MONITORING")
    print("="*50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    monitor = CategoryMonitor()
    
    # Choose monitoring mode
    print("\nSelect monitoring mode:")
    print("1. Monitor ALL retailers")
    print("2. Monitor HomePro only")
    print("3. Monitor specific retailer")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Monitor all retailers
        print("\n📊 Monitoring all retailers...")
        results = await monitor.monitor_all_retailers()
        
        print(f"\n✅ Monitoring complete!")
        print(f"   - Retailers checked: {results['retailers_checked']}")
        print(f"   - Total changes: {results['total_changes']}")
        print(f"   - Duration: {results['duration']:.2f} seconds")
        
        if results['changes_by_type']:
            print("\n📋 Changes by type:")
            for change_type, count in results['changes_by_type'].items():
                print(f"   - {change_type}: {count}")
                
    elif choice == "2":
        # Monitor HomePro
        print("\n📊 Monitoring HomePro...")
        result = await monitor.monitor_retailer('HP')
        
        print(f"\n✅ HomePro monitoring complete!")
        print(f"   - Categories checked: {result['categories_checked']}")
        print(f"   - Changes detected: {result['change_count']}")
        print(f"   - Critical changes: {result['critical_changes']}")
        print(f"   - Warning changes: {result['warning_changes']}")
        
    else:
        # Monitor specific retailer
        print("\nAvailable retailers:")
        print("HP - HomePro")
        print("TWD - Thai Watsadu")
        print("GH - Global House")
        print("DH - DoHome")
        print("BT - Boonthavorn")
        print("MH - MegaHome")
        
        retailer_code = input("\nEnter retailer code: ").strip().upper()
        
        print(f"\n📊 Monitoring {retailer_code}...")
        result = await monitor.monitor_retailer(retailer_code)
        
        print(f"\n✅ Monitoring complete!")
        print(f"   - Categories checked: {result['categories_checked']}")
        print(f"   - Changes detected: {result['change_count']}")
    
    # Show recent changes
    print("\n📝 Recent changes (last 7 days):")
    recent_changes = await monitor.get_recent_changes(days=7)
    
    if recent_changes:
        for change in recent_changes[:5]:  # Show first 5
            print(f"   - [{change['change_type']}] {change.get('retailer_code')} - {change.get('detected_at')}")
    else:
        print("   No changes detected")
    
    # Show category health
    print("\n💚 Category Health Summary:")
    for retailer_code in ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']:
        health = await monitor.get_category_health(retailer_code)
        if 'error' not in health:
            print(f"   {retailer_code}: {health['health_score']}/100 ({health['total_categories']} categories)")

if __name__ == "__main__":
    asyncio.run(run_monitoring())