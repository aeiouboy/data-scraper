"""
Advanced Text Normalizer with enhanced Thai-English multilingual support
Includes phonetic matching, transliteration handling, and proper Thai segmentation
"""
import re
import unicodedata
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict
import logging

# Try to import pythainlp for proper Thai text processing
try:
    from pythainlp import word_tokenize, spell, correct
    from pythainlp.transliterate import romanize
    HAS_PYTHAINLP = True
except ImportError:
    HAS_PYTHAINLP = False
    logger = logging.getLogger(__name__)
    logger.warning("pythainlp not installed. Thai text processing will be limited.")

logger = logging.getLogger(__name__)

class AdvancedTextNormalizer:
    """Advanced text normalizer with comprehensive Thai-English support"""
    
    def __init__(self):
        # Extended Thai-English brand mappings
        self.brand_mappings = {
            # Thai to English normalized form
            'มิตซูบิชิ': 'mitsubishi',
            'มิตซู': 'mitsubishi',
            'มิตชูบิชิ': 'mitsubishi',  # Common misspelling
            'ซัมซุง': 'samsung',
            'แซมซุง': 'samsung',
            'ซัมซัง': 'samsung',  # Variation
            'แอลจี': 'lg',
            'แอลจี': 'lg',
            'พานาโซนิค': 'panasonic',
            'พานาโซนิก': 'panasonic',
            'พานาโซนิค': 'panasonic',
            'โตชิบา': 'toshiba',
            'โตชิบ้า': 'toshiba',
            'โตซิบา': 'toshiba',  # Variation
            'ชาร์ป': 'sharp',
            'ชาร์พ': 'sharp',
            'ไดกิ้น': 'daikin',
            'ไดกิน': 'daikin',
            'ได้กิ้น': 'daikin',
            'ฮิตาชิ': 'hitachi',
            'ฮิตาชิ': 'hitachi',
            'ฮาเออร์': 'haier',
            'ไฮเออร์': 'haier',
            'อีเลคโทรลักซ์': 'electrolux',
            'อีเล็คโทรลักซ์': 'electrolux',
            'อีเลคโทรลักส์': 'electrolux',
            'ฟิลิปส์': 'philips',
            'ฟิลลิป': 'philips',
            'ซันโย': 'sanyo',
            'ซานโย': 'sanyo',
            'คาร์เรียร์': 'carrier',
            'แคเรียร์': 'carrier',
            'ยอร์ค': 'york',
            'ยอร์ก': 'york',
            'เทรน': 'trane',
            'เทรน': 'trane',
            'มิเดีย': 'midea',
            'มีเดีย': 'midea',
            'กรี': 'gree',
            'กรีย์': 'gree',
            'ทีซีแอล': 'tcl',
            'ทีซีอล': 'tcl',
            'เฮเฟเล่': 'hafele',
            'เฮเฟเล': 'hafele',
            'ฮาเฟเล่': 'hafele',
            'บ๊อช': 'bosch',
            'บอช': 'bosch',
            'บอร์ช': 'bosch',
            'ซีเมนส์': 'siemens',
            'ซีเม้นส์': 'siemens',
            'วิรพูล': 'whirlpool',
            'เวิร์ลพูล': 'whirlpool',
            'เวสติ้งเฮาส์': 'westinghouse',
            'เวสติงเฮาส์': 'westinghouse',
            'เคนมอร์': 'kenmore',
            'เคนมอ': 'kenmore',
            'ฟูจิ': 'fuji',
            'ฟูจิตสึ': 'fujitsu',
            'ฟูจิสึ': 'fujitsu',
            'เซ็นทรัล': 'central',
            'เซ็นทรัลแอร์': 'central',
            'อามีน่า': 'amena',
            'อามีนา': 'amena',
            'ซามิค': 'samic',
            'ซามิก': 'samic',
            'ยูนิแอร์': 'uniaire',
            'ยูนิแอ': 'uniaire',
            'สตาร์': 'star',
            'สตาร์แอร์': 'star',
            'คอมฟี่': 'comfee',
            'คอมฟี': 'comfee',
            'คอมฟี่': 'comfee',
            'ไฮเซนส์': 'hisense',
            'ไฮเซ่นส์': 'hisense',
            'ไฮเซน': 'hisense',
            'เอซีอี': 'ace',
            'เอซี': 'ace',
            'เฟรช': 'fresh',
            'เฟรช': 'fresh',
            'อาริสตัน': 'ariston',
            'อาริสตั้น': 'ariston',
            'เบโค': 'beko',
            'เบคโค': 'beko',
            'เบโก': 'beko',
            # English variations to normalized form
            'mitsubishi electric': 'mitsubishi',
            'mitsubishi heavy': 'mitsubishi',
            'samsung electronics': 'samsung',
            'lg electronics': 'lg',
            'panasonic corporation': 'panasonic',
            'toshiba corporation': 'toshiba',
            'sharp corporation': 'sharp',
            'daikin industries': 'daikin',
            'hitachi ltd': 'hitachi',
            'haier group': 'haier',
            'electrolux ab': 'electrolux',
            'philips electronics': 'philips',
            'carrier corporation': 'carrier',
            'york international': 'york',
            'trane technologies': 'trane',
            'midea group': 'midea',
            'gree electric': 'gree',
            'tcl corporation': 'tcl',
            'bosch gmbh': 'bosch',
            'siemens ag': 'siemens',
            'whirlpool corporation': 'whirlpool',
            'westinghouse electric': 'westinghouse',
        }
        
        # Comprehensive unit mappings
        self.unit_mappings = {
            # Thai to English with variations
            'นิ้ว': 'inch',
            'น.': 'inch',
            'นิ้ว': 'inch',
            '"': 'inch',
            '″': 'inch',
            '′': 'feet',
            'ฟุต': 'feet',
            'ฟ.': 'feet',
            'ft': 'feet',
            'เมตร': 'meter',
            'ม.': 'meter',
            'm': 'meter',
            'เซนติเมตร': 'cm',
            'ซม.': 'cm',
            'ซ.ม.': 'cm',
            'เซนติ': 'cm',
            'มิลลิเมตร': 'mm',
            'มม.': 'mm',
            'ม.ม.': 'mm',
            'มิลลิ': 'mm',
            'กิโลกรัม': 'kg',
            'กก.': 'kg',
            'ก.ก.': 'kg',
            'กิโล': 'kg',
            'กรัม': 'g',
            'ก.': 'g',
            'ลิตร': 'liter',
            'ล.': 'liter',
            'ลิต': 'liter',
            'l': 'liter',
            'มิลลิลิตร': 'ml',
            'มล.': 'ml',
            'ม.ล.': 'ml',
            'มิลลิ': 'ml',
            'บีทียู': 'btu',
            'บีทียู/ชม.': 'btu/hr',
            'บีทียู/ชั่วโมง': 'btu/hr',
            'btu/h': 'btu/hr',
            'btuh': 'btu/hr',
            'วัตต์': 'watt',
            'ว.': 'watt',
            'w': 'watt',
            'กิโลวัตต์': 'kw',
            'กว.': 'kw',
            'kilowatt': 'kw',
            'แรงม้า': 'hp',
            'แรงม้า': 'hp',
            'hp': 'hp',
            'horsepower': 'hp',
            'คิว': 'cu.ft',
            'คิวบิกฟุต': 'cu.ft',
            'ลูกบาศก์ฟุต': 'cu.ft',
            'ลบ.ฟ.': 'cu.ft',
            'cubic feet': 'cu.ft',
            'ตัน': 'ton',
            'ton': 'ton',
            'ดีบี': 'db',
            'เดซิเบล': 'db',
            'decibel': 'db',
            'องศา': 'degree',
            '°': 'degree',
            'ปี': 'year',
            'เดือน': 'month',
            'วัน': 'day',
            'ชั่วโมง': 'hour',
            'ชม.': 'hour',
            'hr': 'hour',
            'นาที': 'minute',
            'min': 'minute',
            'วินาที': 'second',
            'sec': 'second',
            's': 'second',
        }
        
        # Enhanced stop words
        self.stop_words = {
            # Thai stop words
            'ที่', 'นี้', 'นั้น', 'ของ', 'และ', 'หรือ', 'แต่', 'กับ', 'ให้',
            'ใน', 'บน', 'ใต้', 'เป็น', 'มี', 'ได้', 'เพื่อ', 'จาก', 'โดย',
            'ไป', 'มา', 'ว่า', 'ซึ่ง', 'อัน', 'คือ', 'แล้ว', 'ด้วย', 'ต่อ',
            'ตาม', 'ถึง', 'ทั้ง', 'นั่น', 'เมื่อ', 'ก็', 'จะ', 'ยัง', 'อีก',
            'รุ่น', 'แบบ', 'ชนิด', 'ประเภท', 'สำหรับ', 'ทุก', 'บาง', 'หลาย',
            'น้อย', 'มาก', 'กว่า', 'สุด', 'ใหม่', 'เก่า', 'ดี', 'เลว',
            # English stop words
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'up', 'down', 'out', 'over',
            'under', 'again', 'is', 'are', 'was', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'shall', 'can',
            'model', 'type', 'series', 'version', 'edition', 'new', 'old',
            'good', 'bad', 'best', 'worst', 'more', 'less', 'most', 'least',
        }
        
        # Thai abbreviations
        self.thai_abbreviations = {
            'ตรม.': 'ตารางเมตร',
            'ตร.ม.': 'ตารางเมตร',
            'ตรว.': 'ตารางวา',
            'ตร.ว.': 'ตารางวา',
            'พ.ศ.': 'พุทธศักราช',
            'ค.ศ.': 'คริสต์ศักราช',
            'จก.': 'จำกัด',
            'บจก.': 'บริษัทจำกัด',
            'บจ.': 'บริษัทจำกัด',
            'มหาชน': 'บริษัทมหาชนจำกัด',
            'อ.': 'อำเภอ',
            'ต.': 'ตำบล',
            'จ.': 'จังหวัด',
            'ถ.': 'ถนน',
            'ซ.': 'ซอย',
            'ม.': 'หมู่',
            'หมู่': 'หมู่บ้าน',
            'รุ่น': 'model',
            'สี': 'color',
            'ขนาด': 'size',
        }
        
        # Product-specific terms
        self.product_terms = {
            # Air conditioner terms
            'แอร์': 'air conditioner',
            'เครื่องปรับอากาศ': 'air conditioner',
            'ปรับอากาศ': 'air conditioner',
            'แอร์บ้าน': 'air conditioner',
            'คอยล์ร้อน': 'condenser',
            'คอยล์เย็น': 'evaporator',
            'คอนเดนเซอร์': 'condenser',
            'อีวาพอเรเตอร์': 'evaporator',
            'รีโมท': 'remote',
            'รีโมต': 'remote',
            'รีโมทคอนโทรล': 'remote control',
            'ประหยัดไฟ': 'energy saving',
            'ประหยัดพลังงาน': 'energy efficient',
            'อินเวอร์เตอร์': 'inverter',
            'อินเวอเตอร์': 'inverter',
            'อินเวอร์เตอร': 'inverter',
            'ไร้เสียง': 'quiet',
            'เงียบ': 'quiet',
            'เย็นเร็ว': 'fast cooling',
            'ฟอกอากาศ': 'air purifier',
            'กรองอากาศ': 'air filter',
            'ระบบฟอก': 'purifying system',
            # Refrigerator terms
            'ตู้เย็น': 'refrigerator',
            'ตู้แช่': 'freezer',
            'ตู้แช่แข็ง': 'freezer',
            'ช่องแช่แข็ง': 'freezer compartment',
            'ช่องธรรมดา': 'fresh compartment',
            'ช่องผัก': 'vegetable compartment',
            'ช่องผลไม้': 'fruit compartment',
            'ประตู': 'door',
            'ประตูเดียว': 'single door',
            'สองประตู': 'two door',
            '2 ประตู': 'two door',
            'ไซด์บายไซด์': 'side by side',
            'มัลติดอร์': 'multi door',
            'ละลายน้ำแข็งอัตโนมัติ': 'auto defrost',
            'โนฟรอสต์': 'no frost',
            # General appliance terms
            'รับประกัน': 'warranty',
            'การรับประกัน': 'warranty',
            'ประกัน': 'warranty',
            'ประหยัดพลังงาน': 'energy efficient',
            'ระบบ': 'system',
            'อัตโนมัติ': 'automatic',
            'ออโต้': 'auto',
            'ดิจิตอล': 'digital',
            'ดิจิทัล': 'digital',
            'สมาร์ท': 'smart',
            'สมาร์ต': 'smart',
            'ไร้สาย': 'wireless',
            'ไวไฟ': 'wifi',
            'ไวฟาย': 'wifi',
            'แอพ': 'app',
            'แอปพลิเคชัน': 'application',
            'ควบคุม': 'control',
            'รีโมทคอนโทรล': 'remote control',
            'จอแสดงผล': 'display',
            'หน้าจอ': 'screen',
            'ปุ่มกด': 'button',
            'ระบบสัมผัส': 'touch',
            'ทัชสกรีน': 'touchscreen',
        }
        
        # Compile regex patterns
        self.patterns = {
            'model': re.compile(
                r'(?:model|รุ่น|โมเดล)?\s*[:.-]?\s*([A-Z0-9][-A-Z0-9\s/]*[A-Z0-9])',
                re.IGNORECASE
            ),
            'thai_model': re.compile(
                r'รุ่น\s*[:.-]?\s*([A-Zก-ฮ0-9][-A-Zก-ฮ0-9\s/]*[A-Zก-ฮ0-9])',
                re.IGNORECASE
            ),
            'sku_pattern': re.compile(
                r'\b([A-Z]{2,}[-]?[A-Z0-9]+(?:[-/][A-Z0-9]+)*)\b',
                re.IGNORECASE
            ),
            'size': re.compile(
                r'(\d+(?:\.\d+)?)\s*(?:inch|นิ้ว|"|″|in\b)',
                re.IGNORECASE
            ),
            'capacity': re.compile(
                r'(\d+(?:\.\d+)?)\s*(?:cu\.?ft|คิว|คิวบิกฟุต|ลิตร|liter|l\b)',
                re.IGNORECASE
            ),
            'power': re.compile(
                r'(\d+(?:,\d+)?)\s*(?:btu|บีทียู|watt|วัตต์|w\b|hp|แรงม้า)',
                re.IGNORECASE
            ),
            'voltage': re.compile(
                r'(\d+)\s*(?:v|volt|โวลต์|โวลท์)',
                re.IGNORECASE
            ),
            'price': re.compile(
                r'(?:ราคา|price|฿|บาท|thb)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                re.IGNORECASE
            ),
            'thai_chars': re.compile(r'[\u0E00-\u0E7F]'),
            'english_chars': re.compile(r'[a-zA-Z]'),
        }
        
        # Phonetic mapping rules for Thai to English
        self.phonetic_rules = {
            # Consonants
            'ก': ['k', 'g'],
            'ข': ['kh', 'k'],
            'ค': ['kh', 'k'],
            'ฆ': ['kh', 'k'],
            'ง': ['ng', 'n'],
            'จ': ['j', 'ch'],
            'ฉ': ['ch'],
            'ช': ['ch', 's'],
            'ซ': ['s', 'z'],
            'ฌ': ['ch'],
            'ญ': ['y', 'n'],
            'ฎ': ['d', 't'],
            'ฏ': ['t'],
            'ฐ': ['th', 't'],
            'ฑ': ['th', 't', 'd'],
            'ฒ': ['th', 't'],
            'ณ': ['n'],
            'ด': ['d', 't'],
            'ต': ['t', 'd'],
            'ถ': ['th', 't'],
            'ท': ['th', 't'],
            'ธ': ['th', 't'],
            'น': ['n'],
            'บ': ['b', 'p'],
            'ป': ['p', 'b'],
            'ผ': ['ph', 'p'],
            'ฝ': ['f'],
            'พ': ['ph', 'p'],
            'ฟ': ['f', 'ph'],
            'ภ': ['ph', 'p'],
            'ม': ['m'],
            'ย': ['y'],
            'ร': ['r', 'l', 'n'],
            'ล': ['l', 'r', 'n'],
            'ว': ['w', 'v'],
            'ศ': ['s'],
            'ษ': ['s'],
            'ส': ['s'],
            'ห': ['h'],
            'ฬ': ['l'],
            'อ': ['', 'o', 'a'],
            'ฮ': ['h'],
            # Common vowel combinations
            'เ': ['e', 'ay'],
            'แ': ['ae', 'a'],
            'โ': ['o'],
            'ไ': ['ai', 'i'],
            'ใ': ['ai', 'i'],
            'า': ['a', 'ar'],
            'ิ': ['i'],
            'ี': ['ee', 'i'],
            'ึ': ['ue', 'u'],
            'ื': ['ue', 'u'],
            'ุ': ['u', 'oo'],
            'ู': ['oo', 'u'],
        }
    
    def normalize(self, text: str) -> str:
        """Normalize text with comprehensive Thai-English handling"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace Thai abbreviations
        for abbr, full in self.thai_abbreviations.items():
            text = text.replace(abbr, full)
        
        # Replace product-specific Thai terms
        for thai, eng in self.product_terms.items():
            text = text.replace(thai, eng)
        
        # Replace Thai brand names
        for thai, eng in self.brand_mappings.items():
            if thai in text:
                text = text.replace(thai, eng)
        
        # Replace English brand variations
        for variant, normalized in self.brand_mappings.items():
            if not self.is_thai_text(variant) and variant in text:
                text = text.replace(variant, normalized)
        
        # Replace Thai units
        for thai, eng in self.unit_mappings.items():
            text = text.replace(thai, eng)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove special characters but keep Thai, numbers, and basic punctuation
        text = re.sub(r'[^\w\s\u0E00-\u0E7F.,-/()]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def normalize_sku(self, sku: str) -> str:
        """Normalize SKU/model numbers"""
        if not sku:
            return ""
        
        # Remove common prefixes
        sku = re.sub(r'^(model|รุ่น|sku|item)[\s:.-]*', '', sku, flags=re.IGNORECASE)
        
        # Normalize separators
        sku = re.sub(r'[\s._]+', '-', sku)
        
        # Remove special characters except alphanumeric and dash
        sku = re.sub(r'[^a-zA-Z0-9-/]', '', sku)
        
        # Convert to uppercase for consistency
        sku = sku.upper()
        
        # Remove trailing/leading dashes
        sku = sku.strip('-')
        
        return sku
    
    def normalize_specification(self, spec: str) -> str:
        """Normalize specification values"""
        if not spec:
            return ""
        
        spec = str(spec).lower()
        
        # Normalize color names
        color_mappings = {
            'ขาว': 'white',
            'ดำ': 'black',
            'แดง': 'red',
            'น้ำเงิน': 'blue',
            'เขียว': 'green',
            'เหลือง': 'yellow',
            'ส้ม': 'orange',
            'ม่วง': 'purple',
            'เทา': 'gray',
            'น้ำตาล': 'brown',
            'ชมพู': 'pink',
            'ทอง': 'gold',
            'เงิน': 'silver',
        }
        
        for thai_color, eng_color in color_mappings.items():
            if thai_color in spec:
                spec = spec.replace(thai_color, eng_color)
        
        # Normalize boolean values
        if spec in ['yes', 'ใช่', 'มี', 'true', '1']:
            return 'yes'
        elif spec in ['no', 'ไม่', 'ไม่มี', 'false', '0']:
            return 'no'
        
        return spec
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract meaningful tokens with proper Thai tokenization"""
        if not text:
            return []
        
        normalized = self.normalize(text)
        
        # Use pythainlp for Thai tokenization if available
        if HAS_PYTHAINLP and self.is_thai_text(text):
            try:
                # Tokenize mixed Thai-English text
                tokens = word_tokenize(normalized, engine='newmm')
            except:
                # Fallback to simple split
                tokens = normalized.split()
        else:
            # Simple tokenization for non-Thai or when pythainlp not available
            tokens = normalized.split()
        
        # Filter out stop words and short tokens
        tokens = [
            t for t in tokens 
            if t not in self.stop_words 
            and len(t) > 1
            and not t.isdigit()  # Keep numbers that are part of models
        ]
        
        return tokens
    
    def extract_specifications(self, text: str) -> Dict[str, Any]:
        """Extract specifications with enhanced patterns"""
        specs = {}
        normalized = self.normalize(text)
        
        # Extract model numbers (multiple patterns)
        model = None
        
        # Try standard model pattern
        model_matches = self.patterns['model'].findall(text)
        if model_matches:
            model = model_matches[0].strip()
        
        # Try Thai model pattern
        if not model:
            thai_model_matches = self.patterns['thai_model'].findall(text)
            if thai_model_matches:
                model = thai_model_matches[0].strip()
        
        # Try SKU pattern
        if not model:
            sku_matches = self.patterns['sku_pattern'].findall(text)
            if sku_matches:
                model = sku_matches[0].strip()
        
        if model:
            specs['model'] = self.normalize_sku(model)
        
        # Extract size
        size_matches = self.patterns['size'].findall(normalized)
        if size_matches:
            specs['size'] = float(size_matches[0])
        
        # Extract capacity
        capacity_matches = self.patterns['capacity'].findall(normalized)
        if capacity_matches:
            specs['capacity'] = float(capacity_matches[0])
        
        # Extract power/BTU
        power_matches = self.patterns['power'].findall(normalized)
        if power_matches:
            power_str = power_matches[0].replace(',', '')
            specs['power'] = float(power_str)
            
            # Determine power type
            if 'btu' in normalized or 'บีทียู' in text:
                specs['power_unit'] = 'btu'
            elif 'hp' in normalized or 'แรงม้า' in text:
                specs['power_unit'] = 'hp'
            else:
                specs['power_unit'] = 'watt'
        
        # Extract voltage
        voltage_matches = self.patterns['voltage'].findall(normalized)
        if voltage_matches:
            specs['voltage'] = int(voltage_matches[0])
        
        # Extract features
        features = []
        feature_keywords = {
            'inverter': ['inverter', 'อินเวอร์เตอร์', 'อินเวอเตอร์'],
            'wifi': ['wifi', 'ไวไฟ', 'wireless', 'ไร้สาย'],
            'smart': ['smart', 'สมาร์ท', 'สมาร์ต', 'iot'],
            'quiet': ['quiet', 'เงียบ', 'ไร้เสียง', 'silent'],
            'eco': ['eco', 'ประหยัด', 'energy saving', 'efficient'],
            'turbo': ['turbo', 'เทอร์โบ', 'fast', 'เร็ว'],
            'auto': ['auto', 'automatic', 'อัตโนมัติ', 'ออโต้'],
        }
        
        for feature, keywords in feature_keywords.items():
            if any(kw in normalized or kw in text for kw in keywords):
                features.append(feature)
        
        if features:
            specs['features'] = features
        
        # Extract color
        color_patterns = [
            (r'สี\s*(\S+)', 'color'),
            (r'color[:\s]+(\S+)', 'color'),
            (r'(\S+)\s*color', 'color'),
        ]
        
        for pattern, key in color_patterns:
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            if matches:
                specs[key] = self.normalize_specification(matches[0])
                break
        
        # Extract warranty
        warranty_patterns = [
            r'(?:รับประกัน|warranty)[:\s]*(\d+)\s*(?:ปี|year)',
            r'(\d+)\s*(?:ปี|year)\s*(?:รับประกัน|warranty)',
            r'(?:ประกัน|guarantee)[:\s]*(\d+)\s*(?:ปี|year)',
        ]
        
        for pattern in warranty_patterns:
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            if matches:
                specs['warranty_years'] = int(matches[0])
                break
        
        # Extract door count (for refrigerators)
        door_patterns = [
            (r'(\d+)\s*(?:ประตู|door)', 'doors'),
            (r'(?:ประตูเดียว|single door)', 'doors'),
            (r'(?:สองประตู|two door|2 door)', 'doors'),
            (r'(?:side by side|ไซด์บายไซด์)', 'door_type'),
            (r'(?:multi door|มัลติดอร์)', 'door_type'),
        ]
        
        for pattern, key in door_patterns:
            if key == 'doors' and pattern.startswith('('):
                matches = re.findall(pattern, normalized, re.IGNORECASE)
                if matches:
                    specs[key] = int(matches[0])
                    break
            else:
                if re.search(pattern, normalized, re.IGNORECASE):
                    if 'เดียว' in pattern or 'single' in pattern:
                        specs['doors'] = 1
                    elif 'สอง' in pattern or 'two' in pattern:
                        specs['doors'] = 2
                    elif 'side by side' in pattern:
                        specs['door_type'] = 'side_by_side'
                    elif 'multi' in pattern:
                        specs['door_type'] = 'multi'
                    break
        
        return specs
    
    def extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name with enhanced matching"""
        if not text:
            return None
        
        normalized = self.normalize(text)
        
        # Check for known brands (both Thai and English)
        for brand_variant, normalized_brand in self.brand_mappings.items():
            if brand_variant.lower() in text.lower():
                return normalized_brand
            if normalized_brand in normalized:
                return normalized_brand
        
        # Try pattern-based extraction
        brand_patterns = [
            r'(?:ยี่ห้อ|brand|แบรนด์)[:\s]+(\S+)',
            r'^(\S+)\s+(?:รุ่น|model)',
            r'^([A-Za-z]+)\s+[A-Z0-9-]+',  # Brand followed by model
            r'by\s+(\S+)',
            r'from\s+(\S+)',
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            if matches:
                potential_brand = matches[0].lower()
                # Check if it's a known brand
                if potential_brand in self.brand_mappings.values():
                    return potential_brand
                # Check partial match
                for known_brand in self.brand_mappings.values():
                    if known_brand in potential_brand or potential_brand in known_brand:
                        return known_brand
        
        return None
    
    def is_thai_text(self, text: str) -> bool:
        """Check if text contains Thai characters"""
        if not text:
            return False
        return bool(self.patterns['thai_chars'].search(text))
    
    def is_mixed_language(self, text: str) -> bool:
        """Check if text contains both Thai and English"""
        if not text:
            return False
        has_thai = bool(self.patterns['thai_chars'].search(text))
        has_english = bool(self.patterns['english_chars'].search(text))
        return has_thai and has_english
    
    def segment_thai_text(self, text: str) -> List[str]:
        """Segment Thai text using pythainlp or fallback method"""
        if not text:
            return []
        
        if HAS_PYTHAINLP:
            try:
                # Use newmm engine for better accuracy
                return word_tokenize(text, engine='newmm')
            except:
                pass
        
        # Fallback: simple segmentation
        # This is a very basic implementation
        segments = []
        current = []
        
        for i, char in enumerate(text):
            if char.isspace():
                if current:
                    segments.append(''.join(current))
                    current = []
            elif i > 0 and self._is_word_boundary(text[i-1], char):
                if current:
                    segments.append(''.join(current))
                    current = [char]
                else:
                    current.append(char)
            else:
                current.append(char)
        
        if current:
            segments.append(''.join(current))
        
        return segments
    
    def _is_word_boundary(self, prev_char: str, curr_char: str) -> bool:
        """Simple heuristic for Thai word boundaries"""
        # Thai to English or vice versa
        if self.patterns['thai_chars'].match(prev_char) and self.patterns['english_chars'].match(curr_char):
            return True
        if self.patterns['english_chars'].match(prev_char) and self.patterns['thai_chars'].match(curr_char):
            return True
        # Number boundaries
        if prev_char.isalpha() and curr_char.isdigit():
            return True
        if prev_char.isdigit() and curr_char.isalpha():
            return True
        return False
    
    def romanize_thai(self, text: str) -> str:
        """Convert Thai text to romanized form"""
        if not self.is_thai_text(text):
            return text
        
        if HAS_PYTHAINLP:
            try:
                return romanize(text)
            except:
                pass
        
        # Fallback: basic romanization using phonetic rules
        romanized = text
        for thai_char, roman_options in self.phonetic_rules.items():
            if thai_char in romanized and roman_options:
                romanized = romanized.replace(thai_char, roman_options[0])
        
        return romanized
    
    def get_phonetic_variations(self, text: str) -> List[str]:
        """Get phonetic variations of text for matching"""
        variations = [text]
        
        if self.is_thai_text(text):
            # Add romanized version
            romanized = self.romanize_thai(text)
            if romanized != text:
                variations.append(romanized)
            
            # Add variations with different romanization choices
            if HAS_PYTHAINLP:
                # Could add different romanization engines here
                pass
        else:
            # English text - add common variations
            # Remove common suffixes
            suffixes = ['s', 'es', 'ed', 'ing', 'er', 'est']
            for suffix in suffixes:
                if text.endswith(suffix) and len(text) > len(suffix) + 2:
                    variations.append(text[:-len(suffix)])
            
            # Add phonetic variations
            phonetic_subs = [
                ('ph', 'f'), ('ck', 'k'), ('x', 'ks'),
                ('tion', 'sion'), ('tial', 'cial'),
                ('ough', 'o'), ('augh', 'aw'),
            ]
            
            for old, new in phonetic_subs:
                if old in text:
                    variations.append(text.replace(old, new))
        
        return list(set(variations))
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity with multilingual support"""
        # Normalize texts
        norm1 = self.normalize(text1)
        norm2 = self.normalize(text2)
        
        # Quick exact match check
        if norm1 == norm2:
            return 1.0
        
        # Extract and compare tokens
        tokens1 = set(self.extract_tokens(text1))
        tokens2 = set(self.extract_tokens(text2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0
        
        # Check for cross-language matches
        cross_lang_boost = 0.0
        if self.is_mixed_language(text1) or self.is_mixed_language(text2):
            # Check if important terms match across languages
            for token1 in tokens1:
                variations1 = self.get_phonetic_variations(token1)
                for token2 in tokens2:
                    if any(v in token2 or token2 in v for v in variations1):
                        cross_lang_boost += 0.1
        
        # Boost for matching important terms
        important_terms = {'model', 'รุ่น', 'size', 'ขนาด', 'btu', 'บีทียู'}
        important_matches = sum(1 for t in intersection if any(imp in t for imp in important_terms))
        importance_boost = min(0.2, important_matches * 0.05)
        
        # Final score
        final_score = min(1.0, jaccard + cross_lang_boost + importance_boost)
        
        return final_score