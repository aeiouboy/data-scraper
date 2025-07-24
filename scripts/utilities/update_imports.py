#!/usr/bin/env python3
"""
Script to update imports from src.* to src.*
"""
import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Update imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if we made changes
        original_content = content
        
        # Update import statements
        # from src.xxx import -> from src.xxx import
        content = re.sub(r'from app\.', 'from src.', content)
        
        # import src.xxx -> import src.xxx
        content = re.sub(r'import app\.', 'import src.', content)
        
        # If content changed, write it back
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def update_all_imports(directory):
    """Update imports in all Python files in directory"""
    updated_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_imports_in_file(file_path):
                    updated_files.append(file_path)
    
    return updated_files

def main():
    """Main function"""
    print("🔄 Updating imports from src.* to src.*")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Directories to update
    directories_to_update = [
        project_root / 'src',
        project_root / 'tests',
        project_root / 'scripts',
        project_root  # Root directory Python files
    ]
    
    all_updated_files = []
    
    for directory in directories_to_update:
        if directory.exists():
            print(f"\n📁 Processing {directory}")
            updated_files = update_all_imports(directory)
            all_updated_files.extend(updated_files)
            print(f"   Updated {len(updated_files)} files")
    
    print(f"\n✅ Total files updated: {len(all_updated_files)}")
    
    if all_updated_files:
        print("\nUpdated files:")
        for file in sorted(all_updated_files):
            print(f"  - {file}")
    
    # Also update specific root files
    root_files_to_check = [
        'run_api.py',
        'scrape.py',
        'scrape_all_categories.py',
        'scrape_multi_retailer.py',
        'run_monitoring_direct.py',
        'improve_matching_algorithm.py'
    ]
    
    print("\n📄 Checking root Python files...")
    for file_name in root_files_to_check:
        file_path = project_root / file_name
        if file_path.exists():
            if update_imports_in_file(file_path):
                print(f"   ✅ Updated {file_name}")

if __name__ == "__main__":
    main()