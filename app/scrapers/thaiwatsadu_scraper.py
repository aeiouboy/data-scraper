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

from app.models.product import Product
from app.services.firecrawl_client import FirecrawlClient
from app.config.retailers import retailer_manager, RetailerType
from app.utils.text_cleaner import clean_text, extract_number_from_string
from app.utils.url_validator import is_valid_product_url

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
        # Try to extract from URL first
        url_match = re.search(r'/p/([A-Z0-9\-]+)', url)
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
        # Try metadata first
        if metadata.get('title'):
            # Clean up title - remove site name
            title = metadata['title']
            title = re.sub(r'\s*\|\s*Thai Watsadu.*$', '', title)
            title = re.sub(r'\s*-\s*Thai Watsadu.*$', '', title)
            return title.strip()
        
        # Try to find in markdown
        lines = markdown.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # Skip if it looks like navigation
                if any(skip in line.lower() for skip in ['home', 'category', 'menu', 'search']):
                    continue
                return line
        
        return None
    
    def _extract_prices(self, markdown: str, html: str) -> Dict[str, Optional[Decimal]]:
        """Extract current and original prices"""
        prices = {'current': None, 'original': None}
        
        # Price patterns for Thai Watsadu
        price_patterns = [
            r'฿\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'THB\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'ราคา[:\s]+([0-9,]+(?:\.[0-9]{2})?)',
            r'Price[:\s]+([0-9,]+(?:\.[0-9]{2})?)'
        ]
        
        # Find all price matches
        all_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, markdown)
            for match in matches:
                price = extract_number_from_string(match)
                if price and price > 0:
                    all_prices.append(price)
        
        # Logic: highest price is original, lowest is current (for sales)
        if all_prices:
            all_prices = sorted(set(all_prices))
            prices['current'] = Decimal(str(all_prices[0]))
            if len(all_prices) > 1:
                prices['original'] = Decimal(str(all_prices[-1]))
        
        return prices
    
    def _extract_brand(self, markdown: str, product_name: str) -> Optional[str]:
        """Extract brand from content"""
        # Common patterns
        brand_patterns = [
            r'ยี่ห้อ[:\s]+([^\n]+)',
            r'แบรนด์[:\s]+([^\n]+)',
            r'Brand[:\s]+([^\n]+)',
            r'Manufacturer[:\s]+([^\n]+)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try to extract from product name
        # Thai Watsadu often has brand at the beginning
        words = product_name.split()
        if words and words[0].isupper():
            return words[0]
        
        return None
    
    def _extract_category(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract category information"""
        # Try breadcrumbs first
        breadcrumb_match = re.search(r'Home\s*[>»]\s*([^>»\n]+)', markdown)
        if breadcrumb_match:
            return breadcrumb_match.group(1).strip()
        
        # Category patterns
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
    
    async def scrape_category(self, category_url: str, max_pages: int = 5) -> List[Product]:
        """Scrape all products from a category"""
        products = []
        
        try:
            logger.info(f"Scraping Thai Watsadu category: {category_url}")
            
            # Discover product URLs
            product_urls = await self._discover_product_urls(category_url, max_pages)
            logger.info(f"Found {len(product_urls)} product URLs")
            
            # Scrape products with rate limiting
            for i, url in enumerate(product_urls):
                if i > 0 and i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(product_urls)} products scraped")
                    await asyncio.sleep(self.retailer_config.rate_limit_delay * 2)
                
                product = await self.scrape_product(url)
                if product:
                    products.append(product)
                
                # Rate limiting
                await asyncio.sleep(self.retailer_config.rate_limit_delay)
            
            logger.info(f"Successfully scraped {len(products)} products from {category_url}")
            
        except Exception as e:
            logger.error(f"Error scraping category {category_url}: {str(e)}")
        
        return products
    
    async def _discover_product_urls(self, category_url: str, max_pages: int) -> List[str]:
        """Discover product URLs from category pages"""
        product_urls = set()
        
        for page in range(1, max_pages + 1):
            try:
                # Build page URL (Thai Watsadu uses query params)
                page_url = f"{category_url}?page={page}" if page > 1 else category_url
                
                result = await self.firecrawl.scrape(page_url)
                
                if not result:
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
                    if '/p/' in url or '/product/' in url:
                        if not url.startswith('http'):
                            url = urljoin(self.base_url, url)
                        product_urls.add(url)
                        page_products += 1
                
                logger.info(f"Found {page_products} products on page {page}")
                
                # Stop if no products found
                if page_products == 0:
                    break
                
                # Rate limiting between pages
                await asyncio.sleep(self.retailer_config.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Error discovering products on page {page}: {str(e)}")
                break
        
        return list(product_urls)