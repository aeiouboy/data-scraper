# RIS Data Scraping - Test Suite Documentation

## Overview

This document provides comprehensive documentation for the RIS Data Scraping test suite. The test suite is designed to ensure reliability, performance, and maintainability of the web scraping platform.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── scrapers/           # Scraper-specific tests
│   ├── utils/              # Utility function tests
│   └── services/           # Service layer tests
├── integration/            # Integration tests
│   ├── api/               # API endpoint tests
│   └── workflows/         # Multi-component workflow tests
├── e2e/                   # End-to-end tests
├── performance/           # Performance and load tests
├── security/              # Security tests
├── fixtures/              # Test fixtures and mocks
├── factories/             # Test data factories
└── test_data/            # Static test data files
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m e2e              # End-to-end tests only

# Run tests for specific component
pytest tests/unit/scrapers/
pytest tests/integration/api/test_products_api.py
```

### Test Categories

- **unit**: Fast, isolated tests of individual components
- **integration**: Tests that verify component interactions
- **e2e**: Full workflow tests including external services
- **slow**: Tests that take more than 5 seconds
- **external**: Tests requiring external services
- **security**: Security-focused tests
- **performance**: Performance and load tests

### Environment Setup

1. Copy test environment configuration:
```bash
cp tests/.env.test.example tests/.env.test
```

2. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

3. Set up test database:
```bash
python -m pytest --setup-only
```

## Test Fixtures

### Database Fixtures

```python
# Use seeded database with test data
def test_product_search(seeded_db):
    products = seeded_db.query(Product).all()
    assert len(products) > 0

# Use clean database
def test_create_product(test_session):
    product = Product(name="Test Product")
    test_session.add(product)
    test_session.commit()
```

### API Client Fixtures

```python
# Authenticated client
def test_protected_endpoint(authenticated_client):
    response = authenticated_client.get("/api/v1/admin/users")
    assert response.status_code == 200

# Regular client
def test_public_endpoint(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
```

### Mock Fixtures

```python
# Mock external services
def test_with_mocked_firecrawl(mock_firecrawl_client):
    mock_firecrawl_client.scrape.return_value = {"content": "..."}
    # Test scraping logic
```

## Test Factories

### ProductFactory

```python
from tests.factories import ProductFactory

# Create single product
product = ProductFactory.create(
    retailer_code="homepro",
    brand="Bosch",
    current_price=2990.0
)

# Create batch
products = ProductFactory.create_batch(10, retailer_code="megahome")

# Create matching pair
product1, product2 = ProductFactory.create_matching_pair()
```

### ScrapingJobFactory

```python
from tests.factories import ScrapingJobFactory

# Create completed job
job = ScrapingJobFactory.create(
    status="completed",
    total_products=100,
    successful_products=95
)

# Create job sequence
jobs = ScrapingJobFactory.create_job_sequence("homepro", job_count=5)
```

## Writing Tests

### Unit Test Example

```python
class TestTextNormalizer:
    def test_normalize_thai_brands(self, normalizer):
        assert normalizer.normalize_brand("บ๊อช") == normalizer.normalize_brand("BOSCH")
    
    def test_extract_numbers(self, normalizer):
        assert normalizer.extract_numbers("600W power") == [600]
```

### Integration Test Example

```python
class TestProductsAPI:
    @pytest.mark.asyncio
    async def test_search_products(self, client, seeded_db):
        response = client.get("/api/v1/products/search?q=drill")
        assert response.status_code == 200
        assert len(response.json()["products"]) > 0
```

### E2E Test Example

```python
class TestScrapingWorkflowE2E:
    @pytest.mark.asyncio
    async def test_full_scraping_cycle(self, test_session):
        # Create scraping job
        job = create_scraping_job("homepro", "category")
        
        # Execute scraping
        products = await scrape_category("https://homepro.co.th/c/tools")
        
        # Verify products saved
        assert len(products) > 0
        assert job.status == "completed"
```

## Performance Testing

### Load Test Example

```python
@pytest.mark.performance
async def test_concurrent_scraping(performance_helper):
    performance_helper.start_timer("concurrent_scraping")
    
    # Run concurrent operations
    results = await asyncio.gather(*tasks)
    
    performance_helper.stop_timer("concurrent_scraping")
    performance_helper.assert_performance("concurrent_scraping", max_duration=5.0)
```

### Throughput Test

```python
async def test_scraping_throughput():
    throughput = await measure_scraping_throughput(duration=10)
    assert throughput > 50  # products per second
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ['-m', 'unit']
```

## Test Coverage

### Coverage Requirements

- Overall: 80% minimum
- Critical paths: 95% minimum
- New code: 90% minimum

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html

# Check specific module
pytest --cov=src.scrapers tests/unit/scrapers/
```

## Debugging Tests

### Running with debugging

```bash
# Run with verbose output
pytest -vv tests/unit/test_specific.py

# Run with print statements
pytest -s tests/unit/test_specific.py

# Run with pdb on failure
pytest --pdb tests/unit/test_specific.py
```

### Common Issues

1. **Database connection errors**
   - Ensure test database is created
   - Check TEST_DATABASE_URL in .env.test

2. **Mock not working**
   - Verify patch path matches import path
   - Use `patch.object()` for class methods

3. **Async test failures**
   - Use `@pytest.mark.asyncio` decorator
   - Ensure all async calls are awaited

## Best Practices

1. **Test Isolation**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Clean up after tests

2. **Test Naming**
   - Use descriptive names
   - Follow pattern: `test_<what>_<condition>_<expected>`
   - Example: `test_scrape_product_invalid_url_returns_none`

3. **Assertions**
   - One logical assertion per test
   - Use specific assertions
   - Include helpful error messages

4. **Mocking**
   - Mock external dependencies
   - Don't mock what you're testing
   - Verify mock calls when appropriate

5. **Performance**
   - Keep unit tests fast (<100ms)
   - Mark slow tests appropriately
   - Run slow tests separately in CI

## Maintenance

### Adding New Tests

1. Create test file in appropriate directory
2. Import necessary fixtures and utilities
3. Write tests following existing patterns
4. Run tests locally before committing
5. Update documentation if needed

### Updating Fixtures

1. Modify fixture in `tests/fixtures/`
2. Run all dependent tests
3. Update factory if data model changed
4. Document changes in this README

### Test Data Management

1. Keep test data minimal
2. Use factories for dynamic data
3. Store static data in `test_data/`
4. Version control test data files