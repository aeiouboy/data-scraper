#!/usr/bin/env python3
"""
Populate product_matches using REAL product IDs from our imported data
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


class RealProductMatcher:
    """Use real imported product data for product_matches"""
    
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
    
    async def process_all_files_with_real_ids(self, json_files: List[str], limit_per_file: int = 50):
        """Process files using real product IDs from database"""
        
        logger.info("🧹 Clearing old imported product_matches...")
        try:
            # Clear old imported data
            result = self.db_service.client.table('product_matches')\
                .delete()\
                .contains('match_criteria', {"source": "imported_json"})\
                .execute()
            logger.info("Cleared existing imported entries")
        except Exception as e:
            logger.warning(f"Could not clear: {e}")
        
        total_created = 0
        
        for json_file in json_files:
            if not Path(json_file).exists():
                continue
                
            logger.info(f"📁 Processing {Path(json_file).name}...")
            
            file_path = Path(json_file)
            category = self.category_mapping.get(file_path.name, "unknown")
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            created = await self.process_products_with_real_ids(data, category, limit_per_file)
            total_created += created
            
            logger.info(f"✅ Created {created} matches from {file_path.name}")
        
        logger.info(f"🎉 Total created: {total_created} product matches")
        return total_created
    
    async def process_products_with_real_ids(self, data: Dict, category: str, limit: int) -> int:
        """Process products using real IDs from database"""
        
        product_matches_to_create = []
        processed = 0
        
        for product_name, retailer_prices in data.items():
            if processed >= limit:
                break
            
            # Skip products with insufficient data
            valid_prices = {retailer: price for retailer, price in retailer_prices.items()
                          if price is not None and price > 0}
            
            if len(valid_prices) < 2:
                continue
            
            try:
                # Find real product IDs for this product name and retailers
                product_ids = {}
                
                for retailer_name, price in valid_prices.items():
                    retailer_code = self.RETAILER_MAPPING.get(retailer_name, retailer_name.upper()[:3])
                    
                    # Search for existing product in database
                    result = self.db_service.client.table('products')\
                        .select('id, name, current_price')\
                        .eq('name', product_name)\
                        .eq('retailer_code', retailer_code)\
                        .limit(1)\
                        .execute()
                    
                    if result.data:
                        product_ids[retailer_code] = {
                            'id': result.data[0]['id'],
                            'price': result.data[0]['current_price'],
                            'name': result.data[0]['name']
                        }
                
                # Need at least 2 real products for comparison
                if len(product_ids) < 2:
                    continue
                
                # Calculate price comparison
                prices = [info['price'] for info in product_ids.values()]
                min_price = min(prices)
                max_price = max(prices)
                
                # Skip if no significant price difference
                if min_price <= 0 or (max_price - min_price) / min_price < 0.01:
                    continue
                
                # Find best price retailer
                best_retailer = min(product_ids.keys(), key=lambda r: product_ids[r]['price'])
                
                # Calculate price variance
                price_variance = ((max_price - min_price) / min_price) * 100
                
                # Extract brand
                brand = self._extract_brand(product_name)
                
                # Create product_matches entry with REAL IDs
                product_match = {
                    'id': str(uuid4()),
                    'master_product_id': list(product_ids.values())[0]['id'],  # First product as master
                    'matched_product_ids': [info['id'] for info in product_ids.values()],
                    'match_confidence': 0.95,
                    'match_criteria': {
                        'algorithm_version': '2.0',
                        'source': 'imported_json',
                        'category': category,
                        'confidence_scores': {'overall': 0.95}
                    },
                    'normalized_name': product_name[:200],
                    'normalized_brand': brand[:50],
                    'unified_category': category,
                    'key_specifications': self._extract_specs(product_name),
                    'price_range_min': float(min_price),
                    'price_range_max': float(max_price),
                    'best_price_retailer': best_retailer,
                    'price_variance_percentage': float(price_variance),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                product_matches_to_create.append(product_match)
                processed += 1
                
                logger.info(f"  Added: {product_name[:60]}... ({len(product_ids)} retailers, {price_variance:.1f}% variance)")
                
            except Exception as e:
                logger.error(f"Error processing {product_name}: {e}")
                continue
        
        # Batch insert
        if product_matches_to_create:
            try:
                logger.info(f"Inserting {len(product_matches_to_create)} product matches...")
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
                    except Exception as e2:
                        logger.warning(f"Individual insert failed: {e2}")
                        continue
                
                logger.info(f"Created {created_count} matches individually")
                return created_count
        
        return 0
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY',
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN',
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC', 'SHARK',
            'WINKING', 'WINDOORS', 'FONTE', 'NK', 'ONLY'
        ]
        
        product_upper = product_name.upper()
        for brand in common_brands:
            if brand in product_upper:
                return brand
        
        # Try first meaningful word
        words = product_name.split()
        for word in words:
            if len(word) > 2 and word[0].isupper():
                return word[:20]
        
        return "UNKNOWN"
    
    def _extract_specs(self, product_name: str) -> Dict:
        """Extract basic specifications"""
        specs = {}
        
        # Look for dimensions
        import re
        
        dimension_match = re.search(r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)', product_name)
        if dimension_match:
            specs['dimensions'] = f"{dimension_match.group(1)}x{dimension_match.group(2)}"
        
        # Look for weight/volume
        weight_match = re.search(r'(\d+\.?\d*)\s*(กก|kg|ลิตร|L|แกลอน)', product_name)
        if weight_match:
            specs['capacity'] = f"{weight_match.group(1)} {weight_match.group(2)}"
        
        return specs


async def main():
    print("🚀 Populating product_matches with REAL product IDs")
    print("=" * 60)
    
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
        processor = RealProductMatcher()
        total_created = await processor.process_all_files_with_real_ids(json_files, limit_per_file=30)
        
        if total_created > 0:
            print(f"\n🎉 Successfully created {total_created} product matches!")
            print("✅ Your matched data is now visible in frontend!")  
            print("🌐 Check: http://localhost:3000/price-comparisons")
            return 0
        else:
            print("❌ No matches were created")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))