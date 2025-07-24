#!/usr/bin/env python3
"""Test database save process to diagnose the 10K campaign issue"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_single_category():
    """Test a single category scraping with debugging"""
    
    print("🧪 TESTING DATABASE SAVE PROCESS")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # Test with a known working category
    test_category = "APP"  # Appliances - should have many products
    category_url = f"https://www.homepro.co.th/c/{test_category}"
    
    # Get initial product count
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        
        print("📊 Getting initial product count...")
        search_data = {"query": "", "page": 1, "page_size": 1}
        async with session.post(
            f"{base_url}/api/products/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                initial_count = result.get("total", 0)
                print(f"   Initial total products: {initial_count}")
            else:
                print(f"   ❌ Failed to get initial count: {response.status}")
                initial_count = 0
        
        # Create a test job
        print(f"\n🚀 Creating test job for category: {test_category}")
        job_data = {
            "job_type": "category",
            "target_url": category_url,
            "retailer_code": "HP",
            "max_pages": 1  # Just 1 page for testing
        }
        
        async with session.post(
            f"{base_url}/api/scraping/jobs",
            json=job_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                job_result = await response.json()
                job_id = job_result["id"]
                print(f"   ✅ Job created: {job_id[:8]}...")
            else:
                error_text = await response.text()
                print(f"   ❌ Failed to create job: {response.status}")
                print(f"      Error: {error_text[:100]}")
                return
        
        # Monitor job progress
        print(f"\n⏳ Monitoring job progress...")
        max_wait = 120  # 2 minutes max
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                print(f"   ⏱️  Timeout after {max_wait}s")
                break
            
            async with session.get(f"{base_url}/api/scraping/jobs/{job_id}") as response:
                if response.status == 200:
                    status_data = await response.json()
                    
                    job_status = status_data.get("status", "unknown")
                    discovered = status_data.get("total_items", 0)
                    success = status_data.get("success_items", 0)
                    failed = status_data.get("failed_items", 0)
                    
                    print(f"   Status: {job_status}, Discovered: {discovered}, Success: {success}, Failed: {failed}")
                    
                    if job_status in ["completed", "failed", "cancelled"]:
                        break
                else:
                    print(f"   ❌ Failed to get job status: {response.status}")
                    break
            
            await asyncio.sleep(10)
        
        # Check final product count
        print(f"\n📊 Getting final product count...")
        await asyncio.sleep(5)  # Wait a bit for database saves
        
        async with session.post(
            f"{base_url}/api/products/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                final_count = result.get("total", 0)
                products_added = final_count - initial_count
                
                print(f"   Final total products: {final_count}")
                print(f"   Products added: {products_added}")
                
                if products_added > 0:
                    print(f"   ✅ Products were saved to database!")
                else:
                    print(f"   ❌ No products were saved despite job success")
            else:
                print(f"   ❌ Failed to get final count: {response.status}")
        
        # Try alternative search methods
        print(f"\n🔍 Testing alternative search methods...")
        
        # Search with retailer filter
        hp_search_data = {"retailer_code": "HP", "page": 1, "page_size": 1}
        async with session.post(
            f"{base_url}/api/products/search",
            json=hp_search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                hp_count = result.get("total", 0)
                print(f"   HomePro-specific search: {hp_count} products")
            else:
                print(f"   ❌ HomePro search failed: {response.status}")
        
        # Get recent products
        recent_search_data = {"query": "", "page": 1, "page_size": 10}
        async with session.post(
            f"{base_url}/api/products/search",
            json=recent_search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                items = result.get("items", [])
                print(f"   Recent products found: {len(items)}")
                
                if items:
                    latest = items[0]
                    print(f"   Latest product: {latest.get('name', 'No name')[:50]}")
                    print(f"   SKU: {latest.get('sku', 'No SKU')}")
                    print(f"   Retailer: {latest.get('retailer_code', 'No retailer')}")
            else:
                print(f"   ❌ Recent products search failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_single_category())