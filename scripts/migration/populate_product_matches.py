#!/usr/bin/env python3
"""
Populate product_matches table from matching_results data
This will make our imported data visible in the frontend price comparisons
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductMatchesPopulator:
    """Transform matching_results into product_matches format"""
    
    def __init__(self):
        self.db_service = SupabaseService()
    
    async def populate_matches(self, limit: int = 1000):
        """Transform confirmed matches from matching_results to product_matches"""
        
        logger.info("Starting population of product_matches table...")
        
        # Get confirmed matches with their product details
        logger.info("Fetching confirmed matches with product details...")
        
        query = """
        SELECT 
            mr.id as match_id,
            mr.confidence_score,
            mr.created_at,
            mr.updated_at,
            p1.id as source_product_id,
            p1.name as source_name,
            p1.current_price as source_price,
            p1.retailer_code as source_retailer,
            p1.category as source_category,
            p1.brand as source_brand,
            p2.id as matched_product_id,
            p2.name as matched_name,
            p2.current_price as matched_price,
            p2.retailer_code as matched_retailer,
            p2.category as matched_category,
            p2.brand as matched_brand
        FROM matching_results mr
        JOIN products p1 ON mr.source_product_id = p1.id
        JOIN products p2 ON mr.matched_product_id = p2.id
        WHERE mr.status = 'confirmed' 
            AND mr.matching_method = 'hybrid'
            AND p1.current_price > 0 
            AND p2.current_price > 0
        ORDER BY mr.created_at DESC
        LIMIT {}
        """.format(limit)
        
        # Execute raw SQL query
        result = self.db_service.client.rpc('execute_sql', {'sql_query': query}).execute()
        
        if not result.data:
            logger.error("No confirmed matches found or query failed")
            return False
        
        logger.info(f"Found {len(result.data)} confirmed matches")
        
        # Group matches by product name/brand to create consolidated entries
        product_groups = defaultdict(list)
        
        for match in result.data:
            # Use normalized product name as grouping key
            product_key = self._normalize_product_name(match['source_name'])
            product_groups[product_key].append(match)
        
        logger.info(f"Grouped into {len(product_groups)} product groups")
        
        # Create product_matches entries
        product_matches_to_create = []
        
        for product_key, matches in list(product_groups.items())[:100]:  # Limit to first 100 for testing
            try:
                match_entry = self._create_product_match_entry(product_key, matches)
                if match_entry:
                    product_matches_to_create.append(match_entry)
            except Exception as e:
                logger.error(f"Error processing product group {product_key}: {e}")
                continue
        
        if not product_matches_to_create:
            logger.error("No valid product matches created")
            return False
        
        logger.info(f"Creating {len(product_matches_to_create)} product_matches entries...")
        
        try:
            # Batch insert
            result = self.db_service.client.table('product_matches')\
                .insert(product_matches_to_create)\
                .execute()
            
            created_count = len(result.data) if result.data else 0
            logger.info(f"✅ Successfully created {created_count} product_matches entries")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inserting product_matches: {e}")
            return False
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for grouping"""
        # Simple normalization - could be enhanced
        return name.strip().lower()[:100]  # First 100 chars
    
    def _create_product_match_entry(self, product_key: str, matches: List[Dict]) -> Dict[str, Any]:
        """Create a product_matches entry from a group of matches"""
        
        if len(matches) < 2:  # Need at least 2 retailers for price comparison
            return None
        
        # Pick the first match as master
        master_match = matches[0]
        
        # Collect all retailer prices
        retailer_prices = {}
        matched_product_ids = []
        
        for match in matches:
            # Add source product
            retailer_prices[match['source_retailer']] = {
                'product_id': match['source_product_id'],
                'price': match['source_price'],
                'name': match['source_name']
            }
            matched_product_ids.append(match['source_product_id'])
            
            # Add matched product
            retailer_prices[match['matched_retailer']] = {
                'product_id': match['matched_product_id'], 
                'price': match['matched_price'],
                'name': match['matched_name']
            }
            matched_product_ids.append(match['matched_product_id'])
        
        # Remove duplicates
        matched_product_ids = list(set(matched_product_ids))
        
        if len(retailer_prices) < 2:
            return None
        
        # Calculate price statistics
        prices = [info['price'] for info in retailer_prices.values()]
        min_price = min(prices)
        max_price = max(prices)
        
        # Find best price retailer
        best_price_retailer = min(retailer_prices.keys(), 
                                 key=lambda r: retailer_prices[r]['price'])
        
        # Calculate price variance percentage
        if min_price > 0:
            price_variance_percentage = ((max_price - min_price) / min_price) * 100
        else:
            price_variance_percentage = 0
        
        # Create the entry
        return {
            'id': str(uuid4()),
            'master_product_id': master_match['source_product_id'],
            'matched_product_ids': matched_product_ids,
            'match_confidence': float(master_match['confidence_score']),
            'match_criteria': {
                'algorithm_version': '2.0',
                'source': 'imported_data',
                'confidence_scores': {
                    'overall': float(master_match['confidence_score'])
                }
            },
            'normalized_name': master_match['source_name'][:200],  # Limit length
            'normalized_brand': master_match.get('source_brand', 'UNKNOWN')[:50],
            'unified_category': master_match.get('source_category', 'unknown'),
            'key_specifications': {},  # Could extract from product names
            'price_range_min': float(min_price),
            'price_range_max': float(max_price),
            'best_price_retailer': best_price_retailer,
            'price_variance_percentage': float(price_variance_percentage),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }


async def main():
    """Main function"""
    print("🔄 Populating product_matches table from imported data")
    print("=" * 60)
    
    try:
        populator = ProductMatchesPopulator()
        success = await populator.populate_matches(limit=2000)  # Process up to 2000 matches
        
        if success:
            print("\n✅ Successfully populated product_matches table")
            print("🌐 Your imported data should now be visible in the frontend!")
            print("🔗 Check: http://localhost:3000/price-comparisons")
            return 0
        else:
            print("\n❌ Failed to populate product_matches table")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))