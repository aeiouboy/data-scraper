"""
Quick monitoring check - no user input required
"""
import asyncio
from datetime import datetime
from app.services.category_monitor import CategoryMonitor

async def quick_monitor():
    """Quick monitoring for HomePro"""
    
    print("🔍 Quick Category Monitor - HomePro")
    print("="*40)
    
    monitor = CategoryMonitor()
    
    # Monitor HomePro
    print("Checking HomePro categories...")
    result = await monitor.monitor_retailer('HP')
    
    print(f"\n✅ Results:")
    print(f"   Categories checked: {result['categories_checked']}")
    print(f"   Changes found: {result['change_count']}")
    
    if result['change_count'] > 0:
        print(f"   ⚠️  Critical: {result['critical_changes']}")
        print(f"   ⚠️  Warnings: {result['warning_changes']}")
        
        if result['changes_by_type']:
            print("\n   Change types:")
            for change_type, count in result['changes_by_type'].items():
                print(f"   - {change_type}: {count}")
    
    # Get health score
    health = await monitor.get_category_health('HP')
    print(f"\n💚 Health Score: {health['health_score']}/100")
    print(f"   Active categories: {health['active_categories']}")
    print(f"   Stale categories: {health['stale_categories']}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(quick_monitor())