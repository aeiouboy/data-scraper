#!/usr/bin/env python3
"""Fix import errors in test files."""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Fix patterns
    import_fixes = [
        # Fix Product imports
        (r'from src\.api\.models import (.*?)Product(.*?)(?=\n|$)', 
         lambda m: f"from src.models.product import Product{m.group(1).replace('Product,', '').replace(', Product', '').strip().rstrip(',')}" if m.group(1).strip() or m.group(2).strip() else "from src.models.product import Product"),
        
        # Fix other model imports that remain
        (r'from src\.api\.models import (.*?)(?=\n|$)',
         r'# TODO: Fix import - \g<0>'),
        
        # Fix database imports
        (r'from src\.api\.database import get_db',
         r'# TODO: Update for Supabase - from src.api.database import get_db'),
        
        # Fix scraper_manager import
        (r'from src\.scrapers\.scraper_manager import ScraperManager',
         r'# TODO: Check if exists - from src.scrapers.scraper_manager import ScraperManager'),
    ]
    
    for pattern, replacement in import_fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made.append(f"Fixed: {pattern}")
    
    # Handle multiple imports on same line
    # Fix lines like: from src.api.models import Product, ScrapingJob, ProductMatch
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'from src.api.models import' in line and ',' in line:
            # Extract all imported items
            match = re.match(r'from src\.api\.models import (.+)', line)
            if match:
                imports = [imp.strip() for imp in match.group(1).split(',')]
                new_imports = []
                product_imported = False
                
                for imp in imports:
                    if imp == 'Product':
                        if not product_imported:
                            new_lines.append('from src.models.product import Product')
                            product_imported = True
                    else:
                        new_imports.append(imp)
                
                if new_imports:
                    new_lines.append(f"# TODO: Fix imports - from src.api.models import {', '.join(new_imports)}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, changes_made
    
    return False, []


def check_missing_models():
    """Check what models are being imported that don't exist."""
    test_files = [
        "tests/e2e/test_price_monitoring_workflow.py",
        "tests/e2e/test_scraping_workflow.py",
        "tests/integration/api/test_matching_api.py",
        "tests/integration/api/test_products_api.py",
        "tests/integration/api/test_scraping_api.py",
        "tests/performance/test_scraping_performance.py",
        "tests/test_api_price_comparisons.py",
        "tests/unit/scrapers/test_homepro_scraper.py",
        "tests/unit/scrapers/test_thaiwatsadu_scraper.py",
        "tests/unit/test_scraper.py",
        "tests/unit/utils/test_product_matcher.py",
        "scripts/testing/test_scraper.py"
    ]
    
    missing_imports = set()
    
    for file_path in test_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find all imports from src.api.models
            imports = re.findall(r'from src\.api\.models import (.+)', content)
            for imp_line in imports:
                items = [item.strip() for item in imp_line.split(',')]
                missing_imports.update(items)
    
    return missing_imports


def main():
    """Main function."""
    os.chdir('/Users/chongraktanaka/Documents/Project/ris data scrap')
    
    # First, check what models are being imported
    print("Checking for missing model imports...")
    missing_models = check_missing_models()
    print(f"Models being imported: {missing_models}")
    
    # Fix the test files
    test_files = [
        "tests/e2e/test_price_monitoring_workflow.py",
        "tests/e2e/test_scraping_workflow.py", 
        "tests/integration/api/test_matching_api.py",
        "tests/integration/api/test_products_api.py",
        "tests/integration/api/test_scraping_api.py",
        "tests/performance/test_scraping_performance.py",
        "tests/test_api_price_comparisons.py",
        "tests/unit/scrapers/test_homepro_scraper.py",
        "tests/unit/scrapers/test_thaiwatsadu_scraper.py",
        "tests/unit/test_scraper.py",
        "tests/unit/utils/test_product_matcher.py",
        "tests/fixtures/database.py",
        "tests/fixtures/products.py",
        "tests/factories/product_factory.py",
        "tests/factories/scraping_job_factory.py",
        "tests/factories/match_factory.py",
        "tests/utils.py",
        "scripts/testing/test_scraper.py"
    ]
    
    print("\nFixing imports in test files...")
    for file_path in test_files:
        if os.path.exists(file_path):
            fixed, changes = fix_imports_in_file(file_path)
            if fixed:
                print(f"✓ Fixed {file_path}")
                for change in changes:
                    print(f"  - {change}")
            else:
                print(f"  No changes needed in {file_path}")
        else:
            print(f"✗ File not found: {file_path}")
    
    print("\nDone! Please review the changes and update TODO comments as needed.")


if __name__ == "__main__":
    main()