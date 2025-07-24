#!/usr/bin/env python3
"""
Final validation of all data quality improvements
"""

import json
import logging
from typing import Dict, Any, List
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_quality_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalQualityValidator:
    """Final validation of data quality improvements"""
    
    def __init__(self):
        self.supabase = SupabaseService()
    
    def get_current_quality_metrics(self) -> Dict[str, Any]:
        """Get current data quality metrics"""
        logger.info("Analyzing current data quality metrics...")
        
        # Get total product count
        total_result = self.supabase.client.table('products').select('id', count='exact').execute()
        total_products = total_result.count
        
        # Missing brands
        missing_brands_result = self.supabase.client.table('products')\
            .select('id', count='exact')\
            .is_('brand', 'null')\
            .execute()
        missing_brands = missing_brands_result.count
        
        # Missing prices
        missing_prices_result = self.supabase.client.table('products')\
            .select('id', count='exact')\
            .is_('current_price', 'null')\
            .execute()
        missing_prices = missing_prices_result.count
        
        # Generic categories
        generic_categories_result = self.supabase.client.table('products')\
            .select('id', count='exact')\
            .in_('category', ['Other', 'General'])\
            .execute()
        generic_categories = generic_categories_result.count
        
        # Missing categories
        missing_categories_result = self.supabase.client.table('products')\
            .select('id', count='exact')\
            .is_('category', 'null')\
            .execute()
        missing_categories = missing_categories_result.count
        
        # Calculate percentages
        brand_completeness = ((total_products - missing_brands) / total_products * 100) if total_products > 0 else 0
        price_completeness = ((total_products - missing_prices) / total_products * 100) if total_products > 0 else 0
        category_specificity = ((total_products - generic_categories - missing_categories) / total_products * 100) if total_products > 0 else 0
        
        # Retailer breakdown
        retailer_stats = {}
        for retailer in ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']:
            retailer_result = self.supabase.client.table('products')\
                .select('id', count='exact')\
                .eq('retailer_code', retailer)\
                .execute()
            retailer_count = retailer_result.count
            
            if retailer_count > 0:
                # Missing brands for this retailer
                retailer_missing_brands = self.supabase.client.table('products')\
                    .select('id', count='exact')\
                    .eq('retailer_code', retailer)\
                    .is_('brand', 'null')\
                    .execute().count
                
                # Missing prices for this retailer
                retailer_missing_prices = self.supabase.client.table('products')\
                    .select('id', count='exact')\
                    .eq('retailer_code', retailer)\
                    .is_('current_price', 'null')\
                    .execute().count
                
                # Generic categories for this retailer
                retailer_generic_categories = self.supabase.client.table('products')\
                    .select('id', count='exact')\
                    .eq('retailer_code', retailer)\
                    .in_('category', ['Other', 'General'])\
                    .execute().count
                
                retailer_stats[retailer] = {
                    'total_products': retailer_count,
                    'missing_brands': retailer_missing_brands,
                    'missing_prices': retailer_missing_prices,
                    'generic_categories': retailer_generic_categories,
                    'brand_completeness': ((retailer_count - retailer_missing_brands) / retailer_count * 100),
                    'price_completeness': ((retailer_count - retailer_missing_prices) / retailer_count * 100),
                    'category_specificity': ((retailer_count - retailer_generic_categories) / retailer_count * 100)
                }
        
        return {
            'timestamp': str(pd.Timestamp.now()) if 'pd' in globals() else 'now',
            'total_products': total_products,
            'missing_brands': missing_brands,
            'missing_prices': missing_prices,
            'generic_categories': generic_categories,
            'missing_categories': missing_categories,
            'quality_metrics': {
                'brand_completeness': round(brand_completeness, 1),
                'price_completeness': round(price_completeness, 1),
                'category_specificity': round(category_specificity, 1)
            },
            'retailer_breakdown': retailer_stats
        }
    
    def get_sample_remaining_issues(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get samples of remaining data quality issues"""
        logger.info("Getting samples of remaining issues...")
        
        samples = {
            'missing_brands': [],
            'missing_prices': [],
            'generic_categories': []
        }
        
        # Sample missing brands
        missing_brands_result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, retailer_code, url')\
            .is_('brand', 'null')\
            .limit(5)\
            .execute()
        samples['missing_brands'] = missing_brands_result.data
        
        # Sample missing prices
        missing_prices_result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
            .is_('current_price', 'null')\
            .limit(5)\
            .execute()
        samples['missing_prices'] = missing_prices_result.data
        
        # Sample generic categories
        generic_categories_result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, retailer_code, url')\
            .in_('category', ['Other', 'General'])\
            .limit(5)\
            .execute()
        samples['generic_categories'] = generic_categories_result.data
        
        return samples
    
    def compare_with_baseline(self, baseline_file: str = 'data_quality_analysis.json') -> Dict[str, Any]:
        """Compare current metrics with baseline"""
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
            
            current = self.get_current_quality_metrics()
            
            comparison = {
                'baseline_total': baseline.get('total_products', 0),
                'current_total': current['total_products'],
                'improvements': {
                    'brands': {
                        'baseline_missing': baseline.get('missing_brand_patterns', {}).get('total_missing', 0),
                        'current_missing': current['missing_brands'],
                        'improvement': baseline.get('missing_brand_patterns', {}).get('total_missing', 0) - current['missing_brands']
                    },
                    'prices': {
                        'baseline_missing': baseline.get('missing_price_patterns', {}).get('total_missing', 0),
                        'current_missing': current['missing_prices'],
                        'improvement': baseline.get('missing_price_patterns', {}).get('total_missing', 0) - current['missing_prices']
                    },
                    'categories': {
                        'baseline_other': baseline.get('category_issues', {}).get('other_category', 0),
                        'current_other': current['generic_categories'],
                        'improvement': baseline.get('category_issues', {}).get('other_category', 0) - current['generic_categories']
                    }
                },
                'quality_progression': {
                    'baseline_brand_completeness': baseline.get('success_metrics', {}).get('brand_completeness', {}).get('current', '0%'),
                    'current_brand_completeness': f"{current['quality_metrics']['brand_completeness']}%",
                    'baseline_price_completeness': baseline.get('success_metrics', {}).get('price_completeness', {}).get('current', '0%'),
                    'current_price_completeness': f"{current['quality_metrics']['price_completeness']}%",
                    'baseline_category_specificity': baseline.get('success_metrics', {}).get('category_specificity', {}).get('current', '0%'),
                    'current_category_specificity': f"{current['quality_metrics']['category_specificity']}%"
                }
            }
            
            return comparison
            
        except FileNotFoundError:
            logger.warning(f"Baseline file {baseline_file} not found")
            return {}

def main():
    """Main function to run final validation"""
    validator = FinalQualityValidator()
    
    print("🔍 FINAL DATA QUALITY VALIDATION")
    print("=" * 50)
    
    # Get current metrics
    current_metrics = validator.get_current_quality_metrics()
    
    # Get remaining issue samples
    remaining_samples = validator.get_sample_remaining_issues()
    
    # Compare with baseline
    comparison = validator.compare_with_baseline()
    
    # Create comprehensive report
    final_report = {
        'validation_timestamp': 'now',
        'current_metrics': current_metrics,
        'remaining_issue_samples': remaining_samples,
        'baseline_comparison': comparison
    }
    
    # Save report
    with open('final_quality_validation_report.json', 'w') as f:
        json.dump(final_report, f, indent=2)
    
    # Display results
    print(f"\n📊 CURRENT DATA QUALITY METRICS:")
    print(f"  Total products: {current_metrics['total_products']:,}")
    print(f"  Missing brands: {current_metrics['missing_brands']} ({current_metrics['quality_metrics']['brand_completeness']}% complete)")
    print(f"  Missing prices: {current_metrics['missing_prices']} ({current_metrics['quality_metrics']['price_completeness']}% complete)")
    print(f"  Generic categories: {current_metrics['generic_categories']} ({current_metrics['quality_metrics']['category_specificity']}% specific)")
    
    if comparison:
        print(f"\n📈 IMPROVEMENTS SINCE BASELINE:")
        print(f"  Brands improved: {comparison['improvements']['brands']['improvement']} products")
        print(f"  Prices improved: {comparison['improvements']['prices']['improvement']} products")
        print(f"  Categories improved: {comparison['improvements']['categories']['improvement']} products")
    
    print(f"\n🏪 RETAILER BREAKDOWN:")
    for retailer, stats in current_metrics['retailer_breakdown'].items():
        if stats['total_products'] > 0:
            print(f"  {retailer}: {stats['total_products']} products")
            print(f"    Brand: {stats['brand_completeness']:.1f}% | Price: {stats['price_completeness']:.1f}% | Category: {stats['category_specificity']:.1f}%")
    
    print(f"\n📋 REMAINING ISSUES SUMMARY:")
    print(f"  Sample missing brands: {len(remaining_samples['missing_brands'])}")
    print(f"  Sample missing prices: {len(remaining_samples['missing_prices'])}")
    print(f"  Sample generic categories: {len(remaining_samples['generic_categories'])}")
    
    print(f"\n📁 Report saved: final_quality_validation_report.json")
    print(f"✅ Final validation completed!")

if __name__ == "__main__":
    main()