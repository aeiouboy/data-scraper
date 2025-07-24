"""
Improved native scraping strategy with better price and brand extraction
"""
import re
import json
import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

class ImprovedNativeStrategy:
    """Enhanced native scraping with improved price and brand extraction"""
    
    def __init__(self):
        self.retailer_name = "HomePro"
        
    def extract_improved_price(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Improved price extraction with multiple fallback strategies
        """
        logger.info(f"Starting improved price extraction for: {url}")
        
        current_price = None
        original_price = None
        
        # Strategy 1: JSON-LD structured data (highest priority)
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if script.string:
                    try:
                        json_data = json.loads(script.string)
                        if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                            offers = json_data.get('offers', {})
                            if offers:
                                if isinstance(offers, list):
                                    offers = offers[0]
                                
                                # Get price from offers
                                price_value = offers.get('price') or offers.get('lowPrice')
                                if price_value:
                                    try:
                                        price_val = float(str(price_value).replace(',', ''))
                                        if price_val > 0:
                                            current_price = price_val
                                            logger.info(f"Found price from JSON-LD: {current_price}")
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Check for highPrice as original price
                                high_price = offers.get('highPrice')
                                if high_price and current_price:
                                    try:
                                        high_val = float(str(high_price).replace(',', ''))
                                        if high_val > current_price:
                                            original_price = high_val
                                            logger.info(f"Found original price from JSON-LD: {original_price}")
                                    except (ValueError, TypeError):
                                        pass
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
        
        # Strategy 2: Enhanced CSS selectors (broader coverage)
        if not current_price:
            logger.info("JSON-LD failed, trying CSS selectors")
            
            # Comprehensive HomePro price selectors
            current_price_selectors = [
                # Main price selectors
                '.product-price .price-sale',
                '.product-price .price-current',
                '.price-now',
                '.current-price',
                '.sale-price',
                '.product-price-value',
                
                # Alternative formats
                'span.price-sale',
                'span.price-current',
                '.price-container .price-sale',
                '.price-container .price-current',
                
                # More generic patterns
                '.price-main',
                '.price-display',
                '.product-price-final',
                '.final-price',
                '.selling-price',
                
                # Fallback patterns
                '[data-price]',
                '.price',
                '.product-price',
                '.price-wrapper .price',
                '.price-section .price'
            ]
            
            for selector in current_price_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_text = element.get_text(strip=True)
                        extracted_price = self._extract_price_from_text(price_text)
                        if extracted_price:
                            current_price = extracted_price
                            logger.info(f"Found price from selector '{selector}': {current_price}")
                            break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
        
        # Strategy 3: Original price extraction
        if not original_price:
            original_price_selectors = [
                '.product-price .price-regular',
                '.product-price .price-original',
                '.original-price',
                '.regular-price',
                '.list-price',
                '.was-price',
                'span.price-regular',
                'span.price-original',
                '.price-container .price-regular',
                '.price-container .price-original',
                '.price-before',
                '.price-old',
                '.strikethrough-price',
                '.crossed-price'
            ]
            
            for selector in original_price_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_text = element.get_text(strip=True)
                        extracted_price = self._extract_price_from_text(price_text)
                        if extracted_price and (not current_price or extracted_price > current_price):
                            original_price = extracted_price
                            logger.info(f"Found original price from selector '{selector}': {original_price}")
                            break
                except Exception as e:
                    logger.debug(f"Original price selector '{selector}' failed: {e}")
        
        # Strategy 4: Text-based price extraction (last resort)
        if not current_price:
            logger.info("Selector-based extraction failed, trying text-based extraction")
            
            # Look for price patterns in all text
            price_patterns = [
                r'ราคา[:\s]*฿\s*([0-9,]+)',
                r'Price[:\s]*฿\s*([0-9,]+)',
                r'฿\s*([0-9,]+)\s*บาท',
                r'฿\s*([0-9,]+)(?:\s|$)',
                r'(\d{1,3}(?:,\d{3})*)\s*บาท',
                r'THB\s*([0-9,]+)',
                r'(\d{1,3}(?:,\d{3})*)\s*THB'
            ]
            
            page_text = soup.get_text()
            found_prices = []
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price_val = self._extract_price_from_text(match)
                    if price_val and 100 <= price_val <= 1000000:  # Reasonable price range
                        found_prices.append(price_val)
            
            if found_prices:
                # Remove duplicates and sort
                unique_prices = sorted(list(set(found_prices)))
                
                # Take the most reasonable price (not too low, not too high)
                reasonable_prices = [p for p in unique_prices if 1000 <= p <= 100000]
                if reasonable_prices:
                    current_price = reasonable_prices[0]  # Take the lowest reasonable price
                    logger.info(f"Found price from text extraction: {current_price}")
                    
                    # If we have multiple prices, check for original price
                    if len(reasonable_prices) > 1:
                        original_price = reasonable_prices[1]
                        logger.info(f"Found original price from text extraction: {original_price}")
        
        # Strategy 5: Meta tag extraction
        if not current_price:
            logger.info("Trying meta tag extraction")
            
            meta_selectors = [
                'meta[property="product:price:amount"]',
                'meta[property="og:price:amount"]',
                'meta[name="price"]',
                'meta[itemprop="price"]',
                'meta[property="product:price"]'
            ]
            
            for selector in meta_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_content = element.get('content', '')
                        extracted_price = self._extract_price_from_text(price_content)
                        if extracted_price:
                            current_price = extracted_price
                            logger.info(f"Found price from meta tag '{selector}': {current_price}")
                            break
                except Exception as e:
                    logger.debug(f"Meta tag '{selector}' failed: {e}")
        
        # Validate and return results
        result = {}
        
        if current_price:
            result['current_price'] = current_price
            result['price'] = current_price
            
        if original_price and original_price > current_price:
            result['original_price'] = original_price
            
            # Calculate discount
            discount_percentage = ((original_price - current_price) / original_price) * 100
            result['discount_percentage'] = round(discount_percentage, 2)
        
        logger.info(f"Price extraction result: {result}")
        return result
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text with improved validation"""
        if not text:
            return None
        
        # Clean the text
        text = str(text).strip()
        
        # Remove Thai baht symbol and common formatting
        cleaned_text = re.sub(r'[฿,\s]', '', text)
        cleaned_text = re.sub(r'บาท|THB', '', cleaned_text, flags=re.IGNORECASE)
        
        # Extract numeric value
        price_match = re.search(r'(\d+(?:\.\d{1,2})?)', cleaned_text)
        if price_match:
            try:
                price_val = float(price_match.group(1))
                if price_val > 0:
                    return price_val
            except (ValueError, TypeError):
                pass
        
        return None
    
    def extract_improved_brand(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Improved brand extraction with multiple fallback strategies
        """
        logger.info(f"Starting improved brand extraction for: {url}")
        
        brand = None
        
        # Strategy 1: JSON-LD structured data
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if script.string:
                    try:
                        json_data = json.loads(script.string)
                        if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                            brand_info = json_data.get('brand')
                            if isinstance(brand_info, dict):
                                brand = brand_info.get('name')
                            elif isinstance(brand_info, str):
                                brand = brand_info
                            
                            if brand:
                                logger.info(f"Found brand from JSON-LD: {brand}")
                                break
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            logger.debug(f"JSON-LD brand extraction failed: {e}")
        
        # Strategy 2: Enhanced CSS selectors
        if not brand:
            logger.info("JSON-LD failed, trying CSS selectors")
            
            brand_selectors = [
                # Direct brand selectors
                '.brand-name',
                '.product-brand',
                '.manufacturer',
                '[data-brand]',
                '.brand',
                '.brand-title',
                
                # Microdata selectors
                '[itemprop="brand"]',
                '[itemprop="manufacturer"]',
                
                # Alternative patterns
                '.product-brand-name',
                '.brand-info',
                '.brand-label',
                '.manufacturer-name',
                '.product-manufacturer',
                
                # Breadcrumb-based (brand might be in breadcrumbs)
                '.breadcrumb .brand',
                '.breadcrumbs .brand',
                
                # Meta-based
                'meta[name="brand"]',
                'meta[property="product:brand"]'
            ]
            
            for selector in brand_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        if element.name == 'meta':
                            brand_text = element.get('content', '')
                        else:
                            brand_text = element.get_text(strip=True)
                        
                        if brand_text:
                            cleaned_brand = self._clean_brand_text(brand_text)
                            if cleaned_brand:
                                brand = cleaned_brand
                                logger.info(f"Found brand from selector '{selector}': {brand}")
                                break
                except Exception as e:
                    logger.debug(f"Brand selector '{selector}' failed: {e}")
        
        # Strategy 3: Extract from product name
        if not brand:
            logger.info("Selector-based brand extraction failed, trying name-based extraction")
            
            # Try to find product name first
            name_selectors = [
                'h1.product-name',
                'h1.product-title',
                '.product-name',
                '.product-title',
                'h1',
                '.title'
            ]
            
            product_name = None
            for selector in name_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        product_name = element.get_text(strip=True)
                        if product_name:
                            break
                except Exception as e:
                    logger.debug(f"Name selector '{selector}' failed: {e}")
            
            if product_name:
                brand = self._extract_brand_from_name(product_name)
                if brand:
                    logger.info(f"Found brand from product name: {brand}")
        
        # Strategy 4: Meta tags
        if not brand:
            logger.info("Trying meta tag extraction for brand")
            
            meta_selectors = [
                'meta[property="og:brand"]',
                'meta[name="brand"]',
                'meta[property="product:brand"]',
                'meta[name="manufacturer"]'
            ]
            
            for selector in meta_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        brand_text = element.get('content', '')
                        if brand_text:
                            cleaned_brand = self._clean_brand_text(brand_text)
                            if cleaned_brand:
                                brand = cleaned_brand
                                logger.info(f"Found brand from meta tag '{selector}': {brand}")
                                break
                except Exception as e:
                    logger.debug(f"Meta tag '{selector}' failed: {e}")
        
        return brand
    
    def _clean_brand_text(self, text: str) -> Optional[str]:
        """Clean and validate brand text"""
        if not text:
            return None
        
        # Clean whitespace
        text = str(text).strip()
        
        # Remove common noise words
        noise_words = [
            'brand:', 'แบรนด์:', 'ยี่ห้อ:', 'manufacturer:', 'ผู้ผลิต:',
            'by', 'from', 'made by', 'produced by'
        ]
        
        for noise in noise_words:
            text = re.sub(rf'^{re.escape(noise)}\s*', '', text, flags=re.IGNORECASE)
        
        # Filter out obviously wrong brands
        invalid_brands = [
            'led', 'lcd', 'tv', 'ทีวี', 'product', 'สินค้า', 'item',
            'other', 'อื่นๆ', 'general', 'ทั่วไป', 'default', 'none',
            'n/a', 'not available', 'ไม่มี', 'home', 'บ้าน'
        ]
        
        if text.lower() in invalid_brands:
            return None
        
        # Length validation
        if len(text) < 2 or len(text) > 50:
            return None
        
        # Return cleaned brand
        return text.title()
    
    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extract brand from product name using patterns"""
        if not name:
            return None
        
        # Common brand patterns
        brand_patterns = [
            # Brand at the beginning
            r'^([A-Z][a-z]+)\s+',
            
            # Known brands (case-insensitive)
            r'\\b(SAMSUNG|LG|SONY|PANASONIC|SHARP|TCL|HAIER|NANO|DAIKIN|CARRIER|MITSUBISHI|TOSHIBA|PHILIPS|BRAUN|DYSON|ELECTROLUX|WHIRLPOOL|BOSCH|SIEMENS|MIELE|BEKO|HITACHI|SANYO|NATIONAL|AKAI|TEAC|ONKYO|YAMAHA|PIONEER|KENWOOD|ALPINE|CLARION|GARMIN|TOMTOM|APPLE|GOOGLE|MICROSOFT|AMAZON|FACEBOOK|TWITTER|INSTAGRAM|YOUTUBE|NETFLIX|SPOTIFY|UBER|GRAB|LAZADA|SHOPEE|TIKTOK|LINE|FACEBOOK|INSTAGRAM|TWITTER|YOUTUBE|NETFLIX|SPOTIFY|UBER|GRAB|LAZADA|SHOPEE|TIKTOK|LINE|GREE|MIDEA|CHANGHONG|HISENSE|SKYWORTH|KONKA|TCLK|HAIERK|GALANZ|GEELY|BYD|GREAT WALL|CHERY|JAC|DONGFENG|FAW|SAIC|BAIC|BRILLIANCE|LIFAN|ZOTYE|CHANGAN|HAFEI|XIALI|HONGQI|ROEWE|MG|MAXUS|IVECO|ISUZU|HINO|FUSO|SCANIA|VOLVO|MAN|MERCEDES|BMW|AUDI|VOLKSWAGEN|PORSCHE|BENTLEY|ROLLS ROYCE|LAMBORGHINI|FERRARI|MASERATI|ALFA ROMEO|FIAT|JEEP|DODGE|CHRYSLER|CADILLAC|BUICK|CHEVROLET|FORD|LINCOLN|MERCURY|PONTIAC|OLDSMOBILE|SATURN|HUMMER|SAAB|ACURA|HONDA|INFINITI|LEXUS|MAZDA|MITSUBISHI|NISSAN|SUBARU|SUZUKI|TOYOTA|ISUZU|DAEWOO|HYUNDAI|KIA|SSANGYONG|PROTON|PERODUA|LOTUS|JAGUAR|LAND ROVER|ASTON MARTIN|MCLAREN|MINI|SMART|OPEL|PEUGEOT|CITROEN|RENAULT|SKODA|SEAT|CUPRA|LADA|DACIA|ALPINE|DS|BUGATTI|KOENIGSEGG|PAGANI|SPYKER|TESLA|LUCID|RIVIAN|FISKER|CANOO|NIKOLA|WORKHORSE|LORDSTOWN|FARADAY FUTURE|BYTON|NIO|XPENG|LI AUTO|GEELY|BYD|GREAT WALL|CHERY|JAC|DONGFENG|FAW|SAIC|BAIC|BRILLIANCE|LIFAN|ZOTYE|CHANGAN|HAFEI|XIALI|HONGQI|ROEWE|MG|MAXUS)\\b',
            
            # Thai brands
            r'\\b(ไทย|THAI|CP|เจริญโภคภัณฑ์|PTT|ปตท|SCG|เอสซีจี|DTAC|ดีแทค|AIS|เอไอเอส|TRUE|ทรู|CENTRAL|เซ็นทรัล|ROBINSON|โรบินสัน|TESCO|เทสโก้|BIG C|บิ๊กซี|LOTUS|โลตัส|MAKRO|แมคโคร|VILLA|วิลล่า|TOPS|ท็อปส์|FOOD LAND|ฟู้ดแลนด์|GOURMET|กูร์เม่ต์|EMPORIUM|เอ็มโพเรี่ยม|PARAGON|พารากอน|ICONSIAM|ไอคอนสยาม|TERMINAL 21|เทอร์มินอล 21|ASIATIQUE|เอเชียทีค|CHATUCHAK|จตุจักร|WEEKEND MARKET|วีคเอนด์มาร์เก็ต|FLOATING MARKET|ตลาดน้ำ|KHAO SAN|ข้าวสาร|SILOM|สีลม|SUKHUMVIT|สุขุมวิท|THONGLOR|ทองหล่อ|EKKAMAI|เอกมัย|PHROM PHONG|พร้อมพงษ์|ASOK|อโศก|NANA|นานา|PLOENCHIT|เพลินจิต|CHIDLOM|ชิดลม|RATCHADAMRI|ราชดำริ|SALA DAENG|ศาลาแดง|SURASAK|สุรศักดิ์|SAPHAN TAKSIN|สะพานตากสิน|KRUNG THONBURI|กรุงธนบุรี|WONGWIAN YAI|วงเวียนใหญ่|PHRA KHANONG|พระโขนง|ON NUT|อ่อนนุช|BANG CHAK|บางจาก|PUNNAWITHI|ปุณณวิถี|UDOM SUK|อุดมสุข|BANG NA|บางนา|BEARING|แบริ่ง|SAMRONG|สำโรง|PUKETAO|ปูเก็ตาว|KHEHA|เคหะ|LAT KRABANG|ลาดกระบัง|SUVARNABHUMI|สุวรรณภูมิ)\\b',
            
            # Pattern for brands in parentheses
            r'\\(([A-Z][A-Za-z]+)\\)',
            
            # Brand after "by" or "from"
            r'\\b(?:by|from)\\s+([A-Z][A-Za-z]+)',
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                potential_brand = match.group(1)
                cleaned_brand = self._clean_brand_text(potential_brand)
                if cleaned_brand:
                    return cleaned_brand
        
        return None
    
    def extract_improved_category(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Improved category extraction with multiple strategies
        """
        logger.info(f"Starting improved category extraction for: {url}")
        
        category = None
        
        # Strategy 1: Breadcrumb navigation
        breadcrumb_selectors = [
            '.breadcrumb a:not(:first-child)',
            '.breadcrumbs a:not(:first-child)',
            '.nav-breadcrumb a:not(:first-child)',
            '.category-path a',
            '.breadcrumb-item a',
            '.breadcrumb li a:not(:first-child)'
        ]
        
        for selector in breadcrumb_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # Take the last breadcrumb item (most specific category)
                    category_text = elements[-1].get_text(strip=True)
                    if category_text and category_text.lower() not in ['home', 'หน้าแรก', 'หน้าหลัก']:
                        category = category_text
                        logger.info(f"Found category from breadcrumb: {category}")
                        break
            except Exception as e:
                logger.debug(f"Breadcrumb selector '{selector}' failed: {e}")
        
        # Strategy 2: URL-based category extraction
        if not category:
            logger.info("Breadcrumb extraction failed, trying URL-based extraction")
            
            # Extract from URL path
            url_patterns = [
                r'/c/([A-Z]{3})',  # HomePro category codes
                r'/category/([^/]+)',
                r'/cat/([^/]+)',
                r'/categories/([^/]+)'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, url)
                if match:
                    category_code = match.group(1)
                    
                    # Map HomePro category codes
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
                    
                    category = category_mapping.get(category_code, category_code)
                    logger.info(f"Found category from URL: {category}")
                    break
        
        # Strategy 3: Meta tags and structured data
        if not category:
            logger.info("URL-based extraction failed, trying meta tags")
            
            meta_selectors = [
                'meta[property="product:category"]',
                'meta[name="category"]',
                'meta[property="og:category"]',
                'meta[itemprop="category"]'
            ]
            
            for selector in meta_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        category_text = element.get('content', '')
                        if category_text:
                            category = category_text
                            logger.info(f"Found category from meta tag: {category}")
                            break
                except Exception as e:
                    logger.debug(f"Meta tag '{selector}' failed: {e}")
        
        # Strategy 4: Product name-based category inference
        if not category:
            logger.info("Meta tag extraction failed, trying name-based inference")
            
            # Get product name
            name_selectors = [
                'h1.product-name',
                'h1.product-title',
                '.product-name',
                '.product-title',
                'h1'
            ]
            
            product_name = None
            for selector in name_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        product_name = element.get_text(strip=True)
                        if product_name:
                            break
                except Exception as e:
                    logger.debug(f"Name selector '{selector}' failed: {e}")
            
            if product_name:
                category = self._infer_category_from_name(product_name)
                if category:
                    logger.info(f"Inferred category from name: {category}")
        
        return category
    
    def _infer_category_from_name(self, name: str) -> Optional[str]:
        """Infer category from product name using patterns"""
        if not name:
            return None
        
        name_lower = name.lower()
        
        # Category patterns
        category_patterns = {
            'เครื่องใช้ไฟฟ้า': [
                'เครื่องซักผ้า', 'เครื่องอบผ้า', 'เครื่องล้างจาน', 'เครื่องปรับอากาศ',
                'แอร์', 'ตู้เย็น', 'ไมโครเวฟ', 'เครื่องดูดฝุ่น', 'เครื่องฟอกอากาศ',
                'washing machine', 'dryer', 'dishwasher', 'air conditioner',
                'refrigerator', 'microwave', 'vacuum', 'air purifier'
            ],
            'เครื่องใช้ไฟฟ้าขนาดเล็ก': [
                'ไดร์เป่าผม', 'เครื่องโกนหนวด', 'เครื่องหนีบผม', 'แกนม้วนผม',
                'เครื่องตีไข่', 'เครื่องปิ้งขนมปัง', 'กาต้มน้ำ', 'เครื่องชงกาแฟ',
                'hair dryer', 'shaver', 'hair straightener', 'hair curler',
                'mixer', 'toaster', 'kettle', 'coffee maker', 'blender'
            ],
            'โคมไฟและหลอดไฟ': [
                'โคมไฟ', 'หลอดไฟ', 'ไฟ', 'แสงไฟ', 'โคมไฟตั้งโต๊ะ',
                'โคมไฟแขวน', 'โคมไฟติดผนัง', 'โคมไฟเพดาน',
                'lamp', 'light', 'bulb', 'lighting', 'ceiling light',
                'table lamp', 'wall light', 'pendant light'
            ],
            'ห้องครัวและอุปกรณ์': [
                'เตาแก๊ส', 'เตาไฟฟ้า', 'เครื่องดูดควัน', 'อ่างล้างจาน',
                'ก๊อกน้ำ', 'ตู้ครัว', 'เคาน์เตอร์', 'แก๊สหุงต้ม',
                'stove', 'cooker', 'range hood', 'sink', 'faucet',
                'cabinet', 'counter', 'gas burner'
            ],
            'ห้องน้ำ': [
                'สุขภัณฑ์', 'โถส้วม', 'อ่างอาบน้ำ', 'ฝักบัว', 'อ่างล้างหน้า',
                'กระจกห้องน้ำ', 'ที่แขวนผ้า', 'ที่วางแปรงสีฟัน',
                'toilet', 'bathtub', 'shower', 'washbasin', 'bathroom mirror',
                'towel rack', 'toothbrush holder'
            ],
            'พัดลม': [
                'พัดลม', 'พัดลมติดเพดาน', 'พัดลมตั้งโต๊ะ', 'พัดลมตั้งพื้น',
                'พัดลมอุตสาหกรรม', 'พัดลมพกพา',
                'fan', 'ceiling fan', 'table fan', 'floor fan',
                'industrial fan', 'portable fan'
            ]
        }
        
        for category, keywords in category_patterns.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category
        
        return None