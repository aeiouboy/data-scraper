#!/usr/bin/env python3
"""
Simple, fast import that just creates products and matches without checking for duplicates
Relies on database constraints to handle duplicates gracefully
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleImporter:
    """Simple importer that creates everything and lets DB handle duplicates"""
    
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
    
    async def import_json_file(self, json_file_path: str) -> tuple[int, int]:
        """Import a single JSON file"""
        file_path = Path(json_file_path)
        category = self.category_mapping.get(file_path.name, "unknown")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Processing {len(data)} products from {file_path.name}")
        
        products_to_create = []
        matches_to_create = []
        
        # Process products and prepare batch inserts
        for product_name, retailer_prices in data.items():
            if len(retailer_prices) < 2:  # Skip single retailer products
                continue
            
            product_ids = {}
            
            # Create products for each retailer
            for retailer_name, price in retailer_prices.items():
                # Skip if price is None or invalid
                if price is None or price <= 0:
                    continue
                    
                retailer_code = self.RETAILER_MAPPING.get(retailer_name, retailer_name.upper()[:3])
                product_uuid = uuid4()
                product_ids[retailer_code] = product_uuid
                
                product = {
                    'id': str(product_uuid),
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
                
                products_to_create.append(product)
            
            # Create matches between all retailer combinations
            retailer_codes = list(product_ids.keys())
            for i in range(len(retailer_codes)):
                for j in range(i + 1, len(retailer_codes)):
                    source_retailer = retailer_codes[i]
                    matched_retailer = retailer_codes[j]
                    
                    match = {
                        'source_product_id': str(product_ids[source_retailer]),
                        'matched_product_id': str(product_ids[matched_retailer]),
                        'confidence_score': 0.95,
                        'matching_method': 'hybrid',
                        'status': 'confirmed',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    matches_to_create.append(match)
        
        # Batch insert products
        products_created = 0
        try:
            if products_to_create:
                logger.info(f"Creating {len(products_to_create)} products...")
                result = self.db_service.client.table('products')\
                    .insert(products_to_create)\
                    .execute()
                products_created = len(result.data) if result.data else 0
                logger.info(f"✅ Created {products_created} products")
        except Exception as e:
            logger.error(f"❌ Error creating products: {e}")
            # If batch fails, try one by one
            products_created = 0
            for product in products_to_create:
                try:
                    result = self.db_service.client.table('products')\
                        .insert([product])\
                        .execute()
                    if result.data:
                        products_created += 1
                except Exception as e2:
                    # Likely duplicate, ignore
                    pass
            logger.info(f"✅ Created {products_created} products individually")
        
        # Batch insert matches
        matches_created = 0
        try:
            if matches_to_create:
                logger.info(f"Creating {len(matches_to_create)} matches...")
                result = self.db_service.client.table('matching_results')\
                    .insert(matches_to_create)\
                    .execute()
                matches_created = len(result.data) if result.data else 0
                logger.info(f"✅ Created {matches_created} matches")
        except Exception as e:
            logger.error(f"❌ Error creating matches: {e}")
            # If batch fails, try one by one  
            matches_created = 0
            for match in matches_to_create:
                try:
                    result = self.db_service.client.table('matching_results')\
                        .insert([match])\
                        .execute()
                    if result.data:
                        matches_created += 1
                except Exception as e2:
                    # Likely duplicate, ignore
                    pass
            logger.info(f"✅ Created {matches_created} matches individually")
        
        return products_created, matches_created
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY', 
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN',
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC', 'SHARK'
        ]
        
        product_upper = product_name.upper()
        for brand in common_brands:
            if brand in product_upper:
                return brand
        
        # Try first word
        words = product_name.split()
        if words and len(words[0]) > 2:
            return words[0].upper()
        
        return "UNKNOWN"


async def main():
    """Test simple import"""
    print("🚀 Testing simple import approach...")
    
    test_file = "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_door_material.json"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    try:
        importer = SimpleImporter()
        
        start_time = datetime.now()
        products_count, matches_count = await importer.import_json_file(test_file)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Simple import completed!")
        print(f"📊 Results: {products_count} products, {matches_count} matches")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        return 0
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))