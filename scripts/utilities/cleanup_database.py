#!/usr/bin/env python3
"""
Clean up database with incorrect product information
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.supabase_service import SupabaseService
from src.scrapers.homepro_scraper import HomeProScraper

async def analyze_and_cleanup_database():
    """Analyze database for incorrect data and offer cleanup options"""
    
    supabase = SupabaseService()
    
    print("🔍 ANALYZING DATABASE FOR DATA QUALITY ISSUES...")
    print("="*60)
    
    # Get all HomePro products
    response = supabase.client.table('products').select('*').eq('retailer_code', 'HP').execute()
    products = response.data
    
    print(f"📊 Found {len(products)} HomePro products")
    
    # Analyze data quality issues
    issues = {
        'missing_category': [],
        'suspicious_prices': [],
        'wrong_category_format': [],
        'missing_brands': []
    }
    
    for product in products:
        # Check for missing categories
        if not product.get('category') or product.get('category') in [None, '', 'None']:
            issues['missing_category'].append(product['sku'])
        
        # Check for wrong category format (has ">" separator)
        elif product.get('category') and '>' in product.get('category', ''):
            issues['wrong_category_format'].append(product['sku'])
        
        # Check for suspicious price combinations (current > original)
        current = product.get('current_price', 0) or 0
        original = product.get('original_price', 0) or 0
        if current > 0 and original > 0 and current > original:
            issues['suspicious_prices'].append(product['sku'])
        
        # Check for missing brands
        if not product.get('brand') or product.get('brand') in [None, '', 'None']:
            issues['missing_brands'].append(product['sku'])
    
    # Display analysis
    print("\n📋 DATA QUALITY ANALYSIS:")
    print(f"   🚫 Missing categories: {len(issues['missing_category'])} products")
    print(f"   📝 Wrong category format: {len(issues['wrong_category_format'])} products")
    print(f"   💰 Suspicious prices: {len(issues['suspicious_prices'])} products") 
    print(f"   🏷️ Missing brands: {len(issues['missing_brands'])} products")
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    print(f"\n⚠️ TOTAL PRODUCTS WITH ISSUES: {total_issues}/{len(products)} ({total_issues/len(products)*100:.1f}%)")
    
    if total_issues > 0:
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print(f"   1. Rescrape all HomePro products with improved scraper")
        print(f"   2. Focus on products with category/price issues")
        print(f"   3. Update database with correct information")
        
        # Show sample problematic products
        if issues['wrong_category_format']:
            print(f"\n📝 Sample products with wrong category format:")
            sample_skus = issues['wrong_category_format'][:5]
            for sku in sample_skus:
                product = next(p for p in products if p['sku'] == sku)
                print(f"      SKU {sku}: '{product.get('category')}' → should be last part only")
        
        if issues['suspicious_prices']:
            print(f"\n💰 Sample products with suspicious prices:")
            sample_skus = issues['suspicious_prices'][:5]
            for sku in sample_skus:
                product = next(p for p in products if p['sku'] == sku)
                current = product.get('current_price', 0)
                original = product.get('original_price', 0)
                print(f"      SKU {sku}: Current ฿{current} > Original ฿{original} (should be reversed)")
    
    return issues

async def rescrape_problematic_products(issues, max_products=50):
    """Rescrape products with identified issues"""
    
    print(f"\n🔄 STARTING RESCRAPE OF PROBLEMATIC PRODUCTS...")
    
    # Combine all problematic SKUs
    all_problem_skus = []
    for issue_type, skus in issues.items():
        all_problem_skus.extend(skus)
    
    # Remove duplicates and limit
    unique_skus = list(set(all_problem_skus))[:max_products]
    
    if not unique_skus:
        print("✅ No problematic products to rescrape!")
        return
    
    print(f"📋 Rescraping {len(unique_skus)} products with data issues...")
    
    scraper = HomeProScraper(use_native=True)
    
    success_count = 0
    for i, sku in enumerate(unique_skus, 1):
        try:
            url = f"https://www.homepro.co.th/p/{sku}"
            print(f"🔄 [{i}/{len(unique_skus)}] Rescraping SKU {sku}...")
            
            result = await scraper.scrape_single_product(url)
            if result:
                success_count += 1
                print(f"   ✅ Updated - Category: {result.get('category', 'N/A')}")
            else:
                print(f"   ❌ Failed to update")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    await scraper.close()
    
    print(f"\n📊 RESCRAPE SUMMARY:")
    print(f"   ✅ Successfully updated: {success_count}/{len(unique_skus)} products")
    print(f"   📈 Success rate: {success_count/len(unique_skus)*100:.1f}%")

async def main():
    """Main cleanup function"""
    
    print("🧹 DATABASE CLEANUP UTILITY")
    print("="*60)
    
    # Step 1: Analyze current data quality
    issues = await analyze_and_cleanup_database()
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    
    if total_issues == 0:
        print("🎉 Database looks good! No major data quality issues found.")
        return
    
    # Step 2: Ask user what to do
    print(f"\n❓ What would you like to do?")
    print(f"   1. Rescrape {min(50, total_issues)} most problematic products")
    print(f"   2. Show detailed analysis only")
    print(f"   3. Exit (you can run full rescrape manually)")
    
    # For automated execution, default to option 1
    choice = "1"  # Auto-select rescrape
    
    if choice == "1":
        await rescrape_problematic_products(issues, max_products=50)
        print(f"\n💡 TIP: For best results, consider running full rescrape:")
        print(f"   python scripts/scraping/scrape.py --retailer HP --force-refresh")
    elif choice == "2":
        print(f"✅ Analysis complete. Run this script again to perform cleanup.")

if __name__ == "__main__":
    asyncio.run(main())