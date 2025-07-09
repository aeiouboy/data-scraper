"""
Price analysis engine with volatility detection, trend analysis, and forecasting
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.models.matching_models import (
    PricePoint,
    PriceTrend,
    PriceAnomaly,
    PriceVolatilityLevel,
    PriceAnalysis,
    SavingsOpportunity
)
from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class PriceAnalysisEngine:
    """Advanced price analysis with statistical methods"""
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        
    async def analyze_price_history(
        self, 
        product_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Comprehensive price analysis for a product"""
        try:
            # Get price history
            history = await self._get_price_history(product_id, days)
            
            if not history:
                return self._empty_analysis()
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(history)
            # Handle both column names for compatibility
            if 'recorded_at' in df.columns:
                df['timestamp'] = pd.to_datetime(df['recorded_at'])
            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df.set_index('timestamp', inplace=True)
            
            # Basic statistics
            current_price = df['price'].iloc[-1]
            price_stats = {
                'current': current_price,
                'mean': df['price'].mean(),
                'median': df['price'].median(),
                'std': df['price'].std(),
                'min': df['price'].min(),
                'max': df['price'].max(),
                'range': df['price'].max() - df['price'].min()
            }
            
            # Volatility analysis
            volatility = self._calculate_volatility(df['price'])
            
            # Trend analysis
            trends = self._analyze_trends(df)
            
            # Anomaly detection
            anomalies = self._detect_anomalies(df)
            
            # Seasonality detection
            seasonality = self._detect_seasonality(df) if len(df) > 14 else None
            
            # Price forecast
            forecast = self._forecast_prices(df) if len(df) > 7 else None
            
            return {
                'statistics': price_stats,
                'volatility': volatility,
                'trends': trends,
                'anomalies': anomalies,
                'seasonality': seasonality,
                'forecast': forecast
            }
            
        except Exception as e:
            logger.error(f"Error analyzing price history: {str(e)}")
            return self._empty_analysis()
    
    async def analyze_match_group_prices(
        self,
        match_group_id: str
    ) -> PriceAnalysis:
        """Analyze prices across all products in a match group"""
        try:
            # Get all products in the group
            mapping_result = self.supabase.client.table('product_match_mapping')\
                .select('product_id, retailer_code')\
                .eq('match_group_id', match_group_id)\
                .execute()
            
            if not mapping_result.data:
                return self._empty_price_analysis()
            
            # Get current prices for all products
            product_ids = [m['product_id'] for m in mapping_result.data]
            products_result = self.supabase.client.table('products')\
                .select('id, retailer_code, current_price, name')\
                .in_('id', product_ids)\
                .execute()
            
            if not products_result.data:
                return self._empty_price_analysis()
            
            # Analyze prices
            prices = [
                (p['retailer_code'], p['current_price']) 
                for p in products_result.data 
                if p['current_price'] and p['current_price'] > 0
            ]
            
            if not prices:
                return self._empty_price_analysis()
            
            # Find best price
            best_retailer, best_price = min(prices, key=lambda x: x[1])
            worst_retailer, worst_price = max(prices, key=lambda x: x[1])
            
            # Calculate volatility
            price_values = [p[1] for p in prices]
            volatility_score = np.std(price_values) / np.mean(price_values) if len(price_values) > 1 else 0
            volatility_level = self._classify_volatility(volatility_score)
            
            # Create savings opportunity
            savings_opportunity = None
            if worst_price > best_price:
                savings_opportunity = SavingsOpportunity(
                    amount=worst_price - best_price,
                    percentage=((worst_price - best_price) / worst_price) * 100,
                    best_retailer=best_retailer,
                    compared_to_retailers=[r for r, _ in prices if r != best_retailer],
                    confidence=0.95
                )
            
            # Get historical trends
            trends = await self._get_price_trends_for_group(match_group_id)
            
            return PriceAnalysis(
                current_best_price=best_price,
                current_best_retailer=best_retailer,
                savings_opportunity=savings_opportunity,
                volatility=volatility_level,
                volatility_score=volatility_score,
                price_trends=trends,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing match group prices: {str(e)}")
            return self._empty_price_analysis()
    
    async def analyze_market_volatility(
        self,
        category: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze price volatility across the market"""
        try:
            # Get products with price history
            query = self.supabase.client.table('products')\
                .select('id, category, brand, retailer_code')
            
            if category:
                query = query.eq('category', category)
            
            products_result = query.limit(1000).execute()
            
            if not products_result.data:
                return {'error': 'No products found'}
            
            # Analyze volatility by category and retailer
            volatility_by_category = {}
            volatility_by_retailer = {}
            volatility_by_brand = {}
            
            for product in products_result.data:
                # Get price history
                history = await self._get_price_history(product['id'], days)
                
                if len(history) < 3:
                    continue
                
                # Calculate volatility
                prices = [h['price'] for h in history]
                volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
                
                # Aggregate by category
                cat = product['category'] or 'Unknown'
                if cat not in volatility_by_category:
                    volatility_by_category[cat] = []
                volatility_by_category[cat].append(volatility)
                
                # Aggregate by retailer
                retailer = product['retailer_code']
                if retailer not in volatility_by_retailer:
                    volatility_by_retailer[retailer] = []
                volatility_by_retailer[retailer].append(volatility)
                
                # Aggregate by brand
                brand = product['brand'] or 'Unknown'
                if brand not in volatility_by_brand:
                    volatility_by_brand[brand] = []
                volatility_by_brand[brand].append(volatility)
            
            # Calculate averages
            result = {
                'by_category': {
                    cat: {
                        'avg_volatility': np.mean(vols),
                        'std_volatility': np.std(vols),
                        'product_count': len(vols),
                        'volatility_level': self._classify_volatility(np.mean(vols))
                    }
                    for cat, vols in volatility_by_category.items()
                },
                'by_retailer': {
                    retailer: {
                        'avg_volatility': np.mean(vols),
                        'std_volatility': np.std(vols),
                        'product_count': len(vols),
                        'volatility_level': self._classify_volatility(np.mean(vols))
                    }
                    for retailer, vols in volatility_by_retailer.items()
                },
                'by_brand': {
                    brand: {
                        'avg_volatility': np.mean(vols),
                        'product_count': len(vols),
                        'volatility_level': self._classify_volatility(np.mean(vols))
                    }
                    for brand, vols in volatility_by_brand.items()
                    if len(vols) >= 3  # Only include brands with enough data
                },
                'market_summary': {
                    'total_products_analyzed': len(products_result.data),
                    'avg_market_volatility': np.mean([v for vols in volatility_by_category.values() for v in vols]),
                    'most_volatile_category': max(
                        volatility_by_category.items(),
                        key=lambda x: np.mean(x[1])
                    )[0] if volatility_by_category else None,
                    'most_stable_category': min(
                        volatility_by_category.items(),
                        key=lambda x: np.mean(x[1])
                    )[0] if volatility_by_category else None
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market volatility: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_volatility(self, prices: pd.Series) -> Dict[str, Any]:
        """Calculate various volatility metrics"""
        # Basic volatility (coefficient of variation)
        cv = prices.std() / prices.mean() if prices.mean() > 0 else 0
        
        # Daily returns volatility
        returns = prices.pct_change().dropna()
        returns_volatility = returns.std() if len(returns) > 0 else 0
        
        # Price range volatility
        price_range = prices.max() - prices.min()
        range_volatility = price_range / prices.mean() if prices.mean() > 0 else 0
        
        # Classify volatility level
        volatility_level = self._classify_volatility(cv)
        
        return {
            'coefficient_of_variation': cv,
            'returns_volatility': returns_volatility,
            'range_volatility': range_volatility,
            'level': volatility_level,
            'score': cv  # 0-1 score
        }
    
    def _analyze_trends(self, df: pd.DataFrame) -> List[PriceTrend]:
        """Analyze price trends over different periods"""
        trends = []
        
        # Define periods
        periods = [
            ('daily', 1),
            ('weekly', 7),
            ('monthly', 30)
        ]
        
        for period_name, days in periods:
            if len(df) < days:
                continue
            
            # Get data for period
            period_data = df.tail(days)
            
            # Calculate trend
            x = np.arange(len(period_data))
            y = period_data['price'].values
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Determine direction
            if abs(slope) < 0.01:
                direction = 'stable'
            elif slope > 0:
                direction = 'up'
            else:
                direction = 'down'
            
            # Calculate change percentage
            start_price = period_data['price'].iloc[0]
            end_price = period_data['price'].iloc[-1]
            change_pct = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
            
            # Calculate volatility for period
            period_volatility = period_data['price'].std() / period_data['price'].mean()
            
            trends.append(PriceTrend(
                period=period_name,
                direction=direction,
                change_percentage=change_pct,
                average_price=period_data['price'].mean(),
                min_price=period_data['price'].min(),
                max_price=period_data['price'].max(),
                volatility_score=period_volatility
            ))
        
        return trends
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[PriceAnomaly]:
        """Detect price anomalies using statistical methods"""
        anomalies = []
        
        # Z-score method
        prices = df['price']
        z_scores = np.abs(stats.zscore(prices))
        threshold = 2.5  # Anomaly if z-score > 2.5
        
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        for idx in anomaly_indices:
            if idx == 0:
                continue
            
            timestamp = df.index[idx]
            actual_price = prices.iloc[idx]
            
            # Calculate expected range (mean ± 2*std)
            recent_prices = prices.iloc[max(0, idx-7):idx]  # Last 7 prices
            mean_price = recent_prices.mean()
            std_price = recent_prices.std()
            expected_range = (
                mean_price - 2 * std_price,
                mean_price + 2 * std_price
            )
            
            # Determine anomaly type
            prev_price = prices.iloc[idx-1]
            price_change = actual_price - prev_price
            change_pct = abs(price_change / prev_price * 100)
            
            if change_pct > 20:
                anomaly_type = 'spike' if price_change > 0 else 'drop'
                severity = 'high'
            elif change_pct > 10:
                anomaly_type = 'spike' if price_change > 0 else 'drop'
                severity = 'medium'
            else:
                # Check for gradual changes
                if idx >= 3:
                    recent_trend = prices.iloc[idx-3:idx+1].pct_change().mean()
                    if recent_trend > 0.05:
                        anomaly_type = 'gradual_increase'
                    else:
                        anomaly_type = 'gradual_decrease'
                    severity = 'low'
                else:
                    continue
            
            anomalies.append(PriceAnomaly(
                timestamp=timestamp,
                anomaly_type=anomaly_type,
                severity=severity,
                actual_price=actual_price,
                expected_range=expected_range,
                confidence=min(z_scores[idx] / 4, 1.0)  # Normalize to 0-1
            ))
        
        return anomalies
    
    def _detect_seasonality(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect seasonal patterns in prices"""
        try:
            if len(df) < 14:  # Need at least 2 weeks of data
                return None
            
            # Resample to daily frequency
            daily_prices = df['price'].resample('D').mean().interpolate()
            
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(
                daily_prices,
                model='additive',
                period=7  # Weekly seasonality
            )
            
            # Calculate seasonality strength
            seasonal_strength = np.std(decomposition.seasonal) / np.std(daily_prices)
            
            # Determine if significant seasonality exists
            has_seasonality = seasonal_strength > 0.1
            
            if has_seasonality:
                # Find high and low seasons
                seasonal_component = decomposition.seasonal
                threshold = np.percentile(seasonal_component, 75)
                
                high_days = []
                low_days = []
                
                for i, value in enumerate(seasonal_component):
                    day_of_week = i % 7
                    if value > threshold:
                        high_days.append(day_of_week)
                    elif value < -threshold:
                        low_days.append(day_of_week)
                
                return {
                    'has_seasonality': True,
                    'seasonality_strength': seasonal_strength,
                    'pattern': 'weekly',
                    'high_price_days': list(set(high_days)),
                    'low_price_days': list(set(low_days)),
                    'amplitude': float(np.max(seasonal_component) - np.min(seasonal_component))
                }
            
            return {
                'has_seasonality': False,
                'seasonality_strength': seasonal_strength
            }
            
        except Exception as e:
            logger.error(f"Error detecting seasonality: {str(e)}")
            return None
    
    def _forecast_prices(self, df: pd.DataFrame, days_ahead: int = 7) -> Optional[Dict[str, Any]]:
        """Forecast future prices using Holt-Winters method"""
        try:
            if len(df) < 7:
                return None
            
            # Prepare data
            prices = df['price'].resample('D').mean().interpolate()
            
            # Fit Holt-Winters model
            model = ExponentialSmoothing(
                prices,
                seasonal_periods=7,
                trend='add',
                seasonal='add' if len(prices) > 14 else None
            )
            
            fitted_model = model.fit()
            
            # Generate forecast
            forecast = fitted_model.forecast(days_ahead)
            
            # Calculate confidence intervals
            residuals = prices - fitted_model.fittedvalues
            residual_std = np.std(residuals)
            
            # Simple confidence intervals (±2 std)
            lower_bound = forecast - 2 * residual_std
            upper_bound = forecast + 2 * residual_std
            
            return {
                'forecast_values': forecast.tolist(),
                'lower_bound': lower_bound.tolist(),
                'upper_bound': upper_bound.tolist(),
                'forecast_dates': [
                    (datetime.now() + timedelta(days=i)).isoformat()
                    for i in range(1, days_ahead + 1)
                ],
                'confidence_level': 0.95,
                'method': 'holt_winters'
            }
            
        except Exception as e:
            logger.error(f"Error forecasting prices: {str(e)}")
            return None
    
    def _classify_volatility(self, volatility_score: float) -> PriceVolatilityLevel:
        """Classify volatility level based on score"""
        if volatility_score < 0.05:
            return PriceVolatilityLevel.STABLE
        elif volatility_score < 0.1:
            return PriceVolatilityLevel.LOW
        elif volatility_score < 0.2:
            return PriceVolatilityLevel.MODERATE
        elif volatility_score < 0.4:
            return PriceVolatilityLevel.HIGH
        else:
            return PriceVolatilityLevel.EXTREME
    
    async def _get_price_history(self, product_id: str, days: int) -> List[Dict[str, Any]]:
        """Get price history for a product"""
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.supabase.client.table('price_history')\
                .select('price, recorded_at, discount_percentage')\
                .eq('product_id', product_id)\
                .gte('recorded_at', since_date)\
                .order('recorded_at')\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting price history: {str(e)}")
            return []
    
    async def _get_price_trends_for_group(self, match_group_id: str) -> List[PriceTrend]:
        """Get aggregated price trends for a match group"""
        # This would aggregate trends across all products in the group
        # For now, return empty list
        return []
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'statistics': {},
            'volatility': {'level': PriceVolatilityLevel.STABLE, 'score': 0},
            'trends': [],
            'anomalies': [],
            'seasonality': None,
            'forecast': None
        }
    
    def _empty_price_analysis(self) -> PriceAnalysis:
        """Return empty price analysis"""
        return PriceAnalysis(
            current_best_price=0,
            current_best_retailer="Unknown",
            volatility=PriceVolatilityLevel.STABLE,
            volatility_score=0,
            last_updated=datetime.now()
        )