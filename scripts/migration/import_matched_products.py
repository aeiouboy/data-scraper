#!/usr/bin/env python3
"""
Import matched product data from JSON files to Supabase database
Converts the JSON format to proper matching_results entries
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4, UUID
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchedProductImporter:
    """Import matched product data from JSON files"""
    
    # Retailer code mapping
    RETAILER_MAPPING = {
        "Thai Watsadu": "TWD",
        "HomePro": "HP",
        "Do Home": "DH",
        "Globalhouse": "GH",
        "Boonthavorn": "BT",
        "Bnbhome": "BNB",
        "MegaHome": "MH"
    }
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.category_mapping = {
            "results_test_door_material.json": "door_material",
            "results_test_hardware_tools.json": "hardware_tools", 
            "results_test_houseware_home.json": "houseware_home",
            "results_test_kitchen_fur_appli.json": "kitchen_furniture_appliances",
            "results_test_kitchen_texttile_door.json": "kitchen_textile_door",
            "results_test_kitchenware.json": "kitchenware",
            "results_test_lighting_electrical.json": "lighting_electrical",
            "results_test_material_ce.json": "material_cement",
            "results_test_plumbing_argiculture.json": "plumbing_agriculture"
        }
    
    async def import_all_files(self, json_files: List[str]) -> bool:
        """Import all JSON files"""
        logger.info(f"🚀 Starting import of {len(json_files)} JSON files...")
        
        total_products = 0
        total_matches = 0
        
        try:
            for json_file in json_files:
                if not Path(json_file).exists():
                    logger.error(f"❌ File not found: {json_file}")
                    continue
                    
                logger.info(f"📁 Processing {Path(json_file).name}...")
                products_count, matches_count = await self.import_json_file(json_file)
                
                total_products += products_count
                total_matches += matches_count
                
                logger.info(f"✅ Processed {products_count} products, {matches_count} matches from {Path(json_file).name}")
            
            logger.info(f"🎉 Import completed!")
            logger.info(f"📊 Total: {total_products} products, {total_matches} matches")
            return True
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False
    
    async def import_json_file(self, json_file_path: str) -> tuple[int, int]:
        """Import a single JSON file"""
        file_path = Path(json_file_path)
        category = self.category_mapping.get(file_path.name, "unknown")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products_created = 0
        matches_created = 0
        
        logger.info(f"Processing {len(data)} products from {file_path.name}")
        
        for product_name, retailer_prices in data.items():
            if not retailer_prices:  # Skip empty entries
                continue
                
            try:
                # Get or create products for each retailer
                product_ids = await self._get_or_create_products(product_name, retailer_prices, category)
                
                if len(product_ids) < 2:
                    logger.debug(f"Skipping {product_name} - not enough retailers ({len(product_ids)})")
                    continue
                
                # Create matches between all retailer combinations
                match_count = await self._create_product_matches(product_name, product_ids)
                
                products_created += len(product_ids)
                matches_created += match_count
                
                if products_created % 10 == 0:  # Log progress every 10 products
                    logger.info(f"Progress: {products_created} products, {matches_created} matches processed...")
                    
            except Exception as e:
                logger.error(f"Error processing product '{product_name}': {e}")
                continue
        
        return products_created, matches_created
    
    async def _get_or_create_products(self, product_name: str, retailer_prices: Dict[str, float], category: str) -> Dict[str, UUID]:
        """Get or create products for each retailer"""
        product_ids = {}
        
        for retailer_name, price in retailer_prices.items():
            retailer_code = self.RETAILER_MAPPING.get(retailer_name, retailer_name.upper()[:3])
            
            try:
                # Try to find existing product by name and retailer
                existing_result = self.db_service.client.table('products')\
                    .select('id')\
                    .eq('name', product_name)\
                    .eq('retailer_code', retailer_code)\
                    .limit(1)\
                    .execute()
                
                if existing_result.data:
                    product_id = UUID(existing_result.data[0]['id'])
                    product_ids[retailer_code] = product_id
                    logger.debug(f"Found existing product: {product_name} @ {retailer_code}")
                else:
                    # Create new product
                    new_product = {
                        'name': product_name,
                        'retailer_code': retailer_code,
                        'category': category,
                        'current_price': float(price),
                        'original_price': float(price),
                        'brand': self._extract_brand(product_name),
                        'sku': f"IMPORT_{uuid4().hex[:8]}",
                        'availability': 'in_stock',
                        'description': f"Imported from {retailer_name}",
                        'url': f"https://imported-{retailer_code.lower()}.example.com/product",
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    result = self.db_service.client.table('products')\
                        .insert(new_product)\
                        .execute()
                    
                    if result.data:
                        product_id = UUID(result.data[0]['id'])
                        product_ids[retailer_code] = product_id
                        logger.debug(f"Created new product: {product_name} @ {retailer_code}")
                    
            except Exception as e:
                logger.error(f"Error creating product {product_name} @ {retailer_name}: {e}")
                continue
        
        return product_ids
    
    async def _create_product_matches(self, product_name: str, product_ids: Dict[str, UUID]) -> int:
        """Create matches between all product combinations"""
        retailer_codes = list(product_ids.keys())
        matches_created = 0
        
        # Create matches for all retailer combinations
        for i in range(len(retailer_codes)):
            for j in range(i + 1, len(retailer_codes)):
                source_retailer = retailer_codes[i]
                matched_retailer = retailer_codes[j]
                
                source_id = product_ids[source_retailer]
                matched_id = product_ids[matched_retailer]
                
                try:
                    # Check if match already exists
                    existing_match = self.db_service.client.table('matching_results')\
                        .select('id')\
                        .eq('source_product_id', str(source_id))\
                        .eq('matched_product_id', str(matched_id))\
                        .execute()
                    
                    # Also check reverse match
                    existing_reverse = self.db_service.client.table('matching_results')\
                        .select('id')\
                        .eq('source_product_id', str(matched_id))\
                        .eq('matched_product_id', str(source_id))\
                        .execute()
                    
                    if existing_match.data or existing_reverse.data:
                        logger.debug(f"Match already exists: {source_retailer} <-> {matched_retailer}")
                        continue
                    
                    # Create new match
                    match_data = {
                        'source_product_id': str(source_id),
                        'matched_product_id': str(matched_id),
                        'confidence_score': 0.95,  # High confidence for pre-matched data
                        'matching_method': 'hybrid',
                        'status': 'confirmed',  # Pre-matched data is confirmed
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    result = self.db_service.client.table('matching_results')\
                        .insert(match_data)\
                        .execute()
                    
                    if result.data:
                        matches_created += 1
                        
                        # Create metadata for the match
                        match_id = result.data[0]['id']
                        await self._create_match_metadata(match_id, product_name, source_retailer, matched_retailer)
                        
                        logger.debug(f"Created match: {product_name} ({source_retailer} <-> {matched_retailer})")
                    
                except Exception as e:
                    logger.error(f"Error creating match for {product_name}: {e}")
                    continue
        
        return matches_created
    
    async def _create_match_metadata(self, match_id: str, product_name: str, source_retailer: str, matched_retailer: str):
        """Create metadata for a match"""
        try:
            metadata = {
                'matching_result_id': match_id,
                'metadata_key': 'import_info',
                'metadata_value': {
                    'source': 'json_import',
                    'product_name': product_name,
                    'retailers': f"{source_retailer} <-> {matched_retailer}",
                    'confidence_reason': 'pre_matched_data',
                    'matching_method': 'hybrid',
                    'import_date': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat()
            }
            
            self.db_service.client.table('matching_metadata')\
                .insert(metadata)\
                .execute()
            
        except Exception as e:
            logger.error(f"Error creating metadata for match {match_id}: {e}")
    
    def _extract_brand(self, product_name: str) -> str:
        """Try to extract brand from product name"""
        # Common brand patterns in Thai product names
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY', 'POWER TOOL',
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN',
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC'
        ]
        
        product_upper = product_name.upper()
        
        for brand in common_brands:
            if brand in product_upper:
                return brand
        
        # Try to extract the first word/phrase that looks like a brand
        words = product_name.split()
        if len(words) > 0:
            # Look for capitalized words or brand-like patterns
            for word in words:
                if len(word) > 2 and (word.isupper() or word.istitle()):
                    return word
        
        return "UNKNOWN"
    
    async def get_import_stats(self) -> Dict[str, Any]:
        """Get statistics about imported data"""
        try:
            # Count total matches
            matches_result = self.db_service.client.table('matching_results')\
                .select('id', count='exact')\
                .execute()
            total_matches = matches_result.count or 0
            
            # Count confirmed matches (imported data)
            confirmed_matches = self.db_service.client.table('matching_results')\
                .select('id', count='exact')\
                .eq('status', 'confirmed')\
                .execute()
            confirmed_count = confirmed_matches.count or 0
            
            # Count imported matches
            imported_matches = self.db_service.client.table('matching_results')\
                .select('id', count='exact')\
                .eq('matching_method', 'imported')\
                .execute()
            imported_count = imported_matches.count or 0
            
            # Get top categories
            products_result = self.db_service.client.table('products')\
                .select('category')\
                .execute()
            
            categories = {}
            for product in products_result.data or []:
                cat = product.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                'total_matches': total_matches,
                'confirmed_matches': confirmed_count,
                'imported_matches': imported_count,
                'categories': categories,
                'top_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"Error getting import stats: {e}")
            return {}


async def main():
    """Main import function"""
    print("🚀 Starting Matched Product Data Import")
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
            print(f"   - {f}")
    
    print(f"📁 Found {len(existing_files)} files to import:")
    for f in existing_files:
        print(f"   ✅ {Path(f).name}")
    
    if not existing_files:
        print("❌ No files found to import")
        return 1
    
    try:
        importer = MatchedProductImporter()
        
        # Import all files
        success = await importer.import_all_files(existing_files)
        
        if success:
            # Show statistics
            print("\n📊 Import Statistics:")
            stats = await importer.get_import_stats()
            
            print(f"   Total matches: {stats.get('total_matches', 0)}")
            print(f"   Confirmed matches: {stats.get('confirmed_matches', 0)}")
            print(f"   Imported matches: {stats.get('imported_matches', 0)}")
            
            if stats.get('top_categories'):
                print("   Top categories:")
                for category, count in stats['top_categories']:
                    print(f"     - {category}: {count} products")
            
            print("\n🎉 Import completed successfully!")
            print("✅ Your matched product data is now in the database")
            print("\n📋 Next steps:")
            print("1. Test price comparison API: http://localhost:8001/api/price-comparisons-v2/detailed-comparisons")
            print("2. Check frontend: http://localhost:3000/price-comparisons")
            print("3. Verify data with v2 API: http://localhost:8001/api/v2/matches/matches/stats")
            return 0
        else:
            print("\n❌ Import failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))