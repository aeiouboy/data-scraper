#!/usr/bin/env python3
"""
Script to reorganize documentation files into a proper structure
"""
import os
import shutil
from pathlib import Path
import re

# Documentation categories mapping
DOC_CATEGORIES = {
    'api': [
        'API_*.md',
        'PRICE_COMPARISON*.md',
        'MATCHING*.md'
    ],
    'architecture': [
        'ARCHITECTURE.md',
        'PROJECT_STRUCTURE.md',
        'MIGRATION*.md'
    ],
    'development': [
        'SETUP.md',
        'TROUBLESHOOTING.md',
        'CLAUDE.md',
        'CODEBASE_CLEANUP*.md',
        'BUILD*.md'
    ],
    'features': [
        'ADAPTIVE*.md',
        'CATEGORY*.md',
        'SCRAPER*.md',
        'SCRAPING*.md',
        'SCHEDULED*.md',
        'PRICE_TRACKING*.md'
    ],
    'deployment': [
        'IMPLEMENTATION*.md',
        'UI_*.md'
    ],
    'analysis': [
        'ANALYSIS.md',
        'Comparison.md',
        '*_REPORT.md',
        '*_RESULTS.md'
    ]
}

def create_docs_structure():
    """Create the new documentation structure"""
    docs_dir = Path('docs')
    
    # Create main docs directory
    docs_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    for category in DOC_CATEGORIES.keys():
        (docs_dir / category).mkdir(exist_ok=True)
    
    # Create index files
    create_index_files(docs_dir)
    
    return docs_dir

def create_index_files(docs_dir):
    """Create index.md files for each category"""
    
    # Main index
    main_index = """# RIS Data Scrap Documentation

Welcome to the RIS Data Scrap project documentation.

## Documentation Categories

### [API Documentation](./api/index.md)
API endpoints, schemas, and integration guides.

### [Architecture](./architecture/index.md)
System design, project structure, and technical decisions.

### [Development](./development/index.md)
Setup guides, development workflows, and troubleshooting.

### [Features](./features/index.md)
Feature documentation for scraping, matching, and monitoring.

### [Deployment](./deployment/index.md)
Deployment guides and production configurations.

### [Analysis](./analysis/index.md)
Reports, analysis results, and performance metrics.

## Quick Links

- [Getting Started](./development/SETUP.md)
- [API Reference](./api/index.md)
- [Troubleshooting](./development/TROUBLESHOOTING.md)
"""
    
    (docs_dir / 'index.md').write_text(main_index)
    
    # Category indices
    category_indices = {
        'api': """# API Documentation

## Overview
Documentation for all API endpoints and integrations.

## Contents
- [Price Comparison API](./PRICE_COMPARISON_OPTIMIZATION.md)
- [Matching API](./MATCHING_IMPROVEMENTS.md)
- [API Models](./API_MODELS.md)
""",
        'architecture': """# Architecture Documentation

## Overview
System architecture, design decisions, and project structure.

## Contents
- [System Architecture](./ARCHITECTURE.md)
- [Project Structure](./PROJECT_STRUCTURE.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
""",
        'development': """# Development Documentation

## Overview
Development setup, workflows, and guidelines.

## Contents
- [Setup Guide](./SETUP.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Code Standards](./CODEBASE_CLEANUP_SUMMARY.md)
""",
        'features': """# Feature Documentation

## Overview
Documentation for all major features.

## Contents
- [Adaptive Scraping](./ADAPTIVE_SCRAPING.md)
- [Category Monitoring](./CATEGORY_MONITORING.md)
- [Price Tracking](./PRICE_TRACKING_DASHBOARD.md)
""",
        'deployment': """# Deployment Documentation

## Overview
Deployment guides and production configurations.

## Contents
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [UI Quickstart](./UI_QUICKSTART.md)
""",
        'analysis': """# Analysis & Reports

## Overview
Analysis results, reports, and performance metrics.

## Contents
- [System Analysis](./ANALYSIS.md)
- [Test Results](./PRICE_MATCHING_TEST_RESULTS.md)
"""
    }
    
    for category, content in category_indices.items():
        (docs_dir / category / 'index.md').write_text(content)

def get_matching_files(pattern):
    """Get all files matching a pattern"""
    if '*' in pattern:
        return list(Path('.').glob(pattern))
    else:
        path = Path(pattern)
        return [path] if path.exists() else []

def reorganize_docs():
    """Main function to reorganize documentation"""
    print("🚀 Starting documentation reorganization...")
    
    # Create new structure
    docs_dir = create_docs_structure()
    print(f"✅ Created documentation structure in {docs_dir}")
    
    # Move files
    moved_files = []
    for category, patterns in DOC_CATEGORIES.items():
        category_dir = docs_dir / category
        
        for pattern in patterns:
            files = get_matching_files(pattern)
            
            for file in files:
                if file.is_file() and file.suffix == '.md':
                    dest = category_dir / file.name
                    
                    # Check if file already exists in destination
                    if dest.exists():
                        print(f"⚠️  {file} already exists in {category_dir}, skipping")
                        continue
                    
                    # Copy file (use copy instead of move for safety)
                    shutil.copy2(file, dest)
                    moved_files.append((file, dest))
                    print(f"📄 Moved {file} → {dest}")
    
    print(f"\n✅ Reorganized {len(moved_files)} documentation files")
    
    # Create a summary report
    report = "# Documentation Reorganization Report\n\n"
    report += f"Moved {len(moved_files)} files:\n\n"
    
    for src, dest in moved_files:
        report += f"- `{src}` → `{dest}`\n"
    
    report_path = docs_dir / 'REORGANIZATION_REPORT.md'
    report_path.write_text(report)
    print(f"\n📝 Created report at {report_path}")
    
    # Update README
    update_readme_links()
    
    print("\n✅ Documentation reorganization complete!")
    print("\n⚠️  Note: Original files were copied, not moved. Review and delete originals manually.")

def update_readme_links():
    """Update links in README.md to point to new documentation structure"""
    readme_path = Path('README.md')
    if not readme_path.exists():
        return
    
    content = readme_path.read_text()
    
    # Update documentation links
    replacements = [
        (r'\./SETUP\.md', './docs/development/SETUP.md'),
        (r'\./ARCHITECTURE\.md', './docs/architecture/ARCHITECTURE.md'),
        (r'\./TROUBLESHOOTING\.md', './docs/development/TROUBLESHOOTING.md'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    readme_path.write_text(content)
    print("✅ Updated README.md links")

if __name__ == "__main__":
    reorganize_docs()