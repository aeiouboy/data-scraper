#!/usr/bin/env python3
"""
Fix products with incorrect categories by rescaping them
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService
from src.scrapers.homepro_scraper import HomeProScraper

async def main():
    print("🧹 FIXING INCORRECT CATEGORIES")
    print("=" * 60)
    
    service = SupabaseService()
    scraper = HomeProScraper()
    
    # Get products with missing or incorrect categories
    print("🔍 Finding products with category issues...")
    
    # Query for products with "General" category specifically
    try:
        response = service.client.table('products').select('sku,name,category,url').eq('retailer_code', 'HP').eq('category', 'General').order('created_at', desc=True).limit(200).execute()
        products = response.data
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return
    
    print(f"📊 Found {len(products)} products with category issues")
    
    if not products:
        print("✅ No products found with category issues!")
        return
    
    # Show sample of problematic products
    print("\n📋 Sample of products to fix:")
    for i, product in enumerate(products[:10]):
        category = product.get('category', 'None')
        print(f"   {i+1}. SKU {product['sku']}: '{category}' -> {product['name'][:50]}...")
    
    # Auto-proceed to fix the issues
    print(f"\n✅ Proceeding to rescrape {len(products)} products...")
    
    print(f"\n🔄 Starting to rescrape {len(products)} products...")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, product in enumerate(products, 1):
        sku = product['sku']
        url = product['url']
        
        print(f"🔄 [{i}/{len(products)}] Rescaping SKU {sku}...")
        
        try:
            # Scrape the product
            result = await scraper.scrape_single_product(url)
            
            if result and result.get('category'):
                print(f"   ✅ Updated - Category: {result['category']}")
                success_count += 1
            else:
                print(f"   ⚠️ No category extracted for SKU {sku}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Failed to scrape SKU {sku}: {str(e)[:100]}")
            error_count += 1
        
        # Progress update every 20 products
        if i % 20 == 0:
            success_rate = (success_count / i) * 100
            print(f"\n📊 Progress Update: {i}/{len(products)} completed")
            print(f"   ✅ Success: {success_count} ({success_rate:.1f}%)")
            print(f"   ❌ Errors: {error_count}")
            print("-" * 40)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   ✅ Successfully updated: {success_count}/{len(products)}")
    print(f"   ❌ Errors: {error_count}/{len(products)}")
    print(f"   📈 Success rate: {(success_count / len(products)) * 100:.1f}%")
    
    if success_count > 0:
        print(f"\n💡 Successfully fixed categories for {success_count} products!")
    
    print("\n🎉 Category cleanup completed!")

if __name__ == "__main__":
    asyncio.run(main())