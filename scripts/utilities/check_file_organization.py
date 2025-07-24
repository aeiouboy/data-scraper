#!/usr/bin/env python3
"""
Check file organization and suggest improvements
"""
from pathlib import Path
import re
from typing import List, Dict, Tuple

def check_root_directory() -> List[Tuple[str, str]]:
    """Check for files that should be moved from root directory"""
    
    suggestions = []
    root = Path('.')
    
    # Patterns for files that should be organized
    patterns = [
        (r'^test_.*\.py$', 'scripts/testing/'),
        (r'^debug_.*\.py$', 'scripts/debug/'),
        (r'^monitor_.*\.py$', 'scripts/monitoring/'),
        (r'^scrape_.*\.py$', 'scripts/scraping/'),
        (r'^analyze_.*\.py$', 'scripts/analysis/'),
        (r'^fix_.*\.py$', 'scripts/utilities/'),
        (r'^validate_.*\.py$', 'scripts/utilities/'),
        (r'^import_.*\.py$', 'scripts/utilities/'),
        (r'.*_report_.*\.json$', 'data/analysis_reports/'),
        (r'.*_results?\.json$', 'data/results/'),
        (r'.*_REPORT\.md$', 'docs/archive/'),
    ]
    
    # Files that are allowed in root
    allowed_root_files = {
        'setup.py', 'config.py', 'run_api.py', 
        'logging_config.py', 'requirements.txt',
        'requirements-test.txt', 'requirements-minimal.txt',
        'pytest.ini', 'Makefile', 'README.md', 
        'CLAUDE.md', '.env', '.env.example',
        'activate.sh', 'run_api_with_logs.sh',
        'run_monitoring.sh', 'complete_organization.sh'
    }
    
    # Check each file in root
    for file_path in root.iterdir():
        if file_path.is_file() and file_path.name not in allowed_root_files:
            # Skip hidden files and special files
            if file_path.name.startswith('.'):
                continue
                
            # Check against patterns
            suggested = False
            for pattern, destination in patterns:
                if re.match(pattern, file_path.name):
                    suggestions.append((file_path.name, destination))
                    suggested = True
                    break
            
            # If no pattern matched, suggest generic location
            if not suggested:
                if file_path.suffix == '.py':
                    suggestions.append((file_path.name, 'scripts/utilities/'))
                elif file_path.suffix == '.json':
                    suggestions.append((file_path.name, 'data/'))
                elif file_path.suffix == '.md':
                    suggestions.append((file_path.name, 'docs/'))
    
    return suggestions

def check_script_organization() -> Dict[str, List[str]]:
    """Check scripts directory for misplaced files"""
    
    issues = {}
    scripts_dir = Path('scripts')
    
    if not scripts_dir.exists():
        return issues
    
    # Expected subdirectories and their file patterns
    expected_patterns = {
        'testing': r'^test_.*\.py$',
        'debug': r'^debug_.*\.py$',
        'monitoring': r'^monitor_.*\.py$',
        'scraping': r'^scrape_.*\.py$',
        'analysis': r'^analyze_.*\.py$',
    }
    
    # Check each subdirectory
    for subdir, pattern in expected_patterns.items():
        subdir_path = scripts_dir / subdir
        if subdir_path.exists():
            for file_path in subdir_path.glob('*.py'):
                if not re.match(pattern, file_path.name):
                    if subdir not in issues:
                        issues[subdir] = []
                    issues[subdir].append(file_path.name)
    
    return issues

def check_data_freshness() -> List[Tuple[str, int]]:
    """Check for old data files that might need archiving"""
    
    import time
    old_files = []
    data_dir = Path('data')
    
    if not data_dir.exists():
        return old_files
    
    # Check files older than 30 days
    thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
    
    for file_path in data_dir.rglob('*'):
        if file_path.is_file():
            if file_path.stat().st_mtime < thirty_days_ago:
                age_days = int((time.time() - file_path.stat().st_mtime) / (24 * 60 * 60))
                old_files.append((str(file_path.relative_to(data_dir)), age_days))
    
    return sorted(old_files, key=lambda x: x[1], reverse=True)

def main():
    """Run file organization check"""
    
    print("🔍 File Organization Check")
    print("=" * 50)
    
    # Check root directory
    print("\n📁 Checking root directory...")
    suggestions = check_root_directory()
    
    if suggestions:
        print(f"\n⚠️  Found {len(suggestions)} files that could be better organized:")
        for filename, destination in suggestions:
            print(f"  • {filename} → {destination}")
    else:
        print("  ✅ Root directory is well organized!")
    
    # Check scripts organization
    print("\n📁 Checking scripts directory...")
    issues = check_script_organization()
    
    if issues:
        print("\n⚠️  Found misplaced files in scripts:")
        for subdir, files in issues.items():
            print(f"  In scripts/{subdir}/:")
            for filename in files:
                print(f"    • {filename} (doesn't match expected pattern)")
    else:
        print("  ✅ Scripts directory is well organized!")
    
    # Check for old data files
    print("\n📁 Checking for old data files...")
    old_files = check_data_freshness()
    
    if old_files:
        print(f"\n⚠️  Found {len(old_files)} files older than 30 days:")
        for filepath, age_days in old_files[:10]:  # Show only top 10
            print(f"  • data/{filepath} ({age_days} days old)")
        if len(old_files) > 10:
            print(f"  ... and {len(old_files) - 10} more")
    else:
        print("  ✅ No old data files found!")
    
    # Summary
    total_issues = len(suggestions) + sum(len(files) for files in issues.values()) + len(old_files)
    
    print("\n" + "=" * 50)
    print(f"📊 Summary: {total_issues} potential improvements found")
    
    if total_issues > 0:
        print("\n💡 Suggestions:")
        print("1. Move misplaced files to their correct directories")
        print("2. Archive or delete old data files")
        print("3. Follow naming conventions for new files")
        print("4. Run this check weekly to maintain organization")
        
        print("\n🤖 To auto-organize files, run:")
        print("   python scripts/utilities/auto_organize_files.py")
    else:
        print("\n🎉 Great job! The codebase is well organized!")

if __name__ == "__main__":
    main()