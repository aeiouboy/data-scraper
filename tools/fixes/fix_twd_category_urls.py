#!/usr/bin/env python3
"""
Fix TWD products with category URLs instead of product URLs
Based on analysis finding 800 products with this issue
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from src.services.supabase_service import SupabaseService
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TWDCategoryURLFixer:
    """Fix TWD products with category URLs instead of product URLs"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.improved_strategy = ImprovedNativeStrategy()
        self.stats = {
            'processed': 0,
            'fixed': 0,
            'failed': 0,
            'url_corrections': 0,
            'price_corrections': 0,
            'brand_corrections': 0,
            'extraction_errors': 0
        }
    
    def search_twd_for_product(self, product_name: str, sku: str) -> str:
        """Search TWD website for correct product URL"""
        try:
            # Clean product name for search
            clean_name = re.sub(r'[^\w\s]', ' ', product_name)
            search_query = ' '.join(clean_name.split()[:5])  # Use first 5 words
            
            search_url = f"https://www.thaiwatsadu.com/en/search?q={search_query}"
            
            response = requests.get(search_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product links
                product_links = soup.find_all('a', href=True)
                
                for link in product_links:
                    href = link.get('href', '')
                    
                    # Check if it's a product URL
                    if '/product/' in href:
                        if href.startswith('/'):
                            href = f"https://www.thaiwatsadu.com{href}"
                        
                        # Verify it contains the product name elements
                        link_text = link.get_text(strip=True).lower()
                        name_words = product_name.lower().split()[:3]  # First 3 words
                        
                        if any(word in link_text for word in name_words if len(word) > 3):
                            logger.info(f"Found potential URL for {sku}: {href}")
                            return href
            
        except Exception as e:
            logger.warning(f"Search failed for {sku}: {str(e)}")
        
        return None
    
    def construct_twd_url_from_sku(self, sku: str, product_name: str) -> str:
        """Try to construct TWD product URL from SKU and name"""
        try:
            # TWD SKUs often contain the product ID at the end
            # Extract potential product ID from SKU
            sku_parts = sku.split('-')
            if len(sku_parts) >= 2:
                potential_id = sku_parts[-1]
                
                # Clean product name for URL
                clean_name = re.sub(r'[^\w\s]', ' ', product_name)
                name_parts = clean_name.split()[:8]  # Limit to 8 words
                url_name = '-'.join(name_parts).lower()
                url_name = re.sub(r'[^a-z0-9-]', '', url_name)
                
                # Construct potential URL
                constructed_url = f"https://www.thaiwatsadu.com/en/product/{url_name}-{potential_id}"
                
                # Test if URL exists
                response = requests.head(constructed_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Constructed valid URL for {sku}: {constructed_url}")
                    return constructed_url
        
        except Exception as e:
            logger.warning(f"URL construction failed for {sku}: {str(e)}")
        
        return None
    
    def fix_twd_category_urls_batch(self, limit: int = 30) -> dict:
        """Fix batch of TWD products with category URLs"""
        
        logger.info(f"Fixing TWD category URL issues (limit: {limit})")
        
        # Get TWD products with category URLs
        result = self.supabase.client.table('products')\
            .select('id, sku, name, brand, category, url, current_price, original_price')\
            .eq('retailer_code', 'TWD')\
            .like('url', '%/category/%')\
            .limit(limit)\
            .execute()
        
        products = result.data
        logger.info(f"Found {len(products)} TWD products with category URLs")
        
        for product in products:
            try:
                logger.info(f"Processing TWD: {product['sku']} - {product['name'][:50]}...")
                
                # Try multiple methods to find correct URL
                correct_url = None
                
                # Method 1: Search TWD website
                correct_url = self.search_twd_for_product(product['name'], product['sku'])
                
                # Method 2: Try to construct URL from SKU if search failed
                if not correct_url:
                    correct_url = self.construct_twd_url_from_sku(product['sku'], product['name'])
                
                updates = {}
                
                if correct_url:
                    logger.info(f"Found correct URL: {correct_url}")
                    updates['url'] = correct_url
                    self.stats['url_corrections'] += 1
                    
                    # Extract correct data from the proper URL
                    try:
                        response = requests.get(correct_url, timeout=30, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Extract improved price
                            price_result = self.improved_strategy.extract_improved_price(soup, correct_url)
                            if price_result.get('current_price'):
                                updates['current_price'] = price_result['current_price']
                                self.stats['price_corrections'] += 1
                                logger.info(f"  Fixed price: ฿{price_result['current_price']}")
                            if price_result.get('original_price'):
                                updates['original_price'] = price_result['original_price']
                            
                            # Extract improved brand if missing
                            if not product.get('brand'):
                                brand_result = self.improved_strategy.extract_improved_brand(soup, correct_url)
                                if brand_result:
                                    updates['brand'] = brand_result
                                    self.stats['brand_corrections'] += 1
                                    logger.info(f"  Fixed brand: {brand_result}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting from {correct_url}: {str(e)}")
                        self.stats['extraction_errors'] += 1
                        # Still keep the URL fix even if extraction fails
                
                # Apply updates if we have any
                if updates:
                    update_result = self.supabase.client.table('products')\
                        .update(updates)\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        self.stats['fixed'] += 1
                        logger.info(f"✅ Fixed TWD {product['sku']}: {list(updates.keys())}")
                    else:
                        self.stats['failed'] += 1
                        logger.error(f"Failed to update TWD {product['sku']}")
                else:
                    self.stats['failed'] += 1
                    logger.warning(f"No correct URL found for TWD {product['sku']}")
                
                self.stats['processed'] += 1
                time.sleep(2)  # Be respectful to TWD servers
                
            except Exception as e:
                logger.error(f"Error processing TWD {product['sku']}: {str(e)}")
                self.stats['failed'] += 1
                self.stats['processed'] += 1
        
        return self.stats.copy()

def main():
    """Fix TWD category URL issues"""
    
    fixer = TWDCategoryURLFixer()
    
    print("🔧 TWD CATEGORY URL FIX")
    print("=" * 40)
    print("This will fix TWD products with /category/ URLs instead of /product/ URLs")
    print("Based on analysis: 800 affected products found")
    
    # Process in manageable batches
    batch_size = 20  # Smaller batch to be respectful to servers
    
    print(f"\n🏪 Processing TWD products (batch size: {batch_size})")
    
    results = fixer.fix_twd_category_urls_batch(limit=batch_size)
    
    print(f"\n📊 BATCH RESULTS:")
    print(f"  Processed: {results['processed']}")
    print(f"  ✅ Fixed: {results['fixed']}")
    print(f"  ❌ Failed: {results['failed']}")
    print(f"  🔗 URL corrections: {results['url_corrections']}")
    print(f"  💰 Price corrections: {results['price_corrections']}")
    print(f"  🏷️ Brand corrections: {results['brand_corrections']}")
    print(f"  ⚠️ Extraction errors: {results['extraction_errors']}")
    
    success_rate = (results['fixed'] / results['processed'] * 100) if results['processed'] > 0 else 0
    print(f"  📈 Success rate: {success_rate:.1f}%")
    
    # Save results
    with open('twd_category_url_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved: twd_category_url_fix_results.json")
    
    if results['fixed'] > 0:
        print(f"\n✅ Successfully fixed {results['fixed']} TWD products!")
        print(f"📝 Recommendation: Run this script multiple times to fix all 800 affected products")
        print(f"📊 Remaining products to fix: ~{800 - results['fixed']}")
    else:
        print(f"\n⚠️ No products were fixed in this batch")
        print(f"💡 Consider checking the search logic or URL construction methods")
    
    print(f"\n🏁 TWD category URL fix completed!")

if __name__ == "__main__":
    main()