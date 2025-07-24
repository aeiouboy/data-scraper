# Source Code Version Matrix

This document tracks the multiple versions of core components and their current status.

## Current Active Versions

### Product Matcher Components
- **Current Production**: `src/services/product_matcher.py` 
- **Optimized Version**: `src/services/product_matcher_service_optimized.py` (actively used)
- **Utils Version**: `src/utils/product_matcher.py` (utility functions)
- **Advanced Version**: `src/utils/product_matcher_advanced.py` (experimental)
- **Enhanced Version**: `src/utils/product_matcher_enhanced.py` (experimental) 
- **Optimized Utils**: `src/utils/product_matcher_optimized.py` (experimental)

### Text Normalizer Components  
- **Current Production**: `src/utils/text_normalizer.py`
- **Advanced Version**: `src/utils/text_normalizer_advanced.py` (experimental)
- **Enhanced Version**: `src/utils/text_normalizer_enhanced.py` (experimental)

### Price Comparison Components
- **Current Production**: `src/services/price_comparison_service.py`
- **Advanced Version**: `src/services/price_comparison_advanced.py` (actively used)
- **Enhanced Version**: `src/services/price_comparison_enhanced.py` (experimental)

### API Router Components
- **Current Production**: `src/api/routers/matching.py`
- **Advanced Version**: `src/api/routers/matching_advanced.py` (experimental)
- **Optimized Version**: `src/api/routers/matching_optimized.py` (actively used)

- **Current Production**: `src/api/routers/price_comparisons.py`
- **V2 Version**: `src/api/routers/price_comparisons_v2.py` (actively used)
- **Advanced Version**: `src/api/routers/price_comparisons_advanced.py` (actively used)
- **V2 Optimized**: `src/api/routers/price_comparisons_v2_optimized.py` (actively used)

### Scraper Components
- **Current Production**: `src/scrapers/thaiwatsadu_scraper.py`
- **Improved Version**: `src/scrapers/thaiwatsadu_scraper_improved.py` (experimental)

## Status Definitions

- **Current Production**: The stable, production-ready version actively used in main workflows
- **Actively Used**: Version currently registered in main.py and serving API endpoints
- **Experimental**: Development/testing version with enhanced features, not in production

## Import Usage in main.py

The following versions are currently imported and registered in `src/api/main.py`:
- `price_comparisons_v2`
- `price_comparisons_advanced` 
- `price_comparisons_v2_optimized`
- `matching_optimized`

## Consolidation Strategy

### Phase 1: Documentation (Current)
- Document all versions and their usage
- Identify which versions are actively serving traffic
- Map dependencies between versions

### Phase 2: Deprecation Planning
- Choose single "winner" for each component type
- Create migration plan for consolidating features
- Set deprecation timeline for unused versions

### Phase 3: Implementation
- Merge best features into chosen versions
- Update all imports to use consolidated versions
- Archive deprecated versions

## Dependencies

The following files have complex cross-dependencies and should be analyzed carefully before any consolidation:
- Product matcher components (used across multiple services)
- Text normalizer (used in multiple matching algorithms)
- Price comparison services (multiple API endpoints depend on different versions)

## Recommendations

1. **Keep Current Structure** for production stability
2. **Document Usage** more clearly in code comments
3. **Create Migration Strategy** before removing any versions
4. **Test Thoroughly** any consolidation changes
5. **Use Feature Flags** for transitioning between versions