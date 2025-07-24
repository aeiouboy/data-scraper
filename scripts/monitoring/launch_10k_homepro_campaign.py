#!/usr/bin/env python3
"""
Launch massive 10K HomePro SKU scraping campaign
Strategy: Create many category jobs to reach 10,000+ products
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def launch_10k_homepro_campaign():
    """Launch comprehensive 10K HomePro scraping campaign"""
    
    print("🚀 LAUNCHING 10K HOMEPRO SKU SCRAPING CAMPAIGN")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Target: 10,000+ HomePro products")
    print("⚡ Strategy: Native scraping with Firecrawl fallback")
    print("=" * 60)
    
    # Comprehensive HomePro category list
    # Each category should yield 50-150 products
    major_categories = [
        # Main product categories (high product count)
        ("APP", "เครื่องใช้ไฟฟ้า", "High volume - appliances"),
        ("TOO", "เครื่องมือและฮาร์ดแวร์", "High volume - tools & hardware"),
        ("ELT", "ระบบไฟฟ้าและความปลอดภัย", "High volume - electrical"),
        ("CON", "วัสดุก่อสร้าง", "High volume - construction"),
        ("FUR", "เฟอร์นิเจอร์และของแต่งบ้าน", "High volume - furniture"),
        ("BAT", "ห้องน้ำ", "High volume - bathroom"),
        ("KIT", "ห้องครัวและอุปกรณ์", "Medium volume - kitchen"),
        ("LIG", "โคมไฟและหลอดไฟ", "Medium volume - lighting"),
        ("PAI", "สีและอุปกรณ์ทาสี", "Medium volume - paint"),
        ("PLU", "งานระบบประปา", "Medium volume - plumbing"),
        ("HHP", "จัดเก็บและของใช้ในบ้าน", "Medium volume - home storage"),
        ("TVA", "ทีวี เครื่องเสียง เกม", "Medium volume - electronics"),
        ("FLO", "วัสดุปูพื้นและผนัง", "Medium volume - flooring"),
        ("DOW", "ประตูและหน้าต่าง", "Medium volume - doors & windows"),
        ("OUT", "เฟอร์นิเจอร์นอกบ้านและสวน", "Medium volume - outdoor"),
        ("BED", "ห้องนอนและเครื่องนอน", "Medium volume - bedroom"),
        ("SPO", "กีฬาและการเดินทาง", "Low volume - sports"),
        ("BEA", "ความงามและดูแลตัว", "Low volume - beauty"),
        ("MOM", "แม่และเด็ก", "Low volume - mother & baby"),
        ("HEA", "สุขภาพ", "Low volume - health"),
        ("PET", "อุปกรณ์สัตว์เลี้ยง", "Low volume - pets"),
        ("ATM", "ยานยนต์", "Low volume - automotive"),
        ("SMA", "เครื่องใช้ไฟฟ้าขนาดเล็ก", "Medium volume - small appliances"),
    ]
    
    # Additional subcategories and specialized sections
    additional_categories = []
    
    # Generate subcategory variations
    for base_code, _, _ in major_categories[:10]:  # Top 10 categories
        for i in range(1, 6):  # Try 5 subcategories each
            additional_categories.append((
                f"{base_code}{i:02d}", 
                f"{base_code} subcategory {i}", 
                f"Subcategory of {base_code}"
            ))
    
    # Combine all categories
    all_categories = major_categories + additional_categories
    
    print(f"📋 Category Strategy:")
    print(f"   - Major categories: {len(major_categories)}")
    print(f"   - Additional subcategories: {len(additional_categories)}")
    print(f"   - Total categories to scrape: {len(all_categories)}")
    print(f"   - Expected products: {len(all_categories) * 80:,}+ (avg 80 per category)")
    print("")
    
    base_url = "http://localhost:8001"
    successful_jobs = []
    failed_categories = []
    
    print("🔄 Creating scraping jobs...")
    print("-" * 40)
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        
        # Process in batches to avoid overwhelming the API
        batch_size = 5
        for batch_start in range(0, len(all_categories), batch_size):
            batch_end = min(batch_start + batch_size, len(all_categories))
            batch_categories = all_categories[batch_start:batch_end]
            
            print(f"\n📦 Batch {batch_start//batch_size + 1}: Processing categories {batch_start+1}-{batch_end}")
            
            # Create batch of jobs
            batch_tasks = []
            for category_code, category_name, description in batch_categories:
                task = create_category_job(session, base_url, category_code, category_name, description)
                batch_tasks.append(task)
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                category_code, category_name, description = batch_categories[i]
                
                if isinstance(result, Exception):
                    failed_categories.append((category_code, str(result)))
                    print(f"   ❌ {category_code}: {str(result)[:50]}")
                elif result:
                    successful_jobs.append(result)
                    print(f"   ✅ {category_code}: {result['id'][:8]}... ({description})")
                else:
                    failed_categories.append((category_code, "Failed to create job"))
                    print(f"   ❌ {category_code}: Failed to create job")
            
            # Brief pause between batches
            if batch_end < len(all_categories):
                print("   ⏸️  Pause between batches...")
                await asyncio.sleep(3)
    
    print(f"\n🎉 Job Creation Phase Complete!")
    print("=" * 60)
    print(f"📊 Results Summary:")
    print(f"   ✅ Successful jobs: {len(successful_jobs)}")
    print(f"   ❌ Failed categories: {len(failed_categories)}")
    print(f"   📈 Success rate: {len(successful_jobs)/(len(successful_jobs)+len(failed_categories))*100:.1f}%")
    print(f"   🎯 Estimated products: {len(successful_jobs) * 80:,}+ (target: 10,000)")
    
    if len(successful_jobs) * 80 >= 10000:
        print(f"🏆 TARGET ACHIEVABLE! Estimated {len(successful_jobs) * 80:,} products")
    else:
        print(f"📊 Progress: {len(successful_jobs) * 80:,}/10,000 estimated")
    
    # Sample of created jobs
    print(f"\n📋 Sample Created Jobs:")
    for job in successful_jobs[:10]:
        print(f"   - {job['category']}: {job['id']}")
    
    if len(successful_jobs) > 10:
        print(f"   ... and {len(successful_jobs) - 10} more jobs")
    
    # Failed categories
    if failed_categories:
        print(f"\n❌ Failed Categories:")
        for category, error in failed_categories[:5]:
            print(f"   - {category}: {error}")
        if len(failed_categories) > 5:
            print(f"   ... and {len(failed_categories) - 5} more failures")
    
    print(f"\n🚀 All jobs are now running with native scraping!")
    print(f"📊 Monitor progress with: curl http://localhost:8001/api/scraping/jobs")
    
    return successful_jobs

async def create_category_job(session, base_url, category_code, category_name, description):
    """Create a single category scraping job"""
    category_url = f"https://www.homepro.co.th/c/{category_code}"
    
    job_data = {
        "job_type": "category",
        "target_url": category_url,
        "retailer_code": "HP",
        "max_pages": 1  # Single page per category since pagination doesn't work well
    }
    
    try:
        async with session.post(
            f"{base_url}/api/scraping/jobs",
            json=job_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "id": result["id"],
                    "category": category_code,
                    "name": category_name,
                    "url": category_url,
                    "description": description
                }
            else:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text[:100]}")
                
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")

async def monitor_campaign_progress(job_list):
    """Monitor the progress of the 10K campaign"""
    
    print(f"\n👀 MONITORING 10K CAMPAIGN PROGRESS")
    print("=" * 60)
    print(f"📊 Monitoring {len(job_list)} jobs")
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        check_count = 0
        
        while True:
            check_count += 1
            print(f"\n📊 Progress Check #{check_count} ({datetime.now().strftime('%H:%M:%S')})")
            print("-" * 40)
            
            total_discovered = 0
            total_success = 0
            total_failed = 0
            completed_jobs = 0
            running_jobs = 0
            
            # Check each job
            for job in job_list[:20]:  # Check first 20 jobs for performance
                try:
                    async with session.get(f"{base_url}/api/scraping/jobs/{job['id']}") as response:
                        if response.status == 200:
                            status_data = await response.json()
                            
                            job_status = status_data.get("status", "unknown")
                            discovered = status_data.get("total_items", 0)
                            success = status_data.get("success_items", 0)
                            failed = status_data.get("failed_items", 0)
                            
                            total_discovered += discovered
                            total_success += success
                            total_failed += failed
                            
                            if job_status == "completed":
                                completed_jobs += 1
                            elif job_status == "running":
                                running_jobs += 1
                            
                except Exception as e:
                    print(f"   ❌ Error checking {job['category']}: {str(e)[:30]}")
            
            # Overall progress
            success_rate = (total_success / total_discovered * 100) if total_discovered > 0 else 0
            
            print(f"🎯 CAMPAIGN STATUS:")
            print(f"   📦 Total Discovered: {total_discovered:,}")
            print(f"   ✅ Successfully Scraped: {total_success:,}")
            print(f"   ❌ Failed: {total_failed:,}")
            print(f"   📊 Success Rate: {success_rate:.1f}%")
            print(f"   🔄 Jobs Running: {running_jobs}")
            print(f"   ✅ Jobs Completed: {completed_jobs}")
            
            if total_success >= 10000:
                print(f"\n🏆 TARGET ACHIEVED! Scraped {total_success:,} products (>10K goal)")
                break
            elif total_discovered >= 10000:
                print(f"\n🎯 Target in sight! Discovered {total_discovered:,} products")
            
            if completed_jobs >= len(job_list[:20]):
                print(f"\n✅ All monitored jobs completed!")
                break
            
            # Wait before next check
            print(f"⏱️  Next check in 60 seconds...")
            await asyncio.sleep(60)

if __name__ == "__main__":
    async def main():
        try:
            # Launch the campaign
            jobs = await launch_10k_homepro_campaign()
            
            if len(jobs) > 0:
                print(f"\n🎯 Campaign launched successfully!")
                
                # Ask user if they want to monitor
                print(f"\n📊 Would you like to monitor progress? (This will run for a while)")
                print(f"💡 You can also check manually with:")
                print(f"   curl http://localhost:8001/api/products/search -X POST -H 'Content-Type: application/json' -d '{{\"query\":\"\",\"page\":1,\"page_size\":1}}' | jq '.total'")
                
                # Auto-start monitoring for a few minutes
                print(f"\n🔄 Starting brief monitoring session...")
                await asyncio.sleep(60)  # Wait for jobs to start
                await monitor_campaign_progress(jobs)
            else:
                print("❌ No jobs were created successfully")
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Campaign monitoring stopped by user")
        except Exception as e:
            print(f"❌ Campaign error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())