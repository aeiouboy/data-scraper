#!/usr/bin/env python3
"""
Debug why category extraction is failing for HomePro products
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.strategies.hybrid_strategy import HybridStrategy

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_category_extraction():
    """Debug category extraction for a specific product"""
    
    test_url = "https://www.homepro.co.th/p/1097133"
    
    logger.info(f"🔍 Debugging category extraction for: {test_url}")
    
    try:
        # Initialize strategy
        config = {
            'name': 'HomePro',
            'code': 'HP',
            'base_url': 'https://www.homepro.co.th',
            'rate_limit_delay': 2.0,
            'max_concurrent': 3,
            'timeout': 30,
            'retry_attempts': 2
        }
        
        strategy = HybridStrategy(config)
        
        # Scrape with native strategy
        result = await strategy.scrape_url(test_url)
        
        if result.success and result.data:
            logger.info(f"✅ Scraping successful using: {result.strategy_used}")
            
            # Check what data was extracted
            data = result.data
            
            logger.info("\n📋 Extracted Data Keys:")
            for key in sorted(data.keys()):
                logger.info(f"   - {key}")
            
            # Look for category-related fields
            logger.info("\n🔍 Category-related fields:")
            category_fields = ['category', 'categories', 'breadcrumb', 'breadcrumbs', 'category_path']
            for field in category_fields:
                if field in data:
                    logger.info(f"   ✅ {field}: {data[field]}")
                else:
                    logger.info(f"   ❌ {field}: NOT FOUND")
            
            # Check the raw HTML for breadcrumb patterns
            if 'content' in data or 'html' in data:
                html_content = data.get('content', data.get('html', ''))
                
                # Search for breadcrumb patterns
                breadcrumb_patterns = [
                    'breadcrumb',
                    'กริ่งไร้สาย',
                    'กริ่งประตู',
                    'หมวดไฟฟ้า',
                    'nav-breadcrumb',
                    'category-path',
                    'ELT0201'
                ]
                
                logger.info("\n🔍 Searching HTML for breadcrumb patterns:")
                for pattern in breadcrumb_patterns:
                    if pattern.lower() in html_content.lower():
                        logger.info(f"   ✅ Found pattern: {pattern}")
                        
                        # Extract context around the pattern
                        idx = html_content.lower().find(pattern.lower())
                        context = html_content[max(0, idx-100):idx+100]
                        logger.info(f"      Context: ...{context}...")
                    else:
                        logger.info(f"   ❌ Pattern not found: {pattern}")
            
            # Show what category was extracted (if any)
            if 'category' in data:
                logger.info(f"\n📊 Final extracted category: {data['category']}")
            else:
                logger.info("\n❌ No category was extracted")
                
        else:
            logger.error(f"❌ Scraping failed: {result.error}")
            
    except Exception as e:
        logger.error(f"💥 Error during debug: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await strategy.close()

if __name__ == "__main__":
    asyncio.run(debug_category_extraction())