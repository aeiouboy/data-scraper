"""
Strategy factory for creating scraping strategies based on configuration
"""
import logging
from typing import Dict, Any, Optional, Union
from enum import Enum

from .strategies.scraping_strategy import ScrapingStrategy
from .strategies.native_strategy import NativeStrategy
from .strategies.firecrawl_strategy import FirecrawlStrategy
from .strategies.hybrid_strategy import HybridStrategy
from ..config.retailers import ScrapingMethod, RetailerConfig
from ..config.retailer_selectors import update_retailer_config_with_selectors

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Available scraping strategy types"""
    NATIVE = "native"
    FIRECRAWL = "firecrawl"
    HYBRID = "hybrid"


class StrategyFactory:
    """Factory for creating scraping strategies"""
    
    @staticmethod
    def create_strategy(
        retailer_config: Union[RetailerConfig, Dict[str, Any]],
        strategy_type: Optional[str] = None
    ) -> ScrapingStrategy:
        """
        Create a scraping strategy based on configuration
        
        Args:
            retailer_config: Retailer configuration object or dictionary
            strategy_type: Override strategy type (optional)
            
        Returns:
            Configured scraping strategy instance
        """
        # Convert RetailerConfig to dict if needed
        if isinstance(retailer_config, RetailerConfig):
            config_dict = StrategyFactory._retailer_config_to_dict(retailer_config)
        else:
            config_dict = retailer_config.copy()
        
        # Add selectors and patterns to config
        config_dict = update_retailer_config_with_selectors(config_dict)
        
        # Determine strategy type
        if strategy_type:
            selected_strategy = strategy_type.lower()
        else:
            scraping_method = config_dict.get('scraping_method', 'hybrid')
            if isinstance(scraping_method, ScrapingMethod):
                selected_strategy = scraping_method.value
            else:
                selected_strategy = str(scraping_method).lower()
        
        # Create strategy instance
        retailer_code = config_dict.get('code', 'unknown')
        
        try:
            if selected_strategy == StrategyType.NATIVE.value:
                strategy = NativeStrategy(config_dict)
                logger.info(f"Created native strategy for {retailer_code}")
                
            elif selected_strategy == StrategyType.FIRECRAWL.value:
                strategy = FirecrawlStrategy(config_dict)
                logger.info(f"Created Firecrawl strategy for {retailer_code}")
                
            elif selected_strategy == StrategyType.HYBRID.value:
                strategy = HybridStrategy(config_dict)
                logger.info(f"Created hybrid strategy for {retailer_code}")
                
            else:
                logger.warning(f"Unknown strategy type '{selected_strategy}' for {retailer_code}, falling back to hybrid")
                strategy = HybridStrategy(config_dict)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to create {selected_strategy} strategy for {retailer_code}: {str(e)}")
            logger.info(f"Falling back to hybrid strategy for {retailer_code}")
            return HybridStrategy(config_dict)
    
    @staticmethod
    def create_native_strategy(retailer_config: Union[RetailerConfig, Dict[str, Any]]) -> NativeStrategy:
        """Create a native scraping strategy"""
        return StrategyFactory.create_strategy(retailer_config, StrategyType.NATIVE.value)
    
    @staticmethod
    def create_firecrawl_strategy(retailer_config: Union[RetailerConfig, Dict[str, Any]]) -> FirecrawlStrategy:
        """Create a Firecrawl scraping strategy"""
        return StrategyFactory.create_strategy(retailer_config, StrategyType.FIRECRAWL.value)
    
    @staticmethod
    def create_hybrid_strategy(retailer_config: Union[RetailerConfig, Dict[str, Any]]) -> HybridStrategy:
        """Create a hybrid scraping strategy"""
        return StrategyFactory.create_strategy(retailer_config, StrategyType.HYBRID.value)
    
    @staticmethod
    def get_available_strategies() -> Dict[str, str]:
        """Get list of available strategies"""
        return {
            StrategyType.NATIVE.value: "Native HTTP scraping with BeautifulSoup",
            StrategyType.FIRECRAWL.value: "Firecrawl API scraping service",
            StrategyType.HYBRID.value: "Intelligent hybrid with fallback"
        }
    
    @staticmethod
    def validate_strategy_type(strategy_type: str) -> bool:
        """Validate if strategy type is supported"""
        return strategy_type.lower() in [s.value for s in StrategyType]
    
    @staticmethod
    def _retailer_config_to_dict(config: RetailerConfig) -> Dict[str, Any]:
        """Convert RetailerConfig to dictionary"""
        return {
            'name': config.name,
            'code': config.code,
            'type': config.type.value if hasattr(config.type, 'value') else str(config.type),
            'base_url': config.base_url,
            'category_urls': config.category_urls,
            'product_url_patterns': config.product_url_patterns,
            'estimated_products': config.estimated_products,
            'rate_limit_delay': config.rate_limit_delay,
            'max_concurrent': config.max_concurrent,
            'retry_attempts': config.retry_attempts,
            'timeout': getattr(config, 'timeout', 30),
            'scraping_method': config.scraping_method.value if hasattr(config.scraping_method, 'value') else str(config.scraping_method),
            'primary_strategy': getattr(config, 'primary_strategy', 'native'),
            'fallback_strategy': getattr(config, 'fallback_strategy', 'firecrawl'),
            'success_rate_threshold': getattr(config, 'success_rate_threshold', 0.8),
            'response_time_threshold': getattr(config, 'response_time_threshold', 10.0),
            'fallback_after_failures': getattr(config, 'fallback_after_failures', 3),
            'min_data_quality_score': getattr(config, 'min_data_quality_score', 0.7),
            'category_mapping': config.category_mapping,
            'url_patterns': config.url_patterns,
            'selectors': config.selectors,
            'search_patterns': getattr(config, 'search_patterns', {}),
            'market_position': config.market_position,
            'focus_categories': config.focus_categories,
            'price_volatility': config.price_volatility
        }


class StrategyManager:
    """Manager for handling multiple scraping strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, ScrapingStrategy] = {}
        self.strategy_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_strategy(self, retailer_code: str, strategy: ScrapingStrategy):
        """Register a strategy for a retailer"""
        self.strategies[retailer_code] = strategy
        logger.info(f"Registered {strategy.strategy_name} strategy for {retailer_code}")
    
    def get_strategy(self, retailer_code: str) -> Optional[ScrapingStrategy]:
        """Get strategy for a retailer"""
        return self.strategies.get(retailer_code)
    
    def create_and_register_strategy(
        self,
        retailer_config: Union[RetailerConfig, Dict[str, Any]],
        strategy_type: Optional[str] = None
    ) -> ScrapingStrategy:
        """Create and register a strategy"""
        strategy = StrategyFactory.create_strategy(retailer_config, strategy_type)
        
        if isinstance(retailer_config, RetailerConfig):
            retailer_code = retailer_config.code
        else:
            retailer_code = retailer_config.get('code', 'unknown')
        
        self.register_strategy(retailer_code, strategy)
        return strategy
    
    def get_all_strategies(self) -> Dict[str, ScrapingStrategy]:
        """Get all registered strategies"""
        return self.strategies.copy()
    
    def get_strategy_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all strategies"""
        stats = {}
        for retailer_code, strategy in self.strategies.items():
            stats[retailer_code] = strategy.get_stats()
        return stats
    
    def close_all_strategies(self):
        """Close all registered strategies"""
        for retailer_code, strategy in self.strategies.items():
            try:
                # Note: This should be called in an async context
                # For now, we'll just log it
                logger.info(f"Closing strategy for {retailer_code}")
            except Exception as e:
                logger.error(f"Error closing strategy for {retailer_code}: {str(e)}")
        
        self.strategies.clear()
    
    def switch_strategy(
        self,
        retailer_code: str,
        new_strategy_type: str,
        retailer_config: Union[RetailerConfig, Dict[str, Any]]
    ) -> bool:
        """Switch strategy for a retailer"""
        try:
            # Close old strategy if exists
            old_strategy = self.strategies.get(retailer_code)
            if old_strategy:
                # Note: This should be called in an async context
                logger.info(f"Switching from {old_strategy.strategy_name} to {new_strategy_type} for {retailer_code}")
            
            # Create new strategy
            new_strategy = StrategyFactory.create_strategy(retailer_config, new_strategy_type)
            self.register_strategy(retailer_code, new_strategy)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch strategy for {retailer_code}: {str(e)}")
            return False
    
    def get_strategy_info(self, retailer_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a strategy"""
        strategy = self.strategies.get(retailer_code)
        if strategy:
            return strategy.get_strategy_info()
        return None
    
    def __len__(self) -> int:
        """Get number of registered strategies"""
        return len(self.strategies)
    
    def __contains__(self, retailer_code: str) -> bool:
        """Check if retailer has a registered strategy"""
        return retailer_code in self.strategies
    
    def __repr__(self) -> str:
        strategy_names = [f"{code}: {strategy.strategy_name}" for code, strategy in self.strategies.items()]
        return f"StrategyManager({', '.join(strategy_names)})"


# Global strategy manager instance
strategy_manager = StrategyManager()