#!/usr/bin/env python3
"""
Monitor the 10K+ product scraping jobs
"""
import requests
import time
import json

# Job IDs for our 10K test
JOBS = [
    {"id": "5f1753fd-f8ce-426c-8e7f-554bf0d6219e", "name": "TOO (Tools)", "pages": 100},
    {"id": "f40c9fcd-f9bc-48e9-a9a4-20ccdfa48e54", "name": "APP (Appliances)", "pages": 80},
    {"id": "e059d71e-01f7-4f8c-8c9e-56d1564b8c96", "name": "CON (Construction)", "pages": 120}
]

BASE_URL = "http://localhost:8001"

def check_job_status(job_id):
    """Check individual job status"""
    try:
        response = requests.get(f"{BASE_URL}/api/scraping/jobs/{job_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error checking job {job_id}: {str(e)}")
        return None

def monitor_jobs():
    """Monitor all 10K scraping jobs"""
    
    print("🔍 Monitoring 10K+ Product Scraping Jobs")
    print("=" * 50)
    
    check_count = 0
    total_discovered = 0
    total_processed = 0
    total_success = 0
    total_failed = 0
    
    while True:
        check_count += 1
        print(f"\n📊 Status Check #{check_count} ({time.strftime('%H:%M:%S')})")
        print("-" * 50)
        
        all_completed = True
        current_total_discovered = 0
        current_total_processed = 0
        current_total_success = 0
        current_total_failed = 0
        
        for job in JOBS:
            status = check_job_status(job["id"])
            
            if status:
                job_status = status.get("status", "unknown")
                total_items = status.get("total_items", 0)
                processed_items = status.get("processed_items", 0)
                success_items = status.get("success_items", 0)
                failed_items = status.get("failed_items", 0)
                
                current_total_discovered += total_items
                current_total_processed += processed_items
                current_total_success += success_items
                current_total_failed += failed_items
                
                # Status icon
                if job_status == "completed":
                    status_icon = "✅"
                elif job_status == "running":
                    status_icon = "🔄"
                    all_completed = False
                elif job_status == "pending":
                    status_icon = "⏳"
                    all_completed = False
                else:
                    status_icon = "❌"
                
                # Progress calculation
                if total_items > 0:
                    progress = (processed_items / total_items) * 100
                    success_rate = (success_items / processed_items * 100) if processed_items > 0 else 0
                    print(f"{status_icon} {job['name']:<15}: {processed_items:>4,}/{total_items:>4,} ({progress:>5.1f}%) | Success: {success_items:>4,} ({success_rate:>5.1f}%)")
                else:
                    print(f"{status_icon} {job['name']:<15}: Discovering URLs... ({job['pages']} pages)")
            else:
                print(f"❌ {job['name']:<15}: Failed to get status")
        
        # Overall summary
        if current_total_discovered > 0:
            overall_progress = (current_total_processed / current_total_discovered) * 100
            overall_success_rate = (current_total_success / current_total_processed * 100) if current_total_processed > 0 else 0
        else:
            overall_progress = 0
            overall_success_rate = 0
        
        print("-" * 50)
        print(f"🎯 TOTAL: {current_total_processed:,}/{current_total_discovered:,} ({overall_progress:.1f}%) | Success: {current_total_success:,} ({overall_success_rate:.1f}%)")
        
        # Check if we've hit our 10K target
        if current_total_processed >= 10000:
            print(f"🏆 TARGET ACHIEVED! Processed {current_total_processed:,} products (>10K goal)")
        elif current_total_discovered >= 10000:
            print(f"🎯 Target in sight! Discovered {current_total_discovered:,} products")
        
        # Show changes from last check
        if check_count > 1:
            new_discovered = current_total_discovered - total_discovered
            new_processed = current_total_processed - total_processed
            new_success = current_total_success - total_success
            
            if new_discovered > 0 or new_processed > 0:
                print(f"📈 Since last check: +{new_discovered:,} discovered, +{new_processed:,} processed, +{new_success:,} successful")
        
        # Update totals
        total_discovered = current_total_discovered
        total_processed = current_total_processed
        total_success = current_total_success
        total_failed = current_total_failed
        
        if all_completed:
            print(f"\n🎉 ALL JOBS COMPLETED!")
            print(f"📊 Final Results:")
            print(f"   - Total Products Discovered: {total_discovered:,}")
            print(f"   - Total Products Processed: {total_processed:,}")
            print(f"   - Successful: {total_success:,}")
            print(f"   - Failed: {total_failed:,}")
            print(f"   - Overall Success Rate: {(total_success/total_processed*100):.2f}%")
            
            if total_processed >= 10000:
                print(f"🏆 10K TARGET ACHIEVED! 🎊")
            else:
                print(f"📊 Processed {total_processed:,} products")
            
            break
        
        # Wait before next check
        print(f"⏱️  Next check in 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    try:
        monitor_jobs()
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")