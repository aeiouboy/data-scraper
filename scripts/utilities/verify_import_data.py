#!/usr/bin/env python3
"""
Comprehensive data verification after import
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import requests
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.services.supabase_service import SupabaseService

class DataVerifier:
    """Verify imported data integrity and quality"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.api_base = "http://localhost:8001"
    
    async def verify_database_counts(self) -> Dict[str, Any]:
        """Verify database product counts"""
        print("📊 Verifying database counts...")
        
        results = {}
        
        try:
            # Total products
            total_response = await self.supabase.search_products(limit=1)
            results['total_products'] = total_response['total']
            
            # HP products
            hp_response = await self.supabase.search_products(
                filters={'retailer_code': 'HP'}, 
                limit=1
            )
            results['hp_products'] = hp_response['total']
            
            # TWD products
            twd_response = await self.supabase.search_products(
                filters={'retailer_code': 'TWD'}, 
                limit=1
            )
            results['twd_products'] = twd_response['total']
            
            # Products with prices
            products_with_prices = await self.supabase.search_products(
                filters={'min_price': 0.01},
                limit=1
            )
            results['products_with_prices'] = products_with_prices['total']
            
            # Products with brands
            all_brands = await self.supabase.get_all_brands()
            results['unique_brands'] = len(all_brands)
            
            # Products with categories
            all_categories = await self.supabase.get_categories()
            results['unique_categories'] = len(all_categories)
            
            print(f"  ✅ Total products: {results['total_products']:,}")
            print(f"  ✅ HP products: {results['hp_products']:,}")
            print(f"  ✅ TWD products: {results['twd_products']:,}")
            print(f"  ✅ Products with prices: {results['products_with_prices']:,}")
            print(f"  ✅ Unique brands: {results['unique_brands']}")
            print(f"  ✅ Unique categories: {results['unique_categories']}")
            
        except Exception as e:
            print(f"  ❌ Error verifying counts: {e}")
            results['error'] = str(e)
        
        return results
    
    async def verify_data_quality(self) -> Dict[str, Any]:
        """Verify data quality metrics"""
        print("\n🔍 Verifying data quality...")
        
        results = {}
        
        try:
            # Sample products for quality check
            sample_response = await self.supabase.search_products(limit=100)
            sample_products = sample_response['products']
            
            if not sample_products:
                print("  ❌ No products found for quality check")
                return {'error': 'No products found'}
            
            # Check required fields
            missing_sku = sum(1 for p in sample_products if not p.get('sku'))
            missing_name = sum(1 for p in sample_products if not p.get('name'))
            missing_retailer = sum(1 for p in sample_products if not p.get('retailer_code'))
            
            # Check optional but important fields
            has_price = sum(1 for p in sample_products if p.get('current_price'))
            has_brand = sum(1 for p in sample_products if p.get('brand'))
            has_category = sum(1 for p in sample_products if p.get('category'))
            has_url = sum(1 for p in sample_products if p.get('url'))
            
            sample_size = len(sample_products)
            
            results.update({
                'sample_size': sample_size,
                'missing_sku': missing_sku,
                'missing_name': missing_name,
                'missing_retailer': missing_retailer,
                'price_coverage': (has_price / sample_size) * 100,
                'brand_coverage': (has_brand / sample_size) * 100,
                'category_coverage': (has_category / sample_size) * 100,
                'url_coverage': (has_url / sample_size) * 100
            })
            
            print(f"  📊 Sample size: {sample_size}")
            print(f"  ✅ Required fields complete: {sample_size - missing_sku - missing_name - missing_retailer}/{sample_size}")
            print(f"  💰 Price coverage: {results['price_coverage']:.1f}%")
            print(f"  🏷️  Brand coverage: {results['brand_coverage']:.1f}%")
            print(f"  📂 Category coverage: {results['category_coverage']:.1f}%")
            print(f"  🔗 URL coverage: {results['url_coverage']:.1f}%")
            
        except Exception as e:
            print(f"  ❌ Error verifying quality: {e}")
            results['error'] = str(e)
        
        return results
    
    def verify_api_endpoints(self) -> Dict[str, Any]:
        """Verify API endpoints with new data"""
        print("\n🌐 Verifying API endpoints...")
        
        results = {}
        endpoints = [
            '/api/products',
            '/api/retailers/summary',
            '/api/price-comparisons-v2',
            '/api/categories'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if endpoint == '/api/products':
                        total = data.get('total', 0)
                        results[endpoint] = {
                            'status': 'success',
                            'total_products': total,
                            'response_time_ms': response.elapsed.total_seconds() * 1000
                        }
                        print(f"  ✅ {endpoint}: {total:,} products")
                    
                    elif endpoint == '/api/retailers/summary':
                        retailers = data.get('retailers', [])
                        results[endpoint] = {
                            'status': 'success',
                            'retailer_count': len(retailers),
                            'retailers': {r['code']: r['actual_products'] for r in retailers}
                        }
                        print(f"  ✅ {endpoint}: {len(retailers)} retailers")
                        for retailer in retailers:
                            print(f"      {retailer['code']}: {retailer['actual_products']:,} products")
                    
                    elif endpoint == '/api/price-comparisons-v2':
                        total = data.get('total', 0)
                        results[endpoint] = {
                            'status': 'success',
                            'total_comparisons': total
                        }
                        print(f"  ✅ {endpoint}: {total:,} comparisons")
                    
                    elif endpoint == '/api/categories':
                        categories = data.get('categories', [])
                        results[endpoint] = {
                            'status': 'success',
                            'category_count': len(categories)
                        }
                        print(f"  ✅ {endpoint}: {len(categories)} categories")
                
                else:
                    results[endpoint] = {
                        'status': 'error',
                        'status_code': response.status_code,
                        'error': response.text[:200]
                    }
                    print(f"  ❌ {endpoint}: HTTP {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ❌ {endpoint}: {str(e)}")
        
        return results
    
    async def verify_price_comparisons(self) -> Dict[str, Any]:
        """Verify price comparison functionality"""
        print("\n💰 Verifying price comparisons...")
        
        results = {}
        
        try:
            # Get products from both retailers with same category
            hp_products = await self.supabase.search_products(
                filters={'retailer_code': 'HP', 'categories': ['Refrigerator']},
                limit=10
            )
            
            twd_products = await self.supabase.search_products(
                filters={'retailer_code': 'TWD', 'categories': ['Refrigerator']},
                limit=10
            )
            
            results.update({
                'hp_refrigerators': len(hp_products['products']),
                'twd_refrigerators': len(twd_products['products'])
            })
            
            # Check for potential matches (same brand)
            hp_brands = {p.get('brand') for p in hp_products['products'] if p.get('brand')}
            twd_brands = {p.get('brand') for p in twd_products['products'] if p.get('brand')}
            common_brands = hp_brands & twd_brands
            
            results['common_brands_refrigerators'] = len(common_brands)
            
            print(f"  🏪 HP Refrigerators: {results['hp_refrigerators']}")
            print(f"  🏪 TWD Refrigerators: {results['twd_refrigerators']}")
            print(f"  🤝 Common brands: {results['common_brands_refrigerators']}")
            
            if common_brands:
                print(f"  📋 Common brands: {', '.join(list(common_brands)[:5])}")
            
        except Exception as e:
            print(f"  ❌ Error verifying comparisons: {e}")
            results['error'] = str(e)
        
        return results
    
    async def generate_verification_report(self) -> None:
        """Generate comprehensive verification report"""
        
        print("🔍 Agent 1 - Data Verification Report")
        print("=" * 60)
        
        # Run all verifications
        db_results = await self.verify_database_counts()
        quality_results = await self.verify_data_quality()
        api_results = self.verify_api_endpoints()
        comparison_results = await self.verify_price_comparisons()
        
        # Generate summary
        print("\n📋 VERIFICATION SUMMARY")
        print("=" * 60)
        
        # Overall status
        errors = []
        if 'error' in db_results:
            errors.append('Database verification failed')
        if 'error' in quality_results:
            errors.append('Data quality check failed')
        if any(r.get('status') == 'error' for r in api_results.values()):
            errors.append('API endpoint errors')
        if 'error' in comparison_results:
            errors.append('Price comparison verification failed')
        
        if not errors:
            print("✅ OVERALL STATUS: ALL VERIFICATIONS PASSED")
        else:
            print(f"⚠️  OVERALL STATUS: {len(errors)} ISSUES FOUND")
            for error in errors:
                print(f"   • {error}")
        
        # Key metrics
        print(f"\n📊 KEY METRICS:")
        if 'total_products' in db_results:
            print(f"   • Total Products: {db_results['total_products']:,}")
        if 'hp_products' in db_results and 'twd_products' in db_results:
            print(f"   • HP Products: {db_results['hp_products']:,}")
            print(f"   • TWD Products: {db_results['twd_products']:,}")
        
        if 'price_coverage' in quality_results:
            print(f"   • Price Coverage: {quality_results['price_coverage']:.1f}%")
        if 'brand_coverage' in quality_results:
            print(f"   • Brand Coverage: {quality_results['brand_coverage']:.1f}%")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'database': db_results,
            'quality': quality_results,
            'api': api_results,
            'comparisons': comparison_results,
            'summary': {
                'status': 'passed' if not errors else 'issues_found',
                'error_count': len(errors),
                'errors': errors
            }
        }
        
        report_file = project_root / 'data' / 'results' / f'verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        print("\n🤖 Agent 1 verification complete!")

async def main():
    """Run comprehensive data verification"""
    verifier = DataVerifier()
    await verifier.generate_verification_report()

if __name__ == "__main__":
    asyncio.run(main())