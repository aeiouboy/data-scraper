#!/usr/bin/env python3
"""
Test the advanced matching system
"""
import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService
from src.services.advanced_product_matcher import AdvancedProductMatcher
from src.models.matching_models import MatchingAlgorithmConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_advanced_matching():
    """Test the advanced matching algorithm"""
    supabase = SupabaseService()
    
    # Configure matcher
    config = MatchingAlgorithmConfig(
        min_name_similarity=0.7,
        min_brand_similarity=0.8,
        use_ml_matching=False,  # Set to False initially to avoid ML model download
        price_variance_threshold=0.5,
        require_same_category=True
    )
    
    matcher = AdvancedProductMatcher(supabase, config)
    
    logger.info("Testing advanced product matching...")
    
    # Get some products to test - using Thai terms
    categories = [
        ('air_conditioner', 'แอร์'),
        ('refrigerator', 'ตู้เย็น'), 
        ('television', 'ทีวี')
    ]
    
    for category_en, category_th in categories:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing category: {category_en}")
        logger.info(f"{'='*60}")
        
        # Search for products in this category using Thai term
        result = await supabase.search_products(
            query=category_th,
            limit=20
        )
        
        if not result or not result.get('products'):
            logger.warning(f"No products found for {category_en}")
            continue
        
        products = result['products']
        logger.info(f"Found {len(products)} products")
        
        # Group by retailer
        by_retailer = {}
        for p in products:
            retailer = p.get('retailer_code', 'Unknown')
            if retailer not in by_retailer:
                by_retailer[retailer] = []
            by_retailer[retailer].append(p)
        
        logger.info("Products by retailer:")
        for retailer, prods in by_retailer.items():
            logger.info(f"  {retailer}: {len(prods)} products")
        
        # Run matching
        logger.info("\nRunning matching algorithm...")
        match_groups = await matcher.match_products(products)
        
        logger.info(f"Found {len(match_groups)} match groups")
        
        # Display results
        for i, group in enumerate(match_groups, 1):
            logger.info(f"\nMatch Group {i}:")
            logger.info(f"  Canonical: {group.canonical_product.normalized_name}")
            logger.info(f"  Brand: {group.canonical_product.brand}")
            logger.info(f"  Confidence: {group.confidence.overall:.2f} ({group.confidence_level.value})")
            logger.info(f"  Products matched: {len(group.matched_products)}")
            
            for product in group.matched_products:
                logger.info(f"    - {product.retailer_code}: {product.product_name[:50]}... (฿{product.current_price:,.0f})")
            
            if group.price_analysis.savings_opportunity:
                savings = group.price_analysis.savings_opportunity
                logger.info(f"  💰 Savings: ฿{savings.amount:,.0f} ({savings.percentage:.1f}%)")
                logger.info(f"  Best price at: {group.price_analysis.current_best_retailer}")
            
            logger.info(f"  Price volatility: {group.price_analysis.volatility.value}")


async def test_price_analysis():
    """Test price analysis capabilities"""
    from src.services.price_analysis_engine import PriceAnalysisEngine
    
    supabase = SupabaseService()
    analyzer = PriceAnalysisEngine(supabase)
    
    logger.info("\n" + "="*60)
    logger.info("Testing Price Analysis Engine")
    logger.info("="*60)
    
    # Get a product with price history
    products_result = supabase.client.table('products')\
        .select('id, name, retailer_code')\
        .limit(10)\
        .execute()
    
    if products_result.data:
        for product in products_result.data[:3]:  # Test first 3 products
            logger.info(f"\nAnalyzing: {product['name'][:50]}...")
            
            analysis = await analyzer.analyze_price_history(
                product['id'],
                days=30
            )
            
            if analysis['statistics']:
                stats = analysis['statistics']
                logger.info(f"  Current price: ฿{stats.get('current', 0):,.0f}")
                logger.info(f"  Average price: ฿{stats.get('mean', 0):,.0f}")
                logger.info(f"  Price range: ฿{stats.get('min', 0):,.0f} - ฿{stats.get('max', 0):,.0f}")
                
                if analysis['volatility']:
                    logger.info(f"  Volatility: {analysis['volatility']['level']} (score: {analysis['volatility']['score']:.2f})")
                
                if analysis['trends']:
                    for trend in analysis['trends']:
                        logger.info(f"  {trend.period} trend: {trend.direction} ({trend.change_percentage:+.1f}%)")


async def main():
    """Run all tests"""
    logger.info("Advanced Price Comparison System Test")
    logger.info("="*60)
    
    # Test matching
    await test_advanced_matching()
    
    # Test price analysis
    await test_price_analysis()
    
    logger.info("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())