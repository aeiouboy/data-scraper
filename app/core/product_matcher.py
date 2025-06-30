"""
Automated product matching algorithm using fuzzy matching
"""
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import re
from difflib import SequenceMatcher
from rapidfuzz import fuzz, process
from collections import defaultdict

from app.models.product import Product
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


@dataclass
class MatchCandidate:
    """Product match candidate with similarity scores"""
    product: Product
    name_similarity: float
    sku_similarity: float
    brand_similarity: float
    price_similarity: float
    overall_score: float
    match_confidence: str  # 'high', 'medium', 'low', 'no_match'


@dataclass
class MatchResult:
    """Result of product matching operation"""
    matched_groups: List[List[Product]]
    unmatched_products: List[Product]
    total_products: int
    match_rate: float
    timestamp: datetime


class ProductMatcher:
    """
    Intelligent product matching across retailers
    Uses multiple signals to identify same products:
    - Product name similarity
    - SKU/model number matching
    - Brand matching
    - Price range similarity
    - Category alignment
    """
    
    # Similarity thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    LOW_CONFIDENCE_THRESHOLD = 0.55
    
    # Weight configuration for overall score
    WEIGHTS = {
        'name': 0.40,
        'sku': 0.30,
        'brand': 0.20,
        'price': 0.10
    }
    
    def __init__(self):
        self.brand_aliases = self._load_brand_aliases()
        self.common_words = self._load_common_words()
        
    def _load_brand_aliases(self) -> Dict[str, str]:
        """Load brand name aliases and variations"""
        return {
            # Electronics
            'lg': 'lg',
            'แอลจี': 'lg',
            'samsung': 'samsung',
            'ซัมซุง': 'samsung',
            'panasonic': 'panasonic',
            'พานาโซนิค': 'panasonic',
            'sharp': 'sharp',
            'ชาร์ป': 'sharp',
            'hitachi': 'hitachi',
            'ฮิตาชิ': 'hitachi',
            'mitsubishi': 'mitsubishi',
            'มิตซูบิชิ': 'mitsubishi',
            'daikin': 'daikin',
            'ไดกิ้น': 'daikin',
            # Sanitary
            'cotto': 'cotto',
            'คอตโต้': 'cotto',
            'kohler': 'kohler',
            'โคห์เลอร์': 'kohler',
            'american standard': 'american standard',
            'อเมริกันสแตนดาร์ด': 'american standard',
            'toto': 'toto',
            'โตโต้': 'toto',
            # Tools
            'bosch': 'bosch',
            'บ๊อช': 'bosch',
            'makita': 'makita',
            'มากิต้า': 'makita',
            'stanley': 'stanley',
            'สแตนเลย์': 'stanley',
        }
    
    def _load_common_words(self) -> Set[str]:
        """Load common words to ignore in matching"""
        return {
            # Thai
            'ชุด', 'เซต', 'แพ็ค', 'กล่อง', 'ถุง', 'ขวด', 'หลอด', 'ชิ้น',
            'รุ่น', 'แบบ', 'ขนาด', 'สี', 'ราคา', 'พิเศษ', 'ลด', 'ถูก',
            # English
            'set', 'pack', 'box', 'bag', 'bottle', 'piece', 'pcs',
            'model', 'type', 'size', 'color', 'price', 'special', 'sale',
            # Units
            'mm', 'cm', 'm', 'ml', 'l', 'g', 'kg', 'w', 'v', 'a',
            'มม', 'ซม', 'ม', 'มล', 'ล', 'กรัม', 'กก', 'วัตต์', 'โวลต์', 'แอมป์'
        }
    
    async def find_matches(self, products: List[Product]) -> MatchResult:
        """
        Find matching products across retailers
        
        Args:
            products: List of products to match
            
        Returns:
            MatchResult with grouped matches
        """
        start_time = datetime.now()
        
        # Group products by category first for efficiency
        category_groups = self._group_by_category(products)
        
        matched_groups = []
        unmatched = []
        
        for category, category_products in category_groups.items():
            # Skip if only one product in category
            if len(category_products) < 2:
                unmatched.extend(category_products)
                continue
            
            # Find matches within category
            category_matches = self._find_matches_in_category(category_products)
            matched_groups.extend(category_matches['groups'])
            unmatched.extend(category_matches['unmatched'])
        
        # Calculate match rate
        total_products = len(products)
        matched_count = sum(len(group) for group in matched_groups)
        match_rate = matched_count / total_products if total_products > 0 else 0
        
        logger.info(f"Product matching completed: {matched_count}/{total_products} products matched ({match_rate:.1%})")
        
        return MatchResult(
            matched_groups=matched_groups,
            unmatched_products=unmatched,
            total_products=total_products,
            match_rate=match_rate,
            timestamp=datetime.now()
        )
    
    def _group_by_category(self, products: List[Product]) -> Dict[str, List[Product]]:
        """Group products by unified category"""
        groups = defaultdict(list)
        for product in products:
            groups[product.unified_category].append(product)
        return dict(groups)
    
    def _find_matches_in_category(self, products: List[Product]) -> Dict:
        """Find matching products within a category"""
        matched_groups = []
        processed = set()
        unmatched = []
        
        for i, product in enumerate(products):
            if i in processed:
                continue
            
            # Find all matches for this product
            matches = []
            for j, candidate in enumerate(products):
                if i == j or j in processed:
                    continue
                
                # Skip if same retailer
                if product.retailer_code == candidate.retailer_code:
                    continue
                
                # Calculate match score
                match_candidate = self._calculate_match_score(product, candidate)
                
                if match_candidate.match_confidence != 'no_match':
                    matches.append((j, match_candidate))
            
            # Process matches
            if matches:
                # Sort by score
                matches.sort(key=lambda x: x[1].overall_score, reverse=True)
                
                # Create match group
                group = [product]
                for idx, match in matches:
                    if match.match_confidence in ['high', 'medium']:
                        group.append(match.product)
                        processed.add(idx)
                
                if len(group) > 1:
                    matched_groups.append(group)
                    processed.add(i)
                else:
                    unmatched.append(product)
            else:
                unmatched.append(product)
        
        return {
            'groups': matched_groups,
            'unmatched': unmatched
        }
    
    def _calculate_match_score(self, product1: Product, product2: Product) -> MatchCandidate:
        """Calculate similarity score between two products"""
        # Name similarity
        name_sim = self._calculate_name_similarity(product1.name, product2.name)
        
        # SKU similarity
        sku_sim = self._calculate_sku_similarity(product1, product2)
        
        # Brand similarity
        brand_sim = self._calculate_brand_similarity(product1.brand, product2.brand)
        
        # Price similarity
        price_sim = self._calculate_price_similarity(
            float(product1.current_price) if product1.current_price else 0,
            float(product2.current_price) if product2.current_price else 0
        )
        
        # Calculate weighted overall score
        overall_score = (
            self.WEIGHTS['name'] * name_sim +
            self.WEIGHTS['sku'] * sku_sim +
            self.WEIGHTS['brand'] * brand_sim +
            self.WEIGHTS['price'] * price_sim
        )
        
        # Determine confidence level
        if overall_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            confidence = 'high'
        elif overall_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = 'medium'
        elif overall_score >= self.LOW_CONFIDENCE_THRESHOLD:
            confidence = 'low'
        else:
            confidence = 'no_match'
        
        # Boost confidence if strong SKU match
        if sku_sim > 0.9 and confidence == 'medium':
            confidence = 'high'
        
        return MatchCandidate(
            product=product2,
            name_similarity=name_sim,
            sku_similarity=sku_sim,
            brand_similarity=brand_sim,
            price_similarity=price_sim,
            overall_score=overall_score,
            match_confidence=confidence
        )
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate product name similarity"""
        # Normalize names
        norm1 = self._normalize_product_name(name1)
        norm2 = self._normalize_product_name(name2)
        
        # Use token sort ratio for better matching of reordered words
        token_score = fuzz.token_sort_ratio(norm1, norm2) / 100
        
        # Also check partial ratio for substring matches
        partial_score = fuzz.partial_ratio(norm1, norm2) / 100
        
        # Weight token score higher
        return 0.7 * token_score + 0.3 * partial_score
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for comparison"""
        # Convert to lowercase
        name = name.lower()
        
        # Remove special characters
        name = re.sub(r'[^\w\s\-]', ' ', name)
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        # Remove common words
        words = name.split()
        filtered_words = [w for w in words if w not in self.common_words]
        
        return ' '.join(filtered_words)
    
    def _calculate_sku_similarity(self, product1: Product, product2: Product) -> float:
        """Calculate SKU/model number similarity"""
        # Extract model numbers from SKUs and names
        models1 = self._extract_model_numbers(product1)
        models2 = self._extract_model_numbers(product2)
        
        if not models1 or not models2:
            return 0.0
        
        # Find best matching model numbers
        best_score = 0.0
        for m1 in models1:
            for m2 in models2:
                # Exact match
                if m1 == m2:
                    return 1.0
                
                # Fuzzy match
                score = fuzz.ratio(m1, m2) / 100
                best_score = max(best_score, score)
        
        return best_score
    
    def _extract_model_numbers(self, product: Product) -> List[str]:
        """Extract potential model numbers from product"""
        models = []
        
        # Pattern for model numbers (alphanumeric codes)
        model_pattern = r'\b[A-Z0-9]{4,}(?:[-][A-Z0-9]+)*\b'
        
        # Check SKU
        if product.sku:
            matches = re.findall(model_pattern, product.sku.upper())
            models.extend(matches)
        
        # Check retailer SKU
        if product.retailer_sku:
            matches = re.findall(model_pattern, product.retailer_sku.upper())
            models.extend(matches)
        
        # Check product name
        matches = re.findall(model_pattern, product.name.upper())
        models.extend(matches)
        
        # Remove duplicates
        return list(set(models))
    
    def _calculate_brand_similarity(self, brand1: Optional[str], brand2: Optional[str]) -> float:
        """Calculate brand similarity"""
        if not brand1 or not brand2:
            return 0.0
        
        # Normalize brands
        norm1 = self._normalize_brand(brand1)
        norm2 = self._normalize_brand(brand2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Fuzzy match
        return fuzz.ratio(norm1, norm2) / 100
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand name"""
        brand = brand.lower().strip()
        
        # Apply aliases
        if brand in self.brand_aliases:
            brand = self.brand_aliases[brand]
        
        return brand
    
    def _calculate_price_similarity(self, price1: float, price2: float) -> float:
        """Calculate price similarity"""
        if price1 == 0 or price2 == 0:
            return 0.0
        
        # Calculate percentage difference
        diff = abs(price1 - price2)
        avg_price = (price1 + price2) / 2
        percentage_diff = diff / avg_price
        
        # Convert to similarity score (closer prices = higher score)
        # Allow up to 20% difference for high similarity
        if percentage_diff <= 0.05:  # Within 5%
            return 1.0
        elif percentage_diff <= 0.10:  # Within 10%
            return 0.8
        elif percentage_diff <= 0.20:  # Within 20%
            return 0.6
        elif percentage_diff <= 0.30:  # Within 30%
            return 0.4
        else:
            return 0.0
    
    async def save_match_groups(self, match_result: MatchResult):
        """Save match groups to database"""
        # Implementation depends on your database schema
        # This is a placeholder for saving matched product groups
        pass
    
    async def find_duplicates_within_retailer(self, retailer_code: str) -> List[List[Product]]:
        """Find potential duplicate products within a single retailer"""
        # Query products for the retailer
        db = SupabaseService()
        result = db.client.table('products').select('*').eq('retailer_code', retailer_code).execute()
        products_data = result.data if result.data else []
        
        # Convert to Product objects
        products = []
        for data in products_data:
            product = Product(
                id=data.get('id'),
                name=data.get('name'),
                sku=data.get('sku'),
                retailer_sku=data.get('retailer_sku'),
                retailer_code=data.get('retailer_code'),
                brand=data.get('brand'),
                category=data.get('category'),
                unified_category=data.get('unified_category'),
                current_price=data.get('current_price'),
                original_price=data.get('original_price'),
                discount_percentage=data.get('discount_percentage'),
                availability=data.get('availability'),
                url=data.get('url'),
                image_url=data.get('image_url'),
                description=data.get('description'),
                specs=data.get('specs'),
                rating=data.get('rating'),
                review_count=data.get('review_count'),
                last_scraped=data.get('last_scraped'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
            products.append(product)
        
        # Group by category
        category_groups = self._group_by_category(products)
        
        duplicates = []
        
        for category, category_products in category_groups.items():
            if len(category_products) < 2:
                continue
            
            # Find very similar products (potential duplicates)
            for i, product1 in enumerate(category_products):
                for j, product2 in enumerate(category_products[i+1:], i+1):
                    # Check name similarity only for duplicates
                    name_sim = self._calculate_name_similarity(product1.name, product2.name)
                    
                    # Very high similarity suggests duplicate
                    if name_sim > 0.95:
                        duplicates.append([product1, product2])
        
        return duplicates