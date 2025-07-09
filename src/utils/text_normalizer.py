"""
Advanced text normalization utilities for Thai/English product matching
Handles various text formats, units, and language-specific patterns
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TextNormalizer:
    """Advanced text normalizer for product name matching"""
    
    def __init__(self):
        # Thai-English brand mappings
        self.brand_mappings = {
            # Electronics brands
            'มิตซูบิชิ': 'mitsubishi',
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
            
            # Construction brands
            'เอสซีจี': 'scg',
            'ทีโอเอ': 'toa',
            'จระเข้': 'crocodile',
            'ตราช้าง': 'elephant',
            
            # Common variations
            'แอร์': 'air',
            'เครื่องปรับอากาศ': 'air conditioner',
            'ตู้เย็น': 'refrigerator',
            'เครื่องซักผ้า': 'washing machine',
            'ทีวี': 'tv',
            'โทรทัศน์': 'television',
        }
        
        # Unit conversions
        self.unit_mappings = {
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
            
            # Power units
            'วัตต์': 'w',
            'กิโลวัตต์': 'kw',
            'แรงม้า': 'hp',
            'บีทียู': 'btu',
            
            # Electrical units
            'โวลต์': 'v',
            'แอมป์': 'a',
            'เฮิรตซ์': 'hz',
        }
        
        # Common stop words to remove
        self.stop_words = {
            # Thai
            'และ', 'หรือ', 'กับ', 'ของ', 'ใน', 'ที่', 'นี้', 'นั้น',
            'จาก', 'ถึง', 'แล้ว', 'ด้วย', 'โดย', 'เพื่อ', 'แบบ', 'รุ่น',
            
            # English
            'and', 'or', 'with', 'for', 'the', 'a', 'an', 'of', 'in',
            'on', 'at', 'to', 'from', 'by', 'model', 'type', 'series'
        }
        
        # Pattern to extract model numbers
        self.model_patterns = [
            r'\b([A-Z]{1,3}[-\s]?[A-Z]?\d{2,6}[A-Z]?)\b',  # MS-123A, RAS-10NK, MSY-KP13VF
            r'\b(\d{2,4}[A-Z]{1,3}\d*)\b',  # 32LM550, 55UN7300
            r'\b([A-Z]\d{2,4}[A-Z]?)\b',  # S100H, M506B
            r'\b(\d{1,2}[,.]?\d{3})\s*(?:BTU|บีทียู)\b',  # 9,000 BTU, 12000BTU, 12,000 บีทียู
            r'\b(\d+)\s*(?:L|l|ลิตร)\b',  # 250L, 300 ลิตร
            r'\b(\d+)\s*(?:inch|นิ้ว|")\b',  # 55 inch, 32"
        ]

    def normalize(self, text: str) -> str:
        """Main normalization function"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Replace Thai brands with English equivalents
        normalized = self._replace_brands(normalized)
        
        # Normalize units
        normalized = self._normalize_units(normalized)
        
        # Extract and preserve model numbers
        model_numbers = self._extract_model_numbers(text)
        
        # Remove special characters but preserve numbers
        normalized = self._clean_special_chars(normalized)
        
        # Remove stop words
        normalized = self._remove_stop_words(normalized)
        
        # Re-add model numbers at the end
        if model_numbers:
            normalized += ' ' + ' '.join(model_numbers)
        
        # Clean up whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU or model number from text"""
        # Special patterns for SKU/Model extraction
        sku_patterns = [
            # Specific model patterns
            r'\b(MSY-KP[0-9]+[A-Z]*)\b',  # MSY-KP13VF
            r'\b(FTKF[0-9]+[A-Z0-9]*)\b',  # FTKF24UV2S
            r'\b(CS-[A-Z0-9]+)\b',  # CS-PU24WKT
            r'\b(WW[0-9]+[A-Z][0-9]+[A-Z]+[/-][A-Z]+)\b',  # WW90T554DAW/ST
            r'\b(RT[0-9]+[A-Z]+[0-9]*[A-Z]*[/-][A-Z]+)\b',  # RT22FGRADSA/ST
            r'\b(GN-[A-Z][0-9]+[A-Z]+)\b',  # GN-X392PBGB
            r'\b(NA-[A-Z][0-9]+[A-Z]?[0-9]*)\b',  # NA-F70B3
            r'\brุ่น\s+([A-Z]+[-]?[A-Z]*[0-9]+[A-Z0-9]*)\b',  # รุ่น CS-PU24WKT
            r'\bModel[:\s]+([A-Z0-9]+[-/]?[A-Z0-9]+(?:[-/][A-Z0-9]+)?)\b',  # Model: WW90T554DAW/ST
            r'\bSKU[:\s]+([A-Z0-9]+[-][0-9]+[-][0-9]+)\b',  # SKU: MH-2023-001
            r'\bCode[:\s]+([A-Z]+[-][0-9]+[-][A-Z0-9]+)\b',  # Product Code: ABC-123-XYZ
            # Generic pattern for model numbers with at least one digit
            r'\b([A-Z][A-Z0-9]*[-]?[A-Z0-9]*[0-9]+[A-Z0-9]*)\b',  # Any alphanumeric with digits
        ]
        
        # List of known brand names to exclude
        brand_names = {
            'MITSUBISHI', 'SAMSUNG', 'LG', 'PANASONIC', 'TOSHIBA', 'SHARP',
            'DAIKIN', 'FUJITSU', 'HAIER', 'ELECTROLUX', 'PHILIPS', 'SONY',
            'HATARI', 'BEKO', 'BOSCH', 'SIEMENS', 'HITACHI', 'CARRIER'
        }
        
        # Try each pattern
        for pattern in sku_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                sku = match
                if isinstance(sku, tuple):
                    sku = sku[0]
                
                # Skip if it's a known brand name
                if sku.upper() in brand_names:
                    continue
                
                # Skip if it's just numbers (likely BTU, size, etc.)
                if sku.replace('-', '').replace('/', '').isdigit():
                    continue
                    
                # Skip if it's too short
                if len(sku) < 4:
                    continue
                
                # Must contain at least one digit
                if not any(c.isdigit() for c in sku):
                    continue
                
                return sku.upper().replace(' ', '-')
        
        return None
    
    def normalize_sku(self, sku: str) -> str:
        """Normalize SKU for comparison"""
        if not sku:
            return ""
        # Remove spaces, dashes, slashes and convert to uppercase
        return sku.upper().replace('-', '').replace('/', '').replace(' ', '')
    
    def compare_skus(self, sku1: Optional[str], sku2: Optional[str]) -> bool:
        """Compare two SKUs with normalization"""
        if not sku1 or not sku2:
            return False
        
        norm1 = self.normalize_sku(sku1)
        norm2 = self.normalize_sku(sku2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Check if one is a substring of the other (partial SKU match)
        if len(norm1) >= 6 and len(norm2) >= 6:
            if norm1 in norm2 or norm2 in norm1:
                return True
        
        return False
    
    def extract_specifications(self, text: str) -> Dict[str, str]:
        """Extract key specifications from product text"""
        specs = {}
        
        # Extract capacity (BTU for AC, Liters for fridge, etc.)
        btu_match = re.search(r'(\d{1,2}[,.]?\d{3})\s*(?:BTU|บีทียู)', text, re.IGNORECASE)
        if btu_match:
            specs['capacity_btu'] = btu_match.group(1).replace(',', '')
        
        # Extract size/dimensions
        size_match = re.search(r'(\d+\.?\d*)\s*(?:inch|นิ้ว|")', text, re.IGNORECASE)
        if size_match:
            specs['size_inch'] = size_match.group(1)
        
        # Extract volume/capacity
        volume_match = re.search(r'(\d+\.?\d*)\s*(?:L|l|ลิตร|liters?)', text, re.IGNORECASE)
        if volume_match:
            specs['volume_liters'] = volume_match.group(1)
        
        # Extract power
        power_match = re.search(r'(\d+\.?\d*)\s*(?:W|w|วัตต์|watts?)', text, re.IGNORECASE)
        if power_match:
            specs['power_watts'] = power_match.group(1)
        
        # Extract weight
        weight_match = re.search(r'(\d+\.?\d*)\s*(?:kg|กก\.|กิโลกรัม)', text, re.IGNORECASE)
        if weight_match:
            specs['weight_kg'] = weight_match.group(1)
        
        return specs
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two normalized texts"""
        # Normalize both texts
        norm1 = self.normalize(text1)
        norm2 = self.normalize(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Token-based similarity
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        jaccard = len(intersection) / len(union) if union else 0
        
        # Check for important tokens (brand, model)
        important_match = 0
        for token in intersection:
            if len(token) > 5 or any(c.isdigit() for c in token):
                important_match += 0.1
        
        # Combine scores
        similarity = min(1.0, jaccard + important_match)
        
        return similarity
    
    def _replace_brands(self, text: str) -> str:
        """Replace Thai brand names with English equivalents"""
        for thai, english in self.brand_mappings.items():
            text = text.replace(thai, english)
        return text
    
    def _normalize_units(self, text: str) -> str:
        """Normalize unit representations"""
        for thai, english in self.unit_mappings.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(thai) + r'\b'
            text = re.sub(pattern, english, text, flags=re.IGNORECASE)
        return text
    
    def _extract_model_numbers(self, text: str) -> List[str]:
        """Extract model numbers from text"""
        model_numbers = []
        
        for pattern in self.model_patterns[:3]:  # Only use alphanumeric patterns
            matches = re.findall(pattern, text)
            model_numbers.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in model_numbers:
            if isinstance(model, tuple):
                model = model[0]
            if model.upper() not in seen:
                seen.add(model.upper())
                unique_models.append(model.upper())
        
        return unique_models
    
    def _clean_special_chars(self, text: str) -> str:
        """Remove special characters while preserving important ones"""
        # Keep alphanumeric (including Thai), spaces, and some punctuation
        # Thai unicode range: \u0E00-\u0E7F
        text = re.sub(r'[^\w\s\-,.ก-๙]', ' ', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _remove_stop_words(self, text: str) -> str:
        """Remove stop words from text"""
        words = text.split()
        filtered = [word for word in words if word not in self.stop_words]
        return ' '.join(filtered)


class ProductMatcher:
    """Enhanced product matcher using advanced normalization"""
    
    def __init__(self):
        self.normalizer = TextNormalizer()
    
    def match_products(self, product1_name: str, product2_name: str, 
                      brand1: Optional[str] = None, brand2: Optional[str] = None) -> Dict[str, float]:
        """Match two products and return detailed scores"""
        
        # Extract SKUs
        sku1 = self.normalizer.extract_sku(product1_name)
        sku2 = self.normalizer.extract_sku(product2_name)
        
        # Extract specifications
        specs1 = self.normalizer.extract_specifications(product1_name)
        specs2 = self.normalizer.extract_specifications(product2_name)
        
        # Calculate name similarity
        name_similarity = self.normalizer.calculate_similarity(product1_name, product2_name)
        
        # SKU match (highest priority)
        sku_match = 1.0 if self.normalizer.compare_skus(sku1, sku2) else 0.0
        
        # Brand match
        brand_match = 0.0
        if brand1 and brand2:
            brand_similarity = self.normalizer.calculate_similarity(brand1, brand2)
            brand_match = 1.0 if brand_similarity > 0.8 else brand_similarity
        
        # Specification match
        spec_match = self._calculate_spec_match(specs1, specs2)
        
        # Calculate overall confidence
        if sku_match == 1.0:
            confidence = 0.95  # Very high confidence for SKU match
        else:
            confidence = (
                name_similarity * 0.4 +
                brand_match * 0.3 +
                spec_match * 0.3
            )
        
        return {
            'overall_confidence': confidence,
            'name_similarity': name_similarity,
            'sku_match': sku_match,
            'brand_match': brand_match,
            'spec_match': spec_match,
            'sku1': sku1,
            'sku2': sku2,
            'specs1': specs1,
            'specs2': specs2
        }
    
    def _calculate_spec_match(self, specs1: Dict[str, str], specs2: Dict[str, str]) -> float:
        """Calculate specification match score"""
        if not specs1 or not specs2:
            return 0.0
        
        common_keys = set(specs1.keys()) & set(specs2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            val1 = float(specs1[key]) if specs1[key].replace('.', '').isdigit() else specs1[key]
            val2 = float(specs2[key]) if specs2[key].replace('.', '').isdigit() else specs2[key]
            
            if isinstance(val1, float) and isinstance(val2, float):
                # Allow 5% tolerance for numeric values
                if abs(val1 - val2) / max(val1, val2) < 0.05:
                    matches += 1
            elif val1 == val2:
                matches += 1
        
        return matches / len(common_keys) if common_keys else 0.0


# Example usage and testing
if __name__ == "__main__":
    normalizer = TextNormalizer()
    matcher = ProductMatcher()
    
    # Test cases
    test_products = [
        ("MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU", "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู"),
        ("Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8", "ซัมซุง ตู้เย็น 2 ประตู 300L รุ่น RT29K5511S8"),
        ("LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC", "แอลจี สมาร์ททีวี 55\" 55UN7300PTC"),
    ]
    
    for prod1, prod2 in test_products:
        print(f"\nComparing:")
        print(f"  Product 1: {prod1}")
        print(f"  Product 2: {prod2}")
        
        match_result = matcher.match_products(prod1, prod2)
        print(f"  Match confidence: {match_result['overall_confidence']:.2%}")
        print(f"  Details: {match_result}")