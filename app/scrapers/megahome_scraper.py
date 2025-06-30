"""
MegaHome product scraper implementation
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


class MegaHomeScraper:
    """Scraper for MegaHome products"""
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self.retailer_config = retailer_manager.get_retailer(RetailerType.MEGAHOME)
        self.base_url = self.retailer_config.base_url
        
    async def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape a single MegaHome product"""
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
            logger.error(f"Error scraping MegaHome product {url}: {str(e)}")
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
        # MegaHome patterns: /product/123456 or /p/SKU123 or ?sku=123456
        url_patterns = [
            r'/product/([A-Z0-9\-]+)',
            r'/p/([A-Z0-9\-]+)',
            r'/pd/([A-Z0-9\-]+)',
            r'[?&]sku=([A-Z0-9\-]+)',
            r'/item/([A-Z0-9\-]+)',
            r'/([A-Z0-9]{5,})',  # 5+ character alphanumeric code in URL
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to find SKU in content
        sku_patterns = [
            r'รหัสสินค้า[:\s]+([A-Z0-9\-]+)',
            r'Product Code[:\s]+([A-Z0-9\-]+)',
            r'SKU[:\s]+([A-Z0-9\-]+)',
            r'Item #([A-Z0-9\-]+)',
            r'รหัส[:\s]+([A-Z0-9\-]+)',
            r'Code[:\s]+([A-Z0-9\-]+)',
            r'#([A-Z0-9]{5,})'  # Look for hash followed by alphanumeric code
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generate SKU from URL
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if parts:
            # Extract any alphanumeric codes from the last part
            codes = re.findall(r'[A-Z0-9]{5,}', parts[-1], re.IGNORECASE)
            if codes:
                return f"MH-{codes[0]}"
            return f"MH-{parts[-1][:20]}"
        
        return None
    
    def _extract_product_name(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract product name"""
        # Try metadata first
        if metadata.get('title'):
            # Clean up title - remove site name and price
            title = metadata['title']
            title = re.sub(r'\s*\|.*$', '', title)  # Remove everything after |
            title = re.sub(r'\s*-\s*MegaHome.*$', '', title, re.IGNORECASE)
            title = re.sub(r'\s*-\s*เมกาโฮม.*$', '', title)  # Thai name
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
        
        # Price patterns for MegaHome
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
            r'ราคาขาย[:\s]+([0-9,]+)',
            r'ราคาสมาชิก[:\s]+([0-9,]+)',  # Member price
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
            r'จาก[:\s]+([0-9,]+)',  # From price
            r'ราคาทั่วไป[:\s]+([0-9,]+)',  # General price
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
            r'จาก[:\s]+([^\n]+)',  # From brand
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                # Clean up brand name
                brand = re.sub(r'\([^)]+\)', '', brand).strip()
                return brand
        
        # Try to extract from product name
        # MegaHome often has brand at the beginning
        words = product_name.split()
        if words and words[0].isupper() and len(words[0]) > 2:
            # Check if it's likely a brand (not a common word)
            common_words = ['THE', 'NEW', 'SET', 'ชุด', 'เซต', 'อุปกรณ์', 'เครื่อง', 'โต๊ะ', 'เก้าอี้']
            if words[0] not in common_words:
                # Common brands at MegaHome
                known_brands = ['SAMSUNG', 'LG', 'PANASONIC', 'SHARP', 'HITACHI', 'MITSUBISHI', 'DAIKIN', 'CARRIER']
                if words[0] in known_brands or len(words[0]) >= 3:
                    return words[0]
        
        return None
    
    def _extract_category(self, markdown: str, metadata: Dict) -> Optional[str]:
        """Extract category information"""
        # Try breadcrumbs first
        breadcrumb_patterns = [
            r'หน้าแรก\s*[>»]\s*([^>»\n]+)\s*[>»]',
            r'Home\s*[>»]\s*([^>»\n]+)\s*[>»]',
            r'›\s*([^›\n]+)\s*›',
            r'MegaHome\s*[>»]\s*([^>»\n]+)',
            r'เมกาโฮม\s*[>»]\s*([^>»\n]+)',
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
            r'ชนิด[:\s]+([^\n]+)',  # Type
            r'แผนก[:\s]+([^\n]+)',  # Department
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
            r'รายละเอียด[:\s]*\n(.*?)(?=\n#|\n\n#|$)',
            r'ภาพรวม[:\s]*\n(.*?)(?=\n#|\n\n#|$)',  # Overview
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
            r'(?:คุณสมบัติ|Features?|จุดเด่น|ข้อดี|ประโยชน์|คุณลักษณะ|ฟีเจอร์).*?\n((?:[-•*✓]?\s*[^-•*✓\n][^\n]+\n?)+)',
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
        
        # Common spec keywords for MegaHome (electronics & appliances)
        spec_keywords = [
            'ขนาด', 'น้ำหนัก', 'สี', 'วัสดุ', 'รุ่น', 'กำลังไฟ', 'แรงดัน', 'ความจุ',
            'Size', 'Weight', 'Color', 'Material', 'Model', 'Power', 'Voltage', 'Capacity',
            'Dimensions', 'Width', 'Height', 'Length', 'Depth', 'Energy',
            'ความกว้าง', 'ความยาว', 'ความสูง', 'ความลึก', 'พลังงาน', 'ประสิทธิภาพ',
            'การใช้งาน', 'Usage', 'Application', 'ฟังก์ชั่น', 'Function',
            'รับประกัน', 'Warranty', 'การติดตั้ง', 'Installation',
            'ระบบ', 'System', 'เทคโนโลยี', 'Technology',
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
        # MegaHome availability patterns
        in_stock_patterns = [
            r'มีสินค้า',
            r'พร้อมส่ง',
            r'In Stock',
            r'Available',
            r'มีของ',
            r'สินค้าพร้อมจำหน่าย',
            r'มีสินค้าในสต็อก',
            r'จัดส่งได้ทันที',
            r'พร้อมจัดส่ง',
        ]
        
        out_of_stock_patterns = [
            r'สินค้าหมด',
            r'ไม่มีสินค้า',
            r'Out of Stock',
            r'Unavailable',
            r'หมดชั่วคราว',
            r'สินค้าหมดชั่วคราว',
            r'สั่งจอง',
            r'Pre-order',
            r'สั่งผลิต',  # Made to order
            r'รอสินค้า',  # Waiting for stock
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
        branch_patterns = [
            r'สาขา.*มี\s*\d+',
            r'มีจำหน่ายที่สาขา',
            r'สต็อกสาขา',
        ]
        
        for pattern in branch_patterns:
            if re.search(pattern, markdown):
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
                skip_patterns = ['logo', 'banner', 'icon', 'loading', 'placeholder', 'payment', 'delivery', 'brand-logo', 'social', 'promotion']
                if not any(pattern in img_url.lower() for pattern in skip_patterns):
                    # MegaHome specific: look for product images
                    if any(pattern in img_url for pattern in ['/product/', '/p/', '/item/', 'product-', '/media/', '/catalog/', '/uploads/']):
                        images.append(img_url)
        
        return images[:10]  # Limit to 10 images
    
    def _map_to_unified_category(self, category: Optional[str]) -> str:
        """Map MegaHome category to unified category"""
        if not category:
            return 'other'
        
        category_lower = category.lower()
        
        # Mapping based on MegaHome's focus on electronics & appliances
        mappings = {
            'appliances': ['เครื่องใช้ไฟฟ้า', 'appliances', 'electrical', 'เครื่องใช้', 'เครื่องไฟฟ้า'],
            'kitchen': ['ครัว', 'kitchen', 'เครื่องครัว', 'อุปกรณ์ครัว'],
            'electronics': ['อิเล็กทรอนิกส์', 'electronics', 'เครื่องเสียง', 'ทีวี', 'audio', 'tv'],
            'furniture': ['เฟอร์นิเจอร์', 'furniture', 'โซฟา', 'เตียง', 'โต๊ะ', 'เก้าอี้', 'ตู้'],
            'lighting': ['โคมไฟ', 'lighting', 'หลอดไฟ', 'ไฟ', 'light'],
            'bathroom': ['ห้องน้ำ', 'bathroom', 'สุขภัณฑ์', 'อ่างล้างหน้า'],
            'bedroom': ['ห้องนอน', 'bedroom', 'ที่นอน', 'หมอน', 'ผ้าปู'],
            'living': ['ห้องนั่งเล่น', 'living', 'รับแขก', 'โฮมเธียเตอร์'],
            'office': ['สำนักงาน', 'office', 'ทำงาน', 'คอมพิวเตอร์', 'computer'],
            'cooling': ['ทำความเย็น', 'cooling', 'แอร์', 'พัดลม', 'air', 'fan', 'เครื่องปรับอากาศ'],
            'cleaning': ['ทำความสะอาด', 'cleaning', 'เครื่องซักผ้า', 'เครื่องดูดฝุ่น', 'washer', 'vacuum'],
            'tools': ['เครื่องมือ', 'tools', 'อุปกรณ์ช่าง', 'hardware'],
        }
        
        for unified, keywords in mappings.items():
            if any(keyword in category_lower for keyword in keywords):
                return unified
        
        return 'appliances'  # Default for MegaHome (electronics/appliances focus)
    
    def _determine_monitoring_tier(self, price: Optional[Decimal]) -> str:
        """Determine monitoring tier based on price"""
        if not price:
            return 'standard'
        
        price_float = float(price)
        
        # MegaHome focuses on electronics and appliances
        # Wide range of pricing from small to large appliances
        if price_float > 30000:
            return 'ultra_critical'
        elif price_float > 10000:
            return 'high_value'
        elif price_float > 2000:
            return 'standard'
        else:
            return 'low_priority'
    
    async def scrape_category(self, category_url: str, max_pages: int = 5) -> List[Product]:
        """Scrape all products from a category"""
        products = []
        
        try:
            logger.info(f"Scraping MegaHome category: {category_url}")
            
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
                # Build page URL (MegaHome uses different pagination patterns)
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
                    
                    # MegaHome product URL patterns
                    if any(pattern in url for pattern in ['/product/', '/p/', '/pd/', '/item/', '/goods/']):
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