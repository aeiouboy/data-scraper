#!/usr/bin/env python3
"""
Monitor 10K HomePro scraping campaign progress
Real-time tracking of jobs and product counts
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def monitor_campaign():
    """Monitor the ongoing 10K campaign"""
    
    print("👀 MONITORING 10K HOMEPRO CAMPAIGN")
    print("=" * 50)
    print(f"Started monitoring at: {datetime.now().strftime('%H:%M:%S')}")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    check_count = 0
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            
            while True:
                check_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\n📊 Check #{check_count} ({timestamp})")
                print("-" * 30)
                
                # Get current product count
                try:
                    search_data = {"retailer_code": "HP", "page": 1, "page_size": 1}
                    async with session.post(
                        f"{base_url}/api/products/search",
                        json=search_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            total_products = result.get("total", 0)
                            progress_percent = (total_products / 10000) * 100
                            
                            print(f"📦 Total Products: {total_products:,}")
                            print(f"🎯 Progress: {progress_percent:.1f}% (target: 10,000)")
                            
                            if total_products >= 10000:
                                print(f"🏆 TARGET ACHIEVED! {total_products:,} products")
                                break
                        else:
                            print(f"❌ Failed to get product count (HTTP {response.status})")
                            total_products = 0
                except Exception as e:
                    print(f"❌ Error getting product count: {str(e)[:50]}")
                    total_products = 0
                
                # Get job status summary
                try:
                    async with session.get(f"{base_url}/api/scraping/jobs?limit=20") as response:
                        if response.status == 200:
                            result = await response.json()
                            jobs = result.get("jobs", [])
                            
                            if jobs:
                                running_jobs = [j for j in jobs if j.get("status") == "running"]
                                completed_jobs = [j for j in jobs if j.get("status") == "completed"]
                                failed_jobs = [j for j in jobs if j.get("status") == "failed"]
                                
                                total_success = sum(j.get("success_items", 0) for j in jobs)
                                total_discovered = sum(j.get("total_items", 0) for j in jobs)
                                
                                print(f"🔄 Jobs Running: {len(running_jobs)}")
                                print(f"✅ Jobs Completed: {len(completed_jobs)}")
                                print(f"❌ Jobs Failed: {len(failed_jobs)}")
                                print(f"📊 URLs Discovered: {total_discovered:,}")
                                print(f"✅ Products Scraped: {total_success:,}")
                                
                                if total_discovered > 0:
                                    success_rate = (total_success / total_discovered) * 100
                                    print(f"📈 Success Rate: {success_rate:.1f}%")
                                
                                # Show active jobs
                                if running_jobs:
                                    print(f"\n🔄 Active Jobs:")
                                    for job in running_jobs[:5]:
                                        category = job.get("target_url", "").split("/")[-1]
                                        success = job.get("success_items", 0)
                                        total = job.get("total_items", 0)
                                        print(f"   - {category}: {success}/{total}")
                            else:
                                print("📭 No active jobs found")
                        else:
                            print(f"❌ Failed to get job status (HTTP {response.status})")
                except Exception as e:
                    print(f"❌ Error getting job status: {str(e)[:50]}")
                
                # Wait before next check
                print(f"\n⏱️  Next check in 30 seconds...")
                await asyncio.sleep(30)
                
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(monitor_campaign())