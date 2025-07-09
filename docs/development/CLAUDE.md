# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraping project for HomePro (Thai home improvement retailer) products. The project uses Python with FastAPI for the REST API, Celery for background job processing, and Firecrawl API for web scraping.

## Quick Start

1. **Setup Environment**
   ```bash
   python3 setup.py
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Configure Credentials**
   - Copy `.env.example` to `.env`
   - Add your Supabase and Firecrawl credentials

3. **Create Database Schema**
   - Run `scripts/create_schema.sql` in Supabase SQL Editor

4. **Test Connections**
   ```bash
   python3 -m app.test_connection
   ```

## Architecture

The project follows a modular architecture:
- **app/core/** - Core scraping logic and Firecrawl integration
- **app/models/** - SQLAlchemy database models for products, prices, categories
- **app/services/** - External service integrations (Firecrawl client)
- **app/workers/** - Celery background tasks for scraping jobs
- **app/api/** - FastAPI REST endpoints
- **app/utils/** - Shared utilities (validation, formatting, logging)

## Key Components

### Firecrawl Integration
The project uses Firecrawl API for web scraping. When implementing scrapers:
- Use the Firecrawl Python SDK
- Handle rate limiting appropriately
- Implement retry logic for failed requests
- Parse structured data from Firecrawl's LLM-powered extraction

### Database Schema
Products are stored with:
- Product details (name, SKU, brand, category)
- Price history tracking
- Inventory status
- Promotion information
- Image URLs

### Background Processing
Celery workers handle:
- Scheduled scraping jobs
- Batch product updates
- Price change notifications
- Data validation and cleaning

## Development Commands

### Setup and Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (run in Supabase SQL Editor)
# See scripts/create_schema.sql
```

### Running the Application
```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8000

# Start Celery worker
celery -A app.workers worker --loglevel=info

# Start Celery beat scheduler
celery -A app.workers beat --loglevel=info
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_scraper.py
```

### Docker Operations
```bash
# Build containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## API Endpoints

Key endpoints to implement:
- `POST /api/v1/scraping/jobs` - Create scraping job
- `GET /api/v1/products` - List products with filtering
- `GET /api/v1/products/{id}/prices` - Price history
- `POST /api/v1/alerts` - Price drop alerts

## Performance Targets

- Scraping: 500+ products/hour
- Success rate: >95%
- API response time: <200ms (p95)
- Database queries: Optimize with proper indexing

## Data Validation

When processing scraped data:
- Validate SKU format
- Ensure prices are positive numbers
- Verify image URLs are accessible
- Check category mappings exist
- Handle Thai language content properly (UTF-8)

## Error Handling

- Implement exponential backoff for Firecrawl API failures
- Log all scraping errors with context
- Store failed job details for retry
- Alert on sustained high error rates

## Monitoring

- Track scraping success/failure rates
- Monitor API latency and error rates
- Alert on data quality issues (missing prices, invalid SKUs)
- Use Prometheus metrics with Grafana dashboards

## COMPREHENSIVE IMPROVEMENT PLAN

Based on comprehensive system analysis conducted on 2025-06-27, the following critical improvements are required:

### 🚨 CRITICAL PRIORITY (Fix Immediately)

#### Security Vulnerabilities
1. **SQL Injection Risk** - `app/services/supabase_service.py:256-258`
   - Issue: User input directly in search queries
   - Fix: Replace with parameterized queries using `.textSearch()` method
   - Impact: Prevents data breach vulnerabilities

2. **Input Validation Missing** - All API endpoints
   - Issue: No URL validation in scraping endpoints
   - Fix: Add validation middleware with request size limits
   - Files: `app/api/routers/scraping.py`, `app/api/routers/products.py`

3. **Authentication Weaknesses** - Database access
   - Issue: Overly permissive RLS policies
   - Fix: Implement user-based access control
   - File: `scripts/create_schema.sql:100-117`

#### Resource Management
4. **Context Manager Leaks** - `app/core/scraper.py:35, 130`
   - Issue: Potential resource leaks in error paths
   - Fix: Add proper cleanup in try/finally blocks
   - Impact: Prevents memory leaks and connection exhaustion

5. **Error Handling** - `app/core/data_processor.py:285`
   - Issue: Generic exception catching loses context
   - Fix: Implement specific exception types with proper logging
   - Impact: Better debugging and error recovery

### ⚠️ HIGH PRIORITY (Next Sprint)

#### Performance Optimization
6. **Rate Limiter Inefficiency** - `app/services/firecrawl_client.py:18-38`
   - Issue: O(n) operation on every API call
   - Fix: Implement sliding window algorithm with deque
   - Impact: Significant performance improvement

7. **Database Optimization** - Missing indexes
   - Issue: Common query patterns not optimized
   - Fix: Add composite indexes for search operations
   - Files: `scripts/create_schema.sql`

8. **Memory Management** - `app/core/scraper.py:132-164`
   - Issue: Large batches held in memory
   - Fix: Implement streaming with backpressure
   - Impact: Reduced memory usage, better scalability

#### Code Quality
9. **Code Duplication** - `app/api/routers/products.py:65-85, 114-132`
   - Issue: Repeated ProductResponse creation logic
   - Fix: Extract to helper function
   - Impact: Improved maintainability

10. **Testing Coverage** - Current <20%
    - Issue: Insufficient test coverage
    - Fix: Add comprehensive unit and integration tests
    - Impact: Better reliability and regression prevention

### 📈 MEDIUM PRIORITY (Future Releases)

#### Infrastructure
11. **Docker Configuration** - Missing containerization
    - Files to create: `Dockerfile`, `docker-compose.yml`
    - Impact: Consistent deployment environments

12. **CI/CD Pipeline** - No automation
    - Create: GitHub Actions workflows
    - Impact: Automated testing and deployment

13. **Health Checks** - Missing monitoring
    - Add: Dependency validation endpoints
    - Impact: Better operational visibility

#### Architecture Improvements
14. **Circuit Breakers** - External service reliability
    - Add: Failure isolation for Firecrawl API
    - Impact: Better resilience to external failures

15. **Caching Layer** - Performance optimization
    - Implement: Redis caching for frequent queries
    - Impact: Reduced database load, faster responses

### 🔧 LOW PRIORITY (Technical Debt)

16. **Structured Logging** - Better observability
17. **API Documentation** - Enhanced OpenAPI specs
18. **Load Testing** - Capacity planning
19. **Backup Strategy** - Data recovery procedures

## Implementation Phases

### Phase 1: Security & Stability (Weeks 1-2)
- Fix SQL injection vulnerabilities
- Add input validation middleware
- Implement proper error handling
- Fix resource management issues

### Phase 2: Performance (Weeks 3-4)
- Optimize rate limiting algorithm
- Add database indexes
- Implement connection pooling
- Add response caching

### Phase 3: Infrastructure (Weeks 5-6)
- Create Docker configuration
- Set up CI/CD pipeline
- Add comprehensive test suite
- Implement health checks

### Phase 4: Production Readiness (Weeks 7-8)
- Complete monitoring setup
- Add alerting systems
- Create operational runbooks
- Conduct load testing

## Critical Files to Monitor

### Security-Sensitive Files
- `app/services/supabase_service.py` - Database operations
- `app/api/routers/*.py` - API endpoints
- `config.py` - Configuration management
- `.env` - Credentials (never commit actual values)

### Performance-Critical Files
- `app/services/firecrawl_client.py` - Rate limiting
- `app/core/scraper.py` - Batch processing
- `app/core/data_processor.py` - Data validation

### Files Requiring Tests
- All files in `app/core/` - Business logic
- All files in `app/services/` - External integrations
- All files in `app/api/routers/` - API endpoints

## Quality Gates

Before any production deployment:
1. ✅ All security vulnerabilities fixed
2. ✅ Test coverage >80%
3. ✅ Performance benchmarks met
4. ✅ Security scan passes
5. ✅ Load testing completed

## Performance Benchmarks

- Product scraping: <1s per item
- API response time: <100ms (p95)
- Batch processing: 500+ items/minute
- Database queries: <50ms average
- Memory usage: <500MB steady state

## Monitoring Alerts

Set up alerts for:
- API error rate >5%
- Scraping success rate <90%
- Response time >500ms
- Memory usage >80%
- Database connection failures

Remember: This plan was generated from comprehensive analysis on 2025-06-27. Refer to this plan when prioritizing development work and implementing improvements.