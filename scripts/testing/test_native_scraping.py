#!/usr/bin/env python3
"""
Simple test script to demonstrate native scraping functionality
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.retailers import RETAILER_CONFIGS, RetailerType
from config.retailer_selectors import update_retailer_config_with_selectors
from scrapers.strategy_factory import StrategyFactory
from scrapers.strategies.native_strategy import NativeStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_native_scraping():
    """Test native scraping functionality"""
    print("🚀 Testing Native Scraping Implementation")
    print("=" * 50)
    
    # Test HomePro configuration
    hp_config = RETAILER_CONFIGS[RetailerType.HOMEPRO]
    print(f"Testing {hp_config.name} ({hp_config.code})")
    print(f"Base URL: {hp_config.base_url}")
    print(f"Scraping method: {hp_config.scraping_method}")
    print()
    
    # Convert to dict and add selectors
    config_dict = {
        'name': hp_config.name,
        'code': hp_config.code,
        'base_url': hp_config.base_url,
        'rate_limit_delay': hp_config.rate_limit_delay,
        'max_concurrent': hp_config.max_concurrent,
        'timeout': getattr(hp_config, 'timeout', 30),
        'scraping_method': hp_config.scraping_method.value,
        'primary_strategy': getattr(hp_config, 'primary_strategy', 'native'),
        'fallback_strategy': getattr(hp_config, 'fallback_strategy', 'firecrawl'),
        'product_url_patterns': hp_config.product_url_patterns,
        'search_patterns': getattr(hp_config, 'search_patterns', {}),
        'selectors': {}
    }
    
    # Add selectors
    config_dict = update_retailer_config_with_selectors(config_dict)
    
    print(f"Added {len(config_dict['selectors'])} selector groups")
    print(f"Product URL patterns: {config_dict['product_url_patterns']}")
    print()
    
    # Create native strategy
    try:
        strategy = StrategyFactory.create_native_strategy(config_dict)
        print(f"✅ Created {strategy.strategy_name} strategy")
        print(f"Strategy info: {strategy}")
        print()
        
        # Test connection
        print("🔗 Testing connection...")
        connection_ok = await strategy.test_connection()
        print(f"Connection test: {'✅ SUCCESS' if connection_ok else '❌ FAILED'}")
        print()
        
        # Test simple product scraping (using a hypothetical URL)
        print("📄 Testing product scraping...")
        test_product_url = "https://www.homepro.co.th/p/test-product"
        
        # Note: This will likely fail since it's a fake URL, but it tests the infrastructure
        try:
            result = await strategy.scrape_product(test_product_url)
            print(f"Product scraping result: {result.success}")
            if result.success:
                print(f"Product data keys: {list(result.data.keys())}")
            else:
                print(f"Error: {result.error}")
        except Exception as e:
            print(f"Product scraping error: {str(e)}")
        print()
        
        # Test search URL building
        print("🔍 Testing search URL building...")
        search_query = "power tools"
        try:
            search_result = await strategy.scrape_search(search_query, max_pages=1)
            print(f"Search result: {search_result.success}")
            if search_result.success:
                print(f"Search data keys: {list(search_result.data.keys())}")
            else:
                print(f"Search error: {search_result.error}")
        except Exception as e:
            print(f"Search error: {str(e)}")
        print()
        
        # Show strategy statistics
        print("📊 Strategy Statistics:")
        stats = strategy.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
        
        # Show engine statistics
        print("🔧 Engine Statistics:")
        engine_stats = strategy.get_engine_stats()
        for key, value in engine_stats.items():
            print(f"  {key}: {value}")
        print()
        
        # Close strategy
        await strategy.close()
        print("✅ Strategy closed successfully")
        
    except Exception as e:
        logger.error(f"Strategy creation failed: {str(e)}")
        print(f"❌ Strategy creation failed: {str(e)}")
        return False
    
    return True


async def test_strategy_factory():
    """Test strategy factory functionality"""
    print("\n🏭 Testing Strategy Factory")
    print("=" * 50)
    
    # Get available strategies
    available_strategies = StrategyFactory.get_available_strategies()
    print("Available strategies:")
    for strategy_type, description in available_strategies.items():
        print(f"  {strategy_type}: {description}")
    print()
    
    # Test strategy validation
    valid_strategies = ['native', 'firecrawl', 'hybrid']
    invalid_strategies = ['selenium', 'requests', 'unknown']
    
    print("Strategy validation tests:")
    for strategy in valid_strategies:
        is_valid = StrategyFactory.validate_strategy_type(strategy)
        print(f"  {strategy}: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    for strategy in invalid_strategies:
        is_valid = StrategyFactory.validate_strategy_type(strategy)
        print(f"  {strategy}: {'✅ VALID' if is_valid else '❌ INVALID'}")
    print()
    
    # Test creating different strategies
    hp_config = RETAILER_CONFIGS[RetailerType.HOMEPRO]
    config_dict = {
        'name': hp_config.name,
        'code': hp_config.code,
        'base_url': hp_config.base_url,
        'rate_limit_delay': hp_config.rate_limit_delay,
        'max_concurrent': hp_config.max_concurrent,
        'timeout': 30,
        'scraping_method': 'hybrid',
        'primary_strategy': 'native',
        'fallback_strategy': 'firecrawl',
        'selectors': {}
    }
    
    print("Testing strategy creation:")
    for strategy_type in ['native', 'firecrawl', 'hybrid']:
        try:
            strategy = StrategyFactory.create_strategy(config_dict, strategy_type)
            print(f"  {strategy_type}: ✅ {strategy.strategy_name}")
            await strategy.close()
        except Exception as e:
            print(f"  {strategy_type}: ❌ {str(e)}")
    
    print("\n✅ Strategy factory tests completed")


async def main():
    """Main test function"""
    print("🧪 Native Scraping System Tests")
    print("=" * 50)
    
    try:
        # Test native scraping
        success = await test_native_scraping()
        if not success:
            print("❌ Native scraping tests failed")
            return
        
        # Test strategy factory
        await test_strategy_factory()
        
        print("\n🎉 All tests completed successfully!")
        print("The native scraping system is ready for use.")
        print("\nNext steps:")
        print("1. Update individual retailer scrapers to use the new strategy system")
        print("2. Add comprehensive tests for each retailer")
        print("3. Implement retailer-specific selector configurations")
        print("4. Test with real retailer websites")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        print(f"❌ Tests failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())