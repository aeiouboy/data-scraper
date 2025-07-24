# File Organization Maintenance Guide

## Overview

This guide helps maintain the organized structure of the RIS Data Scrap codebase. Follow these guidelines when adding new files or working with existing ones.

## Quick Reference - Where Files Belong

### 🐍 Python Scripts

| File Type | Location | Example |
|-----------|----------|---------|
| **Test scripts** | `scripts/testing/` | `test_new_feature.py` |
| **Debug utilities** | `scripts/debug/` | `debug_api_response.py` |
| **Data processing** | `scripts/utilities/` | `clean_product_data.py` |
| **Monitoring tools** | `scripts/monitoring/` | `monitor_scraping_jobs.py` |
| **Scraping scripts** | `scripts/scraping/` | `scrape_new_retailer.py` |
| **Database scripts** | `scripts/database/` | `migrate_schema.py` |
| **Analysis tools** | `scripts/analysis/` | `analyze_price_trends.py` |

### 📁 Data Files

| File Type | Location | Example |
|-----------|----------|---------|
| **Scraping results** | `data/scraping_results/` | `hp_products_20250714.json` |
| **Analysis reports** | `data/analysis_reports/` | `price_comparison_report.json` |
| **Test data** | `data/test_data/` | `sample_products.xlsx` |
| **Processing results** | `data/results/` | `validation_results.json` |
| **Progress tracking** | `data/progress/` | `scraping_progress.json` |

### 📚 Documentation

| File Type | Location | Example |
|-----------|----------|---------|
| **API docs** | `docs/api/` | `API_ENDPOINTS.md` |
| **Feature docs** | `docs/features/` | `SCRAPING_GUIDE.md` |
| **Development guides** | `docs/development/` | `SETUP_GUIDE.md` |
| **Architecture docs** | `docs/architecture/` | `SYSTEM_DESIGN.md` |
| **Archived reports** | `docs/archive/` | `OLD_REPORT_2024.md` |

### 🧪 Test Files

| File Type | Location | Example |
|-----------|----------|---------|
| **Unit tests** | `tests/unit/` | `test_price_calculator.py` |
| **Integration tests** | `tests/integration/` | `test_api_workflow.py` |
| **E2E tests** | `tests/e2e/` | `test_full_scraping_flow.py` |
| **Performance tests** | `tests/performance/` | `test_scraping_speed.py` |

## Adding New Files

### 1. Python Scripts

Before creating a new Python script in the root directory, ask yourself:

- **Is it a test?** → Place in `scripts/testing/`
- **Is it for debugging?** → Place in `scripts/debug/`
- **Is it a utility?** → Place in `scripts/utilities/`
- **Is it for monitoring?** → Place in `scripts/monitoring/`
- **Is it for scraping?** → Place in `scripts/scraping/`

### 2. One-Off Scripts

For temporary or experimental scripts:
1. Create in `scripts/utilities/` with prefix `temp_`
2. Add comment at top explaining purpose
3. Delete when no longer needed

### 3. Documentation

When creating new documentation:
1. Use descriptive UPPERCASE names with underscores
2. Add to appropriate subdirectory
3. Update relevant index.md files
4. Archive old versions to `docs/archive/`

## File Naming Conventions

### Python Files
```
# Good examples:
test_product_matching.py      # Test script
debug_api_response.py         # Debug utility
monitor_scraping_jobs.py      # Monitoring tool
analyze_price_trends.py       # Analysis script

# Bad examples:
test.py                       # Too generic
producttest.py               # No underscores
TestProductMatching.py       # Wrong case
```

### Data Files
```
# Include timestamps:
hp_products_20250714.json
scraping_results_20250714_143022.csv

# Include retailer codes:
twd_categories_analysis.json
hp_price_comparison.json
```

### Documentation
```
# Use UPPERCASE with underscores:
SETUP_GUIDE.md
API_DOCUMENTATION.md
TROUBLESHOOTING_GUIDE.md
```

## Maintenance Tasks

### Daily
- Check root directory for new unorganized files
- Move any misplaced files to correct locations

### Weekly
- Review `scripts/utilities/` for temp files to remove
- Archive old reports from `data/` directories
- Update documentation for any new features

### Monthly
- Full audit of file organization
- Update this guide with any new patterns
- Clean up archived files older than 3 months

## Common Mistakes to Avoid

1. **Don't create scripts in root directory**
   - Always use appropriate subdirectory

2. **Don't mix test and production code**
   - Keep tests in `tests/` or `scripts/testing/`

3. **Don't forget timestamps on data files**
   - Always include date in filename

4. **Don't leave temporary files**
   - Clean up experiments and one-off scripts

5. **Don't duplicate functionality**
   - Check existing scripts before creating new ones

## Quick Commands

### Find misplaced Python files in root
```bash
ls -la *.py | grep -v "__" | grep -v "setup.py" | grep -v "config.py"
```

### Move test files to correct location
```bash
mv test_*.py scripts/testing/
```

### Archive old reports
```bash
mv *_REPORT.md docs/archive/
```

### Find large data files
```bash
find data/ -size +10M -type f
```

## Automated Organization

Run the organization check script weekly:
```bash
python scripts/utilities/check_file_organization.py
```

This will:
- List files in wrong locations
- Suggest correct locations
- Optionally move files automatically

## Getting Help

If unsure where a file belongs:
1. Check `docs/development/PROJECT_FILE_ORGANIZATION.md`
2. Look for similar existing files
3. Ask in team chat
4. When in doubt, use `scripts/utilities/`

Remember: A well-organized codebase is easier to maintain, debug, and scale!