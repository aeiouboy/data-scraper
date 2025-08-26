#!/usr/bin/env python3
"""
Populate product_matches table directly from JSON files
Since the data is already perfectly matched, just transform it for display
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONToProductMatches:
    """Convert JSON match data directly to product_matches format"""
    
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
    
    async def process_all_files(self, json_files: List[str], limit_per_file: int = 100):
        """Process all JSON files and create product_matches entries"""
        
        # Clear existing imported data first
        logger.info("🗑️ Clearing existing imported data...")
        try:
            existing = self.db_service.client.table('product_matches')\
                .delete()\
                .contains('match_criteria', {"source": "imported_json"})\
                .execute()
            logger.info(f"Cleared existing imported entries")
        except Exception as e:
            logger.warning(f"Could not clear existing data: {e}")
        
        total_created = 0
        
        for json_file in json_files:
            if not Path(json_file).exists():
                logger.warning(f"File not found: {json_file}")
                continue
                
            logger.info(f"📁 Processing {Path(json_file).name}...")
            created = await self.process_json_file(json_file, limit_per_file)
            total_created += created
            logger.info(f"✅ Created {created} matches from {Path(json_file).name}")
        
        logger.info(f"🎉 Total created: {total_created} product matches")
        return total_created
    
    async def process_json_file(self, json_file: str, limit: int = 100) -> int:
        """Process single JSON file"""
        
        file_path = Path(json_file)
        category = self.category_mapping.get(file_path.name, "unknown")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        product_matches_to_create = []
        processed = 0
        
        for product_name, retailer_prices in data.items():
            if processed >= limit:
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
                
                # Skip if no meaningful price difference
                if min_price <= 0 or (max_price - min_price) / min_price < 0.01:  # Less than 1% difference
                    continue
                
                # Find best price retailer
                best_retailer_name = min(valid_prices.keys(), key=lambda r: valid_prices[r])
                best_retailer_code = self.RETAILER_MAPPING.get(best_retailer_name, best_retailer_name.upper()[:3])
                
                # Calculate price variance percentage
                price_variance = ((max_price - min_price) / min_price) * 100
                
                # Extract brand from product name
                brand = self._extract_brand(product_name)
                
                # Create product_matches entry
                product_match = {
                    'id': str(uuid4()),
                    'master_product_id': str(uuid4()),  # Fake ID since we don't have actual product records
                    'matched_product_ids': [str(uuid4()) for _ in valid_prices],  # Fake IDs
                    'match_confidence': 0.95,  # High confidence since data is pre-matched
                    'match_criteria': {
                        'algorithm_version': '2.0',
                        'source': 'imported_json',
                        'file': file_path.name,
                        'confidence_scores': {'overall': 0.95}
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
                
                product_matches_to_create.append(product_match)
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing {product_name}: {e}")
                continue
        
        # Batch insert
        if product_matches_to_create:
            try:
                result = self.db_service.client.table('product_matches')\
                    .insert(product_matches_to_create)\
                    .execute()
                
                return len(result.data) if result.data else 0
                
            except Exception as e:
                logger.error(f"Batch insert failed: {e}")
                # Try individual inserts
                created_count = 0
                for match in product_matches_to_create:
                    try:
                        result = self.db_service.client.table('product_matches')\
                            .insert([match])\
                            .execute()
                        if result.data:
                            created_count += 1
                    except:
                        pass
                return created_count
        
        return 0
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY', 
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN',
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC', 'SHARK',
            'WINKING', 'WINDOORS', 'FONTE', 'NK'
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
    print("🚀 Populating ALL product_matches from JSON files")
    print("=" * 60)
    
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
        processor = JSONToProductMatches()
        total_created = await processor.process_all_files(json_files, limit_per_file=200)  # 200 per file
        
        if total_created > 0:
            print(f"\n🎉 Successfully created {total_created} product matches!")
            print("✅ Your pre-matched data is now visible in frontend!")
            print(f"🌐 Check: http://localhost:3000/price-comparisons")
            
            # Show some stats
            print(f"\n📊 Categories available:")
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