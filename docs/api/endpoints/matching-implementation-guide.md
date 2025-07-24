# Product Matching Implementation Guide

## Overview

This guide provides developers with comprehensive instructions for implementing and maintaining the enhanced product matching system in the RIS Data Scrap project.

## Quick Start

### Prerequisites
- Python 3.8+
- Supabase access configured
- Required packages: `fuzzywuzzy`, `python-levenshtein`, `scikit-learn`

### Installation
```bash
pip install -r requirements.txt
cd src/services/
```

### Basic Usage
```python
from src.services.product_matcher import AdvancedProductMatcher

matcher = AdvancedProductMatcher()
matches = matcher.match_products(source_product, target_products)
```

## Architecture Overview

### Core Components

#### 1. Product Matcher (`src/services/product_matcher.py`)
Main matching engine with multiple algorithms:
- Text similarity matching
- Brand normalization
- Model number extraction
- Confidence scoring

#### 2. Text Processor (`src/utils/text_normalizer.py`)
Handles text preprocessing:
- Thai language normalization
- Unicode handling
- Whitespace and punctuation cleanup
- Case normalization

#### 3. Brand Manager (`src/utils/brand_manager.py`)
Manages brand aliases and variations:
- Brand name normalization
- Alias lookup
- Multi-language brand mapping

#### 4. Model Extractor (`src/utils/model_extractor.py`)
Extracts and normalizes model numbers:
- Pattern recognition
- Version handling
- SKU standardization

## Implementation Details

### Enhanced Product Matcher

#### Class Structure
```python
class AdvancedProductMatcher:
    def __init__(self):
        self.brand_manager = BrandManager()
        self.text_processor = TextProcessor()
        self.model_extractor = ModelExtractor()
        self.confidence_calculator = ConfidenceCalculator()
    
    def match_products(self, source_product, target_products):
        """
        Match source product against target products list
        
        Args:
            source_product: Product object to match
            target_products: List of potential matches
            
        Returns:
            List of MatchResult objects sorted by confidence
        """
        results = []
        
        for target in target_products:
            confidence = self._calculate_match_confidence(source_product, target)
            if confidence > self.min_confidence_threshold:
                results.append(MatchResult(target, confidence))
        
        return sorted(results, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_match_confidence(self, source, target):
        """Calculate matching confidence score"""
        scores = {
            'brand': self._compare_brands(source, target),
            'model': self._compare_models(source, target),
            'name': self._compare_names(source, target),
            'price': self._compare_prices(source, target),
            'specs': self._compare_specifications(source, target)
        }
        
        # Weighted average
        weights = {
            'brand': 0.3,
            'model': 0.25,
            'name': 0.2,
            'price': 0.15,
            'specs': 0.1
        }
        
        return sum(scores[key] * weights[key] for key in weights)
```

#### Key Methods Implementation

##### Brand Comparison
```python
def _compare_brands(self, source, target):
    """Compare brand names with normalization"""
    source_brand = self.brand_manager.normalize_brand(source.brand)
    target_brand = self.brand_manager.normalize_brand(target.brand)
    
    if source_brand == target_brand:
        return 1.0
    
    # Check aliases
    if self.brand_manager.are_aliases(source_brand, target_brand):
        return 0.9
    
    # Fuzzy matching
    return self._fuzzy_similarity(source_brand, target_brand)
```

##### Model Number Comparison
```python
def _compare_models(self, source, target):
    """Compare model numbers with extraction"""
    source_model = self.model_extractor.extract_model(source.name)
    target_model = self.model_extractor.extract_model(target.name)
    
    if not source_model or not target_model:
        return 0.0
    
    # Exact match
    if source_model == target_model:
        return 1.0
    
    # Version variations (e.g., "DCD777C2" vs "DCD777C2-B1")
    if self.model_extractor.is_version_variant(source_model, target_model):
        return 0.8
    
    return self._fuzzy_similarity(source_model, target_model)
```

##### Name Comparison
```python
def _compare_names(self, source, target):
    """Compare product names with preprocessing"""
    source_name = self.text_processor.normalize_text(source.name)
    target_name = self.text_processor.normalize_text(target.name)
    
    # Remove brand and model from names for comparison
    source_clean = self._remove_brand_model(source_name, source.brand)
    target_clean = self._remove_brand_model(target_name, target.brand)
    
    return self._semantic_similarity(source_clean, target_clean)
```

### Text Processing Implementation

#### Thai Language Support
```python
class ThaiTextProcessor:
    def __init__(self):
        self.thai_normalizer = ThaiNormalizer()
        self.transliterator = ThaiTransliterator()
    
    def normalize_text(self, text):
        """Normalize Thai and English text"""
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Thai-specific processing
        text = self.thai_normalizer.normalize(text)
        
        # Transliteration for mixed text
        text = self.transliterator.transliterate(text)
        
        # General cleanup
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'[^\w\s\-]', '', text)  # Special chars
        
        return text.strip().lower()
```

#### Brand Manager Implementation
```python
class BrandManager:
    def __init__(self):
        self.brand_aliases = self._load_brand_aliases()
        self.brand_patterns = self._compile_brand_patterns()
    
    def normalize_brand(self, brand):
        """Normalize brand name"""
        if not brand:
            return ""
        
        # Remove common suffixes
        brand = re.sub(r'\s+(co\.?|ltd\.?|inc\.?|corp\.?)$', '', brand, flags=re.IGNORECASE)
        
        # Check aliases
        normalized = self.brand_aliases.get(brand.lower())
        if normalized:
            return normalized
        
        return brand.strip()
    
    def are_aliases(self, brand1, brand2):
        """Check if brands are aliases"""
        return self.brand_aliases.get(brand1.lower()) == self.brand_aliases.get(brand2.lower())
    
    def _load_brand_aliases(self):
        """Load brand aliases from configuration"""
        return {
            'bosch': 'bosch',
            'bosch professional': 'bosch',
            'makita': 'makita',
            'มากิต้า': 'makita',
            'dewalt': 'dewalt',
            'de walt': 'dewalt',
            # Add more aliases...
        }
```

### Model Extraction Implementation

```python
class ModelExtractor:
    def __init__(self):
        self.model_patterns = [
            r'([A-Z]{2,4}[\d]{3,4}[A-Z]*[\d]*)',  # Common format: DCD777C2
            r'([A-Z]+\s[\d]+\s[A-Z]+)',           # Spaced format: GSB 500 RE
            r'([\d]+V[\-\s]*[\d\.]+Ah)',          # Voltage format: 18V-2.0Ah
        ]
    
    def extract_model(self, text):
        """Extract model number from text"""
        for pattern in self.model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_model(match.group(1))
        return None
    
    def _normalize_model(self, model):
        """Normalize model number format"""
        # Remove spaces and hyphens
        model = re.sub(r'[\s\-]+', '', model)
        return model.upper()
    
    def is_version_variant(self, model1, model2):
        """Check if models are version variants"""
        # Remove version suffixes
        base1 = re.sub(r'[\-\.][A-Z\d]+$', '', model1)
        base2 = re.sub(r'[\-\.][A-Z\d]+$', '', model2)
        return base1 == base2
```

## Configuration

### Settings File (`src/config/matching_config.py`)
```python
MATCHING_CONFIG = {
    'min_confidence_threshold': 0.7,
    'weights': {
        'brand': 0.3,
        'model': 0.25,
        'name': 0.2,
        'price': 0.15,
        'specs': 0.1
    },
    'fuzzy_threshold': 0.8,
    'price_tolerance': 0.15,  # 15% price difference allowed
    'batch_size': 100,
    'cache_ttl': 3600,  # 1 hour cache
}
```

### Environment Variables
```bash
# Matching configuration
MATCHING_MIN_CONFIDENCE=0.7
MATCHING_BATCH_SIZE=100
MATCHING_CACHE_TTL=3600

# Performance settings
MATCHING_PARALLEL_WORKERS=4
MATCHING_MEMORY_LIMIT=2GB
```

## API Integration

### FastAPI Router (`src/api/routers/matching_advanced.py`)
```python
from fastapi import APIRouter, HTTPException
from src.services.product_matcher import AdvancedProductMatcher

router = APIRouter(prefix="/api/matching", tags=["matching"])
matcher = AdvancedProductMatcher()

@router.post("/advanced")
async def match_products_advanced(request: MatchRequest):
    """Enhanced product matching endpoint"""
    try:
        results = matcher.match_products(
            source_product=request.source_product,
            target_products=request.target_products
        )
        return {"matches": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/confidence/{product_id}")
async def get_match_confidence(product_id: int, target_id: int):
    """Get confidence score for specific product pair"""
    # Implementation details...
```

### Response Models
```python
from pydantic import BaseModel

class MatchResult(BaseModel):
    product_id: int
    confidence: float
    match_factors: dict
    metadata: dict

class MatchRequest(BaseModel):
    source_product: Product
    target_products: List[Product]
    min_confidence: float = 0.7
```

## Testing Framework

### Unit Tests (`tests/unit/services/test_product_matcher.py`)
```python
import pytest
from src.services.product_matcher import AdvancedProductMatcher

class TestAdvancedProductMatcher:
    def setup_method(self):
        self.matcher = AdvancedProductMatcher()
    
    def test_exact_brand_match(self):
        """Test exact brand name matching"""
        source = Product(brand="Bosch", name="Drill")
        target = Product(brand="Bosch", name="Drill")
        confidence = self.matcher._compare_brands(source, target)
        assert confidence == 1.0
    
    def test_brand_alias_match(self):
        """Test brand alias matching"""
        source = Product(brand="Bosch", name="Drill")
        target = Product(brand="Bosch Professional", name="Drill")
        confidence = self.matcher._compare_brands(source, target)
        assert confidence == 0.9
    
    def test_model_extraction(self):
        """Test model number extraction"""
        result = self.matcher.model_extractor.extract_model("Bosch DCD777C2 Drill")
        assert result == "DCD777C2"
```

### Integration Tests (`tests/integration/test_matching_flow.py`)
```python
def test_full_matching_flow():
    """Test complete matching workflow"""
    matcher = AdvancedProductMatcher()
    
    # Load test data
    source_product = create_test_product("Bosch DCD777C2 Drill")
    target_products = load_test_products("power_tools")
    
    # Run matching
    results = matcher.match_products(source_product, target_products)
    
    # Validate results
    assert len(results) > 0
    assert all(r.confidence >= 0.7 for r in results)
    assert results[0].confidence > results[-1].confidence
```

## Performance Optimization

### Caching Strategy
```python
from functools import lru_cache
import redis

class CachedProductMatcher(AdvancedProductMatcher):
    def __init__(self):
        super().__init__()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour
    
    @lru_cache(maxsize=1000)
    def _compare_brands(self, source_brand, target_brand):
        """Cached brand comparison"""
        return super()._compare_brands(source_brand, target_brand)
    
    def match_products(self, source_product, target_products):
        """Cached product matching"""
        cache_key = f"match:{source_product.id}:{hash(str(target_products))}"
        
        # Check cache
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Compute and cache
        results = super().match_products(source_product, target_products)
        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(results))
        
        return results
```

### Batch Processing
```python
def batch_match_products(self, source_products, target_products, batch_size=100):
    """Process products in batches for better performance"""
    results = []
    
    for i in range(0, len(source_products), batch_size):
        batch = source_products[i:i + batch_size]
        batch_results = self._process_batch(batch, target_products)
        results.extend(batch_results)
        
        # Progress reporting
        print(f"Processed {min(i + batch_size, len(source_products))} / {len(source_products)}")
    
    return results
```

## Monitoring and Logging

### Metrics Collection
```python
import time
from src.utils.metrics import MetricsCollector

class MonitoredProductMatcher(AdvancedProductMatcher):
    def __init__(self):
        super().__init__()
        self.metrics = MetricsCollector()
    
    def match_products(self, source_product, target_products):
        start_time = time.time()
        
        try:
            results = super().match_products(source_product, target_products)
            self.metrics.record_success(
                operation="match_products",
                duration=time.time() - start_time,
                result_count=len(results)
            )
            return results
        except Exception as e:
            self.metrics.record_error(
                operation="match_products",
                error=str(e),
                duration=time.time() - start_time
            )
            raise
```

### Health Checks
```python
@router.get("/health")
async def health_check():
    """Health check endpoint for matching service"""
    try:
        # Test basic functionality
        matcher = AdvancedProductMatcher()
        test_product = Product(name="Test", brand="Test")
        
        # Quick match test
        start_time = time.time()
        results = matcher.match_products(test_product, [test_product])
        duration = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": duration,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Deployment

### Production Considerations
- **Resource Limits**: Configure memory and CPU limits
- **Scaling**: Use horizontal scaling for batch processing
- **Monitoring**: Set up alerting for performance degradation
- **Rollback**: Maintain rollback capabilities

### Docker Configuration
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY config/ config/

CMD ["python", "-m", "src.api.main"]
```

## Troubleshooting

### Common Issues

#### 1. Low Matching Accuracy
- Check brand alias configuration
- Verify text normalization
- Review confidence thresholds

#### 2. Performance Issues
- Enable caching
- Optimize batch sizes
- Check database indices

#### 3. Memory Usage
- Reduce batch sizes
- Clear caches regularly
- Monitor memory leaks

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug matching process
matcher = AdvancedProductMatcher(debug=True)
results = matcher.match_products(source, targets)
```

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document all public methods
- Write comprehensive tests

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Submit PR with clear description

---

*Document Version: 1.0*  
*Last Updated: 2025-01-14*  
*Implementation Status: In Development*