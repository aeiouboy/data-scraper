#!/usr/bin/env python3
"""Quick status check for 10K campaign"""
import requests
import json

def get_quick_status():
    base_url = "http://localhost:8001"
    
    try:
        # Get product count
        search_data = {"retailer_code": "HP", "page": 1, "page_size": 1}
        response = requests.post(
            f"{base_url}/api/products/search",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            total_products = result.get("total", 0)
            print(f"📦 HomePro Products: {total_products:,}")
            print(f"🎯 Progress: {(total_products/10000)*100:.1f}% of 10K target")
        else:
            print(f"❌ Product count error: HTTP {response.status_code}")
        
        # Get job summary
        response = requests.get(f"{base_url}/api/scraping/jobs?limit=20", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            jobs = result.get("jobs", [])
            
            if jobs:
                running = len([j for j in jobs if j.get("status") == "running"])
                completed = len([j for j in jobs if j.get("status") == "completed"])
                failed = len([j for j in jobs if j.get("status") == "failed"])
                
                total_success = sum(j.get("success_items", 0) for j in jobs)
                total_discovered = sum(j.get("total_items", 0) for j in jobs)
                
                print(f"🔄 Jobs: {running} running, {completed} completed, {failed} failed")
                print(f"📊 Scraped: {total_success:,} of {total_discovered:,} discovered")
                
                if total_discovered > 0:
                    success_rate = (total_success / total_discovered) * 100
                    print(f"📈 Success Rate: {success_rate:.1f}%")
            else:
                print("📭 No jobs found")
        else:
            print(f"❌ Job status error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")

if __name__ == "__main__":
    get_quick_status()