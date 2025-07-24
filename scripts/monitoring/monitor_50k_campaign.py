#!/usr/bin/env python3
"""
Monitor 50K HomePro Campaign Progress
Real-time tracking with extended timeouts for heavy load
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import time

class CampaignMonitor:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=60)  # Extended timeout
        
    async def get_campaign_status(self):
        """Get comprehensive campaign status"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                
                # Get job statistics
                async with session.get(f"{self.base_url}/api/scraping/jobs?limit=50") as response:
                    if response.status == 200:
                        jobs_data = await response.json()
                        jobs = jobs_data.get("jobs", [])
                        
                        # Analyze job status
                        running_jobs = [j for j in jobs if j.get("status") == "running"]
                        completed_jobs = [j for j in jobs if j.get("status") == "completed"]
                        failed_jobs = [j for j in jobs if j.get("status") == "failed"]
                        pending_jobs = [j for j in jobs if j.get("status") == "pending"]
                        
                        total_discovered = sum(j.get("total_items", 0) for j in jobs)
                        total_success = sum(j.get("success_items", 0) for j in jobs)
                        total_failed = sum(j.get("failed_items", 0) for j in jobs)
                        
                        return {
                            "total_jobs": len(jobs),
                            "running": len(running_jobs),
                            "completed": len(completed_jobs),
                            "failed": len(failed_jobs),
                            "pending": len(pending_jobs),
                            "urls_discovered": total_discovered,
                            "products_scraped": total_success,
                            "failed_scrapes": total_failed,
                            "success_rate": (total_success / total_discovered * 100) if total_discovered > 0 else 0,
                            "running_jobs_sample": running_jobs[:5],
                            "completed_jobs_sample": completed_jobs[:3]
                        }
                    else:
                        return {"error": f"HTTP {response.status}"}
                        
        except asyncio.TimeoutError:
            return {"error": "Timeout - API under heavy load"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_product_count(self):
        """Get current total product count"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                search_data = {"retailer_code": "HP", "page": 1, "page_size": 1}
                
                async with session.post(
                    f"{self.base_url}/api/products/search",
                    json=search_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("total", 0)
                    else:
                        return None
        except:
            return None
    
    async def monitor_campaign(self, duration_minutes: int = 60):
        """Monitor campaign for specified duration"""
        
        print("🔥 50K HOMEPRO CAMPAIGN MONITOR")
        print("=" * 60)
        print(f"📅 Started monitoring: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"🎯 Target: 50,000+ products")
        print("=" * 60)
        
        start_time = time.time()
        check_count = 0
        last_product_count = 0
        
        while time.time() - start_time < duration_minutes * 60:
            check_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n📊 CHECK #{check_count} ({timestamp})")
            print("-" * 40)
            
            # Get campaign status
            status = await self.get_campaign_status()
            
            if "error" in status:
                print(f"⚠️  API Status: {status['error']}")
                print("   System is under heavy load - this is expected during 50K campaign")
            else:
                print(f"🔄 Jobs: {status['running']} running, {status['completed']} completed, {status['failed']} failed")
                print(f"📊 Progress: {status['products_scraped']:,} scraped from {status['urls_discovered']:,} discovered")
                
                if status['urls_discovered'] > 0:
                    print(f"📈 Success Rate: {status['success_rate']:.1f}%")
                
                # Show sample of active jobs
                if status['running_jobs_sample']:
                    print(f"\n🔄 Active Jobs Sample:")
                    for job in status['running_jobs_sample']:
                        category = job.get("target_url", "").split("/")[-1][:10]
                        success = job.get("success_items", 0)
                        total = job.get("total_items", 0)
                        print(f"   - {category}: {success}/{total}")
            
            # Get product count (if API is responsive)
            product_count = await self.get_product_count()
            if product_count is not None:
                growth = product_count - last_product_count if last_product_count > 0 else 0
                progress_percent = (product_count / 50000) * 100
                
                print(f"\n📦 Database Products: {product_count:,}")
                print(f"📈 Growth this check: +{growth:,}")
                print(f"🎯 Progress to 50K: {progress_percent:.1f}%")
                
                if product_count >= 50000:
                    print(f"\n🏆 🎉 TARGET ACHIEVED! 🎉 🏆")
                    print(f"✅ Successfully scraped {product_count:,} products!")
                    break
                    
                last_product_count = product_count
            else:
                print(f"📦 Database: API timeout (system under load)")
            
            # Campaign health assessment
            if "error" not in status:
                if status['running'] > 10:
                    print(f"💪 Campaign Status: ACTIVE ({status['running']} jobs running)")
                elif status['running'] > 0:
                    print(f"⚡ Campaign Status: FINISHING ({status['running']} jobs remaining)")
                else:
                    print(f"✅ Campaign Status: COMPLETED (all jobs done)")
                    break
            
            # Wait before next check
            print(f"\n⏱️  Next check in 60 seconds...")
            await asyncio.sleep(60)
        
        print(f"\n🎊 MONITORING SESSION COMPLETE")
        print(f"⏱️  Duration: {(time.time() - start_time)/60:.1f} minutes")
        print(f"📊 Final Status: Check the UI for latest results")
        print(f"🌐 Frontend: http://localhost:3000 (Complete Catalog tab)")

async def main():
    monitor = CampaignMonitor()
    
    try:
        # Monitor for 1 hour by default
        await monitor.monitor_campaign(duration_minutes=60)
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())