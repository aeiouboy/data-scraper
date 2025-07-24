#!/usr/bin/env python3
"""
Create a 10K product scraping job using the backend API
"""
import asyncio
import aiohttp
import json
import time

async def create_large_scraping_job():
    """Create a large-scale scraping job through the API"""
    
    print("🚀 Creating 10K Product Scraping Job via Backend API")
    print("=" * 60)
    
    # Since we have 398 unique URLs, let's create multiple category jobs to reach 10K
    # We'll create multiple category scraping jobs to reach our target
    
    categories_for_10k = [
        ("APP", "https://www.homepro.co.th/c/APP", 50),    # ~2000-3000 products
        ("TOO", "https://www.homepro.co.th/c/TOO", 50),    # ~2000-3000 products  
        ("ELT", "https://www.homepro.co.th/c/ELT", 50),    # ~1500-2000 products
        ("CON", "https://www.homepro.co.th/c/CON", 50),    # ~2000-3000 products
        ("FUR", "https://www.homepro.co.th/c/FUR", 30),    # ~1000-1500 products
        ("BAT", "https://www.homepro.co.th/c/BAT", 30),    # ~1000 products
        ("KIT", "https://www.homepro.co.th/c/KIT", 20),    # ~800 products
        ("LIG", "https://www.homepro.co.th/c/LIG", 20),    # ~800 products
    ]
    
    base_url = "http://localhost:8001"
    jobs_created = []
    
    async with aiohttp.ClientSession() as session:
        print("📋 Creating category scraping jobs...")
        
        for category_code, category_url, max_pages in categories_for_10k:
            job_data = {
                "job_type": "category",
                "target_url": category_url,
                "retailer_code": "HP",
                "max_pages": max_pages
            }
            
            try:
                print(f"\n🔄 Creating job for {category_code} (max {max_pages} pages)...")
                print(f"🔗 URL: {category_url}")
                
                async with session.post(
                    f"{base_url}/api/scraping/jobs",
                    json=job_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        jobs_created.append({
                            "id": result["id"],
                            "category": category_code,
                            "url": category_url,
                            "max_pages": max_pages,
                            "status": result["status"]
                        })
                        print(f"✅ Job created: {result['id']}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create job for {category_code}: {error_text}")
                        
            except Exception as e:
                print(f"❌ Error creating job for {category_code}: {str(e)}")
                continue
        
        print(f"\n🎉 Job Creation Complete!")
        print(f"📊 Created {len(jobs_created)} category scraping jobs")
        
        # Display all created jobs
        print(f"\n📋 Created Jobs Summary:")
        total_estimated_products = 0
        for job in jobs_created:
            estimated = job["max_pages"] * 40  # Rough estimate: 40 products per page
            total_estimated_products += estimated
            print(f"   - {job['category']}: {job['id']} ({estimated} est. products)")
        
        print(f"\n🎯 Estimated Total Products: ~{total_estimated_products:,}")
        print(f"📊 This should easily exceed our 10K target!")
        
        return jobs_created

async def monitor_jobs(jobs):
    """Monitor the progress of all scraping jobs"""
    
    print(f"\n👀 Monitoring {len(jobs)} Large-Scale Scraping Jobs")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        while True:
            all_completed = True
            total_products = 0
            total_success = 0
            total_failed = 0
            
            print(f"\n📊 Job Status Update ({time.strftime('%H:%M:%S')})")
            print("-" * 60)
            
            for job in jobs:
                try:
                    async with session.get(
                        f"{base_url}/api/scraping/jobs/{job['id']}",
                        headers={"Accept": "application/json"}
                    ) as response:
                        if response.status == 200:
                            status = await response.json()
                            
                            total_items = status.get("total_items", 0)
                            success_items = status.get("success_items", 0) 
                            failed_items = status.get("failed_items", 0)
                            job_status = status.get("status", "unknown")
                            
                            total_products += total_items
                            total_success += success_items
                            total_failed += failed_items
                            
                            if job_status in ["pending", "running"]:
                                all_completed = False
                            
                            # Status indicator
                            if job_status == "completed":
                                status_icon = "✅"
                            elif job_status == "running":
                                status_icon = "🔄"
                            elif job_status == "pending":
                                status_icon = "⏳"
                            else:
                                status_icon = "❌"
                            
                            success_rate = (success_items / total_items * 100) if total_items > 0 else 0
                            
                            print(f"{status_icon} {job['category']}: {success_items:,}/{total_items:,} ({success_rate:.1f}%) - {job_status}")
                            
                except Exception as e:
                    print(f"❌ Error checking {job['category']}: {str(e)}")
            
            # Overall summary
            overall_success_rate = (total_success / total_products * 100) if total_products > 0 else 0
            print("-" * 60)
            print(f"🎯 OVERALL: {total_success:,}/{total_products:,} ({overall_success_rate:.1f}%) | Failed: {total_failed:,}")
            
            if total_products >= 10000:
                print(f"🏆 TARGET ACHIEVED! Processed {total_products:,} products (>10K goal)")
            
            if all_completed:
                print(f"\n🎉 ALL JOBS COMPLETED!")
                print(f"📊 Final Results:")
                print(f"   - Total Products Processed: {total_products:,}")
                print(f"   - Successful: {total_success:,}")
                print(f"   - Failed: {total_failed:,}")
                print(f"   - Success Rate: {overall_success_rate:.2f}%")
                break
            
            # Wait before next check
            print(f"⏱️  Next update in 30 seconds...")
            await asyncio.sleep(30)

async def main():
    """Main execution"""
    try:
        # Create jobs
        jobs = await create_large_scraping_job()
        
        if not jobs:
            print("❌ No jobs were created successfully")
            return
        
        # Start monitoring
        await monitor_jobs(jobs)
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())