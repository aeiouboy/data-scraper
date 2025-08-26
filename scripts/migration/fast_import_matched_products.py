#!/usr/bin/env python3
"""
Optimized import of matched product data from JSON files to Supabase database
Batch processing to reduce API calls and improve performance
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4, UUID
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastMatchedProductImporter:
    """Optimized import with batch operations"""
    
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
        # Cache for existing products to avoid repeated queries
        self.product_cache: Dict[str, UUID] = {}  # key: "product_name:retailer_code"
        self.existing_matches: Set[tuple] = set()  # Set of (source_id, matched_id) tuples
    
    async def import_json_file(self, json_file_path: str) -> tuple[int, int]:
        """Import a single JSON file with batch operations"""
        file_path = Path(json_file_path)
        category = self.category_mapping.get(file_path.name, "unknown")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Processing {len(data)} products from {file_path.name}")
        
        # Pre-load existing products to cache
        await self._load_product_cache(data, category)
        
        # Pre-load existing matches
        await self._load_existing_matches()
        
        # Batch process products
        products_to_create = []
        matches_to_create = []
        metadata_to_create = []
        
        for product_name, retailer_prices in data.items():
            if not retailer_prices or len(retailer_prices) < 2:  # Skip empty or single retailer
                continue
                
            # Get or prepare products for each retailer
            product_ids = await self._get_or_prepare_products(
                product_name, retailer_prices, category, products_to_create
            )
            
            if len(product_ids) < 2:
                continue
                
            # Prepare matches between all retailer combinations
            self._prepare_product_matches(
                product_name, product_ids, matches_to_create, metadata_to_create
            )
        
        # Batch insert new products
        products_created = 0
        if products_to_create:
            try:
                result = self.db_service.client.table('products')\
                    .insert(products_to_create)\
                    .execute()
                products_created = len(result.data) if result.data else 0
                logger.info(f"Created {products_created} new products")
                
                # Update cache with new products
                for product in result.data:
                    cache_key = f"{product['name']}:{product['retailer_code']}"
                    self.product_cache[cache_key] = UUID(product['id'])
                    
            except Exception as e:
                logger.error(f"Error batch creating products: {e}")
        
        # Batch insert matches
        matches_created = 0
        if matches_to_create:
            try:
                result = self.db_service.client.table('matching_results')\
                    .insert(matches_to_create)\
                    .execute()
                matches_created = len(result.data) if result.data else 0
                logger.info(f"Created {matches_created} new matches")
                
                # Prepare metadata with actual match IDs
                if result.data and metadata_to_create:
                    # Update metadata with actual match IDs
                    for i, match in enumerate(result.data):
                        if i < len(metadata_to_create):
                            metadata_to_create[i]['matching_result_id'] = match['id']
                    
                    # Batch insert metadata
                    try:
                        self.db_service.client.table('matching_metadata')\
                            .insert(metadata_to_create[:len(result.data)])\
                            .execute()
                        logger.info(f"Created {len(result.data)} metadata records")
                    except Exception as e:
                        logger.error(f"Error creating metadata: {e}")
                        
            except Exception as e:
                logger.error(f"Error batch creating matches: {e}")
        
        return products_created, matches_created
    
    async def _load_product_cache(self, data: Dict[str, Dict[str, float]], category: str):
        """Pre-load existing products into cache"""
        logger.info("Loading existing products into cache...")
        
        # Get all unique product names and retailers from the JSON
        all_combinations = []
        for product_name, retailer_prices in data.items():
            for retailer_name in retailer_prices.keys():
                retailer_code = self.RETAILER_MAPPING.get(retailer_name, retailer_name.upper()[:3])
                all_combinations.append((product_name, retailer_code))
        
        # Query in batches to avoid URL length limits
        batch_size = 50
        for i in range(0, len(all_combinations), batch_size):
            batch = all_combinations[i:i + batch_size]
            
            try:
                # Build OR query for this batch
                or_conditions = []
                for product_name, retailer_code in batch:
                    or_conditions.append(f"and(name.eq.{product_name},retailer_code.eq.{retailer_code})")
                
                if or_conditions:
                    or_query = f"or({','.join(or_conditions)})"
                    
                    result = self.db_service.client.table('products')\
                        .select('id,name,retailer_code')\
                        .or_(or_query)\
                        .execute()
                    
                    if result.data:
                        for product in result.data:
                            cache_key = f"{product['name']}:{product['retailer_code']}"
                            self.product_cache[cache_key] = UUID(product['id'])
                            
            except Exception as e:
                logger.warning(f"Error loading product batch: {e}")
                # Fallback to individual queries if batch fails
                for product_name, retailer_code in batch:
                    try:
                        result = self.db_service.client.table('products')\
                            .select('id')\
                            .eq('name', product_name)\
                            .eq('retailer_code', retailer_code)\
                            .limit(1)\
                            .execute()
                        
                        if result.data:
                            cache_key = f"{product_name}:{retailer_code}"
                            self.product_cache[cache_key] = UUID(result.data[0]['id'])
                            
                    except Exception as e2:
                        logger.warning(f"Error loading individual product {product_name}:{retailer_code}: {e2}")
        
        logger.info(f"Loaded {len(self.product_cache)} existing products into cache")
    
    async def _load_existing_matches(self):
        """Pre-load existing matches to avoid duplicates"""
        logger.info("Loading existing matches...")
        
        try:
            result = self.db_service.client.table('matching_results')\
                .select('source_product_id,matched_product_id')\
                .execute()
            
            if result.data:
                for match in result.data:
                    source_id = UUID(match['source_product_id'])
                    matched_id = UUID(match['matched_product_id'])
                    self.existing_matches.add((source_id, matched_id))
                    self.existing_matches.add((matched_id, source_id))  # Both directions
                    
            logger.info(f"Loaded {len(self.existing_matches)//2} existing matches")
            
        except Exception as e:
            logger.warning(f"Error loading existing matches: {e}")
    
    async def _get_or_prepare_products(
        self, 
        product_name: str, 
        retailer_prices: Dict[str, float], 
        category: str,
        products_to_create: List[Dict]
    ) -> Dict[str, UUID]:
        """Get existing products or prepare new ones for batch creation"""
        product_ids = {}
        
        for retailer_name, price in retailer_prices.items():
            retailer_code = self.RETAILER_MAPPING.get(retailer_name, retailer_name.upper()[:3])
            cache_key = f"{product_name}:{retailer_code}"
            
            if cache_key in self.product_cache:
                # Product exists
                product_ids[retailer_code] = self.product_cache[cache_key]
            else:
                # Prepare new product for batch creation
                product_uuid = uuid4()
                product_ids[retailer_code] = product_uuid
                
                new_product = {
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
                
                products_to_create.append(new_product)
                # Update cache immediately for this session
                self.product_cache[cache_key] = product_uuid
        
        return product_ids
    
    def _prepare_product_matches(
        self, 
        product_name: str, 
        product_ids: Dict[str, UUID],
        matches_to_create: List[Dict],
        metadata_to_create: List[Dict]
    ):
        """Prepare matches for batch creation"""
        retailer_codes = list(product_ids.keys())
        
        # Create matches for all retailer combinations
        for i in range(len(retailer_codes)):
            for j in range(i + 1, len(retailer_codes)):
                source_retailer = retailer_codes[i]
                matched_retailer = retailer_codes[j]
                
                source_id = product_ids[source_retailer]
                matched_id = product_ids[matched_retailer]
                
                # Check if match already exists
                if (source_id, matched_id) in self.existing_matches:
                    continue
                
                # Prepare match data
                match_data = {
                    'source_product_id': str(source_id),
                    'matched_product_id': str(matched_id),
                    'confidence_score': 0.95,
                    'matching_method': 'hybrid',
                    'status': 'confirmed',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                matches_to_create.append(match_data)
                
                # Prepare metadata (will be updated with actual match ID later)
                metadata = {
                    'matching_result_id': None,  # Will be filled after match creation
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
                
                metadata_to_create.append(metadata)
                
                # Add to existing matches to prevent duplicates in this session
                self.existing_matches.add((source_id, matched_id))
                self.existing_matches.add((matched_id, source_id))
    
    def _extract_brand(self, product_name: str) -> str:
        """Try to extract brand from product name"""
        # Common brand patterns in Thai product names
        common_brands = [
            'TOA', 'DAIKIN', 'HAIER', 'SAMSUNG', 'LG', 'PANASONIC', 'MITSUBISHI',
            'DEWALT', 'MAKITA', 'BOSCH', 'BLACK+DECKER', 'STANLEY', 'POWER TOOL',
            'GIANT KINGKONG', 'BARCO', 'MATALL', 'ECO DOOR', 'HYUNDAI', 'PUMPKIN',
            'SOLO', 'ROWEL', 'AAA', 'TURBO', 'BEKO', 'ELECTROLUX', 'ACONATIC', 'SHARK'
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


async def main():
    """Test with one file"""
    print("🧪 Testing optimized import with one file...")
    
    # Test with just one file first
    test_file = "/Users/chongraktanaka/Projects/data-scraper/database/db/results_test_door_material.json"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    try:
        importer = FastMatchedProductImporter()
        
        start_time = datetime.now()
        products_count, matches_count = await importer.import_json_file(test_file)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Optimized import completed!")
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