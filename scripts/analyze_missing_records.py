#!/usr/bin/env python3
"""
Analyze what records are missing from the import
"""
import json
from pathlib import Path

def analyze_missing_records():
    """Analyze what records didn't make it into the import"""
    
    json_files = [
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_door_material.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_hardware_tools.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_houseware_home.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_kitchen_fur_appli.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_kitchen_texttile_door.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_kitchenware.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_lighting_electrical.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_material_ce.json",
        "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_plumbing_argiculture.json"
    ]
    
    print("🔍 Analyzing Missing Records")
    print("=" * 50)
    
    total_products = 0
    total_single_retailer = 0
    total_zero_prices = 0
    total_valid = 0
    
    for json_file in json_files:
        file_path = Path(json_file)
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_products = len(data)
        file_single_retailer = 0
        file_zero_prices = 0
        file_valid = 0
        
        for product_name, retailer_prices in data.items():
            total_products += 1
            
            # Check valid prices (> 0 and not None)
            valid_prices = {retailer: price for retailer, price in retailer_prices.items() 
                          if price is not None and price > 0}
            
            if len(valid_prices) < 2:
                if len(valid_prices) == 1:
                    file_single_retailer += 1
                    total_single_retailer += 1
                else:
                    file_zero_prices += 1
                    total_zero_prices += 1
            else:
                # Check if price difference exists
                prices = list(valid_prices.values())
                min_price = min(prices)
                if min_price > 0:
                    file_valid += 1
                    total_valid += 1
        
        print(f"{file_path.name}:")
        print(f"  Total products: {file_products}")
        print(f"  Single retailer only: {file_single_retailer}")
        print(f"  Zero/invalid prices: {file_zero_prices}")
        print(f"  Valid for comparison: {file_valid}")
        print(f"  Missing: {file_products - file_valid}")
        print()
    
    print("Overall Summary:")
    print(f"  Total products in JSON: {total_products}")
    print(f"  Single retailer only: {total_single_retailer}")
    print(f"  Zero/invalid prices: {total_zero_prices}")
    print(f"  Valid for comparison: {total_valid}")
    print(f"  Records we should import: {total_valid}")
    print()
    
    if total_valid == 5310:
        print("✅ All valid comparison records were imported successfully!")
    else:
        print(f"❌ Expected {total_valid} but got 5310 - difference: {total_valid - 5310}")
    
    # Show breakdown of why records can't be compared
    print("\n📊 Why records can't be used for price comparison:")
    print(f"  Products with only 1 retailer: {total_single_retailer} ({total_single_retailer/total_products*100:.1f}%)")
    print(f"  Products with no valid prices: {total_zero_prices} ({total_zero_prices/total_products*100:.1f}%)")
    print(f"  Products suitable for comparison: {total_valid} ({total_valid/total_products*100:.1f}%)")

if __name__ == "__main__":
    analyze_missing_records()