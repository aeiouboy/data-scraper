# Scripts Integration Tests

This directory contains integration tests that were moved from `scripts/testing/`. These tests focus on testing script functionality and integration workflows.

## Test Categories

### Scraper Testing
- **TWD (Thai Watsadu) Tests**: Multiple test files for TWD scraper functionality
- **Adaptive Scraping Tests**: Tests for adaptive scraping capabilities
- **Multi-retailer Tests**: Tests across different retailer scrapers

### Matching Tests
- **Advanced Matching**: Tests for enhanced product matching algorithms
- **Brand Aliases**: Tests for brand alias functionality
- **Complete Matching Flow**: End-to-end matching workflow tests

### Data Validation Tests
- **Data Validator**: Tests for data validation pipelines
- **Database Operations**: Tests for database interaction scripts

### Performance Tests
- **Scraping Performance**: Tests for scraper performance and efficiency

## Running Tests

These tests can be run individually or as a group:

```bash
# Run all scripts integration tests
pytest tests/scripts_integration/

# Run specific test category
pytest tests/scripts_integration/test_advanced_matching*.py

# Run single test file
pytest tests/scripts_integration/test_adaptive_scraping.py -v
```

## Notes

- These tests were originally located in `scripts/testing/`
- They test script functionality rather than core unit functionality
- Some tests may require specific environment setup or data fixtures
- Review individual test files for specific requirements and dependencies