#!/usr/bin/env python3
"""
Export existing Brave API matching results for migration to database
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService
from src.services.product_matcher import ProductMatcher
from src.utils.product_matcher_improved import ImprovedProductMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BraveMatchExporter:
    """Export existing Brave API matching results"""
    
    def __init__(self):
        self.db_service = SupabaseService()
        self.improved_matcher = ImprovedProductMatcher()
        self.export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0.0',
                'source': 'brave_api_migration'
            },
            'products': [],
            'matching_results': [],
            'statistics': {}
        }
    
    async def export_all_matches(
        self,
        output_file: str,
        retailer_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
        confidence_threshold: float = 0.5
    ):
        """
        Export all existing product matches from Brave API results
        
        Args:
            output_file: Path to output JSON file
            retailer_filter: Optional list of retailer codes to include
            limit: Maximum number of products to process
            confidence_threshold: Minimum confidence to export
        """
        logger.info("Starting Brave API match export...")
        
        try:
            # Get all products from database
            products = await self._get_products(retailer_filter, limit)
            logger.info(f"Found {len(products)} products to analyze")
            
            # Process products in batches to avoid memory issues
            batch_size = 50
            total_matches = 0
            
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                batch_matches = await self._process_product_batch(
                    batch, confidence_threshold
                )
                total_matches += len(batch_matches)
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}, found {len(batch_matches)} matches")
            
            # Generate statistics
            self.export_data['statistics'] = self._generate_statistics()
            
            # Save to file
            self._save_export_data(output_file)
            
            logger.info(f"Export completed: {total_matches} matches exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error during export: {e}")
            raise
    
    async def _get_products(
        self,
        retailer_filter: Optional[List[str]],
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Get products from database"""
        try:
            query = self.db_service.client.table('products').select('*')
            
            if retailer_filter:
                query = query.in_('retailer_code', retailer_filter)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    async def _process_product_batch(
        self,
        products: List[Dict[str, Any]],
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Process a batch of products to find matches"""
        batch_matches = []
        
        for product in products:
            try:
                # Skip if product already processed
                if any(p['id'] == product['id'] for p in self.export_data['products']):
                    continue
                
                # Add product to export data
                self.export_data['products'].append({
                    'id': product['id'],
                    'name': product['name'],
                    'brand': product.get('brand'),
                    'sku': product.get('sku'),
                    'retailer_code': product['retailer_code'],
                    'category': product.get('category'),
                    'price': product.get('price'),
                    'specifications': product.get('specifications', {})
                })
                
                # Find potential matches using existing algorithms
                potential_matches = await self._find_potential_matches(product)
                
                # Process each potential match
                for match_candidate in potential_matches:
                    if match_candidate['confidence'] >= confidence_threshold:
                        match_data = {
                            'source_product_id': product['id'],
                            'matched_product_id': match_candidate['id'],
                            'confidence_score': round(match_candidate['confidence'], 3),
                            'matching_method': match_candidate.get('method', 'hybrid'),
                            'brave_api_metadata': {
                                'original_query': match_candidate.get('query'),
                                'brave_response': match_candidate.get('brave_data'),
                                'algorithm_details': match_candidate.get('algorithm_info'),
                                'export_timestamp': datetime.now().isoformat()
                            }
                        }
                        
                        batch_matches.append(match_data)
                        self.export_data['matching_results'].append(match_data)
                
                # Add small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing product {product.get('id', 'unknown')}: {e}")
                continue
        
        return batch_matches
    
    async def _find_potential_matches(
        self,
        product: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find potential matches for a product using existing algorithms
        This simulates the current Brave API matching process
        """
        try:
            # Get products from different retailers for matching
            other_retailers = await self._get_other_retailer_products(
                product['retailer_code'],
                product.get('category')
            )
            
            matches = []
            
            for candidate in other_retailers:
                # Use improved matcher to calculate similarity
                match_result = self.improved_matcher.match_products(
                    product, candidate, category=product.get('category', 'default')
                )
                confidence = match_result.confidence
                
                if confidence > 0.3:  # Only consider reasonable matches
                    matches.append({
                        'id': candidate['id'],
                        'confidence': confidence,
                        'method': 'hybrid',
                        'query': f"{product['name']} {product.get('brand', '')}",
                        'algorithm_info': {
                            'name_similarity': confidence,
                            'brand_match': product.get('brand') == candidate.get('brand'),
                            'category_match': product.get('category') == candidate.get('category')
                        }
                    })
            
            # Sort by confidence and return top matches
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            return matches[:10]  # Limit to top 10 matches
            
        except Exception as e:
            logger.error(f"Error finding matches for product {product.get('id')}: {e}")
            return []
    
    async def _get_other_retailer_products(
        self,
        current_retailer: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get products from other retailers for comparison"""
        try:
            query = self.db_service.client.table('products')\
                .select('*')\
                .neq('retailer_code', current_retailer)
            
            if category:
                query = query.eq('category', category)
            
            # Limit to avoid memory issues
            result = query.limit(500).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error fetching other retailer products: {e}")
            return []
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate export statistics"""
        total_products = len(self.export_data['products'])
        total_matches = len(self.export_data['matching_results'])
        
        # Count by retailer
        retailer_counts = {}
        for product in self.export_data['products']:
            retailer = product['retailer_code']
            retailer_counts[retailer] = retailer_counts.get(retailer, 0) + 1
        
        # Count by method
        method_counts = {}
        for match in self.export_data['matching_results']:
            method = match['matching_method']
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Confidence distribution
        confidences = [m['confidence_score'] for m in self.export_data['matching_results']]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_products_analyzed': total_products,
            'total_matches_found': total_matches,
            'average_confidence': round(avg_confidence, 3),
            'matches_per_product': round(total_matches / total_products, 2) if total_products > 0 else 0,
            'retailer_distribution': retailer_counts,
            'method_distribution': method_counts,
            'confidence_ranges': {
                'high_confidence': len([c for c in confidences if c >= 0.8]),
                'medium_confidence': len([c for c in confidences if 0.6 <= c < 0.8]),
                'low_confidence': len([c for c in confidences if c < 0.6])
            }
        }
    
    def _save_export_data(self, output_file: str):
        """Save export data to JSON file"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Export data saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving export data: {e}")
            raise


async def main():
    """Main export function"""
    parser = argparse.ArgumentParser(description='Export Brave API matching results')
    parser.add_argument('--output', '-o', default='data/migration/brave_matches_export.json',
                       help='Output file path')
    parser.add_argument('--retailers', nargs='+', 
                       help='Filter by retailer codes (HP, TWD, GH, etc.)')
    parser.add_argument('--limit', type=int,
                       help='Limit number of products to process')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Minimum confidence threshold (default: 0.5)')
    
    args = parser.parse_args()
    
    exporter = BraveMatchExporter()
    
    try:
        await exporter.export_all_matches(
            output_file=args.output,
            retailer_filter=args.retailers,
            limit=args.limit,
            confidence_threshold=args.confidence
        )
        
        print(f"\n✅ Export completed successfully!")
        print(f"📁 Output file: {args.output}")
        print(f"📊 Statistics: {exporter.export_data['statistics']}")
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())