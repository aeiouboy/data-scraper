"""
DoHome product scraper implementation
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


class DoHomeScraper:
    """Scraper for DoHome products"""
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.retailer_config = retailer_manager.get_retailer(RetailerType.DOHOME)
        self.base_url = self.retailer_config.base_url
        
    async def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single DoHome product"""
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
            logger.error(f"Error scraping DoHome product {url}: {str(e)}")
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
        # DoHome patterns: /product/123456 or /p/123456 or ?sku=123456
        url_patterns = [
            r'/product/(\d+)',
            r'/p/(\d+)',
            r'/pd/(\d+)',
            r'[?&]sku=(\d+)',
            r'/(\d{6,})',  # 6+ digit number in URL
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to find SKU in content
        sku_patterns = [
            r'รหัสสินค้า[:\s]+(\d+)',
            r'Product Code[:\s]+(\d+)',
            r'SKU[:\s]+(\d+)',
            r'Item #(\d+)',
            r'รหัส[:\s]+(\d+)',
            r'#(\d{6,})'  # Look for hash followed by 6+ digit code
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generate SKU from URL
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if parts:
            # Extract any numbers from the last part
            numbers = re.findall(r'\d+', parts[-1])
            if numbers:
                return f"DH-{numbers[0]}"
            return f"DH-{parts[-1][:20]}"
        
        return None
    
    def _extract_product_name(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract product name"""
        # Try metadata first
        if metadata.get('title'):
            # Clean up title - remove site name and price
            title = metadata['title']
            title = re.sub(r'\s*\|.*$', '', title)  # Remove everything after |
            title = re.sub(r'\s*-\s*DoHome.*$', '', title, re.IGNORECASE)
            title = re.sub(r'\s*ราคา.*$', '', title)  # Remove price info
            title = re.sub(r'\s*\d+\s*บาท.*$', '', title)  # Remove price
            return title.strip()
        
        # Try to find product name in markdown
        # Look for H1 headers first
        h1_match = re.search(r'^#\s+([^#\n]+)', markdown, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Look for product name patterns
        name_patterns = [
            r'ชื่อสินค้า[:\s]+([^\n]+)',
            r'Product Name[:\s]+([^\n]+)',
            r'สินค้า[:\s]+([^\n]+)',
            r'^([^\n]+?)(?:\s*ราคา|\s*฿|\s*\d+\s*บาท)'  # Name before price
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_prices(self, markdown: str, html: str) -> Dict[str, Optional[Decimal]]:
        """Extract current and original prices"""
        prices = {'current': None, 'original': None}
        
        # Price patterns for DoHome
        price_patterns = [
            r'฿\s*([0-9,]+(?:\.\d{2})?)',
            r'THB\s*([0-9,]+(?:\.\d{2})?)',
            r'ราคา[:\s]+([0-9,]+(?:\.\d{2})?)',
            r'Price[:\s]+([0-9,]+(?:\.\d{2})?)',
            r'([0-9,]+(?:\.\d{2})?)\s*บาท',
            r'ขาย[:\s]+([0-9,]+)',  # Sale price
            r'ปกติ[:\s]+([0-9,]+)',  # Regular price
        ]
        
        # Find all price matches
        all_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, markdown)
            for match in matches:
                price = extract_number_from_string(match)
                if price and price > 0:
                    all_prices.append(price)
        
        # Look for specific sale/original price patterns
        sale_patterns = [
            r'ราคาพิเศษ[:\s]+([0-9,]+)',
            r'ราคาโปรโมชั่น[:\s]+([0-9,]+)',
            r'Sale Price[:\s]+([0-9,]+)',
            r'ลด[:\s]+([0-9,]+)',
        ]
        
        for pattern in sale_patterns:
            match = re.search(pattern, markdown)
            if match:
                prices['current'] = Decimal(str(extract_number_from_string(match.group(1))))
                break
        
        orig_patterns = [
            r'ราคาปกติ[:\s]+([0-9,]+)',
            r'ราคาเดิม[:\s]+([0-9,]+)',
            r'Regular Price[:\s]+([0-9,]+)',
            r'Was[:\s]+([0-9,]+)',
        ]
        
        for pattern in orig_patterns:
            match = re.search(pattern, markdown)
            if match:
                prices['original'] = Decimal(str(extract_number_from_string(match.group(1))))
                break
        
        # If we didn't find specific prices, use logic
        if not prices['current'] and all_prices:
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
            r'ผู้ผลิต[:\s]+([^\n]+)',
            r'Manufacturer[:\s]+([^\n]+)',
            r'โดย[:\s]+([^\n]+)',
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                # Clean up brand name
                brand = re.sub(r'\([^)]+\)', '', brand).strip()
                return brand
        
        # Try to extract from product name
        # DoHome often has brand at the beginning
        words = product_name.split()
        if words and words[0].isupper() and len(words[0]) > 2:
            # Check if it's likely a brand (not a common word)
            common_words = ['THE', 'NEW', 'SET', 'ชุด', 'เซต', 'อุปกรณ์']
            if words[0] not in common_words:
                return words[0]
        
        return None
    
    def _extract_category(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract category information"""
        # Try breadcrumbs first
        breadcrumb_patterns = [
            r'หน้าแรก\s*[>»]\s*([^>»\n]+)\s*[>»]',
            r'Home\s*[>»]\s*([^>»\n]+)\s*[>»]',
            r'›\s*([^›\n]+)\s*›',
            r'DoHome\s*[>»]\s*([^>»\n]+)',
        ]
        
        for pattern in breadcrumb_patterns:
            matches = re.findall(pattern, markdown)
            if matches and len(matches) > 0:
                # Return the first category after home
                return matches[0].strip()
        
        # Category patterns
        category_patterns = [
            r'หมวดหมู่[:\s]+([^\n]+)',
            r'ประเภท[:\s]+([^\n]+)',
            r'Category[:\s]+([^\n]+)',
            r'กลุ่มสินค้า[:\s]+([^\n]+)',
            r'ประเภทสินค้า[:\s]+([^\n]+)',
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
            r'Description[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'ข้อมูลสินค้า[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'คำอธิบาย[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
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
            r'(?:คุณสมบัติ|Features?|จุดเด่น|ข้อดี|ประโยชน์).*?\n((?:[-•*✓]?\s*[^-•*✓\n][^\n]+\n?)+)',
            markdown,
            re.IGNORECASE | re.DOTALL
        )
        
        for section in feature_sections:
            lines = section.strip().split('\n')
            for line in lines:
                # Clean up bullet points
                line = re.sub(r'^[-•*✓]\s*', '', line).strip()
                if line and len(line) > 5 and not line.startswith('ราคา'):
                    features.append(clean_text(line))
        
        # Remove duplicates and limit
        features = list(dict.fromkeys(features))[:10]
        
        return features
    
    def _extract_specifications(self, markdown: str) -> Dict[str, Any]:
        """Extract product specifications"""
        specs = {}
        
        # Look for spec tables or lists
        spec_patterns = [
            r'([^:\n]+)[:\s]+([^:\n]+?)(?=\n|$)',
            r'\|([^|]+)\|([^|]+)\|',
        ]
        
        # Common spec keywords for DoHome (hardware store focus)
        spec_keywords = [
            'ขนาด', 'น้ำหนัก', 'สี', 'วัสดุ', 'รุ่น', 'กำลังไฟ', 'แรงดัน',
            'Size', 'Weight', 'Color', 'Material', 'Model', 'Power', 'Voltage',
            'Dimensions', 'Width', 'Height', 'Length', 'Depth', 'Diameter',
            'ความจุ', 'Capacity', 'ความหนา', 'Thickness', 'ยาว', 'กว้าง', 'สูง',
            'จำนวน', 'Quantity', 'ประเภท', 'Type', 'รูปแบบ', 'Style',
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
                                # Skip if it's a price or category
                                if not any(skip in key.lower() for skip in ['ราคา', 'price', 'หมวด', 'category']):
                                    specs[key] = value
                            break
        
        return specs
    
    def _extract_availability(self, markdown: str) -> str:
        """Extract availability status"""
        # DoHome availability patterns
        in_stock_patterns = [
            r'มีสินค้า',
            r'พร้อมส่ง',
            r'In Stock',
            r'Available',
            r'มีของ',
            r'สินค้าพร้อมจำหน่าย',
            r'มีสินค้าในสต็อก',
        ]
        
        out_of_stock_patterns = [
            r'สินค้าหมด',
            r'ไม่มีสินค้า',
            r'Out of Stock',
            r'Unavailable',
            r'หมดชั่วคราว',
            r'สินค้าหมดชั่วคราว',
            r'สั่งจอง',
        ]
        
        markdown_lower = markdown.lower()
        
        for pattern in out_of_stock_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                return 'out_of_stock'
        
        for pattern in in_stock_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                return 'in_stock'
        
        # Check for quantity indicators
        qty_match = re.search(r'จำนวน[:\s]*(\d+)', markdown)
        if qty_match and int(qty_match.group(1)) > 0:
            return 'in_stock'
        
        # Check for stock in branches
        branch_match = re.search(r'สาขา.*มี\s*\d+', markdown)
        if branch_match:
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
                skip_patterns = ['logo', 'banner', 'icon', 'loading', 'placeholder', 'payment', 'delivery', 'brand-logo']
                if not any(pattern in img_url.lower() for pattern in skip_patterns):
                    # DoHome specific: look for product images
                    if any(pattern in img_url for pattern in ['/product/', '/p/', '/item/', 'product-', '/uploads/']):
                        images.append(img_url)
        
        return images[:10]  # Limit to 10 images
    
    def _map_to_unified_category(self, category: Optional[str]) -> str:
        """Map DoHome category to unified category"""
        if not category:
            return 'other'
        
        category_lower = category.lower()
        
        # Mapping based on DoHome's focus on hardware and DIY
        mappings = {
            'tools': ['เครื่องมือ', 'tools', 'hardware', 'ฮาร์ดแวร์', 'อุปกรณ์ช่าง'],
            'electrical': ['ไฟฟ้า', 'electrical', 'electric', 'สายไฟ', 'หลอดไฟ', 'ปลั๊ก'],
            'plumbing': ['ประปา', 'plumbing', 'ท่อ', 'ก๊อกน้ำ', 'วาล์ว'],
            'paint': ['สี', 'paint', 'ทาสี', 'แปรง', 'ลูกกลิ้ง'],
            'construction': ['ก่อสร้าง', 'construction', 'building', 'ปูน', 'อิฐ', 'หิน', 'ทราย'],
            'garden': ['สวน', 'garden', 'ต้นไม้', 'ดิน', 'ปุ๋ย'],
            'automotive': ['ยานยนต์', 'automotive', 'รถยนต์', 'รถ', 'น้ำมันเครื่อง'],
            'safety': ['ความปลอดภัย', 'safety', 'อุปกรณ์นิรภัย', 'ถุงมือ', 'หน้ากาก'],
            'storage': ['จัดเก็บ', 'storage', 'ชั้นวาง', 'กล่อง', 'ตู้'],
            'bathroom': ['ห้องน้ำ', 'bathroom', 'สุขภัณฑ์', 'อ่างล้างหน้า'],
            'kitchen': ['ครัว', 'kitchen', 'เครื่องครัว', 'อ่างล้างจาน'],
            'flooring': ['พื้น', 'floor', 'กระเบื้อง', 'ไม้พื้น', 'พรม'],
        }
        
        for unified, keywords in mappings.items():
            if any(keyword in category_lower for keyword in keywords):
                return unified
        
        return 'tools'  # Default for DoHome (hardware store)
    
    def _determine_monitoring_tier(self, price: Optional[Decimal]) -> str:
        """Determine monitoring tier based on price"""
        if not price:
            return 'standard'
        
        price_float = float(price)
        
        # DoHome focuses on hardware and tools
        # Generally lower-priced items
        if price_float > 10000:
            return 'ultra_critical'
        elif price_float > 3000:
            return 'high_value'
        elif price_float > 500:
            return 'standard'
        else:
            return 'low_priority'
    
    async def scrape_category(self, category_url: str, max_pages: int = 5) -> List[Product]:
        """Scrape all products from a category"""
        products = []
        
        try:
            logger.info(f"Scraping DoHome category: {category_url}")
            
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
                # Build page URL (DoHome uses different pagination patterns)
                if '?' in category_url:
                    page_url = f"{category_url}&page={page}"
                else:
                    page_url = f"{category_url}?page={page}"
                
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
                    
                    # DoHome product URL patterns
                    if any(pattern in url for pattern in ['/product/', '/p/', '/pd/', '/item/']):
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