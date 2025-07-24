#!/usr/bin/env python3
"""
Analyze products with potentially incorrect URLs and pricing
"""

import json
from src.services.supabase_service import SupabaseService
import re

def analyze_url_issues():
    """Find products with URL and pricing issues"""
    
    supabase = SupabaseService()
    
    print("🔍 ANALYZING URL AND PRICING ISSUES")
    print("=" * 50)
    
    issues = {
        'category_urls': [],
        'suspicious_prices': [],
        'url_patterns': {},
        'price_anomalies': []
    }
    
    # Get all TWD products first (where we found the issue)
    print("\n📊 Analyzing TWD products...")
    twd_result = supabase.client.table('products')\
        .select('id, sku, name, brand, category, url, current_price, original_price')\
        .eq('retailer_code', 'TWD')\
        .execute()
    
    twd_products = twd_result.data
    print(f"Found {len(twd_products)} TWD products")
    
    # Analyze TWD URL patterns
    twd_category_urls = 0
    twd_product_urls = 0
    
    for product in twd_products:
        url = product.get('url', '')
        
        # Check for category URLs
        if '/category/' in url:
            twd_category_urls += 1
            issues['category_urls'].append({
                'sku': product['sku'],
                'name': product['name'],
                'url': url,
                'current_price': product.get('current_price'),
                'retailer': 'TWD'
            })
        elif '/product/' in url:
            twd_product_urls += 1
        
        # Check for suspicious prices
        current_price = product.get('current_price')
        original_price = product.get('original_price')
        
        if current_price and original_price:
            # Suspicious if current > original (should be discount)
            if current_price > original_price:
                issues['price_anomalies'].append({
                    'sku': product['sku'],
                    'name': product['name'],
                    'current_price': current_price,
                    'original_price': original_price,
                    'issue': 'current > original',
                    'retailer': 'TWD'
                })
            
            # Suspicious if current price is extremely low
            if current_price < 100 and original_price > 1000:
                issues['suspicious_prices'].append({
                    'sku': product['sku'],
                    'name': product['name'],
                    'current_price': current_price,
                    'original_price': original_price,
                    'ratio': original_price / current_price if current_price > 0 else 0,
                    'retailer': 'TWD'
                })
    
    print(f"  TWD Category URLs: {twd_category_urls}")
    print(f"  TWD Product URLs: {twd_product_urls}")
    
    # Check other retailers for similar patterns
    print(f"\n📊 Analyzing other retailers...")
    
    for retailer in ['HP', 'GH', 'DH', 'BT', 'MH']:
        print(f"\n  Checking {retailer}...")
        
        retailer_result = supabase.client.table('products')\
            .select('id, sku, name, url, current_price, original_price')\
            .eq('retailer_code', retailer)\
            .limit(500)\
            .execute()
        
        retailer_products = retailer_result.data
        print(f"    Found {len(retailer_products)} {retailer} products (sample)")
        
        retailer_category_urls = 0
        retailer_suspicious = 0
        
        for product in retailer_products:
            url = product.get('url', '')
            
            # Check for category-like URLs
            if any(pattern in url for pattern in ['/category/', '/categories/', '/cat/', '/c/']):
                retailer_category_urls += 1
                issues['category_urls'].append({
                    'sku': product['sku'],
                    'name': product['name'],
                    'url': url,
                    'current_price': product.get('current_price'),
                    'retailer': retailer
                })
            
            # Check for suspicious prices
            current_price = product.get('current_price')
            original_price = product.get('original_price')
            
            if current_price and original_price:
                if current_price < 100 and original_price > 1000:
                    retailer_suspicious += 1
                    issues['suspicious_prices'].append({
                        'sku': product['sku'],
                        'name': product['name'],
                        'current_price': current_price,
                        'original_price': original_price,
                        'ratio': original_price / current_price if current_price > 0 else 0,
                        'retailer': retailer
                    })
        
        print(f"    Category URLs: {retailer_category_urls}")
        print(f"    Suspicious prices: {retailer_suspicious}")
    
    # Analyze URL patterns
    print(f"\n📈 URL PATTERN ANALYSIS:")
    all_category_urls = len(issues['category_urls'])
    all_suspicious_prices = len(issues['suspicious_prices'])
    all_price_anomalies = len(issues['price_anomalies'])
    
    print(f"  Total category URLs found: {all_category_urls}")
    print(f"  Total suspicious prices: {all_suspicious_prices}")
    print(f"  Total price anomalies: {all_price_anomalies}")
    
    # Show samples of issues
    print(f"\n📋 SAMPLE CATEGORY URL ISSUES:")
    for issue in issues['category_urls'][:5]:
        print(f"  {issue['retailer']}-{issue['sku']}: {issue['name'][:50]}...")
        print(f"    Price: ฿{issue['current_price']} | URL: {issue['url'][:80]}...")
    
    print(f"\n💰 SAMPLE SUSPICIOUS PRICE ISSUES:")
    for issue in issues['suspicious_prices'][:5]:
        print(f"  {issue['retailer']}-{issue['sku']}: {issue['name'][:50]}...")
        print(f"    Current: ฿{issue['current_price']} | Original: ฿{issue['original_price']} | Ratio: {issue['ratio']:.1f}x")
    
    # Save results
    with open('url_and_price_issues_analysis.json', 'w') as f:
        json.dump(issues, f, indent=2)
    
    print(f"\n📁 Analysis saved: url_and_price_issues_analysis.json")
    
    # Recommend fixing priority
    print(f"\n🎯 RECOMMENDED FIXING PRIORITY:")
    print(f"  1. Category URLs: {all_category_urls} products (causes wrong data extraction)")
    print(f"  2. Suspicious prices: {all_suspicious_prices} products (likely extraction errors)")
    print(f"  3. Price anomalies: {all_price_anomalies} products (data validation issues)")
    
    return issues

if __name__ == "__main__":
    analyze_url_issues()