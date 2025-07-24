# Remaining File Organization Tasks

## After import_manual_data.py completes:
1. Move import_manual_data.py to scripts/utilities/
2. Move monitor_import.py to scripts/monitoring/
3. Move import_excel_data.py to scripts/utilities/

## Duplicate File Consolidation:
### Product Matchers (choose best version):
- src/utils/product_matcher.py (base)
- src/utils/product_matcher_advanced.py
- src/utils/product_matcher_enhanced.py
- src/utils/product_matcher_improved.py
- src/utils/product_matcher_optimized.py
- src/utils/product_matcher_ultra_strict.py

### Text Normalizers:
- src/utils/text_normalizer.py (base)
- src/utils/text_normalizer_advanced.py
- src/utils/text_normalizer_enhanced.py

### Services Consolidation:
- src/services/product_matcher.py
- src/services/advanced_product_matcher.py
- src/services/product_matcher_service_optimized.py

## Test File Review:
Check if files in scripts/testing/ should move to tests/:
- Are they pytest test files? → Move to tests/
- Are they operational test scripts? → Keep in scripts/testing/

## Commands to run:
```bash
# After import completes
./complete_organization.sh

# Check organization
python scripts/utilities/check_file_organization.py

# Review duplicates
find src/ -name '*matcher*' -o -name '*normalizer*' | sort
```