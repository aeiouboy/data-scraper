"""
Enhanced Price Comparison Engine with improved Thai-English support
"""
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
import statistics

from src.utils.product_matcher_enhanced import EnhancedProductMatcher, MatchResult
from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class PriceComparison:
    """Enhanced price comparison result"""
    base_product: Dict[str, any]
    matched_products: List[Dict[str, any]]
    match_results: List[MatchResult]
    price_analysis: Dict[str, any]
    savings_opportunities: List[Dict[str, any]]
    confidence_level: str  # 'high', 'medium', 'low'
    warnings: List[str]

@dataclass
class RetailerAnalysis:
    """Retailer competitiveness analysis"""
    retailer_code: str
    retailer_name: str
    avg_price_position: float  # -1 to 1 (-1 = cheapest, 1 = most expensive)
    price_competitiveness_score: float  # 0 to 1
    product_coverage: float  # 0 to 1
    savings_opportunities: int
    total_potential_savings: Decimal

class EnhancedPriceComparisonEngine:
    """Enhanced price comparison engine with Thai-English support"""
    
    def __init__(self):
        self.matcher = EnhancedProductMatcher()
        self.normalizer = EnhancedTextNormalizer()
        
        # Configuration
        self.config = {
            'min_match_confidence': 0.65,
            'high_confidence_threshold': 0.85,
            'price_outlier_threshold': 2.0,  # Standard deviations
            'min_retailers_for_comparison': 2,
            'include_historical_prices': True,
            'historical_days': 30,
        }
    
    async def compare_prices(
        self,
        products: List[Dict[str, any]],
        options: Optional[Dict[str, any]] = None
    ) -> List[PriceComparison]:
        """
        Compare prices across products with enhanced matching
        
        Args:
            products: List of products from different retailers
            options: Optional configuration overrides
            
        Returns:
            List of price comparisons grouped by matched products
        """
        if options:
            self.config.update(options)
        
        # Group products by potential matches
        product_groups = await self._group_similar_products(products)
        
        # Analyze each group
        comparisons = []
        for group in product_groups:
            if len(group['products']) >= self.config['min_retailers_for_comparison']:
                comparison = await self._analyze_product_group(group)
                comparisons.append(comparison)
        
        # Sort by savings potential
        comparisons.sort(
            key=lambda x: x.price_analysis.get('max_savings_amount', 0),
            reverse=True
        )
        
        return comparisons
    
    async def _group_similar_products(
        self,
        products: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Group products that are likely the same across retailers"""
        groups = []
        used_products = set()
        
        # Sort products by confidence in matching (SKU first, then brand+model)
        sorted_products = sorted(
            products,
            key=lambda p: (
                bool(p.get('sku')),
                bool(p.get('brand')),
                len(p.get('name', ''))
            ),
            reverse=True
        )
        
        for i, base_product in enumerate(sorted_products):
            if base_product['id'] in used_products:
                continue
            
            # Find all matches for this product
            group = {
                'base_product': base_product,
                'products': [base_product],
                'match_results': [],
                'avg_confidence': 1.0
            }
            used_products.add(base_product['id'])
            
            # Find matches
            candidates = [p for p in products[i+1:] if p['id'] not in used_products]
            matches = self.matcher.find_best_matches(
                base_product,
                candidates,
                min_confidence=self.config['min_match_confidence']
            )
            
            for matched_product, match_result in matches:
                group['products'].append(matched_product)
                group['match_results'].append(match_result)
                used_products.add(matched_product['id'])
            
            # Calculate average confidence
            if group['match_results']:
                total_confidence = sum(r.confidence for r in group['match_results'])
                group['avg_confidence'] = total_confidence / len(group['match_results'])
            
            groups.append(group)
        
        return groups
    
    async def _analyze_product_group(
        self,
        group: Dict[str, any]
    ) -> PriceComparison:
        """Analyze a group of matched products for price comparison"""
        base_product = group['base_product']
        products = group['products']
        match_results = group['match_results']
        
        # Extract prices with validation
        prices = []
        price_data = []
        for product in products:
            try:
                price = float(product.get('current_price', 0))
                if price > 0:
                    prices.append(price)
                    price_data.append({
                        'product': product,
                        'price': price,
                        'retailer': product.get('retailer_name', product.get('retailer_code', 'Unknown'))
                    })
            except (ValueError, TypeError):
                logger.warning(f"Invalid price for product {product.get('id')}")
        
        # Perform price analysis
        price_analysis = self._analyze_prices(prices, price_data)
        
        # Find savings opportunities
        savings_opportunities = self._find_savings_opportunities(price_data, price_analysis)
        
        # Determine confidence level
        avg_confidence = group.get('avg_confidence', 0)
        if avg_confidence >= self.config['high_confidence_threshold']:
            confidence_level = 'high'
        elif avg_confidence >= self.config['min_match_confidence']:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        # Generate warnings
        warnings = self._generate_warnings(
            products,
            match_results,
            price_analysis
        )
        
        return PriceComparison(
            base_product=base_product,
            matched_products=products[1:],  # Exclude base product
            match_results=match_results,
            price_analysis=price_analysis,
            savings_opportunities=savings_opportunities,
            confidence_level=confidence_level,
            warnings=warnings
        )
    
    def _analyze_prices(
        self,
        prices: List[float],
        price_data: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """Perform statistical analysis on prices"""
        if not prices:
            return {}
        
        analysis = {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': statistics.mean(prices),
            'median_price': statistics.median(prices),
            'price_range': max(prices) - min(prices),
            'price_variance_percent': 0.0,
            'std_dev': 0.0,
            'outliers': [],
            'retailer_prices': {}
        }
        
        # Calculate variance percentage
        if analysis['avg_price'] > 0:
            analysis['price_variance_percent'] = (
                analysis['price_range'] / analysis['avg_price'] * 100
            )
        
        # Calculate standard deviation and find outliers
        if len(prices) > 1:
            analysis['std_dev'] = statistics.stdev(prices)
            
            # Find outliers (prices beyond threshold * std_dev)
            for pd in price_data:
                z_score = abs(pd['price'] - analysis['avg_price']) / analysis['std_dev']
                if z_score > self.config['price_outlier_threshold']:
                    analysis['outliers'].append({
                        'retailer': pd['retailer'],
                        'price': pd['price'],
                        'z_score': z_score,
                        'direction': 'high' if pd['price'] > analysis['avg_price'] else 'low'
                    })
        
        # Group by retailer
        for pd in price_data:
            retailer = pd['retailer']
            analysis['retailer_prices'][retailer] = pd['price']
        
        # Calculate savings
        if len(prices) > 1:
            analysis['max_savings_amount'] = analysis['max_price'] - analysis['min_price']
            analysis['max_savings_percent'] = (
                analysis['max_savings_amount'] / analysis['max_price'] * 100
            )
        else:
            analysis['max_savings_amount'] = 0
            analysis['max_savings_percent'] = 0
        
        return analysis
    
    def _find_savings_opportunities(
        self,
        price_data: List[Dict[str, any]],
        price_analysis: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Find specific savings opportunities"""
        if len(price_data) < 2:
            return []
        
        opportunities = []
        
        # Sort by price
        sorted_data = sorted(price_data, key=lambda x: x['price'])
        cheapest = sorted_data[0]
        
        # Compare each retailer with the cheapest
        for pd in sorted_data[1:]:
            savings_amount = pd['price'] - cheapest['price']
            savings_percent = (savings_amount / pd['price']) * 100
            
            opportunities.append({
                'from_retailer': pd['retailer'],
                'to_retailer': cheapest['retailer'],
                'current_price': pd['price'],
                'better_price': cheapest['price'],
                'savings_amount': savings_amount,
                'savings_percent': savings_percent,
                'product_info': {
                    'name': pd['product'].get('name', ''),
                    'sku': pd['product'].get('sku', ''),
                    'url': pd['product'].get('url', '')
                }
            })
        
        # Sort by savings amount
        opportunities.sort(key=lambda x: x['savings_amount'], reverse=True)
        
        return opportunities
    
    def _generate_warnings(
        self,
        products: List[Dict[str, any]],
        match_results: List[MatchResult],
        price_analysis: Dict[str, any]
    ) -> List[str]:
        """Generate warnings about the comparison"""
        warnings = []
        
        # Check for low confidence matches
        low_confidence = [r for r in match_results if r.confidence < 0.7]
        if low_confidence:
            warnings.append(
                f"{len(low_confidence)} products have low match confidence"
            )
        
        # Check for missing brands
        missing_brands = [p for p in products if not p.get('brand')]
        if missing_brands:
            warnings.append(
                f"{len(missing_brands)} products missing brand information"
            )
        
        # Check for price outliers
        if price_analysis.get('outliers'):
            for outlier in price_analysis['outliers']:
                warnings.append(
                    f"{outlier['retailer']} has {outlier['direction']} "
                    f"price outlier (z-score: {outlier['z_score']:.1f})"
                )
        
        # Check for large price variance
        variance_percent = price_analysis.get('price_variance_percent', 0)
        if variance_percent > 50:
            warnings.append(
                f"Large price variance detected: {variance_percent:.1f}%"
            )
        
        # Check for missing specifications
        products_without_specs = [
            p for p in products
            if not p.get('specifications') and not p.get('specs')
        ]
        if len(products_without_specs) > len(products) / 2:
            warnings.append(
                "Many products missing detailed specifications"
            )
        
        return warnings
    
    async def analyze_retailer_competitiveness(
        self,
        comparisons: List[PriceComparison],
        retailer_info: Dict[str, str]
    ) -> List[RetailerAnalysis]:
        """Analyze retailer competitiveness based on price comparisons"""
        retailer_stats = defaultdict(lambda: {
            'total_products': 0,
            'cheapest_count': 0,
            'most_expensive_count': 0,
            'price_positions': [],  # -1 to 1
            'total_savings_opportunities': 0,
            'total_potential_savings': Decimal('0')
        })
        
        # Analyze each comparison
        for comparison in comparisons:
            price_analysis = comparison.price_analysis
            retailer_prices = price_analysis.get('retailer_prices', {})
            
            if len(retailer_prices) < 2:
                continue
            
            # Sort retailers by price
            sorted_retailers = sorted(
                retailer_prices.items(),
                key=lambda x: x[1]
            )
            
            min_price = sorted_retailers[0][1]
            max_price = sorted_retailers[-1][1]
            price_range = max_price - min_price
            
            # Calculate position for each retailer
            for retailer, price in retailer_prices.items():
                stats = retailer_stats[retailer]
                stats['total_products'] += 1
                
                # Calculate position (-1 = cheapest, 1 = most expensive)
                if price_range > 0:
                    position = (price - min_price) / price_range * 2 - 1
                else:
                    position = 0
                
                stats['price_positions'].append(position)
                
                # Count cheapest/most expensive
                if price == min_price:
                    stats['cheapest_count'] += 1
                elif price == max_price:
                    stats['most_expensive_count'] += 1
            
            # Count savings opportunities
            for opportunity in comparison.savings_opportunities:
                from_retailer = opportunity['from_retailer']
                retailer_stats[from_retailer]['total_savings_opportunities'] += 1
                retailer_stats[from_retailer]['total_potential_savings'] += \
                    Decimal(str(opportunity['savings_amount']))
        
        # Create analysis results
        results = []
        for retailer_code, stats in retailer_stats.items():
            if stats['total_products'] == 0:
                continue
            
            # Calculate average position
            avg_position = statistics.mean(stats['price_positions'])
            
            # Calculate competitiveness score (0 = worst, 1 = best)
            competitiveness = (1 - avg_position) / 2  # Convert from [-1,1] to [0,1]
            
            # Calculate coverage (what percentage of products they have)
            coverage = stats['total_products'] / len(comparisons)
            
            results.append(RetailerAnalysis(
                retailer_code=retailer_code,
                retailer_name=retailer_info.get(retailer_code, retailer_code),
                avg_price_position=avg_position,
                price_competitiveness_score=competitiveness,
                product_coverage=coverage,
                savings_opportunities=stats['total_savings_opportunities'],
                total_potential_savings=stats['total_potential_savings']
            ))
        
        # Sort by competitiveness
        results.sort(key=lambda x: x.price_competitiveness_score, reverse=True)
        
        return results
    
    def generate_comparison_report(
        self,
        comparisons: List[PriceComparison],
        retailer_analysis: List[RetailerAnalysis]
    ) -> Dict[str, any]:
        """Generate a comprehensive comparison report"""
        total_products = len(comparisons)
        high_confidence = len([c for c in comparisons if c.confidence_level == 'high'])
        
        # Calculate totals
        total_savings_opportunities = sum(
            len(c.savings_opportunities) for c in comparisons
        )
        
        max_potential_savings = sum(
            c.price_analysis.get('max_savings_amount', 0)
            for c in comparisons
        )
        
        # Find top savings
        all_opportunities = []
        for comp in comparisons:
            for opp in comp.savings_opportunities:
                opp['product_name'] = comp.base_product.get('name', '')
                all_opportunities.append(opp)
        
        all_opportunities.sort(key=lambda x: x['savings_amount'], reverse=True)
        
        # Generate report
        report = {
            'summary': {
                'total_product_groups': total_products,
                'high_confidence_matches': high_confidence,
                'total_savings_opportunities': total_savings_opportunities,
                'max_potential_savings': max_potential_savings,
                'report_generated': datetime.now().isoformat()
            },
            'retailer_rankings': [
                {
                    'rank': i + 1,
                    'retailer': ra.retailer_name,
                    'competitiveness_score': round(ra.price_competitiveness_score, 3),
                    'avg_price_position': round(ra.avg_price_position, 3),
                    'coverage': f"{ra.product_coverage * 100:.1f}%",
                    'savings_opportunities': ra.savings_opportunities,
                    'potential_customer_savings': float(ra.total_potential_savings)
                }
                for i, ra in enumerate(retailer_analysis)
            ],
            'top_savings_opportunities': all_opportunities[:20],
            'price_variance_analysis': {
                'avg_variance': statistics.mean([
                    c.price_analysis.get('price_variance_percent', 0)
                    for c in comparisons
                    if c.price_analysis.get('price_variance_percent', 0) > 0
                ]) if comparisons else 0,
                'high_variance_products': len([
                    c for c in comparisons
                    if c.price_analysis.get('price_variance_percent', 0) > 30
                ])
            },
            'data_quality': {
                'products_with_sku': len([
                    c for c in comparisons
                    if c.base_product.get('sku')
                ]),
                'products_with_brand': len([
                    c for c in comparisons
                    if c.base_product.get('brand')
                ]),
                'avg_match_confidence': statistics.mean([
                    r.confidence
                    for c in comparisons
                    for r in c.match_results
                ]) if comparisons else 0
            }
        }
        
        return report