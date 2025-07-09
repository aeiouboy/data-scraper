#!/usr/bin/env python3
"""
Organize JSON data files into appropriate directories
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# JSON file categories based on their purpose
JSON_CATEGORIES = {
    'scraping_results': [
        '*_firecrawl.json',
        '*_discovered.json',
        '*_categories.json',
        '*_products_*.json',
        '*_pages_*.json',
        '*_category_*.json',
        'boonthavorn_*.json',
        'twd_*.json',
        'other_retailers_*.json',
    ],
    'analysis_reports': [
        '*_analysis_*.json',
        '*_report_*.json',
        '*_test_report.json',
        'database_status_report_*.json',
    ],
    'test_data': [
        '*_response.json',
        '*_tiles_page.json',
    ],
    'progress': [
        'scraping_progress.json',
    ],
}

# Files to keep in root (none for JSON files)
KEEP_IN_ROOT = []

def categorize_json_files():
    """Categorize all JSON files in root directory"""
    root_path = Path(__file__).parent.parent
    categorized = {cat: [] for cat in JSON_CATEGORIES}
    uncategorized = []
    
    # Get all JSON files in root
    for file in root_path.glob('*.json'):
        if file.name == 'package-lock.json':
            # Skip npm package lock file
            continue
            
        matched = False
        for category, patterns in JSON_CATEGORIES.items():
            for pattern in patterns:
                if file.match(pattern):
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
    categorized, uncategorized = categorize_json_files()
    
    print("📋 JSON File Organization Plan\n")
    print("=" * 60)
    
    for category, files in categorized.items():
        if files:
            print(f"\n📁 data/{category}/")
            for file in sorted(files):
                # Get file size
                file_path = Path(__file__).parent.parent / file
                if file_path.exists():
                    size = file_path.stat().st_size
                    size_str = format_file_size(size)
                    print(f"   {file} ({size_str})")
                else:
                    print(f"   {file}")
    
    if uncategorized:
        print(f"\n❓ Uncategorized (review manually):")
        for file in sorted(uncategorized):
            print(f"   {file}")
    
    print("\n" + "=" * 60)
    print(f"\n📊 Summary:")
    total = sum(len(files) for files in categorized.values()) + len(uncategorized)
    print(f"   Total JSON files: {total}")
    print(f"   Categorized: {sum(len(files) for files in categorized.values())}")
    print(f"   Uncategorized: {len(uncategorized)}")

def format_file_size(size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def move_json_files(dry_run=True):
    """Move JSON files to their categories"""
    categorized, uncategorized = categorize_json_files()
    root_path = Path(__file__).parent.parent
    data_path = root_path / 'data'
    
    moved_count = 0
    total_size = 0
    
    for category, files in categorized.items():
        if not files:
            continue
            
        category_path = data_path / category
        category_path.mkdir(exist_ok=True, parents=True)
        
        for file in files:
            source = root_path / file
            if not source.exists():
                continue
                
            dest = category_path / file
            file_size = source.stat().st_size
            
            if file in KEEP_IN_ROOT:
                # Copy instead of move
                if dry_run:
                    print(f"Would copy: {file} → data/{category}/{file}")
                else:
                    shutil.copy2(source, dest)
                    print(f"Copied: {file} → data/{category}/{file}")
            else:
                # Move the file
                if dry_run:
                    print(f"Would move: {file} → data/{category}/{file}")
                else:
                    shutil.move(str(source), str(dest))
                    print(f"Moved: {file} → data/{category}/{file}")
                    moved_count += 1
                    total_size += file_size
    
    if uncategorized:
        print(f"\n⚠️  {len(uncategorized)} uncategorized files remain in root")
        for file in uncategorized:
            print(f"   - {file}")
    
    if not dry_run:
        print(f"\n✅ Moved {moved_count} files ({format_file_size(total_size)})")
    
    return moved_count

def create_data_readme():
    """Create README for data directory"""
    readme_content = """# Data Directory

This directory contains JSON data files from scraping and analysis operations.

## Directory Structure

```
data/
├── scraping_results/   # Raw scraping output from retailers
├── analysis_reports/   # Analysis and report JSON files
├── test_data/         # Test data and sample responses
└── progress/          # Progress tracking files
```

## Categories

### 📊 scraping_results/
Raw data from web scraping operations:
- Retailer category discoveries
- Product listings
- Firecrawl API responses

### 📈 analysis_reports/
Analysis outputs and reports:
- Database status reports
- Product analysis results
- Test reports

### 🧪 test_data/
Test data and sample responses:
- API response samples
- Test fixtures

### 📝 progress/
Progress tracking files:
- Scraping progress logs
- Job status tracking

## Important Notes

- These files are generated by scraping and analysis scripts
- Most files are git-ignored to avoid committing large data files
- Files are timestamped when relevant
- Old files can be safely deleted if no longer needed

## File Naming Convention

- `{retailer}_{category}_{type}.json` - Scraping results
- `{analysis}_report_{timestamp}.json` - Analysis reports
- `{test}_{data}.json` - Test data

---

*Generated on: {date}*
""".format(date=datetime.now().strftime('%Y-%m-%d'))
    
    readme_path = Path(__file__).parent.parent / 'data' / 'README.md'
    readme_path.write_text(readme_content)
    print(f"\n📝 Created {readme_path}")

def update_gitignore():
    """Update .gitignore to include data directory"""
    gitignore_path = Path(__file__).parent.parent / '.gitignore'
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if 'data/' not in content:
            print("\n⚠️  Remember to ensure 'data/' is in .gitignore")
    
def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize JSON data files')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually move files (default is dry run)')
    args = parser.parse_args()
    
    print("🔧 JSON File Organization Tool\n")
    
    if args.execute:
        print("🚀 EXECUTING JSON file organization...\n")
        moved = move_json_files(dry_run=False)
        create_data_readme()
        update_gitignore()
        print(f"\n✅ Organization complete!")
    else:
        print("🔍 DRY RUN - Showing what would be done:\n")
        print_organization_plan()
        print("\n" + "-" * 60)
        move_json_files(dry_run=True)
        print("\n💡 To execute: python scripts/organize_json_files.py --execute")

if __name__ == "__main__":
    main()