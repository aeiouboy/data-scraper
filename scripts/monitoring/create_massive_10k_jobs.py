#!/usr/bin/env python3
"""
Create multiple jobs to reach 10K products by using many categories
Since pagination doesn't work, we'll use breadth (many categories) instead of depth
"""
import asyncio
import aiohttp
import json

async def create_massive_scraping_campaign():
    """Create many category jobs to reach 10K products"""
    
    print("🚀 Creating Massive 10K Product Scraping Campaign")
    print("=" * 60)
    print("Strategy: Many categories instead of deep pagination")
    
    # All major HomePro categories (each category ~50-100 products)
    # Need ~100-200 categories to reach 10K products
    categories = [
        # Major categories
        "APP", "TOO", "ELT", "CON", "FUR", "BAT", "KIT", "LIG", "PAI", "PLU",
        "HHP", "TVA", "FLO", "DOW", "OUT", "BED", "SPO", "BEA", "MOM", "HEA", 
        "PET", "ATM", "SMA", 
        
        # Sub-categories (if they exist)
        "APP01", "APP02", "APP03", "APP04", "APP05",
        "TOO01", "TOO02", "TOO03", "TOO04", "TOO05",
        "ELT01", "ELT02", "ELT03", "ELT04", "ELT05",
        "CON01", "CON02", "CON03", "CON04", "CON05",
        "FUR01", "FUR02", "FUR03", "FUR04", "FUR05",
        "BAT01", "BAT02", "BAT03", "BAT04", "BAT05",
        "KIT01", "KIT02", "KIT03", "KIT04", "KIT05",
        "LIG01", "LIG02", "LIG03", "LIG04", "LIG05",
        
        # More potential categories
        "PAI01", "PAI02", "PAI03", "PLU01", "PLU02", "PLU03",
        "HHP01", "HHP02", "HHP03", "TVA01", "TVA02", "TVA03",
        "FLO01", "FLO02", "FLO03", "DOW01", "DOW02", "DOW03",
        "OUT01", "OUT02", "OUT03", "BED01", "BED02", "BED03",
    ]
    
    base_url = "http://localhost:8001"
    successful_jobs = []
    failed_categories = []
    
    print(f"📋 Attempting to create jobs for {len(categories)} categories")
    print("🎯 Target: 10,000+ products total")
    
    async with aiohttp.ClientSession() as session:
        for i, category in enumerate(categories):
            category_url = f"https://www.homepro.co.th/c/{category}"
            
            job_data = {
                "job_type": "category",
                "target_url": category_url,
                "retailer_code": "HP",
                "max_pages": 1  # Single page per category since pagination doesn't work
            }
            
            try:
                print(f"\n🔄 [{i+1:3d}/{len(categories)}] Creating job for {category}...")
                
                async with session.post(
                    f"{base_url}/api/scraping/jobs",
                    json=job_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        successful_jobs.append({
                            "id": result["id"],
                            "category": category,
                            "url": category_url
                        })
                        print(f"   ✅ Job created: {result['id'][:8]}...")
                    else:
                        error_text = await response.text()
                        failed_categories.append(category)
                        print(f"   ❌ Failed: {response.status}")
                        
            except Exception as e:
                failed_categories.append(category)
                print(f"   ❌ Error: {str(e)[:50]}...")
                continue
            
            # Small delay to avoid overwhelming the API
            if i % 10 == 9:  # Every 10 jobs
                print(f"   ⏸️  Brief pause after {i+1} jobs...")
                await asyncio.sleep(2)
        
        print(f"\n🎉 Job Creation Complete!")
        print(f"📊 Results:")
        print(f"   ✅ Successful jobs: {len(successful_jobs)}")
        print(f"   ❌ Failed categories: {len(failed_categories)}")
        print(f"   📦 Estimated products: {len(successful_jobs) * 60:,} (assuming 60 per category)")
        
        if len(successful_jobs) * 60 >= 10000:
            print(f"🏆 TARGET ACHIEVED! Estimated {len(successful_jobs) * 60:,} products")
        else:
            print(f"📈 Progress: {len(successful_jobs) * 60:,}/10,000 products")
        
        print(f"\n📋 Sample Job IDs:")
        for job in successful_jobs[:10]:
            print(f"   - {job['category']}: {job['id']}")
        
        if len(successful_jobs) > 10:
            print(f"   ... and {len(successful_jobs) - 10} more jobs")
        
        return successful_jobs

if __name__ == "__main__":
    asyncio.run(create_massive_scraping_campaign())