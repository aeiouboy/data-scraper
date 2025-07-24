#!/usr/bin/env python3
"""
Controlled 10K HomePro SKU scraping campaign
Strategy: Resource-aware job creation with progressive scaling
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

class ControlledScrapingCampaign:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.max_concurrent_jobs = 3  # Conservative limit
        self.job_batch_size = 2
        self.job_creation_delay = 5  # seconds between batches
        
    async def launch_controlled_campaign(self):
        """Launch controlled 10K campaign with resource management"""
        
        print("🎯 CONTROLLED 10K HOMEPRO CAMPAIGN")
        print("=" * 50)
        print(f"📅 Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⚡ Strategy: Progressive scaling with resource limits")
        print(f"🛡️ Max concurrent jobs: {self.max_concurrent_jobs}")
        print("=" * 50)
        
        # High-yield categories with proven product counts
        priority_categories = [
            ("APP", "เครื่องใช้ไฟฟ้า", 5),  # 5 pages for high-volume categories
            ("TOO", "เครื่องมือและฮาร์ดแวร์", 5),
            ("ELT", "ระบบไฟฟ้าและความปลอดภัย", 5),
            ("CON", "วัสดุก่อสร้าง", 5),
            ("FUR", "เฟอร์นิเจอร์และของแต่งบ้าน", 5),
            ("BAT", "ห้องน้ำ", 4),
            ("KIT", "ห้องครัวและอุปกรณ์", 4),
            ("LIG", "โคมไฟและหลอดไฟ", 4),
            ("PAI", "สีและอุปกรณ์ทาสี", 4),
            ("PLU", "งานระบบประปา", 4),
            ("HHP", "จัดเก็บและของใช้ในบ้าน", 3),
            ("TVA", "ทีวี เครื่องเสียง เกม", 3),
            ("FLO", "วัสดุปูพื้นและผนัง", 3),
            ("DOW", "ประตูและหน้าต่าง", 3),
            ("OUT", "เฟอร์นิเจอร์นอกบ้านและสวน", 3),
        ]
        
        successful_jobs = []
        current_product_count = await self.get_current_product_count()
        
        print(f"📊 Current product count: {current_product_count:,}")
        target_remaining = 10000 - current_product_count
        print(f"🎯 Target remaining: {target_remaining:,} products")
        
        if target_remaining <= 0:
            print("🏆 Target already achieved!")
            return successful_jobs
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            
            for batch_start in range(0, len(priority_categories), self.job_batch_size):
                batch_end = min(batch_start + self.job_batch_size, len(priority_categories))
                batch_categories = priority_categories[batch_start:batch_end]
                
                print(f"\n📦 Batch {batch_start//self.job_batch_size + 1}: Creating {len(batch_categories)} jobs")
                
                # Create jobs in this batch
                batch_jobs = []
                for category_code, category_name, max_pages in batch_categories:
                    try:
                        job = await self.create_category_job(
                            session, category_code, category_name, max_pages
                        )
                        if job:
                            batch_jobs.append(job)
                            print(f"   ✅ {category_code}: {job['id'][:8]}... ({max_pages} pages)")
                        else:
                            print(f"   ❌ {category_code}: Failed to create")
                    except Exception as e:
                        print(f"   ❌ {category_code}: {str(e)[:50]}")
                
                successful_jobs.extend(batch_jobs)
                
                # Wait for jobs to complete before creating more
                if batch_jobs:
                    print(f"   ⏳ Waiting for batch completion...")
                    await self.wait_for_batch_completion(session, batch_jobs)
                    
                    # Check progress
                    new_count = await self.get_current_product_count()
                    products_added = new_count - current_product_count
                    current_product_count = new_count
                    
                    print(f"   📈 Products added this batch: {products_added}")
                    print(f"   📊 Total products now: {current_product_count:,}")
                    
                    if current_product_count >= 10000:
                        print(f"\n🏆 TARGET ACHIEVED! {current_product_count:,} products")
                        break
                
                # Pause between batches to prevent overload
                if batch_end < len(priority_categories):
                    print(f"   ⏸️  Cooling down for {self.job_creation_delay}s...")
                    await asyncio.sleep(self.job_creation_delay)
        
        final_count = await self.get_current_product_count()
        print(f"\n🎉 CAMPAIGN COMPLETE!")
        print(f"📊 Final product count: {final_count:,}")
        print(f"🎯 Target status: {'✅ ACHIEVED' if final_count >= 10000 else '📈 IN PROGRESS'}")
        print(f"✅ Jobs created: {len(successful_jobs)}")
        
        return successful_jobs
    
    async def create_category_job(self, session: aiohttp.ClientSession, 
                                 category_code: str, category_name: str, max_pages: int) -> Optional[Dict]:
        """Create a single category scraping job with pagination"""
        category_url = f"https://www.homepro.co.th/c/{category_code}"
        
        job_data = {
            "job_type": "category",
            "target_url": category_url,
            "retailer_code": "HP",
            "max_pages": max_pages
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/scraping/jobs",
                json=job_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "id": result["id"],
                        "category": category_code,
                        "name": category_name,
                        "max_pages": max_pages
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def wait_for_batch_completion(self, session: aiohttp.ClientSession, 
                                      batch_jobs: List[Dict], timeout: int = 300):
        """Wait for all jobs in batch to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            completed_count = 0
            
            for job in batch_jobs:
                try:
                    async with session.get(f"{self.base_url}/api/scraping/jobs/{job['id']}") as response:
                        if response.status == 200:
                            status_data = await response.json()
                            job_status = status_data.get("status", "unknown")
                            
                            if job_status in ["completed", "failed", "cancelled"]:
                                completed_count += 1
                                
                except Exception:
                    # Assume completed if we can't check
                    completed_count += 1
            
            if completed_count >= len(batch_jobs):
                print(f"   ✅ All {len(batch_jobs)} jobs completed")
                break
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        if completed_count < len(batch_jobs):
            print(f"   ⚠️  Timeout waiting for completion ({completed_count}/{len(batch_jobs)} done)")
    
    async def get_current_product_count(self) -> int:
        """Get current total product count"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
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
                        return 0
        except Exception:
            return 0

async def main():
    campaign = ControlledScrapingCampaign()
    try:
        jobs = await campaign.launch_controlled_campaign()
        print(f"\n🎊 Campaign completed with {len(jobs)} jobs created")
    except KeyboardInterrupt:
        print(f"\n⏹️  Campaign stopped by user")
    except Exception as e:
        print(f"❌ Campaign error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())