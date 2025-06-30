#!/usr/bin/env python3
"""
Data quality checker for scraped HomePro products
"""
import asyncio
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.services.supabase_service import SupabaseService

class QualityChecker:
    """Check data quality of scraped products"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        
    async def check_all_quality(self) -> Dict[str, Any]:
        """Run comprehensive quality checks"""
        print("🔍 Running data quality checks...")
        
        # Get all products
        products_data = await self.supabase.search_products(limit=10000)
        products = products_data.get('products', [])
        
        if not products:
            return {"error": "No products found in database"}
        
        print(f"📊 Analyzing {len(products):,} products...")
        
        quality_report = {
            "total_products": len(products),
            "completeness": self._check_completeness(products),
            "duplicates": self._check_duplicates(products),
            "data_consistency": self._check_consistency(products),
            "pricing": self._check_pricing(products),
            "brands": self._analyze_brands(products),
            "categories": self._analyze_categories(products),
            "recommendations": []
        }
        
        # Generate recommendations
        quality_report["recommendations"] = self._generate_recommendations(quality_report)
        
        return quality_report
    
    def _check_completeness(self, products: List[Dict]) -> Dict[str, Any]:
        """Check data completeness"""
        total = len(products)
        
        fields_to_check = [
            'name', 'sku', 'brand', 'category', 'current_price',
            'description', 'url', 'availability'
        ]
        
        completeness = {}
        
        for field in fields_to_check:
            complete_count = sum(1 for p in products if p.get(field) not in [None, '', 0])
            completeness[field] = {
                "complete_count": complete_count,
                "completion_rate": (complete_count / total * 100) if total > 0 else 0,
                "missing_count": total - complete_count
            }
        
        # Overall completeness score
        avg_completion = sum(data["completion_rate"] for data in completeness.values()) / len(completeness)
        
        return {
            "overall_score": round(avg_completion, 1),
            "field_details": completeness,
            "critical_missing": {
                field: data for field, data in completeness.items() 
                if data["completion_rate"] < 90 and field in ['name', 'sku', 'current_price']
            }
        }
    
    def _check_duplicates(self, products: List[Dict]) -> Dict[str, Any]:
        """Check for duplicate products"""
        # Check SKU duplicates
        skus = [p.get('sku') for p in products if p.get('sku')]
        sku_counts = Counter(skus)
        sku_duplicates = {sku: count for sku, count in sku_counts.items() if count > 1}
        
        # Check name duplicates (similar names)
        names = [p.get('name', '').strip().lower() for p in products if p.get('name')]
        name_counts = Counter(names)
        name_duplicates = {name: count for name, count in name_counts.items() if count > 1}
        
        # Check URL duplicates
        urls = [p.get('url') for p in products if p.get('url')]
        url_counts = Counter(urls)
        url_duplicates = {url: count for url, count in url_counts.items() if count > 1}
        
        return {
            "sku_duplicates": {
                "count": len(sku_duplicates),
                "examples": dict(list(sku_duplicates.items())[:5])
            },
            "name_duplicates": {
                "count": len(name_duplicates),
                "examples": dict(list(name_duplicates.items())[:5])
            },
            "url_duplicates": {
                "count": len(url_duplicates),
                "examples": dict(list(url_duplicates.items())[:5])
            },
            "duplicate_rate": round((len(sku_duplicates) + len(name_duplicates) + len(url_duplicates)) / len(products) * 100, 2)
        }
    
    def _check_consistency(self, products: List[Dict]) -> Dict[str, Any]:
        """Check data consistency"""
        issues = []
        
        # Check price consistency
        price_issues = 0
        for product in products:
            current_price = product.get('current_price')
            original_price = product.get('original_price')
            discount_pct = product.get('discount_percentage')
            
            if current_price and original_price:
                if current_price > original_price:
                    price_issues += 1
                elif discount_pct:
                    expected_discount = ((original_price - current_price) / original_price) * 100
                    if abs(expected_discount - discount_pct) > 1:  # Allow 1% tolerance
                        price_issues += 1
        
        # Check SKU format consistency
        skus = [p.get('sku') for p in products if p.get('sku')]
        sku_patterns = {}
        for sku in skus:
            if sku.isdigit():
                pattern = "numeric"
            elif '-' in sku:
                pattern = "alphanumeric-dash"
            elif any(c.isalpha() for c in sku) and any(c.isdigit() for c in sku):
                pattern = "alphanumeric"
            else:
                pattern = "other"
            sku_patterns[pattern] = sku_patterns.get(pattern, 0) + 1
        
        return {
            "price_inconsistencies": {
                "count": price_issues,
                "rate": round(price_issues / len(products) * 100, 2)
            },
            "sku_patterns": sku_patterns,
            "consistency_score": round(100 - (price_issues / len(products) * 100), 1)
        }
    
    def _check_pricing(self, products: List[Dict]) -> Dict[str, Any]:
        """Analyze pricing data"""
        prices = [p.get('current_price') for p in products if p.get('current_price')]
        
        if not prices:
            return {"error": "No pricing data found"}
        
        prices = [float(p) for p in prices]
        
        # Price statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        # Price ranges
        ranges = {
            "0-500": sum(1 for p in prices if 0 <= p <= 500),
            "501-1000": sum(1 for p in prices if 501 <= p <= 1000),
            "1001-2000": sum(1 for p in prices if 1001 <= p <= 2000),
            "2001-5000": sum(1 for p in prices if 2001 <= p <= 5000),
            "5000+": sum(1 for p in prices if p > 5000)
        }
        
        # Discount analysis
        discounted_products = [p for p in products if p.get('discount_percentage', 0) > 0]
        avg_discount = sum(p.get('discount_percentage', 0) for p in discounted_products) / len(discounted_products) if discounted_products else 0
        
        return {
            "statistics": {
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "avg_price": round(avg_price, 2),
                "total_products_with_price": len(prices)
            },
            "price_ranges": ranges,
            "discounts": {
                "products_on_sale": len(discounted_products),
                "sale_rate": round(len(discounted_products) / len(products) * 100, 1),
                "avg_discount_percentage": round(avg_discount, 1)
            }
        }
    
    def _analyze_brands(self, products: List[Dict]) -> Dict[str, Any]:
        """Analyze brand distribution"""
        brands = [p.get('brand', '').strip() for p in products if p.get('brand')]
        brand_counts = Counter(brands)
        
        # Filter out empty/unknown brands
        brand_counts = {k: v for k, v in brand_counts.items() if k and k.lower() not in ['unknown', 'n/a', '']}
        
        total_branded = sum(brand_counts.values())
        top_brands = dict(brand_counts.most_common(10))
        
        return {
            "total_brands": len(brand_counts),
            "total_branded_products": total_branded,
            "brand_coverage": round(total_branded / len(products) * 100, 1),
            "top_brands": top_brands,
            "brand_diversity": len(brand_counts)
        }
    
    def _analyze_categories(self, products: List[Dict]) -> Dict[str, Any]:
        """Analyze category distribution"""
        categories = [p.get('category', '').strip() for p in products if p.get('category')]
        category_counts = Counter(categories)
        
        # Filter out empty categories
        category_counts = {k: v for k, v in category_counts.items() if k}
        
        total_categorized = sum(category_counts.values())
        top_categories = dict(category_counts.most_common(10))
        
        return {
            "total_categories": len(category_counts),
            "total_categorized_products": total_categorized,
            "category_coverage": round(total_categorized / len(products) * 100, 1),
            "top_categories": top_categories
        }
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Completeness recommendations
        completeness = quality_report.get('completeness', {})
        if completeness.get('overall_score', 0) < 80:
            recommendations.append("🔧 Improve data completeness - overall score is below 80%")
        
        critical_missing = completeness.get('critical_missing', {})
        for field in critical_missing:
            recommendations.append(f"⚠️  Critical field '{field}' has low completion rate")
        
        # Duplicate recommendations
        duplicates = quality_report.get('duplicates', {})
        if duplicates.get('duplicate_rate', 0) > 5:
            recommendations.append("🔍 Review and remove duplicate products")
        
        # Pricing recommendations
        pricing = quality_report.get('pricing', {})
        consistency = quality_report.get('data_consistency', {})
        if consistency.get('price_inconsistencies', {}).get('rate', 0) > 5:
            recommendations.append("💰 Fix price inconsistencies (current > original price)")
        
        # Brand recommendations
        brands = quality_report.get('brands', {})
        if brands.get('brand_coverage', 0) < 70:
            recommendations.append("🏷️  Improve brand extraction - many products missing brand info")
        
        # Category recommendations
        categories = quality_report.get('categories', {})
        if categories.get('category_coverage', 0) < 60:
            recommendations.append("📂 Improve category classification for products")
        
        if not recommendations:
            recommendations.append("✅ Data quality looks good! No major issues found.")
        
        return recommendations
    
    def print_quality_report(self, report: Dict[str, Any]):
        """Print formatted quality report"""
        print("\n" + "="*80)
        print("📊 HOMEPRO DATA QUALITY REPORT")
        print("="*80)
        
        if 'error' in report:
            print(f"❌ Error: {report['error']}")
            return
        
        total = report['total_products']
        print(f"Total Products Analyzed: {total:,}")
        print()
        
        # Completeness
        completeness = report['completeness']
        print("📋 DATA COMPLETENESS")
        print("-" * 40)
        print(f"Overall Score: {completeness['overall_score']:.1f}%")
        print()
        for field, data in completeness['field_details'].items():
            rate = data['completion_rate']
            emoji = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
            print(f"{emoji} {field:15} {rate:6.1f}% ({data['complete_count']:,}/{total:,})")
        print()
        
        # Duplicates
        duplicates = report['duplicates']
        print("🔍 DUPLICATE DETECTION")
        print("-" * 40)
        print(f"SKU Duplicates:  {duplicates['sku_duplicates']['count']:,}")
        print(f"Name Duplicates: {duplicates['name_duplicates']['count']:,}")
        print(f"URL Duplicates:  {duplicates['url_duplicates']['count']:,}")
        print(f"Overall Duplicate Rate: {duplicates['duplicate_rate']:.2f}%")
        print()
        
        # Pricing
        pricing = report['pricing']
        if 'error' not in pricing:
            print("💰 PRICING ANALYSIS")
            print("-" * 40)
            stats = pricing['statistics']
            print(f"Products with Price: {stats['total_products_with_price']:,}")
            print(f"Price Range: ฿{stats['min_price']:,.2f} - ฿{stats['max_price']:,.2f}")
            print(f"Average Price: ฿{stats['avg_price']:,.2f}")
            
            discounts = pricing['discounts']
            print(f"Products on Sale: {discounts['products_on_sale']:,} ({discounts['sale_rate']:.1f}%)")
            print(f"Average Discount: {discounts['avg_discount_percentage']:.1f}%")
            print()
        
        # Brands
        brands = report['brands']
        print("🏷️  BRAND ANALYSIS")
        print("-" * 40)
        print(f"Total Brands: {brands['total_brands']:,}")
        print(f"Brand Coverage: {brands['brand_coverage']:.1f}%")
        print("Top Brands:")
        for brand, count in list(brands['top_brands'].items())[:5]:
            print(f"  {brand}: {count:,} products")
        print()
        
        # Categories
        categories = report['categories']
        print("📂 CATEGORY ANALYSIS")
        print("-" * 40)
        print(f"Total Categories: {categories['total_categories']:,}")
        print(f"Category Coverage: {categories['category_coverage']:.1f}%")
        print("Top Categories:")
        for category, count in list(categories['top_categories'].items())[:5]:
            print(f"  {category}: {count:,} products")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        for rec in report['recommendations']:
            print(f"  {rec}")
        print()
        
        print("="*80)

async def main():
    """Main function"""
    checker = QualityChecker()
    report = await checker.check_all_quality()
    checker.print_quality_report(report)

if __name__ == "__main__":
    asyncio.run(main())