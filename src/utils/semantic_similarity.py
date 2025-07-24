"""
Semantic Similarity Scoring System
Implements lightweight ML-based semantic matching for product names
"""

import re
import math
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from collections import Counter, defaultdict
import pickle
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SemanticResult:
    """Result of semantic similarity calculation"""
    similarity: float
    method: str
    details: Dict[str, Any]
    features: Dict[str, float]


class TFIDFVectorizer:
    """Simple TF-IDF vectorizer for text similarity"""
    
    def __init__(self, max_features: int = 1000, ngram_range: Tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vocabulary = {}
        self.idf_values = {}
        self.feature_names = []
        self.is_fitted = False
    
    def fit(self, texts: List[str]):
        """Fit the vectorizer on a corpus of texts"""
        # Extract all n-grams
        all_ngrams = []
        for text in texts:
            ngrams = self._extract_ngrams(text)
            all_ngrams.extend(ngrams)
        
        # Count term frequencies across documents
        doc_frequencies = defaultdict(int)
        for text in texts:
            unique_ngrams = set(self._extract_ngrams(text))
            for ngram in unique_ngrams:
                doc_frequencies[ngram] += 1
        
        # Select top features by document frequency
        sorted_ngrams = sorted(doc_frequencies.items(), key=lambda x: x[1], reverse=True)
        selected_ngrams = sorted_ngrams[:self.max_features]
        
        # Build vocabulary
        self.vocabulary = {ngram: idx for idx, (ngram, _) in enumerate(selected_ngrams)}
        self.feature_names = [ngram for ngram, _ in selected_ngrams]
        
        # Calculate IDF values
        total_docs = len(texts)
        for ngram, doc_freq in selected_ngrams:
            self.idf_values[ngram] = math.log(total_docs / (doc_freq + 1))
        
        self.is_fitted = True
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to TF-IDF vectors"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transform")
        
        vectors = []
        for text in texts:
            vector = self._text_to_vector(text)
            vectors.append(vector)
        
        return np.array(vectors)
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Fit and transform texts in one step"""
        self.fit(texts)
        return self.transform(texts)
    
    def _extract_ngrams(self, text: str) -> List[str]:
        """Extract n-grams from text"""
        tokens = text.lower().split()
        ngrams = []
        
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i + n])
                ngrams.append(ngram)
        
        return ngrams
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """Convert text to TF-IDF vector"""
        vector = np.zeros(len(self.vocabulary))
        ngrams = self._extract_ngrams(text)
        ngram_counts = Counter(ngrams)
        
        # Calculate TF-IDF for each n-gram
        total_ngrams = len(ngrams)
        for ngram, count in ngram_counts.items():
            if ngram in self.vocabulary:
                tf = count / total_ngrams if total_ngrams > 0 else 0
                idf = self.idf_values.get(ngram, 0)
                tfidf = tf * idf
                vector[self.vocabulary[ngram]] = tfidf
        
        return vector


class WordEmbedding:
    """Simple word embedding using co-occurrence matrix"""
    
    def __init__(self, embedding_dim: int = 100, window_size: int = 3):
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.word_to_idx = {}
        self.embeddings = None
        self.vocabulary_size = 0
    
    def fit(self, texts: List[str]):
        """Train word embeddings on corpus"""
        # Build vocabulary
        word_counts = Counter()
        for text in texts:
            words = text.lower().split()
            word_counts.update(words)
        
        # Select top words for vocabulary
        vocab_words = [word for word, _ in word_counts.most_common(1000)]
        self.word_to_idx = {word: idx for idx, word in enumerate(vocab_words)}
        self.vocabulary_size = len(vocab_words)
        
        # Build co-occurrence matrix
        cooccurrence_matrix = np.zeros((self.vocabulary_size, self.vocabulary_size))
        
        for text in texts:
            words = text.lower().split()
            for i, word in enumerate(words):
                if word in self.word_to_idx:
                    word_idx = self.word_to_idx[word]
                    
                    # Look at context window
                    start = max(0, i - self.window_size)
                    end = min(len(words), i + self.window_size + 1)
                    
                    for j in range(start, end):
                        if i != j and words[j] in self.word_to_idx:
                            context_idx = self.word_to_idx[words[j]]
                            cooccurrence_matrix[word_idx][context_idx] += 1
        
        # Apply SVD for dimensionality reduction
        try:
            U, s, Vt = np.linalg.svd(cooccurrence_matrix, full_matrices=False)
            self.embeddings = U[:, :self.embedding_dim] * np.sqrt(s[:self.embedding_dim])
        except np.linalg.LinAlgError:
            # Fallback to random embeddings if SVD fails
            self.embeddings = np.random.randn(self.vocabulary_size, self.embedding_dim) * 0.1
    
    def get_word_vector(self, word: str) -> Optional[np.ndarray]:
        """Get embedding vector for a word"""
        if self.embeddings is None:
            return None
        
        word = word.lower()
        if word in self.word_to_idx:
            return self.embeddings[self.word_to_idx[word]]
        return None
    
    def get_text_vector(self, text: str) -> np.ndarray:
        """Get averaged embedding vector for text"""
        if self.embeddings is None:
            return np.zeros(self.embedding_dim)
        
        words = text.lower().split()
        vectors = []
        
        for word in words:
            vector = self.get_word_vector(word)
            if vector is not None:
                vectors.append(vector)
        
        if vectors:
            return np.mean(vectors, axis=0)
        else:
            return np.zeros(self.embedding_dim)


class SemanticSimilarity:
    """Semantic similarity calculator using multiple approaches"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Component weights
        self.method_weights = {
            'tfidf_cosine': 0.4,
            'word_embedding': 0.3,
            'category_similarity': 0.2,
            'feature_overlap': 0.1
        }
        
        # Initialize components
        self.tfidf_vectorizer = TFIDFVectorizer(max_features=500, ngram_range=(1, 2))
        self.word_embedding = WordEmbedding(embedding_dim=50, window_size=3)
        
        # Product category mappings
        self.category_keywords = {
            'air_conditioner': ['แอร์', 'เครื่องปรับอากาศ', 'air conditioner', 'ac', 'conditioner', 'cooling'],
            'refrigerator': ['ตู้เย็น', 'refrigerator', 'fridge', 'freezer', 'cooling'],
            'television': ['ทีวี', 'โทรทัศน์', 'tv', 'television', 'smart tv', 'display'],
            'washing_machine': ['เครื่องซักผ้า', 'washing machine', 'washer', 'laundry'],
            'microwave': ['ไมโครเวฟ', 'microwave', 'oven'],
            'vacuum': ['เครื่องดูดฝุ่น', 'vacuum', 'cleaner'],
            'fan': ['พัดลม', 'fan', 'cooling'],
            'power_tools': ['drill', 'saw', 'grinder', 'สว่าน', 'เลื่อย'],
            'kitchen': ['kitchen', 'cooking', 'ครัว', 'หุงต้ม']
        }
        
        # Feature extraction patterns
        self.feature_patterns = {
            'size': r'(\d+(?:\.\d+)?)\s*(?:inch|นิ้ว|"|cm|ซม)',
            'capacity': r'(\d+(?:\.\d+)?)\s*(?:l|liter|ลิตร|btu|บีทียู)',
            'power': r'(\d+(?:\.\d+)?)\s*(?:w|watt|วัตต์|hp|แรงม้า)',
            'voltage': r'(\d+(?:\.\d+)?)\s*(?:v|volt|โวลต์)',
            'frequency': r'(\d+(?:\.\d+)?)\s*(?:hz|เฮิรตซ์)',
            'doors': r'(\d+)\s*(?:door|ประตู)',
            'speed': r'(\d+)\s*(?:speed|ความเร็ว)'
        }
        
        self.is_trained = False
    
    def train(self, product_texts: List[str]):
        """Train semantic similarity models on product corpus"""
        logger.info(f"Training semantic models on {len(product_texts)} products")
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in product_texts]
        
        # Train TF-IDF vectorizer
        self.tfidf_vectorizer.fit(processed_texts)
        
        # Train word embeddings
        self.word_embedding.fit(processed_texts)
        
        self.is_trained = True
        logger.info("Semantic models training completed")
    
    def calculate_similarity(self, text1: str, text2: str) -> SemanticResult:
        """Calculate semantic similarity between two texts"""
        if not self.is_trained:
            # Use lightweight similarity if not trained
            return self._lightweight_similarity(text1, text2)
        
        # Preprocess texts
        processed_text1 = self._preprocess_text(text1)
        processed_text2 = self._preprocess_text(text2)
        
        # Calculate similarities using different methods
        similarities = {}
        details = {}
        features = {}
        
        # TF-IDF cosine similarity
        tfidf_sim, tfidf_details = self._tfidf_similarity(processed_text1, processed_text2)
        similarities['tfidf_cosine'] = tfidf_sim
        details['tfidf_cosine'] = tfidf_details
        
        # Word embedding similarity
        embedding_sim, embedding_details = self._embedding_similarity(processed_text1, processed_text2)
        similarities['word_embedding'] = embedding_sim
        details['word_embedding'] = embedding_details
        
        # Category similarity
        category_sim, category_details = self._category_similarity(text1, text2)
        similarities['category_similarity'] = category_sim
        details['category_similarity'] = category_details
        
        # Feature overlap
        feature_sim, feature_details = self._feature_similarity(text1, text2)
        similarities['feature_overlap'] = feature_sim
        details['feature_overlap'] = feature_details
        
        # Extract features for ML training
        features = self._extract_features(text1, text2, similarities)
        
        # Calculate weighted average
        weighted_similarity = sum(
            similarities[method] * self.method_weights[method]
            for method in similarities.keys()
        )
        
        return SemanticResult(
            similarity=weighted_similarity,
            method='weighted_semantic',
            details={
                'individual_similarities': similarities,
                'method_details': details,
                'weights': self.method_weights,
                'processed_text1': processed_text1,
                'processed_text2': processed_text2
            },
            features=features
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for semantic analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Thai
        text = re.sub(r'[^\w\s\u0E00-\u0E7F]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _tfidf_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate TF-IDF cosine similarity"""
        try:
            vectors = self.tfidf_vectorizer.transform([text1, text2])
            
            if vectors.shape[0] != 2:
                return 0.0, {'error': 'Failed to vectorize texts'}
            
            # Calculate cosine similarity
            vec1, vec2 = vectors[0], vectors[1]
            
            # Handle zero vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0, {'norm1': norm1, 'norm2': norm2}
            
            cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
            
            return float(cosine_sim), {
                'norm1': float(norm1),
                'norm2': float(norm2),
                'dot_product': float(np.dot(vec1, vec2))
            }
        
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            return 0.0, {'error': str(e)}
    
    def _embedding_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate word embedding similarity"""
        try:
            vec1 = self.word_embedding.get_text_vector(text1)
            vec2 = self.word_embedding.get_text_vector(text2)
            
            # Calculate cosine similarity
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0, {'norm1': float(norm1), 'norm2': float(norm2)}
            
            cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
            
            return float(cosine_sim), {
                'norm1': float(norm1),
                'norm2': float(norm2),
                'embedding_dim': len(vec1)
            }
        
        except Exception as e:
            logger.warning(f"Embedding similarity calculation failed: {e}")
            return 0.0, {'error': str(e)}
    
    def _category_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate category-based similarity"""
        cat1 = self._detect_category(text1)
        cat2 = self._detect_category(text2)
        
        if cat1 is None or cat2 is None:
            return 0.0, {'category1': cat1, 'category2': cat2}
        
        # Exact category match
        if cat1 == cat2:
            return 1.0, {'category1': cat1, 'category2': cat2, 'match': 'exact'}
        
        # Related categories
        related_categories = {
            'air_conditioner': ['refrigerator', 'fan'],
            'refrigerator': ['air_conditioner'],
            'television': [],
            'washing_machine': [],
            'power_tools': []
        }
        
        if cat1 in related_categories and cat2 in related_categories[cat1]:
            return 0.5, {'category1': cat1, 'category2': cat2, 'match': 'related'}
        
        return 0.0, {'category1': cat1, 'category2': cat2, 'match': 'none'}
    
    def _detect_category(self, text: str) -> Optional[str]:
        """Detect product category from text"""
        text_lower = text.lower()
        
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def _feature_similarity(self, text1: str, text2: str) -> Tuple[float, Dict]:
        """Calculate similarity based on extracted features"""
        features1 = self._extract_product_features(text1)
        features2 = self._extract_product_features(text2)
        
        if not features1 or not features2:
            return 0.0, {'features1': features1, 'features2': features2}
        
        # Calculate feature overlap
        common_features = set(features1.keys()) & set(features2.keys())
        
        if not common_features:
            return 0.0, {'common_features': 0}
        
        # Calculate similarity for each common feature
        similarities = []
        feature_details = {}
        
        for feature in common_features:
            val1 = float(features1[feature])
            val2 = float(features2[feature])
            
            # Calculate relative difference
            if val1 == 0 and val2 == 0:
                sim = 1.0
            elif val1 == 0 or val2 == 0:
                sim = 0.0
            else:
                diff = abs(val1 - val2) / max(val1, val2)
                sim = max(0.0, 1.0 - diff)
            
            similarities.append(sim)
            feature_details[feature] = {
                'value1': val1,
                'value2': val2,
                'similarity': sim
            }
        
        # Average similarity
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        return avg_similarity, {
            'feature_details': feature_details,
            'common_features': len(common_features),
            'total_features': len(set(features1.keys()) | set(features2.keys()))
        }
    
    def _extract_product_features(self, text: str) -> Dict[str, str]:
        """Extract numerical features from product text"""
        features = {}
        
        for feature_name, pattern in self.feature_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first match
                features[feature_name] = matches[0]
        
        return features
    
    def _extract_features(self, text1: str, text2: str, similarities: Dict[str, float]) -> Dict[str, float]:
        """Extract features for ML training"""
        features = {}
        
        # Basic text features
        features['length_ratio'] = len(text2) / len(text1) if len(text1) > 0 else 0
        features['word_count_ratio'] = len(text2.split()) / len(text1.split()) if len(text1.split()) > 0 else 0
        
        # Character overlap
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        features['char_overlap'] = len(chars1 & chars2) / len(chars1 | chars2) if chars1 | chars2 else 0
        
        # Word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        features['word_overlap'] = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
        
        # Similarity scores as features
        features.update(similarities)
        
        return features
    
    def _lightweight_similarity(self, text1: str, text2: str) -> SemanticResult:
        """Lightweight similarity when models are not trained"""
        # Simple token overlap
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            similarity = 0.0
        else:
            intersection = tokens1 & tokens2
            union = tokens1 | tokens2
            similarity = len(intersection) / len(union)
        
        # Category boost
        cat1 = self._detect_category(text1)
        cat2 = self._detect_category(text2)
        
        if cat1 and cat2 and cat1 == cat2:
            similarity = min(1.0, similarity + 0.2)
        
        return SemanticResult(
            similarity=similarity,
            method='lightweight_token_overlap',
            details={
                'tokens1': len(tokens1),
                'tokens2': len(tokens2),
                'intersection': len(intersection) if 'intersection' in locals() else 0,
                'union': len(union) if 'union' in locals() else 0,
                'category1': cat1,
                'category2': cat2
            },
            features={'token_overlap': similarity}
        )
    
    def save_models(self, filepath: str):
        """Save trained models to file"""
        if not self.is_trained:
            logger.warning("Models not trained, nothing to save")
            return
        
        models_data = {
            'tfidf_vocabulary': self.tfidf_vectorizer.vocabulary,
            'tfidf_idf_values': self.tfidf_vectorizer.idf_values,
            'tfidf_feature_names': self.tfidf_vectorizer.feature_names,
            'word_embedding_word_to_idx': self.word_embedding.word_to_idx,
            'word_embedding_embeddings': self.word_embedding.embeddings.tolist() if self.word_embedding.embeddings is not None else None,
            'config': self.config,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(models_data, f)
        
        logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from file"""
        try:
            with open(filepath, 'rb') as f:
                models_data = pickle.load(f)
            
            # Restore TF-IDF vectorizer
            self.tfidf_vectorizer.vocabulary = models_data['tfidf_vocabulary']
            self.tfidf_vectorizer.idf_values = models_data['tfidf_idf_values']
            self.tfidf_vectorizer.feature_names = models_data['tfidf_feature_names']
            self.tfidf_vectorizer.is_fitted = True
            
            # Restore word embedding
            self.word_embedding.word_to_idx = models_data['word_embedding_word_to_idx']
            if models_data['word_embedding_embeddings']:
                self.word_embedding.embeddings = np.array(models_data['word_embedding_embeddings'])
            
            self.config = models_data.get('config', {})
            self.is_trained = models_data.get('is_trained', False)
            
            logger.info(f"Models loaded from {filepath}")
        
        except Exception as e:
            logger.error(f"Failed to load models from {filepath}: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize semantic similarity calculator
    semantic = SemanticSimilarity()
    
    # Sample product corpus for training
    training_corpus = [
        "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
        "Samsung ตู้เย็น 2 ประตู 300 ลิตร RT29K5511S8",
        "LG Smart TV 55 นิ้ว รุ่น 55UN7300PTC",
        "Panasonic เครื่องซักผ้า NA-F70B3 7 กิโลกรัม",
        "Sharp ตู้เย็น 1 ประตู 150 ลิตร SJ-D14E",
        "Daikin แอร์ รุ่น FTKF25UV2S 24000BTU อินเวอร์เตอร์",
        "Sony Smart TV 43 นิ้ว KD-43X80J 4K",
        "Electrolux เครื่องซักผ้า EWF8025DGWA 8 กิโลกรัม",
        "Toshiba ตู้เย็น 2 ประตู 253 ลิตร GR-A28KD",
        "Haier แอร์ HSU-12LEK03 12000BTU",
        "Bosch เครื่องซักผ้า WAW28660TH 9 กิโลกรัม",
        "Hitachi ตู้เย็น 4 ประตู 455 ลิตร R-WB560PZ7",
        "Carrier แอร์ 42QHC018 18000BTU อินเวอร์เตอร์",
        "Whirlpool เครื่องซักผ้า 3LWTW4815FW 15 กิโลกรัม"
    ]
    
    print("Training semantic models...")
    semantic.train(training_corpus)
    
    # Test cases
    test_pairs = [
        ("MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF", "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF"),
        ("Samsung ตู้เย็น RT29K5511S8 300L", "ซัมซุง ตู้เย็น RT29K5511S8 300 ลิตร"),
        ("LG Smart TV 55 นิ้ว", "แอลจี สมาร์ททีวี 55 inch"),
        ("Daikin แอร์ 24000BTU", "Sharp ตู้เย็น 150L"),
        ("เครื่องซักผ้า 8 กิโลกรัม", "washing machine 8 kg"),
        ("completely different product", "อีกผลิตภัณฑ์ที่แตกต่างโดยสิ้นเชิง")
    ]
    
    print("\nSemantic Similarity Test Results:")
    print("=" * 60)
    
    for i, (text1, text2) in enumerate(test_pairs, 1):
        result = semantic.calculate_similarity(text1, text2)
        
        print(f"\nTest {i}:")
        print(f"  Text 1: {text1}")
        print(f"  Text 2: {text2}")
        print(f"  Similarity: {result.similarity:.3f}")
        print(f"  Method: {result.method}")
        
        # Show individual method scores
        individual_sims = result.details.get('individual_similarities', {})
        print(f"  Individual Scores:")
        for method, score in individual_sims.items():
            print(f"    {method}: {score:.3f}")
        
        # Show extracted features
        print(f"  Features: {result.features}")
    
    # Test without training (lightweight mode)
    print(f"\n\nLightweight Mode Test (No Training):")
    print("=" * 60)
    
    semantic_light = SemanticSimilarity()
    
    light_result = semantic_light.calculate_similarity(
        "Samsung Smart TV 55 นิ้ว",
        "ซัมซุง สมาร์ททีวี 55 inch"
    )
    
    print(f"Text 1: Samsung Smart TV 55 นิ้ว")
    print(f"Text 2: ซัมซุง สมาร์ททีวี 55 inch")
    print(f"Similarity: {light_result.similarity:.3f}")
    print(f"Method: {light_result.method}")
    print(f"Details: {light_result.details}")
    
    # Test model saving/loading
    print(f"\n\nModel Persistence Test:")
    print("=" * 60)
    
    model_path = "/tmp/semantic_models.pkl"
    semantic.save_models(model_path)
    
    # Create new instance and load models
    semantic_loaded = SemanticSimilarity()
    semantic_loaded.load_models(model_path)
    
    # Test loaded model
    loaded_result = semantic_loaded.calculate_similarity(
        "LG Smart TV 55 นิ้ว",
        "แอลจี ทีวี 55 inch"
    )
    
    print(f"Loaded model similarity: {loaded_result.similarity:.3f}")
    print(f"Is trained: {semantic_loaded.is_trained}")
    
    # Clean up
    Path(model_path).unlink(missing_ok=True)
    print("Model persistence test completed")