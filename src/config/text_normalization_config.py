"""
Configuration for text normalization and product matching
Edit this file to customize brand mappings, units, patterns, and thresholds
"""

# Thai-English brand mappings
BRAND_MAPPINGS = {
    # Electronics brands
    'มิตซูบิชิ': 'mitsubishi',
    'มิตซู': 'mitsubishi',
    'ซัมซุง': 'samsung',
    'แอลจี': 'lg',
    'พานาโซนิค': 'panasonic',
    'โตชิบา': 'toshiba',
    'ชาร์ป': 'sharp',
    'ไดกิ้น': 'daikin',
    'ฟูจิตสึ': 'fujitsu',
    'ไฮเออร์': 'haier',
    'อีเลคโทรลักซ์': 'electrolux',
    'ฟิลิปส์': 'philips',
    'โซนี่': 'sony',
    'ฮิตาชิ': 'hitachi',
    'แคเรียร์': 'carrier',
    'แฮทารี': 'hatari',
    'เบโก': 'beko',
    'บอช': 'bosch',
    'ซีเมนส์': 'siemens',
    
    # Power tool brands
    'มากิต้า': 'makita',
    'ดีวอลท์': 'dewalt',
    'มิลวอกี': 'milwaukee',
    'ฮิลติ': 'hilti',
    'แบล็คแอนด์เดคเกอร์': 'black decker',
    'ไรโอบิ': 'ryobi',
    'เฟสตูล': 'festool',
    
    # Construction brands
    'เอสซีจี': 'scg',
    'ทีโอเอ': 'toa',
    'จระเข้': 'crocodile',
    'ตราช้าง': 'elephant',
    'ตราเพชร': 'diamond',
    'ไวท์ซีเมนท์': 'white cement',
    
    # Common product terms
    'แอร์': 'air conditioner',
    'เครื่องปรับอากาศ': 'air conditioner',
    'เครืองปรับอากาศ': 'air conditioner',
    'ตู้เย็น': 'refrigerator',
    'เครื่องซักผ้า': 'washing machine',
    'ทีวี': 'tv',
    'โทรทัศน์': 'television',
    'เครื่องดูดฝุ่น': 'vacuum cleaner',
    'ไมโครเวฟ': 'microwave',
    'หม้อหุงข้าว': 'rice cooker',
    'พัดลม': 'fan',
    'เครื่องทำน้ำอุ่น': 'water heater',
    'เครื่องฟอกอากาศ': 'air purifier',
    'เครื่องลดความชื้น': 'dehumidifier',
    'เครื่องเพิ่มความชื้น': 'humidifier',
}

# Unit conversions (Thai to English)
UNIT_MAPPINGS = {
    # Size units
    'นิ้ว': 'inch',
    'ฟุต': 'ft',
    'เมตร': 'm',
    'ซม.': 'cm',
    'ซม': 'cm',
    'มม.': 'mm',
    'มม': 'mm',
    'ตร.ม.': 'sqm',
    'ตารางเมตร': 'sqm',
    
    # Capacity units
    'ลิตร': 'l',
    'แกลลอน': 'gal',
    'กิโลกรัม': 'kg',
    'กก.': 'kg',
    'กรัม': 'g',
    'ตัน': 'ton',
    
    # Power units
    'วัตต์': 'w',
    'กิโลวัตต์': 'kw',
    'แรงม้า': 'hp',
    'บีทียู': 'btu',
    
    # Electrical units
    'โวลต์': 'v',
    'แอมป์': 'a',
    'เฮิรตซ์': 'hz',
    'แอมแปร์': 'amp',
    
    # Pressure units
    'บาร์': 'bar',
    'พีเอสไอ': 'psi',
    'ปอนด์': 'lb',
    
    # Temperature units
    'เซลเซียส': 'celsius',
    'ฟาเรนไฮต์': 'fahrenheit',
    'องศา': 'degree',
}

# Stop words to remove during normalization
STOP_WORDS = {
    # Thai stop words
    'และ', 'หรือ', 'กับ', 'ของ', 'ใน', 'ที่', 'นี้', 'นั้น',
    'จาก', 'ถึง', 'แล้ว', 'ด้วย', 'โดย', 'เพื่อ', 'แบบ', 'รุ่น',
    'ชิ้น', 'ตัว', 'เครื่อง', 'อัน', 'ใบ', 'ลูก', 'ชุด', 'คู่',
    'สี', 'ขาว', 'ดำ', 'แดง', 'น้ำเงิน', 'เขียว', 'เหลือง',
    'ใหม่', 'เก่า', 'ดี', 'เยี่ยม', 'ยอดนิยม', 'ขายดี',
    
    # English stop words
    'and', 'or', 'with', 'for', 'the', 'a', 'an', 'of', 'in',
    'on', 'at', 'to', 'from', 'by', 'model', 'type', 'series',
    'new', 'old', 'good', 'best', 'popular', 'top', 'brand',
    'piece', 'unit', 'set', 'pair', 'item', 'product',
    'white', 'black', 'red', 'blue', 'green', 'yellow',
    'color', 'colour', 'size', 'large', 'small', 'medium',
}

# Patterns for extracting model numbers and SKUs
MODEL_PATTERNS = [
    # Standard model patterns
    r'\b([A-Z]{1,3}[-\s]?[A-Z]?\d{2,6}[A-Z]?)\b',  # MS-123A, RAS-10NK, MSY-KP13VF
    r'\b(\d{2,4}[A-Z]{1,3}\d*)\b',  # 32LM550, 55UN7300
    r'\b([A-Z]\d{2,4}[A-Z]?)\b',  # S100H, M506B
    r'\b(\d{1,2}[,.]?\d{3})\s*(?:BTU|บีทียู)\b',  # 9,000 BTU, 12000BTU
    r'\b(\d+)\s*(?:L|l|ลิตร)\b',  # 250L, 300 ลิตร
    r'\b(\d+)\s*(?:inch|นิ้ว|")\b',  # 55 inch, 32"
    r'\b(\d+)\s*(?:W|w|วัตต์)\b',  # 1500W, 2000 วัตต์
    r'\b(\d+)\s*(?:V|v|โวลต์)\b',  # 220V, 110 โวลต์
    r'\b(\d+)\s*(?:A|a|แอมป์)\b',  # 10A, 15 แอมป์
    r'\b(\d+)\s*(?:Hz|hz|เฮิรตซ์)\b',  # 50Hz, 60 เฮิรตซ์
]

# SKU extraction patterns (more specific)
SKU_PATTERNS = [
    # Brand-specific patterns
    r'\b(MSY-KP[0-9]+[A-Z]*)\b',  # MSY-KP13VF
    r'\b(FTKF[0-9]+[A-Z0-9]*)\b',  # FTKF24UV2S
    r'\b(CS-[A-Z0-9]+)\b',  # CS-PU24WKT
    r'\b(WW[0-9]+[A-Z][0-9]+[A-Z]+[/-][A-Z]+)\b',  # WW90T554DAW/ST
    r'\b(RT[0-9]+[A-Z]+[0-9]*[A-Z]*[/-][A-Z]+)\b',  # RT22FGRADSA/ST
    r'\b(GN-[A-Z][0-9]+[A-Z]+)\b',  # GN-X392PBGB
    r'\b(NA-[A-Z][0-9]+[A-Z]?[0-9]*)\b',  # NA-F70B3
    r'\b(UN[0-9]+[A-Z]+[0-9]*[A-Z]*)\b',  # UN43AU7000
    r'\b(QN[0-9]+[A-Z]+[0-9]*[A-Z]*)\b',  # QN65Q70A
    r'\b(KD-[0-9]+[A-Z]+[0-9]*[A-Z]*)\b',  # KD-55X80J
    
    # Thai model patterns
    r'\bรุ่น\s+([A-Z]+[-]?[A-Z]*[0-9]+[A-Z0-9]*)\b',  # รุ่น CS-PU24WKT
    r'\bModel[:\s]+([A-Z0-9]+[-/]?[A-Z0-9]+(?:[-/][A-Z0-9]+)?)\b',  # Model: WW90T554DAW/ST
    r'\bSKU[:\s]+([A-Z0-9]+[-][0-9]+[-][0-9]+)\b',  # SKU: MH-2023-001
    r'\bCode[:\s]+([A-Z]+[-][0-9]+[-][A-Z0-9]+)\b',  # Product Code: ABC-123-XYZ
    
    # Generic patterns
    r'\b([A-Z][A-Z0-9]*[-]?[A-Z0-9]*[0-9]+[A-Z0-9]*)\b',  # Any alphanumeric with digits
    r'\b([0-9]+[A-Z]+[0-9]+[A-Z]*)\b',  # Numbers + letters + numbers
]

# Brand names to exclude from SKU extraction
BRAND_EXCLUSIONS = {
    'MITSUBISHI', 'SAMSUNG', 'LG', 'PANASONIC', 'TOSHIBA', 'SHARP',
    'DAIKIN', 'FUJITSU', 'HAIER', 'ELECTROLUX', 'PHILIPS', 'SONY',
    'HATARI', 'BEKO', 'BOSCH', 'SIEMENS', 'HITACHI', 'CARRIER',
    'MAKITA', 'DEWALT', 'MILWAUKEE', 'HILTI', 'RYOBI', 'FESTOOL',
    'SCG', 'TOA', 'CROCODILE', 'ELEPHANT', 'DIAMOND',
    'BLACK', 'DECKER', 'WHITE', 'CEMENT', 'PROFESSIONAL'
}

# Matching thresholds and weights
MATCHING_THRESHOLDS = {
    'min_confidence': 0.7,
    'name_similarity_min': 0.75,
    'brand_exact_match_bonus': 0.15,
    'category_match_bonus': 0.10,
    'specification_match_bonus': 0.05,
    'price_tolerance': 0.20,  # 20% price difference allowed
    'sku_match_confidence': 0.95,
    'fuzzy_threshold': 0.8,
}

# Confidence calculation weights
CONFIDENCE_WEIGHTS = {
    'name_similarity': 0.4,
    'brand_match': 0.3,
    'spec_match': 0.2,
    'price_match': 0.1,
    'sku_boost': 0.3,  # Additional boost for SKU matches
}

# Specification matching tolerances
SPEC_TOLERANCES = {
    'capacity_btu': 0.05,  # 5% tolerance
    'size_inch': 0.02,     # 2% tolerance
    'volume_liters': 0.05,  # 5% tolerance
    'power_watts': 0.10,    # 10% tolerance
    'weight_kg': 0.15,      # 15% tolerance
    'voltage_v': 0.05,      # 5% tolerance
    'frequency_hz': 0.02,   # 2% tolerance
}

# Text processing settings
TEXT_PROCESSING = {
    'min_sku_length': 4,
    'max_sku_length': 20,
    'min_model_length': 3,
    'preserve_case_patterns': [
        r'\b[A-Z]{2,}\b',  # Keep all-caps words
        r'\b[a-z]+[A-Z][a-z]*\b',  # Keep camelCase
    ],
    'unicode_normalization': 'NFKC',
    'remove_accents': True,
    'preserve_numbers': True,
    'preserve_hyphens': True,
}

# Performance settings
PERFORMANCE = {
    'cache_size': 10000,
    'batch_size': 1000,
    'parallel_workers': 4,
    'timeout_seconds': 30,
    'max_comparisons': 100000,
}

# Debugging and logging
DEBUG_SETTINGS = {
    'log_level': 'INFO',
    'log_matches': False,
    'log_performance': True,
    'save_failed_matches': True,
    'detailed_scoring': False,
}

# Export commonly used configurations
DEFAULT_CONFIG = {
    'brand_mappings': BRAND_MAPPINGS,
    'unit_mappings': UNIT_MAPPINGS,
    'stop_words': STOP_WORDS,
    'model_patterns': MODEL_PATTERNS,
    'sku_patterns': SKU_PATTERNS,
    'brand_exclusions': BRAND_EXCLUSIONS,
    'thresholds': MATCHING_THRESHOLDS,
    'weights': CONFIDENCE_WEIGHTS,
    'spec_tolerances': SPEC_TOLERANCES,
    'text_processing': TEXT_PROCESSING,
    'performance': PERFORMANCE,
    'debug': DEBUG_SETTINGS,
}