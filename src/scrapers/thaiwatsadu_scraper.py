"""
Thai Watsadu product scraper implementation
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

from src.models.product import Product
from src.services.firecrawl_client import FirecrawlClient
from src.config.retailers import retailer_manager, RetailerType
from src.utils.text_cleaner import clean_text, extract_number_from_string
from src.utils.url_validator import is_valid_product_url

logger = logging.getLogger(__name__)


class ThaiWatsaduScraper:
    """Scraper for Thai Watsadu products"""
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.retailer_config = retailer_manager.get_retailer(RetailerType.TWD)
        self.base_url = self.retailer_config.base_url
        
    async def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single Thai Watsadu product"""
        try:
            if not is_valid_product_url(url, self.base_url):
                logger.warning(f"Invalid product URL: {url}")
                return None
            
            # Use Firecrawl to get product data
            result = await self.firecrawl.scrape(url)
            
            if not result:
                logger.error(f"Failed to scrape product: {url}")
                return None
            
            # Extract product data
            product_data = self._extract_product_data(result, url)
            
            if not product_data:
                logger.error(f"Failed to extract product data from: {url}")
                return None
            
            # Create Product model
            product = Product(
                sku=product_data['sku'],
                name=product_data['name'],
                brand=product_data.get('brand'),
                category=product_data.get('category'),
                current_price=product_data.get('current_price'),
                original_price=product_data.get('original_price'),
                description=product_data.get('description'),
                features=product_data.get('features', []),
                specifications=product_data.get('specifications', {}),
                availability=product_data.get('availability', 'unknown'),
                images=product_data.get('images', []),
                url=url,
                retailer_code=self.retailer_config.code,
                retailer_name=self.retailer_config.name,
                retailer_sku=product_data.get('retailer_sku'),
                unified_category=self._map_to_unified_category(product_data.get('category')),
                monitoring_tier=self._determine_monitoring_tier(product_data.get('current_price'))
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Error scraping Thai Watsadu product {url}: {str(e)}")
            return None
    
    def _extract_product_data(self, firecrawl_result: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
        """Extract product data from Firecrawl result"""
        try:
            markdown = firecrawl_result.get('markdown', '')
            html = firecrawl_result.get('html', '')
            metadata = firecrawl_result.get('metadata', {})
            
            # Extract SKU from URL or page
            sku = self._extract_sku(url, markdown)
            if not sku:
                logger.warning(f"No SKU found for {url}")
                return None
            
            # Extract product name
            name = self._extract_product_name(markdown, metadata)
            if not name:
                logger.warning(f"No product name found for {url}")
                return None
            
            # Extract prices
            price_data = self._extract_prices(markdown, html)
            
            # Extract other details
            brand = self._extract_brand(markdown, name)
            category = self._extract_category(markdown, metadata)
            description = self._extract_description(markdown)
            features = self._extract_features(markdown)
            specifications = self._extract_specifications(markdown)
            availability = self._extract_availability(markdown)
            images = self._extract_images(firecrawl_result)
            
            return {
                'sku': sku,
                'retailer_sku': sku,
                'name': clean_text(name),
                'brand': clean_text(brand) if brand else None,
                'category': category,
                'current_price': price_data.get('current'),
                'original_price': price_data.get('original'),
                'description': clean_text(description) if description else None,
                'features': features,
                'specifications': specifications,
                'availability': availability,
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data: {str(e)}")
            return None
    
    def _extract_sku(self, url: str, markdown: str) -> Optional[str]:
        """Extract SKU from URL or content"""
        # Try to extract from URL first - Thai Watsadu pattern
        # Example: /th/product/product-name-SKU123
        url_match = re.search(r'/product/.*-([A-Z0-9]+)(?:\?|$)', url)
        if url_match:
            return url_match.group(1)
        
        # Try to find SKU in content
        sku_patterns = [
            r'รหัสสินค้า[:\s]+([A-Z0-9\-]+)',
            r'Product Code[:\s]+([A-Z0-9\-]+)',
            r'SKU[:\s]+([A-Z0-9\-]+)',
            r'Item #([A-Z0-9\-]+)'
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generate SKU from URL
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if parts:
            return f"TWD-{parts[-1]}"
        
        return None
    
    def _extract_product_name(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract product name"""
        # Method 1: Try metadata title first (most reliable)
        if metadata.get('title'):
            title = metadata['title']
            # Remove " - ไทวัสดุ" suffix
            title = re.sub(r'\s*-\s*ไทวัสดุ\s*$', '', title)
            # Only return if it's not the site tagline
            if title and title != "THAI WATSADU | ไทวัสดุ ครบเรื่องบ้าน ถูกและดี":
                return title.strip()
        
        # Method 2: Look for H1 headers in markdown
        h1_matches = re.findall(r'^#\s+(.+)$', markdown, re.MULTILINE)
        for h1 in h1_matches:
            # Skip navigation/menu items
            if not any(skip in h1.lower() for skip in ['menu', 'หมวดหมู่', 'navigation']):
                return h1.strip()
        
        # Method 3: Look for product name pattern near price
        # Thai Watsadu often has product name right before price
        price_pattern = r'(.+?)\s*฿\d+[,\d]*/EACH'
        price_match = re.search(price_pattern, markdown)
        if price_match:
            potential_name = price_match.group(1).strip()
            # Clean up and validate
            if len(potential_name) > 10 and not potential_name.startswith('!'):
                # Remove any image markdown
                potential_name = re.sub(r'!\[.*?\]\(.*?\)', '', potential_name).strip()
                if potential_name:
                    return potential_name
        
        # Method 4: Fallback to first meaningful text after breadcrumb
        # Look for text after category links
        category_end = re.search(r'\[สินค้าตามแบรนด์\].*?\n\n(.+?)(?:\n|$)', markdown)
        if category_end:
            potential_name = category_end.group(1).strip()
            if len(potential_name) > 10:
                return potential_name
        
        return None
    
    def _extract_prices(self, markdown: str, html: str) -> Dict[str, Optional[Decimal]]:
        """Extract current and original prices"""
        prices = {'current': None, 'original': None}
        
        # Look for specific Thai Watsadu price patterns
        # Pattern 1: ราคาเดิม (original price)
        original_match = re.search(r'ราคาเดิม\s*([0-9,]+(?:\.[0-9]{2})?)', markdown)
        if original_match:
            original_price = extract_number_from_string(original_match.group(1))
            if original_price:
                prices['original'] = Decimal(str(original_price))
        
        # Pattern 2: Current price (฿XXX/EACH pattern)
        # Get all price/EACH patterns
        current_pattern = r'฿([0-9,]+(?:\.[0-9]{2})?)\s*/\s*EACH'
        current_matches = re.findall(current_pattern, markdown)
        valid_current_prices = []
        for match in current_matches:
            price = extract_number_from_string(match)
            if price and price > 0:
                valid_current_prices.append(price)
        
        # Pattern 3: Additional discount amount
        additional_discount = 0
        discount_match = re.search(r'ซื้อตอนนี้ลดเพิ่ม\s*([0-9,]+)', markdown)
        if discount_match:
            additional_discount = extract_number_from_string(discount_match.group(1)) or 0
        
        # Determine current price
        if valid_current_prices:
            # If we have an original price, current should be less than original
            if prices['original']:
                for price in sorted(valid_current_prices):
                    if price < prices['original']:
                        prices['current'] = Decimal(str(price))
                        break
            else:
                # Take the first valid price
                prices['current'] = Decimal(str(valid_current_prices[0]))
            
            # Apply additional discount if found
            if additional_discount and prices['current']:
                actual_current = float(prices['current']) - additional_discount
                if actual_current > 0:
                    # Store the price before additional discount as current
                    # The actual selling price would be current - additional_discount
                    pass  # Keep current as is, since the pattern shows both prices
        
        # Fallback: general price extraction
        if not prices['current'] and not prices['original']:
            price_patterns = [
                r'฿\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'THB\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'ราคา[:\s]+([0-9,]+(?:\.[0-9]{2})?)',
            ]
            
            all_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, markdown)
                for match in matches:
                    price = extract_number_from_string(match)
                    if price and price > 0:
                        all_prices.append(price)
            
            if all_prices:
                all_prices = sorted(set(all_prices))
                prices['current'] = Decimal(str(all_prices[0]))
                if len(all_prices) > 1:
                    prices['original'] = Decimal(str(all_prices[-1]))
        
        return prices
    
    def _extract_brand(self, markdown: str, product_name: str) -> Optional[str]:
        """Extract brand from content"""
        # Look for Thai Watsadu specific brand patterns
        # Pattern 1: Link with brand name [BRAND](URL)
        brand_link = re.search(r'\[([A-Z][A-Z0-9\s&-]+)\]\([^)]*brand[^)]*\)', markdown)
        if brand_link:
            return brand_link.group(1).strip()
        
        # Pattern 2: In specifications section
        brand_patterns = [
            r'Brand\s*\n+\s*([^\n]+)',  # Brand followed by newline
            r'ยี่ห้อ[:\s]+([^\n]+)',
            r'แบรนด์[:\s]+([^\n]+)',
            r'Brand[:\s]+([^\n]+)',
            r'Manufacturer[:\s]+([^\n]+)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE)
            if match:
                brand = match.group(1).strip()
                # Clean up brand name
                if brand and not brand.lower() in ['null', 'none', '-']:
                    return brand
        
        # Try to extract from product name
        # Look for known patterns in Thai Watsadu products
        if product_name:
            # Common brand position patterns
            brand_match = re.match(r'^([A-Z][A-Z0-9\s&-]+?)\s+', product_name)
            if brand_match:
                potential_brand = brand_match.group(1).strip()
                # Validate it's likely a brand (all caps, reasonable length)
                if len(potential_brand) >= 3 and potential_brand.isupper():
                    return potential_brand
        
        return None
    
    def _extract_category(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract category information"""
        # Look for Thai Watsadu specific breadcrumb structure
        # Pattern: [Category Link](URL) > [Subcategory](URL) > ...
        breadcrumb_patterns = [
            # Match links in breadcrumb format
            r'\[([^\]]+)\]\([^)]+/category/[^)]+\)',
            # Match after navigation structure
            r'\n\[([^\]]+)\]\([^)]*category[^)]*\)\s*\n\s*\n\s*\[([^\]]+)\]',
        ]
        
        categories = []
        for pattern in breadcrumb_patterns:
            matches = re.findall(pattern, markdown)
            for match in matches:
                if isinstance(match, tuple):
                    # Take the last non-empty match
                    for cat in match:
                        if cat and not any(skip in cat.lower() for skip in ['home', 'หน้าแรก', 'category', 'หมวดหมู่']):
                            categories.append(cat.strip())
                else:
                    if match and not any(skip in match.lower() for skip in ['home', 'หน้าแรก', 'category', 'หมวดหมู่']):
                        categories.append(match.strip())
        
        # Return the most specific (last) category
        if categories:
            return categories[-1]
        
        # Fallback: Look for category in common patterns
        category_patterns = [
            r'หมวดหมู่[:\s]+([^\n]+)',
            r'ประเภท[:\s]+([^\n]+)',
            r'Category[:\s]+([^\n]+)',
            r'Type[:\s]+([^\n]+)'
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_description(self, markdown: str) -> Optional[str]:
        """Extract product description"""
        # Look for description sections
        desc_patterns = [
            r'รายละเอียดสินค้า[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'คุณสมบัติ[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'Product Description[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'Description[:\s]*\n(.*?)(?=\n#|\n\n#|$)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                # Clean up description
                desc = re.sub(r'\n+', ' ', desc)
                desc = re.sub(r'\s+', ' ', desc)
                return desc[:1000]  # Limit length
        
        return None
    
    def _extract_features(self, markdown: str) -> List[str]:
        """Extract product features"""
        features = []
        
        # Look for feature sections
        feature_sections = re.findall(
            r'(?:คุณสมบัติ|Features?|จุดเด่น).*?\n((?:[-•*]\s*[^\n]+\n?)+)',
            markdown,
            re.IGNORECASE | re.DOTALL
        )
        
        for section in feature_sections:
            lines = section.strip().split('\n')
            for line in lines:
                line = re.sub(r'^[-•*]\s*', '', line).strip()
                if line and len(line) > 5:
                    features.append(clean_text(line))
        
        return features[:10]  # Limit to 10 features
    
    def _extract_specifications(self, markdown: str) -> Dict[str, Any]:
        """Extract product specifications"""
        specs = {}
        
        # Look for spec tables or lists
        spec_patterns = [
            r'([^\n:]+)[:\s]+([^\n]+)',
            r'\|([^|]+)\|([^|]+)\|'
        ]
        
        # Common spec keywords
        spec_keywords = [
            'ขนาด', 'น้ำหนัก', 'สี', 'วัสดุ', 'รุ่น',
            'Size', 'Weight', 'Color', 'Material', 'Model',
            'Dimensions', 'Width', 'Height', 'Length'
        ]
        
        lines = markdown.split('\n')
        for line in lines:
            for keyword in spec_keywords:
                if keyword in line:
                    for pattern in spec_patterns:
                        match = re.search(pattern, line)
                        if match:
                            key = clean_text(match.group(1))
                            value = clean_text(match.group(2))
                            if key and value and len(key) < 50:
                                specs[key] = value
                            break
        
        return specs
    
    def _extract_availability(self, markdown: str) -> str:
        """Extract availability status"""
        # Thai Watsadu availability patterns
        in_stock_patterns = [
            r'มีสินค้า',
            r'พร้อมส่ง',
            r'In Stock',
            r'Available',
            r'มีของ'
        ]
        
        out_of_stock_patterns = [
            r'สินค้าหมด',
            r'ไม่มีสินค้า',
            r'Out of Stock',
            r'Unavailable',
            r'หมดชั่วคราว'
        ]
        
        markdown_lower = markdown.lower()
        
        for pattern in out_of_stock_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                return 'out_of_stock'
        
        for pattern in in_stock_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                return 'in_stock'
        
        return 'unknown'
    
    def _extract_images(self, firecrawl_result: Dict[str, Any]) -> List[str]:
        """Extract product images"""
        images = []
        
        # Get images from Firecrawl
        if 'images' in firecrawl_result:
            for img in firecrawl_result['images']:
                if isinstance(img, dict) and 'src' in img:
                    img_url = img['src']
                elif isinstance(img, str):
                    img_url = img
                else:
                    continue
                
                # Make absolute URL
                if not img_url.startswith('http'):
                    img_url = urljoin(self.base_url, img_url)
                
                # Filter out common non-product images
                skip_patterns = ['logo', 'banner', 'icon', 'loading', 'placeholder']
                if not any(pattern in img_url.lower() for pattern in skip_patterns):
                    images.append(img_url)
        
        return images[:10]  # Limit to 10 images
    
    def _map_to_unified_category(self, category: Optional[str]) -> str:
        """Map Thai Watsadu category to unified category"""
        if not category:
            return 'other'
        
        category_lower = category.lower()
        
        # Mapping based on Thai Watsadu's focus on construction
        mappings = {
            'construction': ['ก่อสร้าง', 'construction', 'building', 'วัสดุก่อสร้าง'],
            'tools': ['เครื่องมือ', 'tools', 'hardware', 'อุปกรณ์'],
            'electrical': ['ไฟฟ้า', 'electrical', 'electric', 'สายไฟ'],
            'plumbing': ['ประปา', 'plumbing', 'ท่อ', 'pipe'],
            'paint': ['สี', 'paint', 'ทาสี'],
            'flooring': ['พื้น', 'floor', 'กระเบื้อง', 'tile'],
            'roofing': ['หลังคา', 'roof', 'กระเบื้องหลังคา'],
            'doors_windows': ['ประตู', 'หน้าต่าง', 'door', 'window'],
            'safety': ['ความปลอดภัย', 'safety', 'security'],
            'garden': ['สวน', 'garden', 'outdoor']
        }
        
        for unified, keywords in mappings.items():
            if any(keyword in category_lower for keyword in keywords):
                return unified
        
        return 'hardware'  # Default for Thai Watsadu
    
    def _determine_monitoring_tier(self, price: Optional[Decimal]) -> str:
        """Determine monitoring tier based on price"""
        if not price:
            return 'standard'
        
        price_float = float(price)
        
        # Thai Watsadu focuses on construction materials
        # Generally lower margins but higher volumes
        if price_float > 8000:
            return 'ultra_critical'
        elif price_float > 2500:
            return 'high_value'
        elif price_float > 800:
            return 'standard'
        else:
            return 'low_priority'
    
    async def scrape_category(self, category_url: str, max_pages: int = 5, max_concurrent: int = 5) -> Dict[str, Any]:
        """Scrape all products from a category"""
        logger.info(f"Scraping Thai Watsadu category: {category_url}")
        
        print(f"\n🏪 Thai Watsadu Category Scraping")
        print(f"📂 Category URL: {category_url}")
        print(f"📄 Max pages to scan: {max_pages}")
        print(f"\n{'='*60}\n")
        
        # Initialize result dictionary
        result = {
            'category_url': category_url,
            'discovered': 0,
            'success': 0,
            'failed': 0
        }
        
        try:
            # Discover product URLs
            print("🔍 Phase 1: Discovering product URLs...")
            product_urls = await self._discover_product_urls(category_url, max_pages)
            result['discovered'] = len(product_urls)
            
            print(f"✅ Discovery complete! Found {len(product_urls)} products")
            logger.info(f"Found {len(product_urls)} product URLs")
            
            if not product_urls:
                print("⚠️  No product URLs discovered")
                logger.warning("No product URLs discovered")
                return result
            
            print(f"\n📦 Phase 2: Scraping {len(product_urls)} products...")
            print(f"{'─'*60}\n")
            
            # Scrape products with rate limiting
            from src.services.supabase_service import SupabaseService
            supabase = SupabaseService()
            
            for i, url in enumerate(product_urls, 1):
                print(f"\n[{i}/{len(product_urls)}] Processing: {url}")
                
                # Extra delay every 10 products
                if i > 1 and (i-1) % 10 == 0:
                    print(f"\n⏸️  Pause after 10 products (extra {self.retailer_config.rate_limit_delay}s delay)")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay * 2)
                
                try:
                    print(f"   🔍 Fetching product data...")
                    product = await self.scrape_product(url)
                    
                    if product:
                        print(f"   ✅ Product extracted: {product.name[:50]}...")
                        print(f"      SKU: {product.sku}")
                        
                        saved = await supabase.upsert_product(product)
                        if saved:
                            result['success'] += 1
                            print(f"   ✅ Saved to database!")
                        else:
                            result['failed'] += 1
                            print(f"   ❌ Failed to save")
                    else:
                        result['failed'] += 1
                        print(f"   ❌ Failed to extract product data")
                        
                except Exception as e:
                    logger.error(f"Error scraping product {url}: {str(e)}")
                    result['failed'] += 1
                    print(f"   ❌ Error: {str(e)}")
                
                # Progress update
                success_rate = (result['success'] / i * 100) if i > 0 else 0
                print(f"\n   Progress: {result['success']} success, {result['failed']} failed ({success_rate:.1f}% success rate)")
                
                # Rate limiting
                if i < len(product_urls):
                    print(f"   ⏳ Rate limit delay: {self.retailer_config.rate_limit_delay}s")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
            
            print(f"\n{'='*60}")
            print(f"✅ Category scraping completed!")
            print(f"   Total discovered: {result['discovered']}")
            print(f"   Successfully scraped: {result['success']}")
            print(f"   Failed: {result['failed']}")
            print(f"   Success rate: {(result['success']/result['discovered']*100):.1f}%" if result['discovered'] > 0 else "N/A")
            print(f"{'='*60}\n")
            
            logger.info(f"Successfully scraped {result['success']} products from {category_url}")
            
        except Exception as e:
            logger.error(f"Error scraping category {category_url}: {str(e)}")
            result['error'] = str(e)
            print(f"\n❌ Fatal error during category scraping: {str(e)}")
        
        return result
    
    async def scrape_batch(self, urls: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Scrape multiple products in batch
        
        Args:
            urls: List of product URLs
            max_concurrent: Maximum concurrent scrapes (not used for now, sequential processing)
            
        Returns:
            Results summary
        """
        result = {
            'total': len(urls),
            'success': 0,
            'failed': 0
        }
        
        print(f"\n🏪 Thai Watsadu Batch Scraping")
        print(f"📦 Products to scrape: {len(urls)}")
        print(f"⏱️  Rate limit delay: {self.retailer_config.rate_limit_delay}s between requests")
        print(f"\n{'='*60}\n")
        
        try:
            from src.services.supabase_service import SupabaseService
            supabase = SupabaseService()
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing: {url}")
                print(f"{'─'*50}")
                
                try:
                    print(f"   🔍 Fetching product data...")
                    product = await self.scrape_product(url)
                    
                    if product:
                        print(f"   ✅ Product extracted: {product.name}")
                        print(f"      SKU: {product.sku}")
                        print(f"      Price: ฿{product.current_price or 'N/A'}")
                        print(f"      Category: {product.category or 'N/A'}")
                        
                        print(f"   💾 Saving to database...")
                        saved = await supabase.upsert_product(product)
                        
                        if saved:
                            result['success'] += 1
                            print(f"   ✅ Successfully saved!")
                        else:
                            result['failed'] += 1
                            print(f"   ❌ Failed to save to database")
                    else:
                        result['failed'] += 1
                        print(f"   ❌ Failed to extract product data")
                        
                except Exception as e:
                    logger.error(f"Error scraping product {url}: {str(e)}")
                    result['failed'] += 1
                    print(f"   ❌ Error: {str(e)}")
                
                # Progress summary
                print(f"\n   Progress: Success: {result['success']}/{i} | Failed: {result['failed']}/{i}")
                
                # Rate limiting
                if i < len(urls):
                    print(f"   ⏳ Waiting {self.retailer_config.rate_limit_delay}s for rate limit...")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
            
            result['success_rate'] = (result['success'] / len(urls) * 100) if urls else 0
            
            print(f"\n{'='*60}")
            print(f"✅ Batch scraping completed!")
            print(f"   Success rate: {result['success_rate']:.1f}%")
            print(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Batch scrape error: {str(e)}")
            result['error'] = str(e)
            print(f"\n❌ Fatal error during batch scraping: {str(e)}")
        
        return result
    
    async def _discover_product_urls(self, category_url: str, max_pages: int) -> List[str]:
        """Discover product URLs from category pages"""
        product_urls = set()
        
        print(f"\n🔍 Discovering products from category pages...")
        print(f"   Max pages to scan: {max_pages}")
        
        for page in range(1, max_pages + 1):
            try:
                # Build page URL (Thai Watsadu uses query params)
                page_url = f"{category_url}?page={page}" if page > 1 else category_url
                
                print(f"\n   📄 Page {page}/{max_pages}: {page_url}")
                print(f"   🌐 Fetching page content...")
                
                result = await self.firecrawl.scrape(page_url)
                
                if not result:
                    print(f"   ❌ Failed to scrape page {page}")
                    logger.warning(f"Failed to scrape page {page}")
                    break
                
                # Extract product links
                links = result.get('linksOnPage', result.get('links', []))
                page_products = 0
                
                for link in links:
                    if isinstance(link, dict):
                        url = link.get('url', link.get('href', ''))
                    else:
                        url = str(link)
                    
                    # Thai Watsadu product URL patterns
                    if '/th/product/' in url or '/product/' in url:
                        if not url.startswith('http'):
                            url = urljoin(self.base_url, url)
                        product_urls.add(url)
                        page_products += 1
                
                print(f"   ✅ Found {page_products} products on this page")
                print(f"   📊 Total products discovered so far: {len(product_urls)}")
                logger.info(f"Found {page_products} products on page {page}")
                
                # Stop if no products found
                if page_products == 0:
                    print(f"   ⚠️  No products found on page {page}, stopping discovery")
                    break
                
                # Rate limiting between pages
                if page < max_pages:
                    print(f"   ⏳ Rate limit delay: {self.retailer_config.rate_limit_delay}s")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay)
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {str(e)}")
                logger.error(f"Error discovering products on page {page}: {str(e)}")
                break
        
        print(f"\n✅ Discovery complete! Total unique products found: {len(product_urls)}")
        return list(product_urls)