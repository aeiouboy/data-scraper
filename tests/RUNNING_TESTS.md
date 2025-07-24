# Running Tests - Quick Guide

## Test Setup

1. **Install test dependencies:**
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

2. **Activate virtual environment:**
```bash
source venv/bin/activate
```

## Running Tests

### 1. Run All Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### 2. Run Specific Test Categories

```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests (requires Selenium)
pytest tests/e2e/

# Run performance tests
pytest tests/performance/
```

### 3. Run Individual Test Files

```bash
# Run a specific test file
pytest tests/unit/test_data_processor.py

# Run with verbose output
pytest tests/unit/test_data_processor.py -v

# Run a specific test function
pytest tests/unit/test_data_processor.py::TestDataProcessor::test_extract_price_valid_numbers
```

### 4. Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Run tests excluding slow ones
pytest -m "not slow"
```

### 5. Run with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html

# Coverage with missing lines
pytest --cov=src --cov-report=term-missing
```

## Current Test Status

### ✅ Working Tests
- `tests/test_simple.py` - Basic pytest functionality
- `tests/unit/test_data_processor.py` - Data processing tests (7 failures, 29 passed)
- `tests/unit/test_firecrawl_client.py` - Firecrawl client tests
- `tests/unit/test_scraper.py` - Scraper tests
- `tests/unit/test_supabase_service.py` - Supabase service tests

### ⚠️ Tests Needing Fixes
- Tests importing from `src.api.models` need to use `src.models.product`
- Tests importing database models need adjustment for Supabase integration
- Tests requiring `selenium` need the package installed

## Common Issues and Solutions

### Import Errors
If you see `ImportError: cannot import name 'Product' from 'src.api.models'`:
- Change imports from `src.api.models` to `src.models.product`

### Missing Dependencies
If you see `ModuleNotFoundError`:
```bash
# Install missing test dependencies
pip install selenium faker factory-boy
```

### Database Connection Errors
The project uses Supabase, not SQLAlchemy. Database-dependent tests need to be updated.

## Quick Test Commands

```bash
# Quick smoke test
pytest tests/test_simple.py -v

# Run existing working tests
pytest tests/unit/test_data_processor.py -v

# Run tests with short traceback
pytest --tb=short

# Run tests in parallel (faster)
pytest -n auto

# Run only passing tests (skip known failures)
pytest -k "not (test_clean_text_special_characters or test_extract_sku_no_match)"
```

## Writing New Tests

1. Create test files with `test_` prefix
2. Test classes should start with `Test`
3. Test methods should start with `test_`
4. Use fixtures from `tests/fixtures/`
5. Use factories from `tests/factories/`

Example:
```python
import pytest
from src.models.product import Product

def test_product_creation():
    product = Product(
        sku="TEST001",
        name="Test Product",
        retailer_code="homepro"
    )
    assert product.sku == "TEST001"
```

## Next Steps

1. Fix import statements in test files
2. Install missing dependencies
3. Update database-dependent tests for Supabase
4. Run full test suite
5. Achieve 80%+ code coverage