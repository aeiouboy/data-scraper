#!/usr/bin/env python3
"""
Show Thai Watsadu products in database with proper counting
"""
import asyncio
from src.services.supabase_service import SupabaseService
from datetime import datetime

async def show_twd_products():
    """Display TWD products with proper statistics"""
    
    supabase = SupabaseService()
    
    print("\n🏪 Thai Watsadu Products in Database")
    print("=" * 80)
    
    # Get total count
    count_response = supabase.client.table('products').select('id', count='exact').eq('retailer_code', 'TWD').execute()
    total_count = count_response.count
    
    print(f"\n📊 Total TWD Products: {total_count}")
    
    # Get products grouped by category
    all_products = supabase.client.table('products').select('*').eq('retailer_code', 'TWD').execute()
    
    # Group by category
    categories = {}
    for product in all_products.data:
        cat = product.get('category', 'Uncategorized')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(product)
    
    print(f"\n📂 Products by Category:")
    for category, products in sorted(categories.items(), key=lambda x: str(x[0]) if x[0] is not None else ''):
        print(f"   • {category}: {len(products)} products")
    
    # Show recent products
    print(f"\n🆕 10 Most Recent Products:")
    recent = supabase.client.table('products').select('*').eq('retailer_code', 'TWD').order('scraped_at', desc=True).limit(10).execute()
    
    for i, product in enumerate(recent.data, 1):
        price = f"฿{product['current_price']:,.2f}" if product['current_price'] else "No price"
        scraped = datetime.fromisoformat(product['scraped_at'].replace('Z', '+00:00'))
        print(f"   {i}. {product['name'][:60]}...")
        print(f"      SKU: {product['sku']} | Price: {price} | Scraped: {scraped.strftime('%Y-%m-%d %H:%M')}")
    
    # Show price statistics
    products_with_prices = [p for p in all_products.data if p.get('current_price')]
    if products_with_prices:
        prices = [float(p['current_price']) for p in products_with_prices]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        print(f"\n💰 Price Statistics:")
        print(f"   • Products with prices: {len(products_with_prices)}/{total_count} ({len(products_with_prices)/total_count*100:.1f}%)")
        print(f"   • Average price: ฿{avg_price:,.2f}")
        print(f"   • Price range: ฿{min_price:,.2f} - ฿{max_price:,.2f}")
    
    # Show scraping timeline
    print(f"\n📅 Scraping Timeline:")
    if all_products.data:
        dates = {}
        for product in all_products.data:
            date = product['scraped_at'][:10]  # Get date part only
            dates[date] = dates.get(date, 0) + 1
        
        for date in sorted(dates.keys(), reverse=True)[:5]:
            print(f"   • {date}: {dates[date]} products scraped")
    
    return total_count

if __name__ == "__main__":
    asyncio.run(show_twd_products())