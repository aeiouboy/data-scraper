# Scripts Directory

This directory contains all utility scripts organized by category.

## Directory Structure

```
scripts/
├── analysis/         # Data analysis and debugging scripts
├── maintenance/      # System maintenance and runtime scripts
├── matching/         # Product matching scripts
├── migration/        # Database and data migration scripts
├── monitoring/       # Monitoring and health check scripts
├── scraping/         # Web scraping scripts
├── setup/           # Project setup scripts
└── testing/         # Test scripts
```

## Categories

### 📊 analysis/
Scripts for analyzing data and debugging issues:
- `analyze_products.py` - Analyze product data
- `check_database_*.py` - Database status checks
- `debug_*.py` - Debugging utilities
- `inspect_*.py` - Data inspection tools

### 🔧 maintenance/
Core system scripts (copies also kept in root):
- `run_api.py` - Start API server
- `run_celery_*.py` - Celery worker management
- `quality_checker.py` - Code quality checks
- `config.py` - Configuration management
- `logging_config.py` - Logging setup

### 🔗 matching/
Product matching and comparison scripts:
- `create_*_matches.py` - Create product matches
- `fix_*_matches.py` - Fix matching issues
- `improve_matching_algorithm.py` - Enhance matching
- `run_advanced_matching.py` - Run matching algorithms

### 🔄 migration/
Database and data migration scripts:
- `migrate_*.py` - Data migration utilities
- `execute_*_migration.py` - Run migrations
- `fix_categories.py` - Category fixes

### 📡 monitoring/
System monitoring scripts:
- `monitor_scraping.py` - Monitor scraping jobs
- `quick_monitor.py` - Quick health check
- `run_monitoring_direct.py` - Direct monitoring

### 🕷️ scraping/
Web scraping scripts for all retailers:
- `scrape.py` - Main scraping script
- `scrape_*.py` - Retailer-specific scrapers
- `discover_*.py` - Category discovery
- `import_*.py` - Data import utilities

### ⚙️ setup/
Project setup scripts:
- `setup.py` - Package setup

### 🧪 testing/
Test scripts (consider moving to tests/):
- `test_*.py` - Various test scripts

## Usage Examples

### Run API Server
```bash
python run_api.py
# or
python scripts/maintenance/run_api.py
```

### Run Scraping
```bash
python scripts/scraping/scrape.py --retailer HP --limit 100
```

### Run Matching
```bash
python scripts/matching/improve_matching_algorithm.py
```

### Check Database
```bash
python scripts/analysis/check_database_status.py
```

## Essential Scripts in Root

These scripts remain in the root directory for easy access:
- `run_api.py` - API server entry point
- `setup.py` - Package installation
- `config.py` - Global configuration
- `logging_config.py` - Logging setup

All other scripts have been organized into their respective categories.