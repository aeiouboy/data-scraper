#!/usr/bin/env python3
"""
Safely organize codebase files, skipping files that are currently in use
"""
import shutil
from pathlib import Path
import psutil
import os

def get_running_python_files():
    """Get list of Python files currently being executed"""
    running_files = set()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    for arg in cmdline:
                        if arg.endswith('.py'):
                            running_files.add(Path(arg).name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return running_files

def safe_organize():
    """Organize files safely, avoiding files in use"""
    
    # Get files currently being executed
    running_files = get_running_python_files()
    print(f"🔍 Found {len(running_files)} Python files currently running:")
    for f in running_files:
        print(f"  • {f}")
    
    # Files to skip (currently running or critical)
    skip_files = running_files | {
        'import_manual_data.py',  # Currently importing data
        'monitor_import.py',      # Monitoring tool
        'organize_codebase.py',   # This script
        'safe_organize.py'        # This script
    }
    
    print(f"\n⚠️  Will skip {len(skip_files)} files that are in use")
    
    # Define safe movements (excluding running files)
    movements = {
        # Test scripts to scripts/testing/
        'test_scripts': {
            'destination': 'scripts/testing',
            'files': [
                f for f in [
                    'test_db_save.py',
                    'test_elt0201_category.py',
                    'test_homepro_pagination.py',
                    'test_hybrid_integration.py',
                    'test_improved_matching.py',
                    'test_native_scraping.py',
                    'test_native_simple.py',
                    'test_price_fix.py',
                    'test_product_matching.py',
                    'test_specific_url.py',
                    'test_strict_model_matching.py'
                ] if f not in skip_files
            ]
        },
        
        # Debug scripts to scripts/debug/
        'debug_scripts': {
            'destination': 'scripts/debug',
            'files': [
                f for f in [
                    'debug_category_extraction.py',
                    'debug_matcher.py',
                    'debug_price_extraction.py',
                    'debug_specs.py',
                    'debug_url_discovery.py'
                ] if f not in skip_files
            ]
        },
        
        # Archive old reports to docs/archive/
        'archive_reports': {
            'destination': 'docs/archive',
            'files': [
                'FRONTEND_BACKEND_INTEGRATION_REPORT.md',
                'FRONTEND_PERFORMANCE_FIXES.md',
                'MATCHING_IMPROVEMENT_REPORT.md',
                'NATIVE_SCRAPING_IMPLEMENTATION_SUMMARY.md',
                'PAGINATION_IMPROVEMENT_REPORT.md',
                'PRICE_EXTRACTION_FIX_SUMMARY.md',
                'PRODUCTION_NATIVE_SCRAPING_SUCCESS.md',
                'TESTING_VALIDATION_REPORT.md'
            ]
        },
        
        # JSON result files to data/results/
        'result_files': {
            'destination': 'data/results',
            'files': [
                'elt0201_validation_results.json',
                'enhanced_report_HP_20250712_110607.json',
                'enhanced_report_HP_20250712_110637.json',
                'enhanced_report_HP_20250712_111411.json',
                'native_scraping_demo_20250711_225322.json'
            ]
        }
    }
    
    # Create directories if they don't exist
    for category_data in movements.values():
        dest_dir = Path(category_data['destination'])
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Move files
    moved_count = 0
    skipped_count = 0
    
    for category, data in movements.items():
        if not data['files']:  # Skip if no files to move
            continue
            
        print(f"\n📂 Processing {category}...")
        dest_dir = Path(data['destination'])
        
        for filename in data['files']:
            src_file = Path(filename)
            dest_file = dest_dir / filename
            
            if src_file.exists():
                try:
                    shutil.move(str(src_file), str(dest_file))
                    print(f"  ✓ Moved: {filename} → {dest_dir}/")
                    moved_count += 1
                except Exception as e:
                    print(f"  ✗ Error moving {filename}: {e}")
            else:
                print(f"  ⚠️  Skipped: {filename} (not found)")
                skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  • Files moved: {moved_count}")
    print(f"  • Files skipped: {skipped_count}")
    print(f"  • Files in use (not moved): {len(skip_files)}")
    
    # Create a follow-up script for remaining files
    remaining_files = []
    for category_data in movements.values():
        for f in category_data['files']:
            if f in skip_files and Path(f).exists():
                remaining_files.append(f)
    
    if remaining_files:
        print(f"\n📝 Creating script to move {len(remaining_files)} remaining files after import completes...")
        
        with open('organize_remaining.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Run this after import_manual_data.py completes\n\n")
            f.write("echo '🔄 Moving remaining files...'\n\n")
            
            # Add move commands for remaining files
            f.write("# Move monitoring scripts\n")
            f.write("mv monitor_import.py scripts/monitoring/ 2>/dev/null\n")
            f.write("mv import_manual_data.py scripts/utilities/ 2>/dev/null\n")
            f.write("\necho '✅ Done!'\n")
        
        os.chmod('organize_remaining.sh', 0o755)
        print("  ✓ Created organize_remaining.sh - run this after import completes")
    
    print("\n✅ Safe organization complete!")

if __name__ == "__main__":
    safe_organize()