#!/usr/bin/env python3
"""
Fix TWD category URLs by extracting actual product URLs from category pages
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from src.services.supabase_service import SupabaseService
from src.scrapers.strategies.improved_native_strategy import ImprovedNativeStrategy
import logging
import re
from fuzzywuzzy import fuzz
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TWDCategoryURLExtractor:
    """Extract actual product URLs from TWD category pages"""
    
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
            'category_corrections': 0
        }
        self.category_cache = {}  # Cache category page content
    
    def extract_products_from_category(self, category_url: str) -> list:
        """Extract all product URLs and names from a category page"""
        if category_url in self.category_cache:
            return self.category_cache[category_url]
        
        try:
            response = requests.get(category_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Find all product links
            product_links = soup.find_all('a', href=True)
            
            for link in product_links:
                href = link.get('href', '')
                
                if '/product/' in href:
                    if href.startswith('/'):
                        href = f"https://www.thaiwatsadu.com{href}"
                    
                    # Get product name from link text or nearby elements
                    product_name = self._extract_product_name_from_link(link)
                    
                    if product_name:
                        products.append({
                            'url': href,
                            'name': product_name,
                            'name_clean': self._clean_product_name(product_name)
                        })
            
            # Remove duplicates
            unique_products = []
            seen_urls = set()
            for product in products:
                if product['url'] not in seen_urls:
                    unique_products.append(product)
                    seen_urls.add(product['url'])
            
            self.category_cache[category_url] = unique_products
            logger.info(f"Extracted {len(unique_products)} products from category page")
            return unique_products
            
        except Exception as e:
            logger.error(f"Error extracting from category {category_url}: {str(e)}")
            return []
    
    def _extract_product_name_from_link(self, link) -> str:
        """Extract product name from link element"""
        # Try different methods to get product name
        
        # Method 1: Link text
        link_text = link.get_text(strip=True)
        if link_text and len(link_text) > 5:
            return link_text
        
        # Method 2: Title attribute
        title = link.get('title', '')
        if title and len(title) > 5:
            return title
        
        # Method 3: Alt text from images
        img = link.find('img')
        if img:
            alt = img.get('alt', '')
            if alt and len(alt) > 5:
                return alt
        
        # Method 4: From URL decode
        href = link.get('href', '')
        if '/product/' in href:
            try:
                decoded_url = unquote(href)
                # Extract product name from URL path
                product_part = decoded_url.split('/product/')[-1]
                product_name = product_part.split('-')[:-1]  # Remove ID at end
                if product_name:
                    return ' '.join(product_name).replace('-', ' ')
            except:
                pass
        
        # Method 5: Nearby text elements
        parent = link.parent
        if parent:
            nearby_text = parent.get_text(strip=True)
            if nearby_text and len(nearby_text) > 5:
                return nearby_text[:100]  # Limit length
        
        return ""
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name for matching"""
        if not name:
            return ""
        
        # Remove extra whitespace and normalize
        clean = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common noise
        noise_patterns = [
            r'\s*\(\s*\)\s*',  # Empty parentheses
            r'\s*\[\s*\]\s*',  # Empty brackets
            r'\s*\d+\s*$',     # Trailing numbers
            r'\s*-\s*$',       # Trailing dashes
        ]
        
        for pattern in noise_patterns:
            clean = re.sub(pattern, '', clean)
        
        return clean.lower()
    
    def find_matching_product_url(self, target_product: dict, category_products: list) -> str:
        """Find matching product URL from category products"""
        if not category_products:
            return None
        
        target_name = target_product['name']
        target_clean = self._clean_product_name(target_name)
        
        best_match = None
        best_score = 0
        
        for category_product in category_products:
            category_name = category_product['name']
            category_clean = category_product['name_clean']
            
            # Calculate similarity scores
            scores = [
                fuzz.ratio(target_clean, category_clean),
                fuzz.partial_ratio(target_clean, category_clean),
                fuzz.token_sort_ratio(target_clean, category_clean),
                fuzz.token_set_ratio(target_clean, category_clean)
            ]
            
            max_score = max(scores)
            
            # Additional scoring for key terms
            target_words = set(target_clean.split())
            category_words = set(category_clean.split())
            
            # Boost score if key identifiers match
            key_terms = ['samsung', 'lg', 'haier', 'daikin', 'toshiba', 'beko', 'electrolux', 'hitachi']
            for term in key_terms:
                if term in target_words and term in category_words:
                    max_score += 10
            
            # Boost score for model numbers
            target_models = re.findall(r'[A-Z]+[0-9]+[A-Z0-9]*', target_name.upper())
            category_models = re.findall(r'[A-Z]+[0-9]+[A-Z0-9]*', category_name.upper())
            
            for model in target_models:
                if model in category_models:
                    max_score += 20
            
            if max_score > best_score:
                best_score = max_score
                best_match = category_product
        
        # Only return match if score is high enough
        if best_score >= 75:  # Threshold for confidence
            logger.info(f"Found match with score {best_score}: {best_match['name'][:50]}...")
            return best_match['url']
        
        return None
    
    def fix_twd_category_products_batch(self, limit: int = 25) -> dict:
        """Fix batch of TWD products with category URLs"""
        
        logger.info(f"Fixing TWD category URL products (limit: {limit})")
        
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
                logger.info(f"Processing {product['sku']}: {product['name'][:50]}...")
                
                # Extract products from category page
                category_products = self.extract_products_from_category(product['url'])
                
                if not category_products:
                    logger.warning(f"No products found on category page for {product['sku']}")
                    self.stats['failed'] += 1
                    self.stats['processed'] += 1
                    continue
                
                # Find matching product URL
                correct_url = self.find_matching_product_url(product, category_products)
                
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
                                logger.info(f"  ✅ Price: ฿{price_result['current_price']}")
                            if price_result.get('original_price'):
                                updates['original_price'] = price_result['original_price']
                            
                            # Extract improved brand if missing
                            if not product.get('brand'):
                                brand_result = self.improved_strategy.extract_improved_brand(soup, correct_url)
                                if brand_result:
                                    updates['brand'] = brand_result
                                    self.stats['brand_corrections'] += 1
                                    logger.info(f"  ✅ Brand: {brand_result}")
                            
                            # Extract improved category if generic
                            if product.get('category') in ['Other', 'General', None]:
                                category_result = self.improved_strategy.extract_improved_category(soup, correct_url)
                                if category_result and category_result not in ['Other', 'General']:
                                    updates['category'] = category_result
                                    self.stats['category_corrections'] += 1
                                    logger.info(f"  ✅ Category: {category_result}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting from {correct_url}: {str(e)}")
                        # Still keep the URL fix even if extraction fails
                
                # Apply updates if we have any
                if updates:
                    update_result = self.supabase.client.table('products')\
                        .update(updates)\
                        .eq('id', product['id'])\
                        .execute()
                    
                    if update_result.data:
                        self.stats['fixed'] += 1
                        logger.info(f"✅ Fixed {product['sku']}: {list(updates.keys())}")
                    else:
                        self.stats['failed'] += 1
                        logger.error(f"Failed to update {product['sku']}")
                else:
                    self.stats['failed'] += 1
                    logger.warning(f"No matching product found for {product['sku']}")
                
                self.stats['processed'] += 1
                time.sleep(1)  # Be respectful to servers
                
            except Exception as e:
                logger.error(f"Error processing {product['sku']}: {str(e)}")
                self.stats['failed'] += 1
                self.stats['processed'] += 1
        
        return self.stats.copy()

def main():
    """Fix TWD category URL issues by extracting correct URLs"""
    
    extractor = TWDCategoryURLExtractor()
    
    print("🔧 TWD CATEGORY URL EXTRACTION FIX")
    print("=" * 50)
    print("This will extract correct product URLs from TWD category pages")
    print("Target: 800 products with category URLs")
    
    # Process in batches
    batch_size = 20  # Conservative batch size
    
    print(f"\n🏪 Processing TWD products (batch size: {batch_size})")
    
    results = extractor.fix_twd_category_products_batch(limit=batch_size)
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"  Processed: {results['processed']}")
    print(f"  ✅ Fixed: {results['fixed']}")
    print(f"  ❌ Failed: {results['failed']}")
    print(f"  🔗 URL corrections: {results['url_corrections']}")
    print(f"  💰 Price corrections: {results['price_corrections']}")
    print(f"  🏷️ Brand corrections: {results['brand_corrections']}")
    print(f"  📂 Category corrections: {results['category_corrections']}")
    
    success_rate = (results['fixed'] / results['processed'] * 100) if results['processed'] > 0 else 0
    print(f"  📈 Success rate: {success_rate:.1f}%")
    
    # Save results
    with open('twd_extraction_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved: twd_extraction_fix_results.json")
    
    if results['fixed'] > 0:
        print(f"\n✅ Successfully fixed {results['fixed']} TWD products!")
        remaining = 800 - results['fixed']
        print(f"📊 Estimated remaining products to fix: ~{remaining}")
        print(f"🔄 Run this script {remaining // batch_size + 1} more times to fix all products")
    else:
        print(f"\n⚠️ No products were fixed in this batch")
        print(f"💡 Check fuzzy matching thresholds or category page structure")
    
    print(f"\n🏁 TWD category URL extraction completed!")

if __name__ == "__main__":
    main()