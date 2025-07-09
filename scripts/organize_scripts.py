#!/usr/bin/env python3
"""
Organize root Python scripts into categorized directories
"""
import os
import shutil
from pathlib import Path

# Script categories based on their purpose
SCRIPT_CATEGORIES = {
    'setup': [
        'setup.py',
        'activate.sh',  # Not Python but related to setup
    ],
    'testing': [
        'test_*.py',
        'pytest.ini',  # Not Python but test config
    ],
    'scraping': [
        'scrape.py',
        'scrape_*.py',
        'batch_scrape.py',
        'discover_*.py',
        'extract_*.py',
        'verify_*.py',
        'get_verified_*.py',
        'import_*.py',
    ],
    'analysis': [
        'analyze_*.py',
        'check_*.py',
        'inspect_*.py',
        'debug_*.py',
    ],
    'matching': [
        'create_*_matches.py',
        'fix_*_matches.py',
        'improve_matching_*.py',
        'run_*_matching.py',
        'create_aircon_matches.py',
        'create_category_matches_simple.py',
        'create_more_category_matches.py',
        'create_more_product_matches.py',
        'create_real_matches.py',
        'create_sample_matches.py',
        'create_simple_matches.py',
        'fix_refrigerator_matches.py',
        'run_advanced_matching.py',
    ],
    'monitoring': [
        'monitor_*.py',
        'quick_monitor.py',
        'run_monitoring*.py',
    ],
    'migration': [
        'migrate_*.py',
        'fix_categories.py',
        'execute_*_migration.py',
        'execute_brand_aliases_migration.py',
    ],
    'maintenance': [
        'run_api*.py',
        'run_celery*.py',
        'quality_checker.py',
        'config.py',
        'logging_config.py',
    ],
}

# Scripts to keep in root (essential entry points)
KEEP_IN_ROOT = [
    'run_api.py',
    'setup.py',
    'config.py',
    'logging_config.py',
]

def categorize_scripts():
    """Categorize all Python scripts in root directory"""
    root_path = Path(__file__).parent.parent
    categorized = {cat: [] for cat in SCRIPT_CATEGORIES}
    uncategorized = []
    
    # Get all Python files in root
    for file in root_path.glob('*.py'):
        if file.name == 'organize_scripts.py':
            continue
            
        matched = False
        for category, patterns in SCRIPT_CATEGORIES.items():
            for pattern in patterns:
                if pattern.endswith('*.py'):
                    prefix = pattern[:-4]
                    if file.name.startswith(prefix):
                        categorized[category].append(file.name)
                        matched = True
                        break
                elif file.name == pattern:
                    categorized[category].append(file.name)
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            uncategorized.append(file.name)
    
    return categorized, uncategorized

def print_organization_plan():
    """Print the organization plan"""
    categorized, uncategorized = categorize_scripts()
    
    print("📋 Script Organization Plan\n")
    print("=" * 60)
    
    for category, scripts in categorized.items():
        if scripts:
            print(f"\n📁 scripts/{category}/")
            for script in sorted(scripts):
                if script in KEEP_IN_ROOT:
                    print(f"   {script} (keep copy in root)")
                else:
                    print(f"   {script}")
    
    if uncategorized:
        print(f"\n❓ Uncategorized (review manually):")
        for script in sorted(uncategorized):
            print(f"   {script}")
    
    print("\n" + "=" * 60)
    print(f"\n📊 Summary:")
    total = sum(len(scripts) for scripts in categorized.values()) + len(uncategorized)
    print(f"   Total Python files: {total}")
    print(f"   Categorized: {sum(len(scripts) for scripts in categorized.values())}")
    print(f"   Uncategorized: {len(uncategorized)}")
    print(f"   Keep in root: {len(KEEP_IN_ROOT)}")

def move_scripts(dry_run=True):
    """Move scripts to their categories"""
    categorized, uncategorized = categorize_scripts()
    root_path = Path(__file__).parent.parent
    scripts_path = root_path / 'scripts'
    
    moved_count = 0
    
    for category, scripts in categorized.items():
        if not scripts:
            continue
            
        category_path = scripts_path / category
        category_path.mkdir(exist_ok=True)
        
        for script in scripts:
            source = root_path / script
            if not source.exists():
                continue
                
            dest = category_path / script
            
            if script in KEEP_IN_ROOT:
                # Copy instead of move
                if dry_run:
                    print(f"Would copy: {script} → scripts/{category}/{script}")
                else:
                    shutil.copy2(source, dest)
                    print(f"Copied: {script} → scripts/{category}/{script}")
            else:
                # Move the file
                if dry_run:
                    print(f"Would move: {script} → scripts/{category}/{script}")
                else:
                    shutil.move(str(source), str(dest))
                    print(f"Moved: {script} → scripts/{category}/{script}")
                    moved_count += 1
    
    if uncategorized:
        print(f"\n⚠️  {len(uncategorized)} uncategorized files remain in root")
    
    return moved_count

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize Python scripts')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually move files (default is dry run)')
    args = parser.parse_args()
    
    print("🔧 Python Script Organization Tool\n")
    
    if args.execute:
        print("🚀 EXECUTING script organization...\n")
        moved = move_scripts(dry_run=False)
        print(f"\n✅ Moved {moved} scripts to organized directories")
        print(f"📌 Essential scripts kept in root: {', '.join(KEEP_IN_ROOT)}")
    else:
        print("🔍 DRY RUN - Showing what would be done:\n")
        print_organization_plan()
        print("\n" + "-" * 60)
        move_scripts(dry_run=True)
        print("\n💡 To execute: python scripts/organize_scripts.py --execute")

if __name__ == "__main__":
    main()