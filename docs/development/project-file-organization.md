# RIS Data Scrap - Complete File Organization Guide

## Overview

This document provides a comprehensive guide to the file organization structure of the RIS Data Scrap project, detailing the architectural patterns, naming conventions, and organizational principles that govern the codebase.

## Project Architecture Summary

The project follows a **layered, domain-driven architecture** with clear separation of concerns:

```
RIS Data Scrap/
├── 📁 Backend Core (src/)           # FastAPI application & business logic
├── 📁 Frontend (frontend/)          # React application & UI components  
├── 📁 Testing (tests/)              # Comprehensive testing infrastructure
├── 📁 Scripts (scripts/)            # Operational & maintenance scripts
├── 📁 Documentation (docs/)         # Technical documentation
├── 📁 Data & Runtime (data/, logs/) # Runtime data & logging
└── 📁 Configuration                 # Project setup & configuration
```

## 🏗️ Backend Architecture (`src/`)

### Core Structure
```
src/
├── api/           # FastAPI application layer
├── scrapers/      # Web scraping implementations  
├── services/      # Business logic layer
├── utils/         # Utility functions & helpers
├── core/          # Core application logic
├── models/        # Data models & schemas
├── config/        # Configuration management
├── tasks/         # Background task definitions
└── database/      # Database utilities
```

### Key Components

#### **API Layer (`api/`)**
- **`main.py`**: FastAPI application bootstrap & configuration
- **`models.py`**: API request/response models (Pydantic)
- **`routers/`**: REST endpoint definitions (12 modules)
  - `products.py`, `scraping.py`, `matching.py`
  - `price_comparisons.py` (+ v2, advanced, optimized versions)
  - `analytics.py`, `monitoring.py`, `categories.py`

#### **Scrapers (`scrapers/`)**
- **`base_scraper.py`**: Abstract base class defining scraper interface
- **Retailer-specific implementations**:
  - `homepro_scraper.py` - HomePro (HP)
  - `thaiwatsadu_scraper.py` - Thai Watsadu (TWD)
  - `globalhouse_scraper.py` - Global House (GH)
  - `dohome_scraper.py` - DoHome (DH)  
  - `boonthavorn_scraper.py` - Boonthavorn (BT)
  - `megahome_scraper.py` - MegaHome (MH)
- **`adaptive_scraper_mixin.py`**: Advanced scraping capabilities

#### **Services (`services/`)**
Business logic organized by functional domain:
- **Database**: `supabase_service.py` - All database operations
- **Product Matching**: Multiple versions showing evolution
  - `product_matcher.py` (basic)
  - `advanced_product_matcher.py` 
  - `product_matcher_service_optimized.py`
- **Price Comparison**: Iterative improvement versions
  - `price_comparison_service.py`
  - `price_comparison_advanced.py`
  - `price_comparison_enhanced.py`
- **External APIs**: `firecrawl_client.py`, `notification_service.py`

#### **Core (`core/`)**
Foundational application logic:
- `data_processor.py` - Data transformation & validation
- `product_matcher.py` - Core matching algorithms
- `rate_limiter.py` - API rate limiting
- `url_discovery.py` - Dynamic URL discovery
- `scraper_config_manager.py` - Scraper configuration

#### **Utils (`utils/`)**
Reusable utility functions:
- **Text Processing**: `text_normalizer.py` (+ advanced, enhanced versions)
- **Product Matching**: `product_matcher.py` (multiple versions)
- **Validation**: `url_validator.py`
- **Progress**: `progress.py`

#### **Models (`models/`)**
Data model definitions:
- `product.py` - Product & scraping job models
- `matching_models.py` - Product matching models
- `schedule.py` - Scheduling models

### Naming Conventions
- **Files**: `snake_case` with descriptive names
- **Versioning**: Suffix patterns (`_v2`, `_advanced`, `_optimized`, `_enhanced`)
- **Services**: `{function}_service.py` pattern
- **Models**: Domain entity names (`product.py`, `schedule.py`)

## 🖥️ Frontend Architecture (`frontend/src/`)

### Structure
```
frontend/src/
├── components/    # Reusable UI components
├── pages/         # Route-level components
├── services/      # API client & data services
├── contexts/      # React context providers
├── hooks/         # Custom React hooks
├── utils/         # Frontend utilities
├── types/         # TypeScript definitions
└── __tests__/     # Component tests
```

### Key Components

#### **Components (`components/`)**
Reusable UI building blocks:
- **Price Comparison**: 
  - `PriceComparisonCard.tsx`
  - `ImprovedPriceComparisonCard.tsx`
  - `OptimizedPriceComparison.tsx`
- **Filtering**: 
  - `PriceComparisonFilters.tsx`
  - `FilterableRetailerSelector.tsx`
  - `FilterSummary.tsx`
- **Layout**: `Layout.tsx`, `ErrorBoundary.tsx`
- **Tracking**: `PriceTrackingDashboard.tsx`

#### **Pages (`pages/`)**
Route-level components (feature-based):
- **Price Comparisons**: Multiple versions showing UI evolution
  - `PriceComparisons.tsx`
  - `ImprovedPriceComparisons.tsx`
  - `OptimizedPriceComparisons.tsx`
  - `PriceComparisonsOptimized.tsx`
- **Core Pages**: `Dashboard.tsx`, `Products.tsx`, `Scraping.tsx`
- **Analytics**: `Analytics.tsx`, `Monitoring.tsx`

#### **Services (`services/`)**
- `api.ts` - Main API client with React Query integration
- `optimizedMatchingApi.ts` - Optimized API calls for matching

#### **Supporting Modules**
- **Contexts**: `RetailerContext.tsx` - Global retailer state
- **Hooks**: `useCategoryMonitoring.ts`, `useDebounce.ts`
- **Utils**: Performance monitoring, retailer detection, CSS utilities
- **Types**: TypeScript definitions for categories, schedules

### Naming Conventions
- **Components**: `PascalCase` (React standard)
- **Files**: `camelCase` for utilities, `PascalCase` for components
- **Versioning**: Descriptive prefixes (`Improved`, `Optimized`)

## 🧪 Testing Infrastructure (`tests/`)

### Testing Pyramid Structure
```
tests/
├── unit/          # Unit tests (fastest, most isolated)
├── integration/   # Integration tests (medium scope)
├── e2e/          # End-to-end tests (full workflow)
├── performance/   # Performance benchmarks
├── security/      # Security testing (placeholder)
├── factories/     # Test data generation
├── fixtures/      # Test setup & teardown
└── utils/         # Testing utilities
```

### Test Organization

#### **Unit Tests (`unit/`)**
- **`scrapers/`**: Individual scraper testing
  - `test_base_scraper.py`
  - `test_homepro_scraper.py`
  - `test_thaiwatsadu_scraper.py`
- **`services/`**: Service layer testing
- **`utils/`**: Utility function testing
  - `test_product_matcher.py`
  - `test_text_normalizer.py`

#### **Integration Tests (`integration/`)**
- **`api/`**: API endpoint testing
  - `test_matching_api.py`
  - `test_products_api.py`
  - `test_scraping_api.py`
- **`workflows/`**: Multi-component integration

#### **E2E Tests (`e2e/`)**
- **Python**: `test_price_monitoring_workflow.py`
- **TypeScript**: Frontend E2E with Playwright
  - `improved-price-comparisons.spec.ts`

#### **Supporting Infrastructure**
- **Factories**: Test data generation using Factory Boy
  - `product_factory.py`, `match_factory.py`
- **Fixtures**: Reusable test setup
  - `database.py`, `api_client.py`, `scrapers.py`
- **Mocks**: `models_mock.py`, `mock_scraper_manager.py`

### Testing Patterns
- **Pyramid Structure**: More unit tests, fewer E2E tests
- **Factory Pattern**: Consistent test data generation
- **Mock Strategy**: External dependencies mocked appropriately
- **Fixture Reuse**: Common setup shared across tests

## 📋 Scripts Directory (`scripts/`)

### Functional Organization
```
scripts/
├── analysis/      # Data analysis & debugging (13 scripts)
├── scraping/      # Web scraping operations (19 scripts)
├── testing/       # Testing & validation (38 scripts)
├── matching/      # Product matching (9 scripts)
├── monitoring/    # System monitoring (3 scripts)
├── maintenance/   # System maintenance (6 scripts)
├── migration/     # Database migrations (3 scripts)
└── setup/         # Setup & configuration
```

### Script Categories

#### **Analysis (`analysis/`)**
Data investigation and debugging:
- `analyze_products.py` - Product data analysis
- `check_database_status.py` - Database health checks
- `debug_price.py` - Price calculation debugging
- `analyze_twd_scraping_issue.py` - Retailer-specific debugging

#### **Scraping (`scraping/`)**
Web scraping operations:
- **Discovery**: `discover_all_categories.py`, `discover_twd_categories.py`
- **Execution**: `scrape.py`, `batch_scrape.py`, `scrape_all_categories.py`
- **Verification**: `verify_boonthavorn.py`
- **Specialized**: `scrape_refrigerators.py`, `scrape_twd_aircon_category.py`

#### **Testing (`testing/`)**
Comprehensive testing scripts (38 total):
- **Feature Testing**: `test_adaptive_scraping.py`, `test_advanced_matching.py`
- **Scraper Testing**: `test_twd_scraper.py`, `test_gh_scraper.py`
- **URL Testing**: `test_twd_url_patterns.py`, `test_urls.py`
- **Database Testing**: `verify_twd_database_operations.py`

#### **Matching (`matching/`)**
Product matching operations:
- `create_sample_matches.py` - Generate test matches
- `improve_matching_algorithm.py` - Algorithm enhancement
- `fix_refrigerator_matches.py` - Category-specific fixes

#### **Maintenance (`maintenance/`)**
System operation scripts:
- `run_api.py` - API server startup
- `run_celery_worker.py` - Background task processing
- `quality_checker.py` - Code quality validation

### Naming Conventions
- **Action-oriented**: `{verb}_{object}.py` (e.g., `analyze_products.py`)
- **Test prefix**: `test_` for testing scripts
- **Feature grouping**: Related scripts in same directory
- **Descriptive names**: Clear purpose from filename

## 📚 Documentation (`docs/`)

### Hierarchical Organization
```
docs/
├── analysis/           # Technical analysis & reports
├── api/               # API documentation & improvements  
├── architecture/      # System architecture docs
├── development/       # Development guides & setup
├── features/          # Feature-specific documentation
├── project_management/ # Project management docs
├── deployment/        # Deployment guides
└── index.md          # Documentation homepage
```

### Documentation Types

#### **Technical Documentation**
- **Architecture**: System design, migration guides, project structure
- **API**: Endpoint documentation, optimization guides
- **Analysis**: Performance reports, comparison studies

#### **Development Documentation**
- **Setup**: `SETUP.md`, `TROUBLESHOOTING.md`
- **Guides**: `FILE_ORGANIZATION_GUIDE.md`, `MCP_SERVERS_GUIDE.md`
- **Standards**: `CLAUDE.md` (AI assistant configuration)

#### **Feature Documentation**
- **Scraping**: `ADAPTIVE_SCRAPING.md`, `SCRAPING_GUIDE.md`
- **Monitoring**: `CATEGORY_MONITORING.md`, `SCHEDULED_MONITORING.md`
- **Analytics**: `PRICE_TRACKING_DASHBOARD.md`

#### **Project Management**
- **Organization**: `COMPLETE_ORGANIZATION_REPORT.md`
- **Status**: `FINAL_ORGANIZATION_STATUS.md`
- **Summaries**: Various implementation and cleanup summaries

### Documentation Standards
- **Markdown Format**: All documentation in `.md` format
- **Index Files**: Navigation aids in each directory
- **Descriptive Naming**: Clear purpose from filename
- **Comprehensive Coverage**: All major features documented

## 💾 Data & Runtime

### Data Directory (`data/`)
```
data/
├── scraping_results/  # Raw scraping outputs (JSON)
├── analysis_reports/  # Generated analysis reports
├── html_samples/      # Sample HTML for testing
├── progress/          # Runtime progress tracking
├── csv_exports/       # Data exports
└── url_lists/         # Discovered URL collections
```

### Logs Directory (`logs/`)
Component-specific logging:
- **API Logs**: `api.log`, `api_server.log`, `http.log`
- **Service Logs**: `scrapers.log`, `services.log`
- **Application Logs**: `app.log`, `backend.log`

## 🏛️ Organizational Principles

### 1. **Layered Architecture**
- Clear separation between presentation, business logic, and data layers
- Well-defined interfaces between layers
- Dependency injection and inversion of control

### 2. **Domain-Driven Design**
- Business logic organized by functional domains
- Clear bounded contexts (scraping, matching, price comparison)
- Rich domain models with business rules

### 3. **Iterative Improvement**
- Multiple versions of core components showing evolution
- Version suffixes indicating improvement levels
- Backward compatibility maintained where possible

### 4. **Comprehensive Testing**
- Testing pyramid with appropriate test distribution
- Extensive mock and fixture infrastructure
- Both unit and integration test coverage

### 5. **Operational Excellence**
- Extensive automation scripts for common operations
- Comprehensive logging and monitoring
- Robust error handling and recovery

### 6. **Documentation-Driven Development**
- Comprehensive documentation for all major components
- Architecture decision records
- User and developer guides

### 7. **Configuration Management**
- Environment-specific configuration
- Externalized configuration for different deployment targets
- Clear separation of concerns

## 🔧 Development Workflow Integration

### File Creation Patterns
1. **New Features**: Start in `src/`, add tests in `tests/`, document in `docs/`
2. **Scripts**: Add to appropriate `scripts/` subdirectory with descriptive name
3. **Configuration**: Update relevant config files and document changes

### Versioning Strategy
- **Iterative Improvement**: Create new versions rather than breaking changes
- **Deprecation Path**: Keep old versions until migration complete
- **Clear Naming**: Version suffixes indicate improvement level

### Quality Assurance
- **Testing Requirements**: All new code must have corresponding tests
- **Documentation Updates**: Update relevant documentation with changes
- **Script Validation**: Test scripts in development environment first

## 📈 Project Maturity Indicators

### Codebase Maturity
- **84+ Test Cases**: Comprehensive testing coverage
- **Multiple Component Versions**: Iterative improvement approach
- **Extensive Documentation**: Thorough coverage of all aspects
- **Operational Tooling**: Rich set of maintenance and analysis scripts

### Organizational Maturity
- **Clear Architecture**: Well-defined layers and boundaries
- **Consistent Naming**: Standardized naming conventions
- **Separation of Concerns**: Each component has single responsibility
- **Version Management**: Careful handling of component evolution

This file organization represents a mature, production-ready codebase with strong architectural foundations, comprehensive testing, and excellent operational support.