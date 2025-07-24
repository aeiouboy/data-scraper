#!/usr/bin/env python3
"""
Investigate data quality issues based on screenshot observations
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_quality_investigation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataQualityInvestigator:
    """Investigate data quality issues in the product database"""
    
    def __init__(self):
        self.supabase = SupabaseService()
    
    async def analyze_specific_issues(self) -> Dict[str, Any]:
        """Analyze specific data quality issues observed in screenshot"""
        logger.info("Starting detailed data quality investigation...")
        
        try:
            # Get all products
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price, availability, scraped_at')\
                .execute()
            
            products = result.data
            
            # Initialize analysis
            analysis = {
                'total_products': len(products),
                'by_retailer': {},
                'missing_brand_patterns': {},
                'missing_price_patterns': {},
                'category_issues': {},
                'specific_problems': [],
                'recommendations': []
            }
            
            # Analyze by retailer
            for retailer_code in ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']:
                retailer_products = [p for p in products if p['retailer_code'] == retailer_code]
                
                analysis['by_retailer'][retailer_code] = {
                    'total_products': len(retailer_products),
                    'missing_brand': len([p for p in retailer_products if not p.get('brand')]),
                    'missing_price': len([p for p in retailer_products if not p.get('current_price')]),
                    'generic_category': len([p for p in retailer_products if p.get('category') == 'Other']),
                    'missing_category': len([p for p in retailer_products if not p.get('category')]),
                    'no_price_info': len([p for p in retailer_products if not p.get('current_price') and not p.get('original_price')])
                }
            
            # Analyze missing brand patterns
            no_brand_products = [p for p in products if not p.get('brand')]
            analysis['missing_brand_patterns'] = {
                'total_missing': len(no_brand_products),
                'by_retailer': {},
                'common_skus': []
            }
            
            for retailer_code in ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']:
                retailer_no_brand = [p for p in no_brand_products if p['retailer_code'] == retailer_code]
                analysis['missing_brand_patterns']['by_retailer'][retailer_code] = {
                    'count': len(retailer_no_brand),
                    'percentage': (len(retailer_no_brand) / len([p for p in products if p['retailer_code'] == retailer_code])) * 100 if len([p for p in products if p['retailer_code'] == retailer_code]) > 0 else 0,
                    'sample_skus': [p['sku'] for p in retailer_no_brand[:5]]
                }
            
            # Analyze missing price patterns
            no_price_products = [p for p in products if not p.get('current_price')]
            analysis['missing_price_patterns'] = {
                'total_missing': len(no_price_products),
                'by_retailer': {},
                'common_categories': {}
            }
            
            for retailer_code in ['HP', 'TWD', 'GH', 'DH', 'BT', 'MH']:
                retailer_no_price = [p for p in no_price_products if p['retailer_code'] == retailer_code]
                analysis['missing_price_patterns']['by_retailer'][retailer_code] = {
                    'count': len(retailer_no_price),
                    'percentage': (len(retailer_no_price) / len([p for p in products if p['retailer_code'] == retailer_code])) * 100 if len([p for p in products if p['retailer_code'] == retailer_code]) > 0 else 0,
                    'sample_skus': [p['sku'] for p in retailer_no_price[:5]]
                }
            
            # Analyze category issues
            analysis['category_issues'] = {
                'other_category': len([p for p in products if p.get('category') == 'Other']),
                'missing_category': len([p for p in products if not p.get('category')]),
                'generic_categories': {}
            }
            
            # Count category distribution
            category_counts = {}
            for product in products:
                category = product.get('category', 'Missing')
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
            
            analysis['category_issues']['distribution'] = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Specific problems from screenshot analysis
            analysis['specific_problems'] = [
                {
                    'issue': 'HP products with "No Brand" showing',
                    'example_sku': 'HP-0C668A8B',
                    'description': 'HomePro products showing "No Brand" instead of actual brand names',
                    'severity': 'high'
                },
                {
                    'issue': 'TWD products with "No Brand" showing',
                    'examples': ['TWD-64B2E7DF', 'TWD-A6F0C911', 'TWD-2DA3B49B', 'TWD-33259A6A'],
                    'description': 'Thai Watsadu products showing "No Brand" despite likely having brand information',
                    'severity': 'high'
                },
                {
                    'issue': 'HP products with "No Price" showing',
                    'example_sku': 'HP-0C668A8B',
                    'description': 'HomePro products showing "No Price" in both original and sale price',
                    'severity': 'medium'
                },
                {
                    'issue': 'Generic "Other" category assignments',
                    'description': 'Many products defaulting to "Other" category instead of specific categories',
                    'severity': 'medium'
                }
            ]
            
            # Generate recommendations
            analysis['recommendations'] = [
                {
                    'priority': 'high',
                    'action': 'Improve brand extraction for HP products',
                    'description': 'Review HomePro scraping strategy to better extract brand information',
                    'estimated_impact': f"Could improve {analysis['by_retailer']['HP']['missing_brand']} HP products"
                },
                {
                    'priority': 'high',
                    'action': 'Improve brand extraction for TWD products',
                    'description': 'Review Thai Watsadu scraping strategy to better extract brand information',
                    'estimated_impact': f"Could improve {analysis['by_retailer']['TWD']['missing_brand']} TWD products"
                },
                {
                    'priority': 'medium',
                    'action': 'Improve price extraction for HP products',
                    'description': 'Review HomePro price extraction logic, especially for products showing "No Price"',
                    'estimated_impact': f"Could improve {analysis['by_retailer']['HP']['missing_price']} HP products"
                },
                {
                    'priority': 'medium',
                    'action': 'Improve category classification',
                    'description': 'Implement better category mapping to reduce "Other" category assignments',
                    'estimated_impact': f"Could improve {analysis['category_issues']['other_category']} products"
                },
                {
                    'priority': 'low',
                    'action': 'Implement data validation pipeline',
                    'description': 'Add validation checks to prevent saving products with missing critical data',
                    'estimated_impact': 'Prevent future data quality issues'
                }
            ]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in data quality investigation: {str(e)}")
            return {'error': str(e)}
    
    async def get_sample_problematic_products(self, limit: int = 20) -> Dict[str, Any]:
        """Get sample products with data quality issues for manual inspection"""
        logger.info(f"Getting sample problematic products (limit: {limit})...")
        
        try:
            samples = {
                'hp_no_brand': [],
                'hp_no_price': [],
                'twd_no_brand': [],
                'twd_no_price': [],
                'other_category': []
            }
            
            # HP products with no brand
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
                .eq('retailer_code', 'HP')\
                .is_('brand', 'null')\
                .limit(limit//4)\
                .execute()
            samples['hp_no_brand'] = result.data
            
            # HP products with no price
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
                .eq('retailer_code', 'HP')\
                .is_('current_price', 'null')\
                .limit(limit//4)\
                .execute()
            samples['hp_no_price'] = result.data
            
            # TWD products with no brand
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
                .eq('retailer_code', 'TWD')\
                .is_('brand', 'null')\
                .limit(limit//4)\
                .execute()
            samples['twd_no_brand'] = result.data
            
            # TWD products with no price
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
                .eq('retailer_code', 'TWD')\
                .is_('current_price', 'null')\
                .limit(limit//4)\
                .execute()
            samples['twd_no_price'] = result.data
            
            # Products with "Other" category
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, retailer_code, url, current_price, original_price')\
                .eq('category', 'Other')\
                .limit(limit//4)\
                .execute()
            samples['other_category'] = result.data
            
            return samples
            
        except Exception as e:
            logger.error(f"Error getting sample products: {str(e)}")
            return {'error': str(e)}
    
    async def create_improvement_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive improvement plan based on analysis"""
        logger.info("Creating comprehensive improvement plan...")
        
        plan = {
            'priority_phases': {
                'phase_1_critical': {
                    'title': 'Critical Data Quality Issues',
                    'timeline': '1-2 weeks',
                    'tasks': [
                        {
                            'task': 'Fix HP brand extraction',
                            'description': 'Improve HomePro scraper to better extract brand information',
                            'estimated_impact': f"{analysis['by_retailer']['HP']['missing_brand']} products",
                            'technical_approach': 'Review HTML parsing logic for brand selectors'
                        },
                        {
                            'task': 'Fix TWD brand extraction',
                            'description': 'Improve Thai Watsadu scraper to better extract brand information',
                            'estimated_impact': f"{analysis['by_retailer']['TWD']['missing_brand']} products",
                            'technical_approach': 'Review Firecrawl extraction and add brand-specific selectors'
                        },
                        {
                            'task': 'Implement data validation',
                            'description': 'Add validation to prevent saving products with missing critical data',
                            'estimated_impact': 'Prevent future data quality issues',
                            'technical_approach': 'Add validation checks in upsert_product method'
                        }
                    ]
                },
                'phase_2_important': {
                    'title': 'Price and Category Improvements',
                    'timeline': '2-3 weeks',
                    'tasks': [
                        {
                            'task': 'Fix HP price extraction',
                            'description': 'Improve HomePro price extraction for products showing "No Price"',
                            'estimated_impact': f"{analysis['by_retailer']['HP']['missing_price']} products",
                            'technical_approach': 'Review price selector logic and add fallback methods'
                        },
                        {
                            'task': 'Improve category classification',
                            'description': 'Reduce "Other" category assignments with better mapping',
                            'estimated_impact': f"{analysis['category_issues']['other_category']} products",
                            'technical_approach': 'Implement category inference from product names/descriptions'
                        },
                        {
                            'task': 'Fix TWD price extraction',
                            'description': 'Improve Thai Watsadu price extraction',
                            'estimated_impact': f"{analysis['by_retailer']['TWD']['missing_price']} products",
                            'technical_approach': 'Review price parsing and add multiple selector fallbacks'
                        }
                    ]
                },
                'phase_3_optimization': {
                    'title': 'Quality Assurance and Monitoring',
                    'timeline': '1-2 weeks',
                    'tasks': [
                        {
                            'task': 'Implement monitoring dashboard',
                            'description': 'Create real-time data quality monitoring',
                            'estimated_impact': 'Continuous quality assurance',
                            'technical_approach': 'Build dashboard showing data completeness metrics'
                        },
                        {
                            'task': 'Automated quality checks',
                            'description': 'Implement automated data quality validation',
                            'estimated_impact': 'Prevent regression',
                            'technical_approach': 'Add scheduled jobs to check data quality'
                        },
                        {
                            'task': 'Historical data cleanup',
                            'description': 'Clean up existing products with missing data',
                            'estimated_impact': 'Improve all historical data',
                            'technical_approach': 'Batch rescraping with improved scrapers'
                        }
                    ]
                }
            },
            'success_metrics': {
                'brand_completeness': {
                    'current': f"{((analysis['total_products'] - analysis['missing_brand_patterns']['total_missing']) / analysis['total_products']) * 100:.1f}%",
                    'target': '95%'
                },
                'price_completeness': {
                    'current': f"{((analysis['total_products'] - analysis['missing_price_patterns']['total_missing']) / analysis['total_products']) * 100:.1f}%",
                    'target': '90%'
                },
                'category_specificity': {
                    'current': f"{((analysis['total_products'] - analysis['category_issues']['other_category']) / analysis['total_products']) * 100:.1f}%",
                    'target': '85%'
                }
            },
            'estimated_timeline': '4-7 weeks total',
            'resources_needed': [
                'Senior developer for scraper improvements',
                'QA engineer for validation testing',
                'Data analyst for monitoring setup'
            ]
        }
        
        return plan

async def main():
    """Main function to run the investigation"""
    investigator = DataQualityInvestigator()
    
    print("🔍 DATA QUALITY INVESTIGATION")
    print("=" * 50)
    
    # Run detailed analysis
    print("\n📊 Running detailed analysis...")
    analysis = await investigator.analyze_specific_issues()
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return
    
    # Save analysis
    with open('data_quality_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Get sample problematic products
    print("\n🔍 Getting sample problematic products...")
    samples = await investigator.get_sample_problematic_products()
    
    # Save samples
    with open('problematic_products_samples.json', 'w') as f:
        json.dump(samples, f, indent=2)
    
    # Create improvement plan
    print("\n📋 Creating improvement plan...")
    plan = await investigator.create_improvement_plan(analysis)
    
    # Save plan
    with open('data_quality_improvement_plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    # Display summary
    print(f"\n📈 DATA QUALITY SUMMARY")
    print(f"Total products analyzed: {analysis['total_products']}")
    print(f"Missing brand data: {analysis['missing_brand_patterns']['total_missing']} ({(analysis['missing_brand_patterns']['total_missing']/analysis['total_products'])*100:.1f}%)")
    print(f"Missing price data: {analysis['missing_price_patterns']['total_missing']} ({(analysis['missing_price_patterns']['total_missing']/analysis['total_products'])*100:.1f}%)")
    print(f"Generic 'Other' category: {analysis['category_issues']['other_category']} ({(analysis['category_issues']['other_category']/analysis['total_products'])*100:.1f}%)")
    
    print(f"\n🎯 BY RETAILER BREAKDOWN:")
    for retailer, data in analysis['by_retailer'].items():
        if data['total_products'] > 0:
            print(f"{retailer}: {data['total_products']} products")
            print(f"  - Missing brand: {data['missing_brand']} ({(data['missing_brand']/data['total_products'])*100:.1f}%)")
            print(f"  - Missing price: {data['missing_price']} ({(data['missing_price']/data['total_products'])*100:.1f}%)")
            print(f"  - Generic category: {data['generic_category']} ({(data['generic_category']/data['total_products'])*100:.1f}%)")
    
    print(f"\n🚀 RECOMMENDED ACTIONS:")
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        print(f"{i}. [{rec['priority'].upper()}] {rec['action']}")
        print(f"   → {rec['description']}")
        print(f"   → Impact: {rec['estimated_impact']}")
    
    print(f"\n📁 Files created:")
    print(f"  - data_quality_analysis.json")
    print(f"  - problematic_products_samples.json")
    print(f"  - data_quality_improvement_plan.json")

if __name__ == "__main__":
    asyncio.run(main())