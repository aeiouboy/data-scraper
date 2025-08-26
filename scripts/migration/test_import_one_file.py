#!/usr/bin/env python3
"""
Test import of one JSON file first
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.migration.import_matched_products import MatchedProductImporter

async def main():
    print("🧪 Testing import with one file...")
    
    # Test with just one file first
    test_files = ["/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_door_material.json"]
    
    importer = MatchedProductImporter()
    success = await importer.import_all_files(test_files)
    
    if success:
        stats = await importer.get_import_stats()
        print(f"✅ Test successful! Total matches: {stats.get('total_matches', 0)}")
        return 0
    else:
        print("❌ Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))