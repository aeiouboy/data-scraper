#!/usr/bin/env python3
"""
Fix refrigerator product matches that incorrectly link products from the same retailer
"""
import asyncio
from src.services.supabase_service import SupabaseService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_refrigerator_matches():
    """Remove incorrect same-retailer matches and provide analysis"""
    try:
        supabase = SupabaseService()
        
        print("🔧 Fixing Refrigerator Product Matches")
        print("=" * 60)
        
        # Step 1: Identify same-retailer matches
        print("\n1. Identifying problematic matches...")
        
        # Get all product matches
        matches_result = supabase.client.table('product_matches').select('*').execute()
        all_matches = matches_result.data if matches_result.data else []
        
        same_retailer_match_ids = []
        
        for match in all_matches:
            # Get all product IDs in this match
            all_product_ids = [match['master_product_id']] + match.get('matched_product_ids', [])
            
            # Get retailer codes for all products
            retailers = set()
            product_details = []
            
            for pid in all_product_ids:
                try:
                    prod_result = supabase.client.table('products').select(
                        'id, name, retailer_code, retailer_name'
                    ).eq('id', pid).single().execute()
                    
                    if prod_result.data:
                        retailers.add(prod_result.data['retailer_code'])
                        product_details.append(prod_result.data)
                except Exception as e:
                    logger.error(f"Error fetching product {pid}: {e}")
            
            # Check if all products are from the same retailer
            if len(retailers) == 1:
                same_retailer_match_ids.append(match['id'])
                
                print(f"\n❌ Found same-retailer match:")
                print(f"   Match ID: {match['id']}")
                print(f"   Category: {match.get('unified_category')}")
                print(f"   Retailer: {list(retailers)[0]}")
                print(f"   Products:")
                for prod in product_details:
                    print(f"     - {prod['name']}")
        
        print(f"\n📊 Summary:")
        print(f"   Total matches: {len(all_matches)}")
        print(f"   Same-retailer matches: {len(same_retailer_match_ids)}")
        print(f"   Cross-retailer matches: {len(all_matches) - len(same_retailer_match_ids)}")
        
        # Step 2: Delete same-retailer matches
        if same_retailer_match_ids:
            print(f"\n2. Deleting {len(same_retailer_match_ids)} same-retailer matches...")
            
            for match_id in same_retailer_match_ids:
                try:
                    supabase.client.table('product_matches').delete().eq('id', match_id).execute()
                    print(f"   ✅ Deleted match {match_id}")
                except Exception as e:
                    print(f"   ❌ Error deleting match {match_id}: {e}")
            
            print("\n✅ Cleanup completed!")
        else:
            print("\n✅ No same-retailer matches found - database is clean!")
        
        # Step 3: Analyze refrigerator products
        print("\n3. Analyzing refrigerator product availability...")
        
        # Check for refrigerator products across retailers
        retailers = ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']
        refrigerator_count = {}
        
        for retailer in retailers:
            # Check various category names
            count = 0
            
            # Try different category variations
            for category in ['ตู้เย็น', 'refrigerator', 'Refrigerators']:
                result = supabase.client.table('products').select('id').eq('retailer_code', retailer).eq('category', category).execute()
                count += len(result.data) if result.data else 0
                
                result2 = supabase.client.table('products').select('id').eq('retailer_code', retailer).eq('unified_category', category).execute()
                count += len(result2.data) if result2.data else 0
            
            # Also search by name
            result3 = supabase.client.table('products').select('id').eq('retailer_code', retailer).ilike('name', '%ตู้เย็น%').execute()
            count += len(result3.data) if result3.data else 0
            
            refrigerator_count[retailer] = count
        
        print("\nRefrigerator products by retailer:")
        for retailer, count in refrigerator_count.items():
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {retailer}: {count} products")
        
        # Step 4: Provide recommendations
        print("\n📋 Recommendations:")
        print("=" * 60)
        
        retailers_with_products = [r for r, c in refrigerator_count.items() if c > 0]
        
        if len(retailers_with_products) <= 1:
            print("\n⚠️  ISSUE: Refrigerator products are only available from one retailer!")
            print("\nTo enable cross-retailer price comparisons, you need to:")
            print("1. Scrape refrigerator products from other retailers")
            print("2. Ensure consistent category naming across retailers")
            print("3. Run the product matching algorithm again")
            print("\nSuggested actions:")
            print("- Run scrapers for other retailers targeting refrigerator categories")
            print("- Update the unified_category field to use consistent naming")
            print("- Use the advanced product matcher to create proper cross-retailer matches")
        else:
            print("\n✅ Multiple retailers have refrigerator products!")
            print("You can now create proper cross-retailer matches.")
            print("\nNext steps:")
            print("1. Run the advanced product matcher")
            print("2. Verify matches are created between different retailers")
            print("3. Test the price comparison feature")
        
        print("\n🛠️  Quick Fix Commands:")
        print("# To scrape refrigerators from other retailers:")
        print("python scrape_refrigerators.py")
        print("\n# To create proper matches after scraping:")
        print("python run_advanced_matching.py --category refrigerator")
        
    except Exception as e:
        logger.error(f"Error fixing matches: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_refrigerator_matches())