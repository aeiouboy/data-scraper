#!/usr/bin/env python3
"""
Optimized script to populate ALL product_matches from JSON files using batch operations
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizedProductMatchesPopulator:
    """Optimized version that processes all JSON data and creates product_matches entries"""
    
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
    
    async def process_all_files(self, json_files: List[str], limit_per_file: int = None):
        """Process all JSON files and create product_matches entries using fake IDs for display"""
        
        logger.info("🗑️ Clearing existing imported data...")
        try:
            result = self.db_service.client.table('product_matches')\
                .delete()\
                .contains('match_criteria', {"source": "imported_json"})\
                .execute()
            logger.info("Cleared existing imported entries")
        except Exception as e:
            logger.warning(f"Could not clear existing data: {e}")
        
        # Get or create dummy master product for imported JSON data
        logger.info("📦 Getting dummy master product for imported data...")
        try:
            # Try to find existing dummy product first
            result = self.db_service.client.table('products')\
                .select('id')\
                .eq('retailer_code', 'VRT')\
                .eq('sku', 'VRT01')\
                .limit(1)\
                .execute()
            
            if result.data:
                self.dummy_master_id = result.data[0]['id']
                logger.info(f"✅ Using existing dummy master product: {self.dummy_master_id}")
            else:
                # Create new dummy product
                dummy_product = {
                    'sku': 'VRT01',
                    'name': 'JSON_IMPORT_VIRTUAL_MASTER',
                    'brand': 'VRT',
                    'category': 'import', 
                    'retailer_code': 'VRT',
                    'retailer_name': 'Virtual',
                    'current_price': 0.0,
                    'description': 'Virtual master for imported JSON data',
                    'specifications': {'source': 'imported_json'},
                    'url': 'https://virtual.local/master',
                    'availability': 'virtual',
                    'scraped_at': datetime.now().isoformat()
                }
                
                result = self.db_service.client.table('products').insert(dummy_product).execute()
                if result.data:
                    self.dummy_master_id = result.data[0]['id']
                    logger.info(f"✅ Created dummy master product: {self.dummy_master_id}")
                else:
                    raise Exception("Could not create dummy master product")
                    
        except Exception as e:
            if "duplicate key" in str(e):
                # Dummy product exists, find it
                result = self.db_service.client.table('products')\
                    .select('id')\
                    .eq('retailer_code', 'VRT')\
                    .eq('sku', 'VRT01')\
                    .limit(1)\
                    .execute()
                
                if result.data:
                    self.dummy_master_id = result.data[0]['id']
                    logger.info(f"✅ Using existing dummy master product: {self.dummy_master_id}")
                else:
                    logger.error(f"Dummy product exists but could not find it: {e}")
                    raise
            else:
                logger.error(f"Failed to create dummy master product: {e}")
                raise
        
        total_created = 0
        all_matches = []
        
        for json_file in json_files:
            if not Path(json_file).exists():
                logger.warning(f"File not found: {json_file}")
                continue
                
            logger.info(f"📁 Processing {Path(json_file).name}...")
            file_matches = await self.process_json_file(json_file, limit_per_file)
            all_matches.extend(file_matches)
            logger.info(f"✅ Prepared {len(file_matches)} matches from {Path(json_file).name}")
        
        # Batch insert all matches
        if all_matches:
            logger.info(f"💾 Batch inserting {len(all_matches)} product matches...")
            try:
                # Insert in batches of 1000 to avoid timeout
                batch_size = 1000
                created_count = 0
                
                for i in range(0, len(all_matches), batch_size):
                    batch = all_matches[i:i + batch_size]
                    logger.info(f"Inserting batch {i//batch_size + 1}/{(len(all_matches) + batch_size - 1)//batch_size}")
                    
                    result = self.db_service.client.table('product_matches')\
                        .insert(batch)\
                        .execute()
                    
                    if result.data:
                        created_count += len(result.data)
                        logger.info(f"✅ Batch inserted {len(result.data)} records")
                        time.sleep(0.5)  # Brief pause between batches
                
                total_created = created_count
                logger.info(f"🎉 Total created: {total_created} product matches")
                
            except Exception as e:
                logger.error(f"❌ Batch insert failed: {e}")
                return 0
        
        return total_created
    
    async def process_json_file(self, json_file: str, limit: int = None) -> List[Dict]:
        """Process single JSON file and return match records"""
        
        file_path = Path(json_file)
        category = self.category_mapping.get(file_path.name, "unknown")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        product_matches = []
        processed = 0
        
        for product_name, retailer_prices in data.items():
            if limit and processed >= limit:
                break
                
            # Skip products with < 2 retailers or None prices
            valid_prices = {retailer: price for retailer, price in retailer_prices.items() 
                          if price is not None and price > 0}
            
            if len(valid_prices) < 2:
                continue
            
            try:
                # Calculate price statistics
                prices = list(valid_prices.values())
                min_price = min(prices)
                max_price = max(prices)
                
                # Skip only if price is zero or negative
                if min_price <= 0:
                    continue
                
                # Find best price retailer
                best_retailer_name = min(valid_prices.keys(), key=lambda r: valid_prices[r])
                best_retailer_code = self.RETAILER_MAPPING.get(best_retailer_name, best_retailer_name.upper()[:3])
                
                # Calculate price variance percentage (cap at 999% due to database constraint)
                price_variance = ((max_price - min_price) / min_price) * 100
                price_variance = min(price_variance, 999.0)  # Cap at 999% to fit database precision
                
                # Extract brand from product name
                brand = self._extract_brand(product_name)
                
                # Create product_matches entry using dummy master ID
                product_match = {
                    'id': str(uuid4()),
                    'master_product_id': self.dummy_master_id,  # Use dummy master product
                    'matched_product_ids': [],  # Empty array for now
                    'match_confidence': 0.95,  # High confidence since data is pre-matched
                    'match_criteria': {
                        'algorithm_version': '2.0',
                        'source': 'imported_json',
                        'file': file_path.name,
                        'confidence_scores': {'overall': 0.95},
                        'retailers': list(valid_prices.keys()),
                        'prices': valid_prices,
                        'virtual_master_id': str(uuid4()),  # Store virtual ID in criteria instead
                        'virtual_matched_ids': [str(uuid4()) for _ in valid_prices]  # Virtual matched IDs
                    },
                    'normalized_name': product_name[:200],
                    'normalized_brand': brand[:50],
                    'unified_category': category,
                    'key_specifications': self._extract_specifications(product_name),
                    'price_range_min': float(min_price),
                    'price_range_max': float(max_price), 
                    'best_price_retailer': best_retailer_code,
                    'price_variance_percentage': float(price_variance),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                product_matches.append(product_match)
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing {product_name}: {e}")
                continue
        
        return product_matches
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY',
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN', 
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC', 'SHARK',
            'WINKING', 'WINDOORS', 'FONTE', 'NK', 'ONLY', 'ROCKET', 'SEAGULL'
        ]
        
        product_upper = product_name.upper()
        for brand in common_brands:
            if brand in product_upper:
                return brand
        
        # Try first meaningful word
        words = product_name.split()
        for word in words:
            if len(word) > 2 and (word.isupper() or word.istitle()):
                return word[:20]
        
        return "UNKNOWN"
    
    def _extract_specifications(self, product_name: str) -> Dict[str, Any]:
        """Extract specifications from product name"""
        specs = {}
        
        # Look for size patterns
        import re
        
        # Size patterns (cm, mm, inch)
        size_patterns = [
            r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*(?:[xX×]\s*(\d+\.?\d*))?\s*(ซม|cm|มม|mm|นิ้ว|inch)',
            r'ขนาด\s*(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*ซม',
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                dimensions = [g for g in match.groups() if g and g.replace('.', '').isdigit()]
                if len(dimensions) >= 2:
                    specs['dimensions'] = 'x'.join(dimensions[:3])
                break
        
        # Weight patterns
        weight_patterns = [
            r'(\d+\.?\d*)\s*(กก|kg|กรัม|g|แกลอน|gallon)',
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                specs['weight'] = f"{match.group(1)} {match.group(2)}"
                break
        
        return specs


async def main():
    """Main function"""
    print("🚀 Populating ALL product_matches from JSON files (OPTIMIZED)")
    print("=" * 70)
    
    # All JSON files 
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
    
    try:
        start_time = time.time()
        processor = OptimizedProductMatchesPopulator()
        total_created = await processor.process_all_files(json_files, limit_per_file=None)  # Import ALL available data - no limits
        end_time = time.time()
        
        if total_created > 0:
            print(f"\n🎉 Successfully created {total_created} product matches in {end_time - start_time:.1f} seconds!")
            print("✅ Your pre-matched data is now visible in frontend!")
            print(f"🌐 Check: http://localhost:3000/price-comparisons")
            
            # Show some stats
            print(f"\n📊 Categories populated:")
            processor = OptimizedProductMatchesPopulator()
            for file in json_files:
                if Path(file).exists():
                    category = processor.category_mapping.get(Path(file).name, "unknown")
                    print(f"   - {category}")
            
            return 0
        else:
            print("❌ No data was created")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))