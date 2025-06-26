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