#!/usr/bin/env python3
"""
Launch 50K HomePro Product Campaign
Complete catalog scraping with unlimited pagination
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def launch_50k_comprehensive_campaign():
    """Launch the full 50K product campaign"""
    
    print("🚀 LAUNCHING 50K HOMEPRO COMPREHENSIVE CAMPAIGN")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: 50,000+ products")
    print(f"⏱️  Estimated time: 15-30 hours")
    print(f"🔧 Strategy: Complete category discovery + unlimited pagination")
    print("=" * 70)
    
    base_url = "http://localhost:8001"
    
    # Phase 1: Comprehensive category discovery
    print(f"\n📋 PHASE 1: COMPREHENSIVE CATEGORY DISCOVERY")
    print("-" * 50)
    
    # Main categories with extensive subcategory discovery
    main_categories = ["APP", "TOO", "ELT", "CON", "FUR", "BAT", "KIT", "LIG", "PAI", "PLU", 
                      "HHP", "TVA", "FLO", "DOW", "OUT", "SMA", "SPO", "BEA", "MOM", "HEA", 
                      "PET", "ATM", "CLE", "GAR", "TIL", "WOO", "MET", "PLA", "GLX", "INS"]
    
    all_categories = []
    
    # Generate comprehensive subcategory list
    for main_cat in main_categories:
        # Add main category
        all_categories.append((main_cat, f"{main_cat} - Main Category", 50))
        
        # Add numbered subcategories (01-99)
        for i in range(1, 100):
            subcat = f"{main_cat}{i:02d}"
            all_categories.append((subcat, f"{main_cat} Subcategory {i}", 30))
        
        # Add letter subcategories (A-Z)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            subcat = f"{main_cat}{letter}"
            all_categories.append((subcat, f"{main_cat} Section {letter}", 20))
    
    print(f"📊 Generated {len(all_categories):,} potential categories to test")
    
    # Phase 2: Launch jobs with unlimited pagination
    print(f"\n🔄 PHASE 2: LAUNCHING UNLIMITED SCRAPING JOBS")
    print("-" * 50)
    
    successful_jobs = []
    batch_size = 10  # Process in batches to manage resources
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        
        for batch_start in range(0, len(all_categories), batch_size):
            batch_end = min(batch_start + batch_size, len(all_categories))
            batch_categories = all_categories[batch_start:batch_end]
            
            print(f"\n📦 Batch {batch_start//batch_size + 1}: Testing categories {batch_start+1}-{batch_end}")
            
            # Create batch of jobs with unlimited pagination
            batch_tasks = []
            for category_code, category_name, max_pages in batch_categories:
                task = create_unlimited_category_job(session, base_url, category_code, max_pages)
                batch_tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            successful_in_batch = 0
            for i, result in enumerate(batch_results):
                category_code, category_name, max_pages = batch_categories[i]
                
                if isinstance(result, Exception):
                    print(f"   ❌ {category_code}: {str(result)[:30]}")
                elif result:
                    successful_jobs.append(result)
                    successful_in_batch += 1
                    print(f"   ✅ {category_code}: {result['id'][:8]}... ({max_pages} pages)")
                else:
                    print(f"   ❌ {category_code}: Category not found")
            
            print(f"   📊 Batch success: {successful_in_batch}/{len(batch_categories)} categories")
            
            # Monitor resource usage - pause if too many running jobs
            running_jobs = await count_running_jobs(session, base_url)
            if running_jobs > 20:
                print(f"   ⏸️  Pausing - {running_jobs} jobs running (resource management)")
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(10)  # Brief pause between batches
    
    print(f"\n🎉 PHASE 2 COMPLETE!")
    print(f"✅ Successfully created {len(successful_jobs)} scraping jobs")
    print(f"🎯 Estimated products: {len(successful_jobs) * 150:,}+ (avg 150 per job)")
    
    # Phase 3: Monitor progress
    print(f"\n📊 PHASE 3: MONITORING CAMPAIGN PROGRESS")
    print("-" * 50)
    print(f"🔄 Jobs will run automatically in background")
    print(f"📈 Monitor with: python quick_status.py")
    print(f"📊 Track progress: curl http://localhost:8001/api/products/search")
    print(f"⏱️  Expected completion: 15-30 hours")
    
    return successful_jobs

async def create_unlimited_category_job(session, base_url, category_code, max_pages):
    """Create a category job with unlimited pagination"""
    category_url = f"https://www.homepro.co.th/c/{category_code}"
    
    job_data = {
        "job_type": "category",
        "target_url": category_url,
        "retailer_code": "HP",
        "max_pages": max_pages  # Much higher page limits
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
                    "max_pages": max_pages,
                    "url": category_url
                }
            else:
                # Category doesn't exist or other error
                return None
                
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")

async def count_running_jobs(session, base_url):
    """Count currently running jobs for resource management"""
    try:
        async with session.get(f"{base_url}/api/scraping/jobs?limit=50") as response:
            if response.status == 200:
                result = await response.json()
                jobs = result.get("jobs", [])
                running_count = len([j for j in jobs if j.get("status") == "running"])
                return running_count
    except:
        pass
    return 0

if __name__ == "__main__":
    asyncio.run(launch_50k_comprehensive_campaign())