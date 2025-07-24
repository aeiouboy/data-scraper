#!/usr/bin/env python3
"""
Fix products with NULL categories by rescaping them in batches
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService
from src.scrapers.homepro_scraper import HomeProScraper

async def main():
    print("🧹 FIXING NULL CATEGORIES - BATCH PROCESSING")
    print("=" * 60)
    
    service = SupabaseService()
    scraper = HomeProScraper()
    
    print("🔍 Finding products with NULL categories...")
    
    # Process in batches of 100 to avoid memory issues
    batch_size = 100
    total_processed = 0
    total_success = 0
    
    while True:
        # Get next batch of products with NULL categories
        try:
            response = service.client.table('products').select('sku,name,category,url').eq('retailer_code', 'HP').is_('category', 'null').order('created_at', desc=True).limit(batch_size).execute()
            products = response.data
        except Exception as e:
            print(f"❌ Error querying database: {e}")
            break
        
        if not products:
            print("✅ No more products with NULL categories found!")
            break
        
        print(f"\n📦 Processing batch of {len(products)} products...")
        print(f"📊 Total processed so far: {total_processed}")
        
        batch_success = 0
        batch_errors = 0
        
        for i, product in enumerate(products, 1):
            sku = product['sku']
            url = product['url']
            
            print(f"🔄 [{i}/{len(products)}] Rescaping SKU {sku}...")
            
            try:
                # Scrape the product
                result = await scraper.scrape_single_product(url)
                
                if result and result.get('category'):
                    print(f"   ✅ Updated - Category: {result['category']}")
                    batch_success += 1
                    total_success += 1
                else:
                    print(f"   ⚠️ No category extracted for SKU {sku}")
                    batch_errors += 1
                    
            except Exception as e:
                print(f"   ❌ Failed to scrape SKU {sku}: {str(e)[:80]}...")
                batch_errors += 1
            
            # Progress update every 20 products within batch
            if i % 20 == 0:
                batch_rate = (batch_success / i) * 100
                print(f"   📊 Batch progress: {i}/{len(products)} - Success: {batch_rate:.1f}%")
        
        total_processed += len(products)
        
        print(f"\n📊 BATCH RESULTS:")
        print(f"   ✅ Batch success: {batch_success}/{len(products)} ({(batch_success/len(products))*100:.1f}%)")
        print(f"   📈 Total progress: {total_processed} processed, {total_success} successful")
        
        # If batch was smaller than batch_size, we're done
        if len(products) < batch_size:
            break
        
        # Brief pause between batches
        print("⏸️ Brief pause before next batch...")
        await asyncio.sleep(2)
    
    print(f"\n🎉 FINAL SUMMARY:")
    print(f"   📦 Total products processed: {total_processed}")
    print(f"   ✅ Total successful updates: {total_success}")
    print(f"   📈 Overall success rate: {(total_success/total_processed)*100:.1f}%")
    
    if total_success > 0:
        print(f"\n💡 Successfully fixed categories for {total_success} products!")

if __name__ == "__main__":
    asyncio.run(main())