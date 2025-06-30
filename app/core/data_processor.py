"""
Data processing and validation pipeline
"""
import re
from typing import Dict, Any, Optional, List
from decimal import Decimal
import logging
from app.models.product import Product

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate scraped data"""
    
    @staticmethod
    def extract_price(price_text: Any) -> Optional[Decimal]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Handle non-string types
        if isinstance(price_text, (list, dict)):
            return None
        
        if isinstance(price_text, (int, float)):
            if price_text <= 0:
                return None
            try:
                return Decimal(str(price_text))
            except (ValueError, TypeError, ArithmeticError):
                return None
            
        # Convert to string and check if it looks like a price
        price_str = str(price_text).strip()
        
        # If it's just letters or obviously not a price, return None
        if re.match(r'^[a-zA-Z]+$', price_str):
            return None
        
        # Remove Thai baht symbol, commas, spaces
        cleaned_price = re.sub(r'[฿,\s]', '', price_str)
        # Remove "บาท" (baht in Thai)
        cleaned_price = re.sub(r'บาท', '', cleaned_price)
        
        # Extract first number pattern that looks like a price
        match = re.search(r'(\d+(?:\.\d{1,2})?)', cleaned_price)
        if match:
            try:
                decimal_price = Decimal(match.group(1))
                if decimal_price > 0:  # Only positive prices are valid
                    return decimal_price
            except (ValueError, TypeError, ArithmeticError):
                return None
        return None
    
    @staticmethod
    def clean_text(text: Any) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Convert to string and strip whitespace
        text = str(text).strip()
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @staticmethod
    def extract_sku(text: Any) -> Optional[str]:
        """Extract SKU/product code"""
        if not text:
            return None
            
        text = str(text)
        # Look for common SKU patterns
        # Example: 1000012345, SKU-12345, PROD_12345
        patterns = [
            r'(?:SKU|รหัส|Code)[\s:-]*([A-Z0-9-]+)',
            r'\b(\d{10})\b',  # 10-digit code
            r'\b([A-Z]{2,5}-?\d{4,})\b'  # Letter-number combination
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    @staticmethod
    def process_images(images: Any) -> List[str]:
        """Process and validate image URLs"""
        if not images:
            return []
        
        # Handle different input types
        if isinstance(images, str):
            images = [images]
        elif not isinstance(images, list):
            return []
        
        valid_images = []
        for img in images:
            if not img:
                continue
                
            img_url = str(img).strip()
            # Basic URL validation
            if img_url.startswith(('http://', 'https://', '//')):
                # Fix protocol-relative URLs
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                valid_images.append(img_url)
        
        return valid_images
    
    @staticmethod
    def determine_availability(text: Any) -> str:
        """Determine product availability from text"""
        if not text:
            return "unknown"
        
        text = str(text).lower()
        
        # Thai and English availability patterns
        in_stock_patterns = [
            'in stock', 'available', 'มีสินค้า', 'พร้อมส่ง',
            'ready', 'in-stock', 'สินค้าพร้อม'
        ]
        
        out_of_stock_patterns = [
            'out of stock', 'unavailable', 'หมด', 'สินค้าหมด',
            'sold out', 'ไม่มีสินค้า', 'out-of-stock', 'currently unavailable'
        ]
        
        for pattern in in_stock_patterns:
            if pattern in text:
                return "in_stock"
        
        for pattern in out_of_stock_patterns:
            if pattern in text:
                return "out_of_stock"
        
        return "unknown"
    
    def _extract_category(self, url: str, markdown: str, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract category from URL path, markdown, or raw data"""
        # Try raw data first
        category = raw_data.get('category')
        if category:
            return self.clean_text(category)
        
        # Extract from URL path (e.g., homepro.co.th/c/LIG -> Lighting)
        url_match = re.search(r'/c/([A-Z]{3})', url)
        if url_match:
            category_code = url_match.group(1)
            # Map category codes to readable names
            category_mapping = {
                'LIG': 'โคมไฟและหลอดไฟ',
                'PAI': 'สีและอุปกรณ์ทาสี', 
                'BAT': 'ห้องน้ำ',
                'PLU': 'งานระบบประปา',
                'KIT': 'ห้องครัวและอุปกรณ์',
                'SMA': 'เครื่องใช้ไฟฟ้าขนาดเล็ก',
                'HHP': 'จัดเก็บและของใช้ในบ้าน',
                'TVA': 'ทีวี เครื่องเสียง เกม',
                'FLO': 'วัสดุปูพื้นและผนัง',
                'FUR': 'เฟอร์นิเจอร์และของแต่งบ้าน',
                'APP': 'เครื่องใช้ไฟฟ้า',
                'CON': 'วัสดุก่อสร้าง',
                'ELT': 'ระบบไฟฟ้าและความปลอดภัย',
                'DOW': 'ประตูและหน้าต่าง',
                'TOO': 'เครื่องมือและฮาร์ดแวร์',
                'OUT': 'เฟอร์นิเจอร์นอกบ้านและสวน',
                'BED': 'ห้องนอนและเครื่องนอน',
                'SPO': 'กีฬาและการเดินทาง',
                'BEA': 'ความงามและดูแลตัว',
                'MOM': 'แม่และเด็ก',
                'HEA': 'สุขภาพ',
                'PET': 'อุปกรณ์สัตว์เลี้ยง',
                'ATM': 'ยานยนต์'
            }
            return category_mapping.get(category_code, category_code)
        
        # Try to extract from markdown breadcrumbs
        if markdown:
            # Look for breadcrumb pattern
            breadcrumb_match = re.search(r'หน้าแรก\s*>\s*([^>]+)', markdown)
            if breadcrumb_match:
                return self.clean_text(breadcrumb_match.group(1))
            
            # Look for category in title or headings
            category_patterns = [
                r'หมวดหมู่[:\s]*([^\n]+)',
                r'Category[:\s]*([^\n]+)',
                r'ประเภทสินค้า[:\s]*([^\n]+)'
            ]
            
            for pattern in category_patterns:
                match = re.search(pattern, markdown, re.IGNORECASE)
                if match:
                    return self.clean_text(match.group(1))
        
        return None
    
    def _extract_availability(self, markdown: str, raw_data: Dict[str, Any]) -> str:
        """Extract availability status from markdown or raw data"""
        # Check raw data first
        availability = raw_data.get('availability') or raw_data.get('stock_status')
        if availability:
            return self.determine_availability(availability)
        
        # Check markdown for Thai availability indicators
        if markdown:
            # Look for stock status patterns in Thai
            if re.search(r'มีสินค้า|พร้อมส่ง|สินค้าพร้อม|In Stock', markdown, re.IGNORECASE):
                return "in_stock"
            elif re.search(r'หมดสต็อก|สินค้าหมด|หมด|Out of Stock|ไม่มีสินค้า', markdown, re.IGNORECASE):
                return "out_of_stock"
            elif re.search(r'สั่งซื้อได้|สั่งล่วงหน้า|Pre-order|Backorder', markdown, re.IGNORECASE):
                return "preorder"
            elif re.search(r'ใกล้หมด|Limited Stock|จำนวนจำกัด', markdown, re.IGNORECASE):
                return "limited_stock"
        
        return "unknown"
    
    def process_product_data(self, raw_data: Dict[str, Any], url: str) -> Optional[Product]:
        """
        Process raw scraped data into Product model
        
        Args:
            raw_data: Raw data from Firecrawl
            url: Product URL
            
        Returns:
            Validated Product or None if invalid
        """
        try:
            # Get metadata if available
            metadata = raw_data.get('metadata', {})
            markdown = raw_data.get('markdown', '')
            
            # Extract product name from metadata first, then markdown
            name = metadata.get('title', '').strip()
            if not name and markdown:
                # Try to find product title in markdown
                # Look for patterns like "# Product Name" or product name patterns
                lines = markdown.split('\n')
                for line in lines:
                    if line.startswith('# ') and 'เครื่อง' in line:  # Common Thai product prefix
                        name = self.clean_text(line[2:])
                        break
                    elif 'ชื่อสินค้า' in line or 'Product Name' in line:
                        # Extract from next line or same line
                        parts = line.split(':')
                        if len(parts) > 1:
                            name = self.clean_text(parts[1])
                        break
            
            if not name:
                # Try metadata description
                desc = metadata.get('description', '')
                if desc and ',' in desc:
                    # Format often: "Product Name, Brand, SKU"
                    name = desc.split(',')[0].strip()
            
            if not name:
                logger.warning(f"No product name found for {url}")
                return None
            
            # Extract SKU - HomePro uses product ID in URL
            sku = None
            # Try to extract from URL first (e.g., /p/1243357)
            url_match = re.search(r'/p/(\d+)', url)
            if url_match:
                sku = url_match.group(1)
            
            if not sku:
                # Try metadata or markdown
                sku = self.extract_sku(metadata.get('description', ''))
                if not sku and markdown:
                    sku = self.extract_sku(markdown)
            
            if not sku:
                # Generate SKU from URL hash
                import hashlib
                sku = f"HP-{hashlib.md5(url.encode()).hexdigest()[:8].upper()}"
            
            # Process prices - look in markdown for Thai Baht prices
            current_price = None
            original_price = None
            
            if markdown:
                # Look for price pattern near "มีคนซื้อไปแล้ว" (people have bought) section
                # This section typically contains the actual selling price
                bought_section = re.search(r'มีคนซื้อไปแล้ว.*?฿(\d+(?:,\d+)*)\s*/each\s*฿(\d+(?:,\d+)*)', markdown, re.DOTALL)
                if bought_section:
                    # First price after "มีคนซื้อไปแล้ว" is current price, second is original
                    current_price = self.extract_price(bought_section.group(1))
                    original_price = self.extract_price(bought_section.group(2))
                else:
                    # Fallback: Find prices in markdown (฿2,490 format)
                    price_matches = re.findall(r'฿\s*([\d,]+)', markdown)
                    if price_matches:
                        # Look for a pattern where two prices appear close together
                        # The smaller one is likely the sale price
                        if len(price_matches) >= 2:
                            price1 = self.extract_price(price_matches[0])
                            price2 = self.extract_price(price_matches[1])
                            if price1 and price2:
                                current_price = min(price1, price2)
                                original_price = max(price1, price2)
                        else:
                            current_price = self.extract_price(price_matches[0])
            
            # Fallback to raw data
            if not current_price:
                current_price = self.extract_price(raw_data.get('price') or raw_data.get('current_price'))
            if not original_price:
                original_price = self.extract_price(raw_data.get('originalPrice') or raw_data.get('original_price'))
            
            # Calculate discount
            discount_percentage = None
            if current_price and original_price and original_price > current_price:
                discount_percentage = float(((original_price - current_price) / original_price) * 100)
            
            # Process other fields
            brand = None
            # Try to extract brand from metadata description (format: "Name, Brand, SKU")
            if metadata.get('description'):
                parts = metadata['description'].split(',')
                if len(parts) >= 2:
                    brand = self.clean_text(parts[1])
            
            if not brand:
                brand = self.clean_text(raw_data.get('brand'))
            
            # Extract category from URL path or markdown content
            category = self._extract_category(url, markdown, raw_data)
            description = self.clean_text(raw_data.get('description'))
            
            # Process features
            features = raw_data.get('features', [])
            if isinstance(features, str):
                features = [f.strip() for f in features.split(',') if f.strip()]
            elif not isinstance(features, list):
                features = []
            
            # Process specifications
            specifications = raw_data.get('specifications', {})
            if not isinstance(specifications, dict):
                specifications = {}
            
            # Process images
            images = self.process_images(raw_data.get('images', []))
            
            # Determine availability from markdown content
            availability = self._extract_availability(markdown, raw_data)
            
            # Create Product instance
            product = Product(
                sku=sku,
                name=name,
                brand=brand,
                category=category,
                current_price=current_price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                description=description,
                features=features,
                specifications=specifications,
                availability=availability,
                images=images,
                url=url
            )
            
            logger.info(f"Successfully processed product: {sku} - {name}")
            return product
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing product data for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing product data for {url}: {str(e)}")
            return None
    
    def validate_product(self, product: Product) -> bool:
        """
        Validate product data quality
        
        Args:
            product: Product to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Required fields
        if not product.sku or not product.name or not product.url:
            return False
        
        # Price validation
        if product.current_price is not None and product.current_price <= 0:
            return False
        
        # Name length
        if len(product.name) < 3 or len(product.name) > 500:
            return False
        
        # SKU format
        if len(product.sku) < 3 or len(product.sku) > 50:
            return False
        
        return True