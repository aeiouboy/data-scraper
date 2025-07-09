#!/usr/bin/env python3
"""
Check the status of data collection in the database
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_database_status():
    """Check what data is currently in the database"""
    supabase = SupabaseService()
    
    logger.info("🔍 Checking database status...")
    
    try:
        # Get overall statistics
        logger.info("\n📊 OVERALL DATABASE STATISTICS")
        logger.info("="*60)
        
        # Count products by retailer
        retailers = ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']
        retailer_counts = {}
        total_products = 0
        
        for retailer in retailers:
            result = await supabase.search_products(
                filters={"retailer_code": retailer},
                limit=1
            )
            count = result.get('total', 0) if result else 0
            retailer_counts[retailer] = count
            total_products += count
            
            if count > 0:
                logger.info(f"  {retailer}: {count:,} products")
        
        logger.info(f"\n  TOTAL: {total_products:,} products across all retailers")
        
        # Check categories for each retailer
        logger.info("\n📂 CATEGORIES BY RETAILER")
        logger.info("="*60)
        
        for retailer in retailers:
            if retailer_counts[retailer] > 0:
                categories = await supabase.get_categories(retailer_code=retailer)
                if categories:
                    logger.info(f"\n{retailer} Categories ({len(categories)}):")
                    for i, cat in enumerate(sorted(categories)[:10], 1):
                        logger.info(f"  {i}. {cat}")
                    if len(categories) > 10:
                        logger.info(f"  ... and {len(categories) - 10} more categories")
        
        # Check recent scraping activity
        logger.info("\n🕒 RECENT SCRAPING ACTIVITY")
        logger.info("="*60)
        
        # Get recent products (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        recent_by_retailer = {}
        for retailer in retailers:
            if retailer_counts[retailer] > 0:
                # Note: This is a simplified check - would need to query by created_at/updated_at
                recent_by_retailer[retailer] = "Check needed"
        
        # Check specific categories
        logger.info("\n🏷️ SPECIFIC CATEGORY CHECKS")
        logger.info("="*60)
        
        categories_to_check = [
            ("Refrigerators", ["refrigerator", "ตู้เย็น", "fridge"]),
            ("Air Conditioners", ["air conditioner", "แอร์", "เครื่องปรับอากาศ"]),
            ("Washing Machines", ["washing machine", "เครื่องซักผ้า"]),
            ("TVs", ["television", "tv", "ทีวี"])
        ]
        
        for category_name, search_terms in categories_to_check:
            logger.info(f"\n{category_name}:")
            category_total = 0
            
            for retailer in retailers:
                if retailer_counts[retailer] > 0:
                    retailer_category_count = 0
                    
                    for term in search_terms:
                        result = await supabase.search_products(
                            query=term,
                            filters={"retailer_code": retailer},
                            limit=1
                        )
                        if result and 'total' in result:
                            retailer_category_count += result['total']
                    
                    if retailer_category_count > 0:
                        logger.info(f"  {retailer}: {retailer_category_count} products")
                        category_total += retailer_category_count
            
            logger.info(f"  Total {category_name}: {category_total} products")
        
        # Check data quality
        logger.info("\n✅ DATA QUALITY CHECKS")
        logger.info("="*60)
        
        # Sample check for each retailer
        for retailer in retailers:
            if retailer_counts[retailer] > 0:
                # Get a sample of products
                result = await supabase.search_products(
                    filters={"retailer_code": retailer},
                    limit=10
                )
                
                if result and 'products' in result:
                    products = result['products']
                    
                    # Check data completeness
                    with_prices = sum(1 for p in products if p.get('current_price'))
                    with_brands = sum(1 for p in products if p.get('brand'))
                    with_images = sum(1 for p in products if p.get('image_url'))
                    
                    logger.info(f"\n{retailer} Data Quality (sample of {len(products)}):")
                    logger.info(f"  With prices: {with_prices}/{len(products)}")
                    logger.info(f"  With brands: {with_brands}/{len(products)}")
                    logger.info(f"  With images: {with_images}/{len(products)}")
        
        # Summary report
        logger.info("\n📋 SUMMARY REPORT")
        logger.info("="*60)
        
        active_retailers = [r for r, count in retailer_counts.items() if count > 0]
        logger.info(f"Active retailers: {', '.join(active_retailers)}")
        logger.info(f"Total products: {total_products:,}")
        
        # Save report
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_products": total_products,
            "retailer_counts": retailer_counts,
            "active_retailers": active_retailers
        }
        
        filename = f"database_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Report saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await check_database_status()

if __name__ == "__main__":
    asyncio.run(main())