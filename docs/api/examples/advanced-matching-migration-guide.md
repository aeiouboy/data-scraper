# Advanced Matching Algorithm Migration Guide

## Overview

This guide explains how to migrate from the enhanced matcher to the new advanced matcher with improved Thai-English multilingual support.

## Key Improvements

### 1. **Phonetic Matching**
- Handles Thai-English transliteration variations
- Examples: "มิตซูบิชิ" ↔ "Mitsubishi", "ไดกิ้น" ↔ "Daikin"
- Reduces false negatives from language differences

### 2. **N-gram Similarity**
- Better partial matching for model numbers
- Handles variations like "MSY-KP13VF" vs "MSY KP13VF"
- Improves fuzzy matching accuracy

### 3. **Contextual Weighting**
- Dynamic weight adjustment based on product category
- Electronics: Higher weight on SKU/model matching
- General items: Balanced weights across all fields

### 4. **Linguistic Analysis**
- Separate scoring for different matching techniques
- Provides transparency in matching decisions
- Helps identify why products matched or didn't match

### 5. **Cross-lingual Support**
- Improved handling of mixed Thai-English product names
- Better normalization of units and specifications
- Phonetic romanization for Thai text

## Migration Steps

### Step 1: Install Dependencies

```bash
# Install pythainlp for better Thai text processing (optional but recommended)
pip install pythainlp
```

### Step 2: Update Imports

Replace old imports:
```python
# Old
from src.utils.product_matcher_enhanced import EnhancedProductMatcher
from src.utils.text_normalizer_enhanced import EnhancedTextNormalizer

# New
from src.utils.product_matcher_advanced import AdvancedProductMatcher
from src.utils.text_normalizer_advanced import AdvancedTextNormalizer
```

### Step 3: Update Service Layer

Update price comparison service:
```python
# Old
from src.services.price_comparison_enhanced import EnhancedPriceComparisonService

# New
from src.services.price_comparison_advanced import AdvancedPriceComparisonService
```

### Step 4: Update API Endpoints

Add new advanced matching endpoints:
```python
# In src/api/main.py
from src.api.routers import matching_advanced

# Add to router includes
app.include_router(matching_advanced.router)
```

### Step 5: Update Configuration

Adjust matching thresholds if needed:
```python
# Old thresholds
thresholds = {
    'exact': 0.95,
    'high': 0.80,
    'medium': 0.65,
    'low': 0.50
}

# New thresholds (slightly adjusted)
thresholds = {
    'exact': 0.95,
    'high': 0.85,  # More strict
    'medium': 0.70,  # More strict
    'low': 0.55    # More strict
}
```

## API Changes

### New Endpoints

1. **Advanced Comparison**
   ```
   POST /api/v2/matching/compare
   ```
   - Uses advanced multilingual matching
   - Returns linguistic analysis scores

2. **Find Matches**
   ```
   GET /api/v2/matching/find-matches
   ```
   - Improved accuracy for Thai-English products
   - Optional linguistic score details

3. **Analyze Match**
   ```
   POST /api/v2/matching/analyze-match
   ```
   - Detailed match analysis between two products
   - Includes recommendations

### Response Changes

New fields in match results:
```json
{
  "match_result": {
    "confidence": 0.92,
    "match_type": "high",
    "linguistic_scores": {
      "sku": {"phonetic": 0.9, "fuzzy": 0.85},
      "brand": {"transliteration": 0.95},
      "name": {"ngram": 0.88, "crosslingual": 0.8}
    }
  }
}
```

## Testing the Migration

### 1. Run Comparison Tests

```bash
python scripts/testing/test_advanced_matching_comparison.py
```

This will:
- Compare old vs new matcher performance
- Show improvements in Thai-English matching
- Generate detailed results report

### 2. Test Specific Cases

Test Thai-English brand matching:
```python
product1 = {
    'name': 'แอร์มิตซูบิชิ MSY-KP13VF',
    'brand': 'มิตซูบิชิ'
}
product2 = {
    'name': 'Mitsubishi Air MSY-KP13VF',
    'brand': 'Mitsubishi'
}

# Should match with high confidence
```

### 3. Performance Testing

The advanced matcher includes performance optimizations:
- Caching for repeated comparisons
- Parallel processing for bulk matching
- Optimized n-gram calculations

## Rollback Plan

If issues occur, you can run both matchers in parallel:

```python
class HybridMatcher:
    def __init__(self):
        self.enhanced = EnhancedProductMatcher()
        self.advanced = AdvancedProductMatcher()
    
    def match_products(self, p1, p2, use_advanced=True):
        if use_advanced:
            return self.advanced.match_products(p1, p2)
        return self.enhanced.match_products(p1, p2)
```

## Configuration Options

### Environment Variables

```bash
# Enable/disable advanced features
USE_ADVANCED_MATCHER=true
ENABLE_PHONETIC_MATCHING=true
ENABLE_LINGUISTIC_ANALYSIS=true

# Performance tuning
MATCHER_CACHE_SIZE=1000
MATCHER_THREAD_POOL_SIZE=4
```

### Category-Specific Tuning

Customize weights per category:
```python
CATEGORY_WEIGHTS = {
    'air_conditioner': {
        'sku': 0.40,
        'brand': 0.25,
        'specs': 0.20,
        'name': 0.10,
        'category': 0.05
    },
    'refrigerator': {
        'sku': 0.35,
        'brand': 0.25,
        'specs': 0.25,  # Higher for capacity/size
        'name': 0.10,
        'category': 0.05
    }
}
```

## Monitoring

### Key Metrics to Track

1. **Match Accuracy**
   - False positive rate
   - False negative rate
   - Average confidence scores

2. **Performance**
   - Average matching time
   - Cache hit rate
   - API response time

3. **Linguistic Feature Usage**
   - Phonetic matching frequency
   - Cross-lingual matches
   - Fuzzy match activations

### Logging

Enhanced logging for debugging:
```python
import logging

logging.getLogger('src.utils.product_matcher_advanced').setLevel(logging.DEBUG)
```

## Common Issues and Solutions

### Issue 1: Lower Confidence Scores
**Symptom**: Some products show lower confidence than before
**Solution**: This is expected - the advanced matcher is more strict. Adjust thresholds if needed.

### Issue 2: pythainlp Import Error
**Symptom**: ImportError for pythainlp
**Solution**: The matcher works without pythainlp but with reduced Thai text capabilities. Install it for best results.

### Issue 3: Slower Performance
**Symptom**: Matching takes longer
**Solution**: 
- Enable caching
- Use parallel processing for bulk operations
- Consider using the hybrid approach for non-critical matches

## Best Practices

1. **Test Thoroughly**
   - Run comparison tests on your actual data
   - Verify Thai-English matching improvements
   - Check edge cases (typos, abbreviations)

2. **Monitor After Deployment**
   - Track match accuracy metrics
   - Monitor performance impact
   - Collect user feedback

3. **Gradual Rollout**
   - Start with a small percentage of traffic
   - A/B test old vs new matcher
   - Gradually increase usage

## Support

For issues or questions:
1. Check the test results in `matching_comparison_results.json`
2. Review logs for detailed matching decisions
3. Use the analyze-match endpoint for specific product pairs

## Appendix: Algorithm Details

### Phonetic Matching Rules
The advanced matcher uses these Thai-English phonetic mappings:
- ก/ค → k
- พ/ภ/ฟ → ph/f
- ท/ธ/ต/ถ → th/t
- ช/ฉ/จ → ch/j
- And many more...

### N-gram Sizes
- Character n-grams: 2, 3, 4
- Optimized for model numbers and brand names
- Language-agnostic matching

### Fuzzy Matching
- Uses SequenceMatcher for string similarity
- Tolerance for typos and variations
- Configurable thresholds per field