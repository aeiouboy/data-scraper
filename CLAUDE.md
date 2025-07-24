# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RIS Data Scrap is a comprehensive web scraping and price comparison system for Thai home improvement retailers. It uses FastAPI for the backend API, React for the frontend, Supabase for the database, and Firecrawl for web scraping.

## Key Architecture Components

### Backend Structure
- **FastAPI Application**: Main entry at `src/api/main.py`
- **Scrapers**: Individual retailer scrapers in `src/scrapers/` inheriting from `base_scraper.py`
- **Services**: Business logic in `src/services/`, notably `supabase_service.py` for database operations
- **Models**: Pydantic models in `src/models/` (Product, ScrapeJob, etc.)
- **API Routers**: Endpoint definitions in `src/api/routers/`

### Frontend
- **React Application**: Located in `frontend/` directory
- **Material-UI**: Primary UI component library
- **React Query**: For API data fetching and caching

### Database
- **Supabase/PostgreSQL**: All data persistence
- **No SQLAlchemy**: Direct Supabase client usage via `supabase-py`

## Essential Commands

### Development Setup
```bash
# Initial setup
make setup
cp .env.example .env  # Then configure with actual credentials

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install
```

### Running the Application
```bash
# Run both API and frontend
make run-all

# Run separately
make run-api        # API on http://localhost:8001
make run-frontend   # Frontend on http://localhost:3000

# Direct commands
python run_api.py
cd frontend && npm start
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest -m unit
pytest -m "not slow"

# Run single test
pytest tests/unit/test_data_processor.py::TestDataProcessor::test_extract_price_valid_numbers -v

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality
```bash
make lint    # Run linters (flake8, mypy, eslint)
make format  # Format code (black, isort, prettier)
```

### Scraping Operations
```bash
# Scrape all retailers
make scrape-all

# Scrape specific retailer
python scripts/scraping/scrape.py --retailer HP --category "power-tools" --limit 100

# Run product matching
make run-matching
```

## Environment Configuration

Required environment variables in `.env`:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Firecrawl API
FIRECRAWL_API_KEY=your-firecrawl-key

# Application
ENVIRONMENT=development
LOG_LEVEL=info
```

## Supported Retailers

- **HP**: HomePro (`homepro_scraper.py`)
- **TWD**: Thai Watsadu (`thaiwatsadu_scraper.py`)
- **GH**: Global House (`globalhouse_scraper.py`)
- **DH**: DoHome (`dohome_scraper.py`)
- **BT**: Boonthavorn (`boonthavorn_scraper.py`)
- **MH**: MegaHome (`megahome_scraper.py`)

## API Documentation

- Interactive docs: http://localhost:8001/docs
- Key endpoint groups:
  - `/api/products` - Product CRUD and search
  - `/api/scraping` - Scraping job management
  - `/api/price-comparisons-v2` - Price analysis
  - `/api/matching` - Product matching across retailers

## Testing Infrastructure

### Test Organization
- Tests use `pytest` with extensive fixtures
- Mock models in `tests/models_mock.py` for database entities
- Test factories in `tests/factories/` for generating test data

### Common Test Issues
- Import errors: Use `from src.models.product import Product` (not `src.api.models`)
- Missing dependencies: `pip install faker selenium factory-boy`
- Database tests: Use mock models as project uses Supabase directly

## Important Patterns

### Scraper Implementation
All scrapers inherit from `BaseScraper` and must implement:
- `scrape_category(category_url, max_pages)`
- `scrape_product(product_url)`
- `get_category_urls()`

### Product Matching
- Automated matching uses `ProductMatcher` service
- Confidence scoring based on name, brand, SKU, specifications
- Manual matching available through API

### Price Tracking
- Historical prices stored in `price_history` table
- Price comparisons calculate savings across retailers
- Monitoring service tracks price changes

## Common Development Tasks

### Adding a New Scraper
1. Create `src/scrapers/retailer_scraper.py` inheriting from `BaseScraper`
2. Implement required methods
3. Add retailer config to `src/config/retailers.py`
4. Test with `python scripts/scraping/scrape.py --retailer RETAILER_CODE`

### Modifying API Endpoints
1. Update router in `src/api/routers/`
2. Update models if needed in `src/models/`
3. Add tests in `tests/integration/api/`
4. Regenerate API docs automatically at `/docs`

### Database Changes
- Modify schema directly in Supabase dashboard
- Update Pydantic models to match
- No migration files needed (Supabase handles this)

## Project Organization

This project follows a professional enterprise-grade organization established through comprehensive transformation:

### File Organization Structure
- **Always follow the file organization structure documented in** `docs/development/PROJECT_FILE_ORGANIZATION.md`
- **Source code organization**: All application code in `src/` with clear separation of concerns
- **Data lifecycle management**: Complete data organization in `data/` with active/archive/config structure  
- **Documentation hierarchy**: Professional 3-tier documentation in `docs/` with maximum 3-click navigation
- **Development tools**: Organized into `scripts/`, `tools/`, and `tests/` directories
- **Frontend**: React application in `frontend/` with comprehensive test coverage

### Recent Major Improvements (Phase 1-4 Complete)
- **Phase 1**: JSON Data Organization - 49 files organized into data lifecycle management
- **Phase 2**: Documentation Restructure - 107+ files organized into professional hierarchy
- **Phase 3**: Python File Organization - 40 files organized into enterprise categories  
- **Phase 4**: Final Validation & Documentation - System health validated, documentation updated