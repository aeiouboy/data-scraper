#!/usr/bin/env python3
"""
Import all matched product JSON files
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simple_import import SimpleImporter


async def main():
    """Import all JSON files"""
    print("🚀 Starting import of all matched product JSON files")
    print("=" * 60)
    
    # List of JSON files to import
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
    
    # Check which files exist
    existing_files = [f for f in json_files if Path(f).exists()]
    missing_files = [f for f in json_files if not Path(f).exists()]
    
    if missing_files:
        print(f"⚠️ Missing files:")
        for f in missing_files:
            print(f"   - {Path(f).name}")
    
    print(f"📁 Found {len(existing_files)} files to import:")
    for f in existing_files:
        print(f"   ✅ {Path(f).name}")
    
    if not existing_files:
        print("❌ No files found to import")
        return 1
    
    try:
        importer = SimpleImporter()
        
        total_start_time = datetime.now()
        total_products = 0
        total_matches = 0
        
        # Import each file
        for i, json_file in enumerate(existing_files, 1):
            print(f"\n📁 Processing file {i}/{len(existing_files)}: {Path(json_file).name}")
            
            file_start_time = datetime.now()
            products_count, matches_count = await importer.import_json_file(json_file)
            file_end_time = datetime.now()
            
            file_duration = (file_end_time - file_start_time).total_seconds()
            total_products += products_count
            total_matches += matches_count
            
            print(f"   ✅ Results: {products_count} products, {matches_count} matches ({file_duration:.2f}s)")
        
        total_end_time = datetime.now()
        total_duration = (total_end_time - total_start_time).total_seconds()
        
        # Show final statistics
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Total imported: {total_products} products, {total_matches} matches")
        print(f"⏱️  Total duration: {total_duration:.2f} seconds")
        print(f"📈 Average: {total_products/total_duration:.1f} products/sec, {total_matches/total_duration:.1f} matches/sec")
        
        print("\n📋 Next steps:")
        print("1. Test price comparison API: http://localhost:8001/api/price-comparisons-v2/detailed-comparisons")
        print("2. Check frontend: http://localhost:3000/price-comparisons")
        print("3. Verify data with v2 API: http://localhost:8001/api/v2/matches/stats")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))