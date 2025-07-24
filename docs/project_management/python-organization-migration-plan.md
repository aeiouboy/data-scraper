# Python Files Organization Migration Plan
## RIS Data Scrap Project

**Date:** 2025-07-21  
**Target:** Transform 384 Python files from disorganized structure to clean, maintainable organization

## Migration Script

### Phase 1: Backup and Preparation

```bash
#!/bin/bash
# Create backup
cp -r "/Users/chongraktanaka/Documents/Project/ris data scrap" "/Users/chongraktanaka/Documents/Project/ris data scrap_backup_$(date +%Y%m%d_%H%M%S)"

# Create new directory structure
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"

# Create new directories
mkdir -p config
mkdir -p tools/{data_quality,fixes,validation,debug,archive}
mkdir -p tests/manual
```

### Phase 2: Move Configuration Files

```bash
# Move configuration files from root to config/
mv config.py config/app_config.py
mv logging_config.py config/
```

### Phase 3: Categorize Root-Level Scripts

#### 3.1 Data Quality Scripts → tools/data_quality/

```bash
# Move data quality and analysis scripts
mv analyze_false_match.py tools/data_quality/
mv analyze_null_skus.py tools/data_quality/
mv analyze_url_issues.py tools/data_quality/
mv audit_false_matches.py tools/data_quality/
mv investigate_data_quality.py tools/data_quality/
mv investigate_twd_category_products.py tools/data_quality/
mv quick_quality_check.py tools/data_quality/
mv final_quality_validation.py tools/data_quality/
mv check_homepro_categories.py tools/data_quality/
```

#### 3.2 Fix Scripts → tools/fixes/

```bash
# Move one-time fix scripts
mv apply_hp_price_improvements.py tools/fixes/
mv automated_twd_category_fix.py tools/fixes/
mv comprehensive_fix_all.py tools/fixes/
mv fix_specific_products.py tools/fixes/
mv fix_twd_category_url_extraction.py tools/fixes/
mv fix_twd_category_urls.py tools/fixes/
mv fix_twd_url_validation.py tools/fixes/
mv focused_batch_fix.py tools/fixes/
mv targeted_fix_remaining.py tools/fixes/
mv remove_false_positive_match.py tools/fixes/
mv remove_product_from_match.py tools/fixes/
mv disable_false_positive_match.py tools/fixes/
mv rescrap_missing_data.py tools/fixes/
mv rescrape_homepro_categories.py tools/fixes/
mv optimize_import.py tools/fixes/
```

#### 3.3 Debug Scripts → tools/debug/

```bash
# Move debug scripts from root
mv debug_homepro_pricing.py tools/debug/
mv debug_match_schema.py tools/debug/
mv debug_specific_match.py tools/debug/
mv debug_specific_twd_product.py tools/debug/

# Move existing debug scripts from scripts/debug/ to tools/debug/
mv scripts/debug/* tools/debug/
rmdir scripts/debug
```

#### 3.4 Validation Scripts → tools/validation/

```bash
# Move validation scripts
mv validate_homepro_pricing.py tools/validation/
mv verify_false_positive_fix.py tools/validation/
```

#### 3.5 Test Scripts → tests/manual/

```bash
# Move manual test scripts
mv test_false_positive_fix.py tests/manual/
mv test_homepro_pricing_fix.py tests/manual/
mv test_improved_extraction.py tests/manual/
mv test_integration_demo.py tests/manual/
mv test_phase2_simple.py tests/manual/
mv test_phase3_optimization.py tests/manual/
mv test_phase3_simple.py tests/manual/
```

#### 3.6 Utility Scripts → tools/utilities/

```bash
# Move remaining utility scripts
mv search_specific_product.py tools/utilities/
```

### Phase 4: Consolidate Duplicates

#### 4.1 Archive Old Product Matcher Versions

```bash
# Archive older versions of product matchers
mv src/utils/product_matcher_enhanced.py tools/archive/
mv src/utils/product_matcher_enhanced_v2.py tools/archive/
mv src/utils/product_matcher_improved.py tools/archive/

# Keep these versions:
# - src/utils/product_matcher.py (base)
# - src/utils/product_matcher_advanced.py
# - src/utils/product_matcher_optimized.py
# - src/utils/product_matcher_ultra_strict.py
```

#### 4.2 Archive Old Text Normalizer Versions

```bash
# Archive older versions of text normalizers
mv src/utils/text_normalizer_enhanced.py tools/archive/

# Keep these versions:
# - src/utils/text_normalizer.py (base)
# - src/utils/text_normalizer_advanced.py
```

#### 4.3 Archive Old API Router Versions

```bash
# Archive older/experimental API router versions
mv src/api/routers/price_comparisons_v2_fixed.py tools/archive/
mv src/api/routers/price_comparisons_v2_optimized.py tools/archive/

# Keep these versions:
# - src/api/routers/price_comparisons.py
# - src/api/routers/price_comparisons_v2.py
# - src/api/routers/price_comparisons_v3_enhanced.py
# - src/api/routers/matching.py
# - src/api/routers/matching_advanced.py
```

#### 4.4 Archive Old Service Versions

```bash
# Archive older service versions
mv src/services/price_comparison_enhanced.py tools/archive/

# Keep these versions:
# - src/services/price_comparison_service.py (base)
# - src/services/price_comparison_advanced.py
```

### Phase 5: Update Import Statements

#### 5.1 Create Import Update Script

```python
#!/usr/bin/env python3
"""
Script to update import statements after file reorganization
"""
import os
import re
from pathlib import Path

# Define mappings for moved files
IMPORT_MAPPINGS = {
    # Configuration files
    'from config import': 'from config.app_config import',
    'import config': 'import config.app_config as config',
    'from logging_config import': 'from config.logging_config import',
    'import logging_config': 'import config.logging_config',
    
    # Moved scripts (examples)
    'from analyze_false_match import': 'from tools.data_quality.analyze_false_match import',
    'from debug_homepro_pricing import': 'from tools.debug.debug_homepro_pricing import',
    'from validate_homepro_pricing import': 'from tools.validation.validate_homepro_pricing import',
}

def update_imports_in_file(file_path):
    """Update import statements in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
    
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def find_and_update_python_files(root_dir):
    """Find all Python files and update their imports"""
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['venv', 'node_modules', '.git', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_imports_in_file(file_path)

if __name__ == "__main__":
    project_root = "/Users/chongraktanaka/Documents/Project/ris data scrap"
    find_and_update_python_files(project_root)
    print("Import updates completed!")
```

#### 5.2 Update Common Import Patterns

```bash
# Update imports in src/ directory
find src/ -name "*.py" -exec sed -i '' 's/from config import/from config.app_config import/g' {} \;
find src/ -name "*.py" -exec sed -i '' 's/import config$/import config.app_config as config/g' {} \;
find src/ -name "*.py" -exec sed -i '' 's/from logging_config import/from config.logging_config import/g' {} \;

# Update imports in tests/ directory
find tests/ -name "*.py" -exec sed -i '' 's/from config import/from config.app_config import/g' {} \;

# Update imports in scripts/ directory
find scripts/ -name "*.py" -exec sed -i '' 's/from config import/from config.app_config import/g' {} \;
```

### Phase 6: Create __init__.py Files

```bash
# Add __init__.py files to new directories
touch config/__init__.py
touch tools/__init__.py
touch tools/data_quality/__init__.py
touch tools/fixes/__init__.py
touch tools/validation/__init__.py
touch tools/debug/__init__.py
touch tools/archive/__init__.py
touch tests/manual/__init__.py
```

### Phase 7: Validation and Testing

```bash
# Run tests to ensure everything still works
python -m pytest tests/ -v

# Check for any remaining import errors
python -c "
import sys
sys.path.append('.')
try:
    from src.api.main import app
    print('✓ Main API imports successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
"

# Verify moved files exist and are accessible
python -c "
import os
moved_files = [
    'config/app_config.py',
    'config/logging_config.py',
    'tools/data_quality/analyze_false_match.py',
    'tools/fixes/comprehensive_fix_all.py',
    'tools/debug/debug_homepro_pricing.py',
    'tools/validation/validate_homepro_pricing.py',
]

for file_path in moved_files:
    if os.path.exists(file_path):
        print(f'✓ {file_path}')
    else:
        print(f'✗ Missing: {file_path}')
"
```

## Before and After Comparison

### Before (Root Directory - 50+ files)
```
/
├── analyze_false_match.py
├── analyze_null_skus.py
├── analyze_url_issues.py
├── apply_hp_price_improvements.py
├── audit_false_matches.py
├── automated_twd_category_fix.py
├── check_homepro_categories.py
├── comprehensive_fix_all.py
├── config.py
├── debug_homepro_pricing.py
├── debug_match_schema.py
├── debug_specific_match.py
├── debug_specific_twd_product.py
├── disable_false_positive_match.py
├── final_quality_validation.py
├── fix_specific_products.py
├── fix_twd_category_url_extraction.py
├── fix_twd_category_urls.py
├── fix_twd_url_validation.py
├── focused_batch_fix.py
├── investigate_data_quality.py
├── investigate_twd_category_products.py
├── logging_config.py
├── optimize_import.py
├── quick_quality_check.py
├── remove_false_positive_match.py
├── remove_product_from_match.py
├── rescrap_missing_data.py
├── rescrape_homepro_categories.py
├── run_api.py
├── search_specific_product.py
├── setup.py
├── targeted_fix_remaining.py
├── test_false_positive_fix.py
├── test_homepro_pricing_fix.py
├── test_improved_extraction.py
├── test_integration_demo.py
├── test_phase2_simple.py
├── test_phase3_optimization.py
├── test_phase3_simple.py
├── validate_homepro_pricing.py
├── verify_false_positive_fix.py
└── [more files...]
```

### After (Clean Root Directory - 2 files)
```
/
├── run_api.py                    # Main application entry point
├── setup.py                      # Package configuration
├── config/                       # Project configuration
│   ├── __init__.py
│   ├── app_config.py            # Moved from config.py
│   └── logging_config.py        # Moved from root
├── tools/                        # Development and maintenance tools
│   ├── __init__.py
│   ├── data_quality/            # Data quality scripts (9 files)
│   ├── fixes/                   # One-time fix scripts (15 files)
│   ├── validation/              # Validation scripts (2 files)
│   ├── debug/                   # Debug utilities (12 files)
│   └── archive/                 # Archived old versions (8 files)
├── src/                         # Core application (unchanged structure)
├── tests/                       # All tests including manual tests
│   └── manual/                  # Manual test scripts (7 files)
├── scripts/                     # Operational scripts (unchanged)
└── docs/                        # Documentation
```

## File Count Summary

| Category | Before | After | Change |
|----------|--------|-------|--------|
| Root directory | 50+ files | 2 files | -48 files |
| Well organized | 334 files | 334 files | No change |
| New tools/ directory | 0 files | 46 files | +46 files |
| Archived duplicates | 0 files | 8 files | +8 files |
| **Total** | **384 files** | **384 files** | **Same total, better organized** |

## Benefits Achieved

1. **Clean Root Directory**: Reduced from 50+ files to 2 essential files
2. **Logical Organization**: All files grouped by purpose and function
3. **Easier Navigation**: Clear directory structure following Python best practices
4. **Better Maintainability**: Related files grouped together
5. **Professional Structure**: Industry-standard project organization
6. **Reduced Duplicates**: Old versions archived, clear hierarchy established

## Rollback Plan

If issues arise during migration:

```bash
# Stop migration
echo "Rolling back to backup..."

# Remove new directories
rm -rf config tools tests/manual

# Restore from backup
cp -r "/Users/chongraktanaka/Documents/Project/ris data scrap_backup_[timestamp]"/* "/Users/chongraktanaka/Documents/Project/ris data scrap/"

echo "Rollback completed"
```

## Post-Migration Checklist

- [ ] All tests pass (`pytest tests/`)
- [ ] Main API starts successfully (`python run_api.py`)
- [ ] No import errors in core modules
- [ ] All moved files accessible from new locations
- [ ] Documentation updated with new structure
- [ ] Team notified of new organization
- [ ] Development tools updated with new paths

---

**Execution Time Estimate:** 2-3 hours  
**Risk Level:** Low (with proper backup and testing)  
**Impact:** High (significantly improved project organization)