# File Organization Guide

## Overview
This guide documents the best practices for organizing files in the RIS Data Scraper project. Following these conventions ensures a clean, maintainable, and professional codebase.

## Directory Structure

```
ris-data-scrap/
├── src/                    # Source code (app logic)
│   ├── api/               # API endpoints
│   ├── scrapers/          # Web scrapers
│   ├── services/          # Business logic services
│   ├── models/            # Data models
│   ├── config/            # Configuration modules
│   ├── core/              # Core utilities
│   └── utils/             # Helper utilities
├── scripts/               # Executable scripts
│   ├── analysis/          # Data analysis scripts
│   ├── scraping/          # Scraping execution scripts
│   ├── testing/           # Test scripts
│   ├── matching/          # Product matching scripts
│   ├── maintenance/       # System maintenance
│   ├── monitoring/        # Monitoring scripts
│   ├── migration/         # Data migration scripts
│   └── setup/             # Setup and installation
├── data/                  # Data files (git-ignored)
│   ├── scraping_results/  # Raw scraping outputs
│   ├── analysis_reports/  # Analysis outputs
│   ├── test_data/         # Test fixtures
│   └── progress/          # Progress tracking
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── architecture/      # System design docs
│   ├── development/       # Developer guides
│   ├── features/          # Feature documentation
│   ├── deployment/        # Deployment guides
│   ├── analysis/          # Analysis reports
│   └── project_management/# Project docs
├── frontend/              # React frontend
├── tests/                 # Pytest test suite
├── .github/               # GitHub workflows
└── [root files]           # Essential files only

```

## File Organization Rules

### 1. Root Directory Files

**ONLY these files should be in root:**
- `README.md` - Project overview
- `run_api.py` - API entry point
- `setup.py` - Package setup
- `config.py` - Main configuration
- `logging_config.py` - Logging setup
- `requirements*.txt` - Dependencies
- `.env*` - Environment files
- Configuration files (`.gitignore`, `pytest.ini`, etc.)

**NOT in root:**
- Test scripts (`test_*.py`)
- Analysis scripts
- Temporary outputs
- Debug files
- Documentation (except README)

### 2. Test Files

All test files should be organized in appropriate directories:

```python
# ❌ WRONG: Test file in root
/test_scraper.py

# ✅ CORRECT: Organized test files
/tests/unit/test_scraper.py          # Unit tests
/scripts/testing/test_scraper.py     # Integration/manual tests
```

### 3. Script Organization

Scripts are organized by function, not by type:

```python
# ❌ WRONG: Generic script in root
/analyze_data.py

# ✅ CORRECT: Organized by function
/scripts/analysis/analyze_products.py
/scripts/scraping/scrape_multi_retailer.py
/scripts/testing/test_api_endpoints.py
```

### 4. Data Files

All data outputs should be in the `data/` directory:

```python
# ❌ WRONG: Data files in root
/scraping_results.json
/debug_output.txt

# ✅ CORRECT: Organized data files
/data/scraping_results/homepro_20240709.json
/data/analysis_reports/category_analysis.json
/data/test_data/sample_products.json
```

### 5. Documentation

Documentation is organized by audience and purpose:

```python
# ❌ WRONG: Docs in root
/API_GUIDE.md
/SETUP.md

# ✅ CORRECT: Organized documentation
/docs/api/API_GUIDE.md
/docs/development/SETUP.md
/docs/architecture/SYSTEM_DESIGN.md
```

## File Naming Conventions

### Python Files
- Use lowercase with underscores: `product_scraper.py`
- Test files prefix with `test_`: `test_product_scraper.py`
- Scripts should be descriptive: `analyze_price_trends.py`

### Data Files
- Include timestamp when relevant: `products_20240709_141523.json`
- Use descriptive names: `twd_category_analysis.json`
- Group by type in subdirectories

### Documentation
- Use UPPERCASE for main docs: `README.md`, `SETUP.md`
- Use title case for guides: `File_Organization_Guide.md`
- Be descriptive: `API_Authentication_Guide.md`

## Common Mistakes to Avoid

### 1. Test Files in Root
```bash
# ❌ WRONG
/test_api.py
/debug_scraper.py

# ✅ CORRECT
/scripts/testing/test_api.py
/scripts/testing/debug_scraper.py
```

### 2. Temporary Files
```bash
# ❌ WRONG
/output.json
/debug.log

# ✅ CORRECT
/data/analysis_reports/scraper_output_20240709.json
/logs/debug_20240709.log
```

### 3. Mixed Organization
```bash
# ❌ WRONG: Mixed by file type
/python_scripts/
/json_files/
/markdown_docs/

# ✅ CORRECT: Organized by function
/scripts/analysis/
/data/scraping_results/
/docs/development/
```

## Cleanup Commands

### Find Misplaced Files
```bash
# Find test files in root
ls -la *.py | grep test

# Find data files in root
ls -la *.json *.csv *.txt | grep -v requirements

# Find all Python files in root
ls -la *.py | grep -v -E "run_api|setup|config|logging_config"
```

### Organize Files
```bash
# Run the organization script
python scripts/organize_remaining_files.py

# Move test files manually
mv test_*.py scripts/testing/

# Move data files manually
mv *.json data/analysis_reports/
```

## Automation

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Check for test files in root
if ls test_*.py 1> /dev/null 2>&1; then
    echo "Error: Test files found in root directory"
    echo "Move them to scripts/testing/ or tests/"
    exit 1
fi
```

### GitHub Action
Check file organization in CI:
```yaml
- name: Check file organization
  run: |
    # Ensure no test files in root
    ! ls test_*.py 2>/dev/null
    # Ensure no data files in root
    ! ls *.json 2>/dev/null | grep -v package
```

## Summary

Maintaining proper file organization:
1. **Improves code discoverability** - Developers can find files quickly
2. **Reduces clutter** - Root directory stays clean and professional
3. **Enables better tooling** - Scripts can assume consistent structure
4. **Facilitates collaboration** - Team members know where to put files
5. **Looks professional** - Shows attention to detail

Remember: A clean project structure reflects clean code practices!