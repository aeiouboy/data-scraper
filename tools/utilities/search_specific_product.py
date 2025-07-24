#!/usr/bin/env python3
"""
Script to search for a specific HomePro product by URL and analyze pricing data
Usage: python search_specific_product.py
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.services.supabase_service import SupabaseService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "https://www.homepro.co.th/p/1288319"

class ProductAnalyzer:
    def __init__(self):
        self.supabase = SupabaseService()
    
    async def search_product_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Search for a product by its URL"""
        try:
            result = self.supabase.client.table('products').select('*').eq('url', url).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error searching product by URL: {str(e)}")
            return None
    
    async def search_products_by_partial_url(self, url_part: str) -> List[Dict[str, Any]]:
        """Search for products with partial URL match"""
        try:
            result = self.supabase.client.table('products').select('*').ilike('url', f'%{url_part}%').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error searching products by partial URL: {str(e)}")
            return []
    
    async def search_homepro_products_with_1288319(self) -> List[Dict[str, Any]]:
        """Search for HomePro products containing the ID 1288319"""
        try:
            result = self.supabase.client.table('products').select('*').eq('retailer_code', 'HP').ilike('url', '%1288319%').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error searching HomePro products: {str(e)}")
            return []
    
    async def get_price_history_for_product(self, product_id: str) -> List[Dict[str, Any]]:
        """Get price history for a specific product"""
        return await self.supabase.get_price_history(product_id, limit=10)
    
    async def analyze_homepro_pricing_issues(self) -> Dict[str, Any]:
        """Analyze HomePro products for potential pricing issues"""
        try:
            # Get all HomePro products
            result = self.supabase.client.table('products').select('*').eq('retailer_code', 'HP').execute()
            homepro_products = result.data
            
            # Analyze pricing patterns
            total_products = len(homepro_products)
            low_price_products = [p for p in homepro_products if p.get('current_price') and p['current_price'] < 10000]
            high_price_products = [p for p in homepro_products if p.get('current_price') and p['current_price'] > 50000]
            
            # Look for products with unusual price/original_price ratios
            unusual_discount_products = []
            for product in homepro_products:
                current = product.get('current_price')
                original = product.get('original_price')
                
                if current and original and original > 0:
                    discount_ratio = (original - current) / original
                    if discount_ratio > 0.8 or discount_ratio < -0.1:  # More than 80% discount or negative discount
                        unusual_discount_products.append({
                            'product': product,
                            'discount_ratio': discount_ratio
                        })
            
            return {
                'total_homepro_products': total_products,
                'low_price_count': len(low_price_products),
                'high_price_count': len(high_price_products),
                'unusual_discount_count': len(unusual_discount_products),
                'sample_low_price_products': low_price_products[:5],
                'sample_unusual_discounts': unusual_discount_products[:5]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing HomePro pricing: {str(e)}")
            return {}
    
    def format_price(self, price: Optional[float]) -> str:
        """Format price for display"""
        if price is None:
            return "N/A"
        return f"฿{price:,.2f}"
    
    def print_product_details(self, product: Dict[str, Any]):
        """Print detailed product information"""
        print("\n" + "="*80)
        print("PRODUCT DETAILS")
        print("="*80)
        
        print(f"ID: {product.get('id', 'N/A')}")
        print(f"SKU: {product.get('sku', 'N/A')}")
        print(f"Name: {product.get('name', 'N/A')}")
        print(f"Brand: {product.get('brand', 'N/A')}")
        print(f"Category: {product.get('category', 'N/A')}")
        print(f"Retailer: {product.get('retailer_code', 'N/A')}")
        print(f"URL: {product.get('url', 'N/A')}")
        
        print("\nPRICING INFORMATION:")
        print(f"Current Price: {self.format_price(product.get('current_price'))}")
        print(f"Original Price: {self.format_price(product.get('original_price'))}")
        
        discount = product.get('discount_percentage')
        if discount is not None:
            print(f"Discount: {discount:.2f}%")
        else:
            print("Discount: N/A")
        
        # Calculate discount amount if both prices available
        current = product.get('current_price')
        original = product.get('original_price')
        if current and original:
            discount_amount = original - current
            print(f"Discount Amount: {self.format_price(discount_amount)}")
        
        print(f"\nAvailability: {product.get('availability', 'N/A')}")
        print(f"Last Scraped: {product.get('scraped_at', 'N/A')}")
        print(f"Created: {product.get('created_at', 'N/A')}")
        print(f"Updated: {product.get('updated_at', 'N/A')}")
        
        # Show specifications if available
        specs = product.get('specifications')
        if specs:
            print(f"\nSpecifications: {json.dumps(specs, indent=2, ensure_ascii=False)}")
        
        # Show features if available
        features = product.get('features')
        if features:
            print(f"\nFeatures: {features}")
    
    def print_pricing_analysis(self, analysis: Dict[str, Any]):
        """Print pricing analysis results"""
        print("\n" + "="*80)
        print("HOMEPRO PRICING ANALYSIS")
        print("="*80)
        
        print(f"Total HomePro Products: {analysis.get('total_homepro_products', 0)}")
        print(f"Low Price Products (<10,000): {analysis.get('low_price_count', 0)}")
        print(f"High Price Products (>50,000): {analysis.get('high_price_count', 0)}")
        print(f"Unusual Discount Products: {analysis.get('unusual_discount_count', 0)}")
        
        # Show sample low price products
        low_price = analysis.get('sample_low_price_products', [])
        if low_price:
            print(f"\nSample Low Price Products:")
            for product in low_price:
                print(f"  - {product.get('name', 'N/A')}: {self.format_price(product.get('current_price'))}")
        
        # Show unusual discounts
        unusual = analysis.get('sample_unusual_discounts', [])
        if unusual:
            print(f"\nSample Unusual Discount Products:")
            for item in unusual:
                product = item['product']
                ratio = item['discount_ratio']
                print(f"  - {product.get('name', 'N/A')}: {ratio:.2%} discount")
                print(f"    Current: {self.format_price(product.get('current_price'))}, "
                      f"Original: {self.format_price(product.get('original_price'))}")

async def main():
    """Main function to search for the specific product and analyze pricing"""
    analyzer = ProductAnalyzer()
    
    print(f"Searching for product with URL: {TARGET_URL}")
    
    # 1. Search by exact URL
    print("\n1. Searching by exact URL...")
    product = await analyzer.search_product_by_url(TARGET_URL)
    
    if product:
        print("✅ Found product by exact URL!")
        analyzer.print_product_details(product)
        
        # Get price history
        print("\n" + "="*80)
        print("PRICE HISTORY")
        print("="*80)
        
        price_history = await analyzer.get_price_history_for_product(product['id'])
        if price_history:
            for entry in price_history:
                recorded_at = entry.get('recorded_at', 'N/A')
                price = analyzer.format_price(entry.get('price'))
                original = analyzer.format_price(entry.get('original_price'))
                discount = entry.get('discount_percentage', 0)
                print(f"{recorded_at}: Current={price}, Original={original}, Discount={discount:.2f}%")
        else:
            print("No price history found.")
    
    else:
        print("❌ Product not found by exact URL")
        
        # 2. Search by partial URL (product ID)
        print("\n2. Searching by product ID (1288319)...")
        products = await analyzer.search_homepro_products_with_1288319()
        
        if products:
            print(f"✅ Found {len(products)} HomePro product(s) with ID 1288319:")
            for i, prod in enumerate(products, 1):
                print(f"\n--- Product {i} ---")
                analyzer.print_product_details(prod)
        else:
            print("❌ No HomePro products found with ID 1288319")
    
    # 3. General HomePro pricing analysis
    print("\n3. Analyzing HomePro pricing patterns...")
    analysis = await analyzer.analyze_homepro_pricing_issues()
    if analysis:
        analyzer.print_pricing_analysis(analysis)
    
    # 4. Expected vs Actual Price Comparison
    print("\n" + "="*80)
    print("EXPECTED VS ACTUAL PRICE COMPARISON")
    print("="*80)
    
    expected_current = 32190
    expected_original = 45990
    expected_discount = 13800
    
    if product:
        actual_current = product.get('current_price')
        actual_original = product.get('original_price')
        actual_discount = (actual_original - actual_current) if (actual_current and actual_original) else None
        
        print(f"Expected Current Price: ฿{expected_current:,}")
        print(f"Actual Current Price:   {analyzer.format_price(actual_current)}")
        print(f"Difference:             {analyzer.format_price((actual_current - expected_current) if actual_current else None)}")
        
        print(f"\nExpected Original Price: ฿{expected_original:,}")
        print(f"Actual Original Price:   {analyzer.format_price(actual_original)}")
        print(f"Difference:              {analyzer.format_price((actual_original - expected_original) if actual_original else None)}")
        
        print(f"\nExpected Discount: ฿{expected_discount:,}")
        print(f"Actual Discount:   {analyzer.format_price(actual_discount)}")
        
        # Check if this is a widespread issue
        if actual_current and actual_current < expected_current * 0.5:
            print("\n⚠️  WARNING: Database price is significantly lower than expected!")
            print("   This may indicate a systematic pricing extraction issue.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)