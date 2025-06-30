"""
Check monitoring results after running
"""
import asyncio
import json
from datetime import datetime, timedelta
from app.services.supabase_service import SupabaseService
from app.services.category_monitor import CategoryMonitor

async def check_results():
    print("🔍 MONITORING RESULTS")
    print("="*50)
    
    monitor = CategoryMonitor()
    db = SupabaseService()
    
    # 1. Check for recent changes
    print("\n1️⃣ Recent Category Changes:")
    changes = await monitor.get_recent_changes('HP', days=1)
    
    if changes:
        print(f"   Found {len(changes)} changes:")
        for change in changes[:5]:
            print(f"   - {change['change_type']}: {change.get('new_value', {}).get('name', 'N/A')}")
            print(f"     Detected at: {change['detected_at']}")
    else:
        print("   ✅ No changes detected")
    
    # 2. Check category health
    print("\n2️⃣ Category Health:")
    health = await monitor.get_category_health('HP')
    print(f"   Health Score: {health['health_score']}/100")
    print(f"   Total Categories: {health['total_categories']}")
    print(f"   Active Categories: {health['active_categories']}")
    print(f"   Stale Categories: {health['stale_categories']}")
    
    # 3. Check recent alerts
    print("\n3️⃣ Recent Alerts:")
    alerts = db.client.table('scraper_alerts')\
        .select('*')\
        .eq('retailer_code', 'HP')\
        .gte('created_at', (datetime.now() - timedelta(hours=1)).isoformat())\
        .execute()
    
    if alerts.data:
        print(f"   ⚠️  Found {len(alerts.data)} alerts:")
        for alert in alerts.data[:3]:
            print(f"   - [{alert['severity']}] {alert['title']}")
    else:
        print("   ✅ No new alerts")
    
    # 4. Check verification status
    print("\n4️⃣ Category Verification Status:")
    # Get categories verified in last hour
    recent_verified = db.client.table('retailer_categories')\
        .select('category_code, category_name, last_verified')\
        .eq('retailer_code', 'HP')\
        .gte('last_verified', (datetime.now() - timedelta(hours=1)).isoformat())\
        .limit(5)\
        .execute()
    
    if recent_verified.data:
        print(f"   Recently verified {len(recent_verified.data)} categories:")
        for cat in recent_verified.data:
            print(f"   - {cat['category_name']} - Verified at {cat['last_verified'][:19]}")
    
    # 5. Show monitoring job status
    print("\n5️⃣ Recent Monitoring Jobs:")
    jobs = db.client.table('scrape_jobs')\
        .select('*')\
        .eq('job_type', 'category_discovery')\
        .order('created_at', desc=True)\
        .limit(3)\
        .execute()
    
    if jobs.data:
        for job in jobs.data:
            print(f"   - Job {job['id'][:8]}... - Status: {job['status']}")
            if job.get('duration_seconds'):
                print(f"     Duration: {job['duration_seconds']:.1f}s")

if __name__ == "__main__":
    asyncio.run(check_results())