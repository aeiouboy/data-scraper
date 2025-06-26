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
            
        # Convert to string and remove common patterns
        price_str = str(price_text)
        # Remove Thai baht symbol, commas, spaces
        price_str = re.sub(r'[฿,\s]', '', price_str)
        # Remove "บาท" (baht in Thai)
        price_str = re.sub(r'บาท', '', price_str)
        
        # Extract first number pattern
        match = re.search(r'(\d+(?:\.\d{1,2})?)', price_str)
        if match:
            try:
                return Decimal(match.group(1))
            except:
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
            'sold out', 'ไม่มีสินค้า', 'out-of-stock'
        ]
        
        for pattern in in_stock_patterns:
            if pattern in text:
                return "in_stock"
        
        for pattern in out_of_stock_patterns:
            if pattern in text:
                return "out_of_stock"
        
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
            # Check if we have markdown content
            markdown = raw_data.get('markdown', '')
            
            # If we have markdown, parse it for product info
            if markdown:
                logger.debug("Processing markdown content")
                # For now, extract title from markdown
                lines = markdown.split('\n')
                name = None
                for line in lines[:20]:  # Check first 20 lines
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 10:
                        name = self.clean_text(line)
                        break
                
                if not name:
                    # Try to find any heading
                    for line in lines:
                        if line.startswith('# ') and len(line) > 3:
                            name = self.clean_text(line[2:])
                            break
            else:
                # Fallback to extracted data if available
                name = self.clean_text(raw_data.get('name') or raw_data.get('title'))
            
            if not name:
                logger.warning(f"No product name found for {url}")
                return None
            
            # Extract SKU
            sku = self.extract_sku(raw_data.get('sku') or raw_data.get('code'))
            if not sku:
                # Try to extract from URL or name
                sku = self.extract_sku(url) or self.extract_sku(name)
            
            if not sku:
                # Generate SKU from URL hash
                import hashlib
                sku = f"HP-{hashlib.md5(url.encode()).hexdigest()[:8].upper()}"
            
            # Process prices
            current_price = self.extract_price(raw_data.get('price') or raw_data.get('current_price'))
            original_price = self.extract_price(raw_data.get('originalPrice') or raw_data.get('original_price'))
            
            # Calculate discount
            discount_percentage = None
            if current_price and original_price and original_price > current_price:
                discount_percentage = float(((original_price - current_price) / original_price) * 100)
            
            # Process other fields
            brand = self.clean_text(raw_data.get('brand'))
            category = self.clean_text(raw_data.get('category'))
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
            
            # Determine availability
            availability = self.determine_availability(
                raw_data.get('availability') or raw_data.get('stock_status')
            )
            
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
            
        except Exception as e:
            logger.error(f"Error processing product data for {url}: {str(e)}")
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