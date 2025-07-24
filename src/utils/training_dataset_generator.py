"""
Training Dataset Generator
Creates labeled datasets from existing product matches for ML training
"""

import json
import csv
import random
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
from datetime import datetime
import hashlib

from src.services.supabase_service import SupabaseService as SupabaseClient
from src.utils.fuzzy_matcher import FuzzyMatcher
from src.utils.semantic_similarity import SemanticSimilarity

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example with features and label"""
    id: str
    product1_name: str
    product2_name: str
    product1_brand: str
    product2_brand: str
    product1_category: str
    product2_category: str
    product1_price: float
    product2_price: float
    features: Dict[str, float]
    label: int  # 1 for match, 0 for no match
    confidence: float
    source: str
    created_at: str
    metadata: Dict[str, Any]


class TrainingDatasetGenerator:
    """Generates training datasets from product matching data"""
    
    def __init__(self, db_client: Optional[SupabaseClient] = None):
        """Initialize dataset generator"""
        self.db = db_client or SupabaseClient()
        self.fuzzy_matcher = FuzzyMatcher()
        self.semantic_similarity = SemanticSimilarity()
        
        # Feature extractors
        self.feature_extractors = {
            'fuzzy_features': self._extract_fuzzy_features,
            'semantic_features': self._extract_semantic_features,
            'basic_features': self._extract_basic_features,
            'price_features': self._extract_price_features,
            'brand_features': self._extract_brand_features,
            'category_features': self._extract_category_features
        }
        
        # Dataset statistics
        self.stats = {
            'total_examples': 0,
            'positive_examples': 0,
            'negative_examples': 0,
            'feature_count': 0,
            'sources': {}
        }
    
    def generate_from_existing_matches(self, limit: int = 1000, 
                                     include_negative: bool = True,
                                     negative_ratio: float = 2.0) -> List[TrainingExample]:
        """
        Generate training dataset from existing product matches
        
        Args:
            limit: Maximum number of positive examples to extract
            include_negative: Whether to generate negative examples
            negative_ratio: Ratio of negative to positive examples
            
        Returns:
            List of TrainingExample objects
        """
        logger.info(f"Generating training dataset from existing matches (limit: {limit})")
        
        examples = []
        
        # Get positive examples from existing matches
        positive_examples = self._get_positive_examples(limit)
        examples.extend(positive_examples)
        
        logger.info(f"Generated {len(positive_examples)} positive examples")
        
        # Generate negative examples
        if include_negative:
            negative_count = int(len(positive_examples) * negative_ratio)
            negative_examples = self._generate_negative_examples(negative_count)
            examples.extend(negative_examples)
            
            logger.info(f"Generated {len(negative_examples)} negative examples")
        
        # Update statistics
        self._update_stats(examples)
        
        logger.info(f"Total training examples generated: {len(examples)}")
        return examples
    
    def generate_from_product_catalog(self, retailers: List[str], 
                                    categories: List[str] = None,
                                    sample_size: int = 500) -> List[TrainingExample]:
        """
        Generate training dataset by comparing products from catalog
        
        Args:
            retailers: List of retailers to include
            categories: List of categories to focus on
            sample_size: Number of product pairs to sample
            
        Returns:
            List of TrainingExample objects
        """
        logger.info(f"Generating dataset from catalog (retailers: {retailers}, sample_size: {sample_size})")
        
        # Get products from catalog
        products = self._get_catalog_products(retailers, categories, sample_size * 2)
        
        if len(products) < 2:
            logger.warning("Insufficient products for dataset generation")
            return []
        
        # Generate product pairs for comparison
        examples = []
        pairs_generated = 0
        
        for i in range(len(products)):
            if pairs_generated >= sample_size:
                break
                
            for j in range(i + 1, len(products)):
                if pairs_generated >= sample_size:
                    break
                
                product1 = products[i]
                product2 = products[j]
                
                # Create training example
                example = self._create_training_example(
                    product1, product2, 
                    source='catalog_comparison'
                )
                
                examples.append(example)
                pairs_generated += 1
        
        # Update statistics
        self._update_stats(examples)
        
        logger.info(f"Generated {len(examples)} examples from catalog")
        return examples
    
    def augment_dataset(self, examples: List[TrainingExample], 
                       augmentation_factor: float = 1.5) -> List[TrainingExample]:
        """
        Augment training dataset with variations
        
        Args:
            examples: Existing training examples
            augmentation_factor: Factor by which to increase dataset size
            
        Returns:
            Augmented list of training examples
        """
        logger.info(f"Augmenting dataset by factor {augmentation_factor}")
        
        augmented_examples = examples.copy()
        target_size = int(len(examples) * augmentation_factor)
        additional_needed = target_size - len(examples)
        
        if additional_needed <= 0:
            return augmented_examples
        
        # Augmentation strategies
        augmented_count = 0
        
        for example in examples:
            if augmented_count >= additional_needed:
                break
            
            # Text variations
            variations = self._generate_text_variations(example)
            
            for variation in variations:
                if augmented_count >= additional_needed:
                    break
                
                augmented_examples.append(variation)
                augmented_count += 1
        
        logger.info(f"Augmented dataset from {len(examples)} to {len(augmented_examples)} examples")
        return augmented_examples
    
    def _get_positive_examples(self, limit: int) -> List[TrainingExample]:
        """Get positive examples from existing product matches"""
        examples = []
        
        try:
            # Query existing matches from database
            query = """
            SELECT DISTINCT
                p1.id as product1_id,
                p1.name as product1_name,
                p1.brand as product1_brand,
                p1.category as product1_category,
                p1.price as product1_price,
                p1.retailer as product1_retailer,
                p2.id as product2_id,
                p2.name as product2_name,
                p2.brand as product2_brand,
                p2.category as product2_category,
                p2.price as product2_price,
                p2.retailer as product2_retailer,
                pm.confidence_score,
                pm.created_at
            FROM product_matches pm
            JOIN products p1 ON pm.product1_id = p1.id
            JOIN products p2 ON pm.product2_id = p2.id
            WHERE pm.is_validated = true
            AND pm.confidence_score >= 0.7
            ORDER BY pm.confidence_score DESC
            LIMIT %s
            """
            
            # Note: This is a mock query structure - adjust based on actual schema
            # For now, we'll generate synthetic positive examples
            examples = self._generate_synthetic_positive_examples(limit)
            
        except Exception as e:
            logger.warning(f"Failed to query existing matches: {e}")
            # Fallback to synthetic data
            examples = self._generate_synthetic_positive_examples(limit)
        
        return examples
    
    def _generate_synthetic_positive_examples(self, count: int) -> List[TrainingExample]:
        """Generate synthetic positive examples for testing"""
        examples = []
        
        # Template positive pairs (products that should match)
        positive_pairs = [
            {
                "product1": {
                    "name": "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
                    "brand": "MITSUBISHI",
                    "category": "air-conditioner",
                    "price": 15000,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
                    "brand": "มิตซูบิชิ",
                    "category": "air-conditioner",
                    "price": 15500,
                    "retailer": "thaiwatsadu"
                }
            },
            {
                "product1": {
                    "name": "Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8",
                    "brand": "Samsung",
                    "category": "refrigerator",
                    "price": 12000,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "ซัมซุง ตู้เย็น RT29K5511S8 300L 2 doors",
                    "brand": "ซัมซุง",
                    "category": "refrigerator",
                    "price": 12200,
                    "retailer": "globalhouse"
                }
            },
            {
                "product1": {
                    "name": "LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC 4K",
                    "brand": "LG",
                    "category": "television",
                    "price": 18000,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "แอลจี สมาร์ททีวี 55\" 55UN7300PTC 4K UHD",
                    "brand": "แอลจี",
                    "category": "television",
                    "price": 18500,
                    "retailer": "megahome"
                }
            }
        ]
        
        # Generate examples by cycling through templates
        for i in range(count):
            template = positive_pairs[i % len(positive_pairs)]
            
            # Add some variation to avoid overfitting
            example = self._create_training_example(
                template["product1"], 
                template["product2"],
                label=1,
                confidence=0.9 + random.random() * 0.1,
                source='synthetic_positive'
            )
            
            examples.append(example)
        
        return examples
    
    def _generate_negative_examples(self, count: int) -> List[TrainingExample]:
        """Generate negative examples (non-matching products)"""
        examples = []
        
        # Template negative pairs (products that should NOT match)
        negative_pairs = [
            {
                "product1": {
                    "name": "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
                    "brand": "MITSUBISHI",
                    "category": "air-conditioner",
                    "price": 15000,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "Samsung ตู้เย็น RT29K5511S8 300 ลิตร",
                    "brand": "Samsung",
                    "category": "refrigerator",
                    "price": 12000,
                    "retailer": "thaiwatsadu"
                }
            },
            {
                "product1": {
                    "name": "LG Smart TV 55 นิ้ว",
                    "brand": "LG",
                    "category": "television",
                    "price": 18000,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "Panasonic เครื่องซักผ้า NA-F70B3",
                    "brand": "Panasonic",
                    "category": "washing-machine",
                    "price": 8000,
                    "retailer": "globalhouse"
                }
            },
            {
                "product1": {
                    "name": "Bosch Professional Drill GSB500RE",
                    "brand": "Bosch",
                    "category": "power-tools",
                    "price": 2500,
                    "retailer": "homepro"
                },
                "product2": {
                    "name": "Sharp ไมโครเวฟ R-21A0S 20 ลิตร",
                    "brand": "Sharp",
                    "category": "microwave",
                    "price": 3500,
                    "retailer": "megahome"
                }
            }
        ]
        
        # Generate examples by cycling through templates
        for i in range(count):
            template = negative_pairs[i % len(negative_pairs)]
            
            example = self._create_training_example(
                template["product1"],
                template["product2"],
                label=0,
                confidence=0.1 + random.random() * 0.2,
                source='synthetic_negative'
            )
            
            examples.append(example)
        
        return examples
    
    def _get_catalog_products(self, retailers: List[str], 
                            categories: List[str] = None,
                            limit: int = 1000) -> List[Dict]:
        """Get products from catalog for comparison"""
        # Mock implementation - replace with actual database query
        mock_products = [
            {
                "id": 1,
                "name": "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
                "brand": "MITSUBISHI",
                "category": "air-conditioner",
                "price": 15000,
                "retailer": "homepro"
            },
            {
                "id": 2,
                "name": "Samsung ตู้เย็น RT29K5511S8 300L",
                "brand": "Samsung",
                "category": "refrigerator",
                "price": 12000,
                "retailer": "homepro"
            },
            {
                "id": 3,
                "name": "LG Smart TV 55 นิ้ว 55UN7300PTC",
                "brand": "LG",
                "category": "television",
                "price": 18000,
                "retailer": "homepro"
            }
        ]
        
        # Filter by retailers and categories
        filtered_products = []
        for product in mock_products:
            if product['retailer'] in retailers:
                if categories is None or product['category'] in categories:
                    filtered_products.append(product)
        
        return filtered_products[:limit]
    
    def _create_training_example(self, product1: Dict, product2: Dict,
                               label: Optional[int] = None,
                               confidence: Optional[float] = None,
                               source: str = 'manual') -> TrainingExample:
        """Create a training example from two products"""
        
        # Generate unique ID
        example_id = hashlib.md5(
            f"{product1.get('name', '')}{product2.get('name', '')}".encode()
        ).hexdigest()[:12]
        
        # Extract features
        features = {}
        for extractor_name, extractor_func in self.feature_extractors.items():
            try:
                extracted_features = extractor_func(product1, product2)
                features.update(extracted_features)
            except Exception as e:
                logger.warning(f"Feature extraction failed for {extractor_name}: {e}")
        
        # Auto-label if not provided
        if label is None:
            label = self._auto_label(product1, product2, features)
        
        # Auto-confidence if not provided
        if confidence is None:
            confidence = self._estimate_confidence(features, label)
        
        return TrainingExample(
            id=example_id,
            product1_name=product1.get('name', ''),
            product2_name=product2.get('name', ''),
            product1_brand=product1.get('brand', ''),
            product2_brand=product2.get('brand', ''),
            product1_category=product1.get('category', ''),
            product2_category=product2.get('category', ''),
            product1_price=float(product1.get('price', 0)),
            product2_price=float(product2.get('price', 0)),
            features=features,
            label=label,
            confidence=confidence,
            source=source,
            created_at=datetime.now().isoformat(),
            metadata={
                'product1_id': product1.get('id'),
                'product2_id': product2.get('id'),
                'product1_retailer': product1.get('retailer'),
                'product2_retailer': product2.get('retailer')
            }
        )
    
    def _extract_fuzzy_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract fuzzy matching features"""
        name1 = product1.get('name', '')
        name2 = product2.get('name', '')
        
        if not name1 or not name2:
            return {}
        
        fuzzy_result = self.fuzzy_matcher.calculate_similarity(name1, name2)
        
        features = {
            'fuzzy_overall': fuzzy_result.similarity,
            'fuzzy_confidence': fuzzy_result.confidence
        }
        
        # Add individual algorithm scores
        individual_scores = fuzzy_result.details.get('individual_scores', {})
        for method, score in individual_scores.items():
            features[f'fuzzy_{method}'] = score
        
        return features
    
    def _extract_semantic_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract semantic similarity features"""
        name1 = product1.get('name', '')
        name2 = product2.get('name', '')
        
        if not name1 or not name2:
            return {}
        
        semantic_result = self.semantic_similarity.calculate_similarity(name1, name2)
        
        features = {
            'semantic_overall': semantic_result.similarity
        }
        
        # Add individual method scores
        individual_sims = semantic_result.details.get('individual_similarities', {})
        for method, score in individual_sims.items():
            features[f'semantic_{method}'] = score
        
        return features
    
    def _extract_basic_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract basic text features"""
        name1 = product1.get('name', '')
        name2 = product2.get('name', '')
        
        features = {}
        
        if name1 and name2:
            # Length features
            features['length_ratio'] = len(name2) / len(name1) if len(name1) > 0 else 0
            features['length_diff'] = abs(len(name1) - len(name2))
            
            # Word count features
            words1 = name1.split()
            words2 = name2.split()
            features['word_count_ratio'] = len(words2) / len(words1) if len(words1) > 0 else 0
            features['word_count_diff'] = abs(len(words1) - len(words2))
            
            # Character overlap
            chars1 = set(name1.lower())
            chars2 = set(name2.lower())
            features['char_overlap'] = len(chars1 & chars2) / len(chars1 | chars2) if chars1 | chars2 else 0
            
            # Word overlap
            words1_set = set(word.lower() for word in words1)
            words2_set = set(word.lower() for word in words2)
            features['word_overlap'] = len(words1_set & words2_set) / len(words1_set | words2_set) if words1_set | words2_set else 0
        
        return features
    
    def _extract_price_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract price-related features"""
        price1 = product1.get('price', 0)
        price2 = product2.get('price', 0)
        
        features = {}
        
        if price1 > 0 and price2 > 0:
            features['price_ratio'] = price2 / price1
            features['price_diff_pct'] = abs(price1 - price2) / max(price1, price2)
            features['price_diff_abs'] = abs(price1 - price2)
            features['avg_price'] = (price1 + price2) / 2
        
        return features
    
    def _extract_brand_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract brand-related features"""
        brand1 = product1.get('brand', '').lower()
        brand2 = product2.get('brand', '').lower()
        
        features = {}
        
        if brand1 and brand2:
            features['brand_exact_match'] = 1.0 if brand1 == brand2 else 0.0
            
            # Character similarity
            chars1 = set(brand1)
            chars2 = set(brand2)
            features['brand_char_overlap'] = len(chars1 & chars2) / len(chars1 | chars2) if chars1 | chars2 else 0
            
            # Length similarity
            features['brand_length_ratio'] = len(brand2) / len(brand1) if len(brand1) > 0 else 0
        
        return features
    
    def _extract_category_features(self, product1: Dict, product2: Dict) -> Dict[str, float]:
        """Extract category-related features"""
        cat1 = product1.get('category', '').lower()
        cat2 = product2.get('category', '').lower()
        
        features = {}
        
        if cat1 and cat2:
            features['category_exact_match'] = 1.0 if cat1 == cat2 else 0.0
            
            # Related categories
            related_categories = {
                'air-conditioner': ['refrigerator', 'fan'],
                'refrigerator': ['air-conditioner'],
                'television': ['display'],
                'washing-machine': ['dryer']
            }
            
            if cat1 in related_categories and cat2 in related_categories[cat1]:
                features['category_related'] = 1.0
            else:
                features['category_related'] = 0.0
        
        return features
    
    def _auto_label(self, product1: Dict, product2: Dict, features: Dict[str, float]) -> int:
        """Automatically assign label based on features"""
        # Simple heuristic for auto-labeling
        score = 0
        
        # Brand match
        if features.get('brand_exact_match', 0) > 0:
            score += 0.3
        
        # Category match
        if features.get('category_exact_match', 0) > 0:
            score += 0.2
        
        # High text similarity
        if features.get('fuzzy_overall', 0) > 0.8:
            score += 0.3
        
        # Price similarity
        if features.get('price_diff_pct', 1.0) < 0.2:
            score += 0.2
        
        return 1 if score >= 0.6 else 0
    
    def _estimate_confidence(self, features: Dict[str, float], label: int) -> float:
        """Estimate confidence based on features and label"""
        if label == 1:
            # High confidence for strong matches
            confidence = 0.7
            if features.get('brand_exact_match', 0) > 0:
                confidence += 0.1
            if features.get('fuzzy_overall', 0) > 0.9:
                confidence += 0.1
            if features.get('category_exact_match', 0) > 0:
                confidence += 0.1
        else:
            # Lower confidence for non-matches
            confidence = 0.8
            if features.get('brand_exact_match', 0) == 0:
                confidence += 0.1
            if features.get('fuzzy_overall', 0) < 0.3:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _generate_text_variations(self, example: TrainingExample) -> List[TrainingExample]:
        """Generate text variations for data augmentation"""
        variations = []
        
        # Simple variations - in practice, use more sophisticated techniques
        variation_strategies = [
            self._add_whitespace_variation,
            self._add_case_variation,
            self._add_punctuation_variation
        ]
        
        for strategy in variation_strategies:
            try:
                variation = strategy(example)
                if variation:
                    variations.append(variation)
            except Exception as e:
                logger.warning(f"Variation generation failed: {e}")
        
        return variations
    
    def _add_whitespace_variation(self, example: TrainingExample) -> Optional[TrainingExample]:
        """Add whitespace variations"""
        # Add/remove spaces
        name1_var = re.sub(r'\s+', ' ', example.product1_name)
        name2_var = re.sub(r'\s+', '  ', example.product2_name)
        
        # Create new example with variation
        new_example = TrainingExample(
            id=example.id + '_ws',
            product1_name=name1_var,
            product2_name=name2_var,
            product1_brand=example.product1_brand,
            product2_brand=example.product2_brand,
            product1_category=example.product1_category,
            product2_category=example.product2_category,
            product1_price=example.product1_price,
            product2_price=example.product2_price,
            features=example.features.copy(),
            label=example.label,
            confidence=example.confidence * 0.9,  # Slightly lower confidence
            source=example.source + '_augmented',
            created_at=datetime.now().isoformat(),
            metadata=example.metadata.copy()
        )
        
        return new_example
    
    def _add_case_variation(self, example: TrainingExample) -> Optional[TrainingExample]:
        """Add case variations"""
        name1_var = example.product1_name.upper()
        name2_var = example.product2_name.lower()
        
        new_example = TrainingExample(
            id=example.id + '_case',
            product1_name=name1_var,
            product2_name=name2_var,
            product1_brand=example.product1_brand,
            product2_brand=example.product2_brand,
            product1_category=example.product1_category,
            product2_category=example.product2_category,
            product1_price=example.product1_price,
            product2_price=example.product2_price,
            features=example.features.copy(),
            label=example.label,
            confidence=example.confidence * 0.95,
            source=example.source + '_augmented',
            created_at=datetime.now().isoformat(),
            metadata=example.metadata.copy()
        )
        
        return new_example
    
    def _add_punctuation_variation(self, example: TrainingExample) -> Optional[TrainingExample]:
        """Add punctuation variations"""
        name1_var = re.sub(r'[^\w\s\u0E00-\u0E7F]', '', example.product1_name)
        name2_var = example.product2_name.replace('-', ' ')
        
        new_example = TrainingExample(
            id=example.id + '_punct',
            product1_name=name1_var,
            product2_name=name2_var,
            product1_brand=example.product1_brand,
            product2_brand=example.product2_brand,
            product1_category=example.product1_category,
            product2_category=example.product2_category,
            product1_price=example.product1_price,
            product2_price=example.product2_price,
            features=example.features.copy(),
            label=example.label,
            confidence=example.confidence * 0.9,
            source=example.source + '_augmented',
            created_at=datetime.now().isoformat(),
            metadata=example.metadata.copy()
        )
        
        return new_example
    
    def _update_stats(self, examples: List[TrainingExample]):
        """Update dataset statistics"""
        self.stats['total_examples'] = len(examples)
        self.stats['positive_examples'] = sum(1 for ex in examples if ex.label == 1)
        self.stats['negative_examples'] = sum(1 for ex in examples if ex.label == 0)
        
        if examples:
            self.stats['feature_count'] = len(examples[0].features)
        
        # Count sources
        source_counts = {}
        for example in examples:
            source_counts[example.source] = source_counts.get(example.source, 0) + 1
        self.stats['sources'] = source_counts
    
    def save_dataset(self, examples: List[TrainingExample], 
                    filepath: str, format: str = 'json'):
        """Save training dataset to file"""
        logger.info(f"Saving {len(examples)} examples to {filepath}")
        
        if format == 'json':
            self._save_json(examples, filepath)
        elif format == 'csv':
            self._save_csv(examples, filepath)
        elif format == 'parquet':
            self._save_parquet(examples, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save statistics
        stats_path = Path(filepath).with_suffix('.stats.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset saved: {filepath}")
        logger.info(f"Statistics saved: {stats_path}")
    
    def _save_json(self, examples: List[TrainingExample], filepath: str):
        """Save dataset as JSON"""
        data = [asdict(example) for example in examples]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_csv(self, examples: List[TrainingExample], filepath: str):
        """Save dataset as CSV"""
        if not examples:
            return
        
        # Flatten features into columns
        fieldnames = [
            'id', 'product1_name', 'product2_name', 'product1_brand', 'product2_brand',
            'product1_category', 'product2_category', 'product1_price', 'product2_price',
            'label', 'confidence', 'source', 'created_at'
        ]
        
        # Add feature columns
        feature_names = list(examples[0].features.keys())
        fieldnames.extend(feature_names)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for example in examples:
                row = asdict(example)
                # Flatten features
                features = row.pop('features')
                row.update(features)
                # Remove metadata for CSV
                row.pop('metadata', None)
                writer.writerow(row)
    
    def _save_parquet(self, examples: List[TrainingExample], filepath: str):
        """Save dataset as Parquet"""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            # Convert to pandas DataFrame first
            df = pd.DataFrame([asdict(example) for example in examples])
            
            # Flatten features
            features_df = pd.json_normalize(df['features'])
            df = pd.concat([df.drop('features', axis=1), features_df], axis=1)
            
            # Save as Parquet
            table = pa.Table.from_pandas(df)
            pq.write_table(table, filepath)
            
        except ImportError:
            logger.warning("PyArrow not available, falling back to JSON")
            self._save_json(examples, filepath.replace('.parquet', '.json'))
    
    def load_dataset(self, filepath: str) -> List[TrainingExample]:
        """Load training dataset from file"""
        logger.info(f"Loading dataset from {filepath}")
        
        if filepath.endswith('.json'):
            return self._load_json(filepath)
        elif filepath.endswith('.csv'):
            return self._load_csv(filepath)
        elif filepath.endswith('.parquet'):
            return self._load_parquet(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")
    
    def _load_json(self, filepath: str) -> List[TrainingExample]:
        """Load dataset from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for item in data:
            example = TrainingExample(**item)
            examples.append(example)
        
        return examples
    
    def _load_csv(self, filepath: str) -> List[TrainingExample]:
        """Load dataset from CSV"""
        df = pd.read_csv(filepath)
        examples = []
        
        for _, row in df.iterrows():
            # Extract features
            feature_cols = [col for col in df.columns if col.startswith(('fuzzy_', 'semantic_', 'price_', 'brand_', 'category_', 'char_', 'word_', 'length_'))]
            features = {col: row[col] for col in feature_cols if not pd.isna(row[col])}
            
            example = TrainingExample(
                id=row['id'],
                product1_name=row['product1_name'],
                product2_name=row['product2_name'],
                product1_brand=row['product1_brand'],
                product2_brand=row['product2_brand'],
                product1_category=row['product1_category'],
                product2_category=row['product2_category'],
                product1_price=row['product1_price'],
                product2_price=row['product2_price'],
                features=features,
                label=int(row['label']),
                confidence=float(row['confidence']),
                source=row['source'],
                created_at=row['created_at'],
                metadata={}
            )
            
            examples.append(example)
        
        return examples
    
    def _load_parquet(self, filepath: str) -> List[TrainingExample]:
        """Load dataset from Parquet"""
        try:
            df = pd.read_parquet(filepath)
            return self._dataframe_to_examples(df)
        except ImportError:
            logger.error("PyArrow not available for Parquet loading")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset generation statistics"""
        return self.stats.copy()


# Example usage and testing
if __name__ == "__main__":
    # Initialize dataset generator
    generator = TrainingDatasetGenerator()
    
    print("Training Dataset Generator Test:")
    print("=" * 50)
    
    # Generate dataset from existing matches
    print("\n1. Generating from existing matches...")
    existing_examples = generator.generate_from_existing_matches(
        limit=10, 
        include_negative=True, 
        negative_ratio=1.5
    )
    
    print(f"Generated {len(existing_examples)} examples")
    
    # Generate from catalog
    print("\n2. Generating from catalog...")
    catalog_examples = generator.generate_from_product_catalog(
        retailers=['homepro', 'thaiwatsadu'],
        categories=['air-conditioner', 'refrigerator'],
        sample_size=5
    )
    
    print(f"Generated {len(catalog_examples)} examples from catalog")
    
    # Combine datasets
    all_examples = existing_examples + catalog_examples
    
    # Augment dataset
    print("\n3. Augmenting dataset...")
    augmented_examples = generator.augment_dataset(all_examples, augmentation_factor=1.3)
    
    print(f"Augmented to {len(augmented_examples)} examples")
    
    # Show sample examples
    print("\n4. Sample examples:")
    print("-" * 30)
    
    for i, example in enumerate(augmented_examples[:3]):
        print(f"\nExample {i+1}:")
        print(f"  Product 1: {example.product1_name}")
        print(f"  Product 2: {example.product2_name}")
        print(f"  Label: {example.label}")
        print(f"  Confidence: {example.confidence:.3f}")
        print(f"  Features: {len(example.features)} features")
        print(f"  Source: {example.source}")
    
    # Save dataset
    print("\n5. Saving dataset...")
    output_path = "/tmp/training_dataset.json"
    generator.save_dataset(augmented_examples, output_path, format='json')
    
    # Load and verify
    print("\n6. Loading and verifying...")
    loaded_examples = generator.load_dataset(output_path)
    
    print(f"Loaded {len(loaded_examples)} examples")
    print(f"Original: {len(augmented_examples)}, Loaded: {len(loaded_examples)}")
    
    # Show statistics
    print("\n7. Dataset Statistics:")
    print("-" * 30)
    stats = generator.get_statistics()
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Clean up
    Path(output_path).unlink(missing_ok=True)
    Path(output_path.replace('.json', '.stats.json')).unlink(missing_ok=True)
    
    print("\nDataset generation test completed!")