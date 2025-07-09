#!/usr/bin/env python3
"""
Check what categories are available in price comparisons
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_categories():
    """Check categories in product_matches table"""
    supabase = SupabaseService()
    
    logger.info("🔍 Checking price comparison categories...")
    
    try:
        # Get all unique categories from product_matches
        matches_result = supabase.client.table('product_matches')\
            .select('unified_category')\
            .execute()
        
        if matches_result.data:
            # Count categories
            category_counts = {}
            for match in matches_result.data:
                cat = match.get('unified_category', 'Unknown')
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            logger.info(f"\n📊 PRODUCT MATCHES CATEGORIES")
            logger.info("="*60)
            logger.info(f"Total matches: {len(matches_result.data)}")
            logger.info(f"Unique categories: {len(category_counts)}")
            logger.info("\nCategory breakdown:")
            
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {cat}: {count} matches")
        
        # Also check what categories exist in products table
        logger.info(f"\n📦 PRODUCTS TABLE CATEGORIES")
        logger.info("="*60)
        
        # Get categories from products
        products_result = supabase.client.table('products')\
            .select('category, retailer_code')\
            .execute()
        
        if products_result.data:
            retailer_categories = {}
            for product in products_result.data:
                retailer = product.get('retailer_code', 'Unknown')
                cat = product.get('category', 'Unknown')
                
                if retailer not in retailer_categories:
                    retailer_categories[retailer] = {}
                
                retailer_categories[retailer][cat] = retailer_categories[retailer].get(cat, 0) + 1
            
            for retailer, categories in retailer_categories.items():
                logger.info(f"\n{retailer} Categories:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                    logger.info(f"  {cat}: {count} products")
        
        # Check sample product matches
        logger.info(f"\n🔗 SAMPLE PRODUCT MATCHES")
        logger.info("="*60)
        
        sample_matches = supabase.client.table('product_matches')\
            .select('*')\
            .limit(5)\
            .execute()
        
        if sample_matches.data:
            for i, match in enumerate(sample_matches.data, 1):
                logger.info(f"\nMatch {i}:")
                logger.info(f"  ID: {match.get('id')}")
                logger.info(f"  Master Product ID: {match.get('master_product_id')}")
                logger.info(f"  Matched Products: {len(match.get('matched_product_ids', []))}")
                logger.info(f"  Category: {match.get('unified_category')}")
                logger.info(f"  Brand: {match.get('unified_brand')}")
                logger.info(f"  Model: {match.get('unified_model')}")
                logger.info(f"  Price Variance: {match.get('price_variance_percentage')}%")
        
    except Exception as e:
        logger.error(f"Error checking categories: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await check_categories()

if __name__ == "__main__":
    asyncio.run(main())