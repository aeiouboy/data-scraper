#!/usr/bin/env python3
"""
Data Lifecycle Manager for JSON Data Organization
Handles retention policies, archiving, and cleanup
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple

class DataLifecycleManager:
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.setup_logging()
        
        # Retention policies (in days)
        self.retention_policies = {
            'config': -1,  # Permanent
            'analysis_dataquality': 90,  # 3 months
            'analysis_performance': 90,  # 3 months  
            'analysis_debugging': 90,  # 3 months
            'scraping_results': 180,  # 6 months
            'scraping_progress': 30,  # 1 month
            'scraping_validation': 60,  # 2 months
            'test_unit': 30,  # 1 month
            'test_integration': 30,  # 1 month
            'test_e2e': 30,  # 1 month
            'backup_daily': 30,  # 1 month
            'backup_weekly': 90,  # 3 months
            'backup_manual': 365,  # 1 year
            'temp_processing': 7,  # 1 week
            'temp_debug': 14,  # 2 weeks
            'temp_cache': 3,  # 3 days
            'export_csv': 90,  # 3 months
            'export_reports': 180,  # 6 months
            'export_api': 30,  # 1 month
        }
    
    def setup_logging(self):
        """Setup logging for lifecycle management"""
        log_dir = self.base_path / 'data' / 'config' / 'system'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'data_lifecycle.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_file_age_days(self, file_path: Path) -> int:
        """Get file age in days"""
        try:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return (datetime.now() - file_time).days
        except:
            return 0
    
    def get_file_category(self, file_path: Path) -> str:
        """Determine file category from path and name"""
        
        # Get relative path parts
        parts = file_path.relative_to(self.base_path).parts
        
        if 'config' in parts:
            return 'config'
        elif 'temp' in parts:
            if 'processing' in parts:
                return 'temp_processing'
            elif 'debug' in parts:
                return 'temp_debug'
            elif 'cache' in parts:
                return 'temp_cache'
            else:
                return 'temp_processing'
        elif 'backups' in parts:
            if 'daily' in parts:
                return 'backup_daily'
            elif 'weekly' in parts:
                return 'backup_weekly'
            else:
                return 'backup_manual'
        elif 'testing' in parts:
            if 'unit' in parts:
                return 'test_unit'
            elif 'integration' in parts:
                return 'test_integration'
            elif 'e2e' in parts:
                return 'test_e2e'
            else:
                return 'test_integration'
        elif 'analysis' in parts:
            if 'data-quality' in parts:
                return 'analysis_dataquality'
            elif 'performance' in parts:
                return 'analysis_performance'
            elif 'debugging' in parts:
                return 'analysis_debugging'
            else:
                return 'analysis_dataquality'
        elif 'scraping' in parts:
            if 'results' in parts:
                return 'scraping_results'
            elif 'progress' in parts:
                return 'scraping_progress'
            elif 'validation' in parts:
                return 'scraping_validation'
            else:
                return 'scraping_results'
        elif 'exports' in parts:
            if 'csv' in parts:
                return 'export_csv'
            elif 'reports' in parts:
                return 'export_reports'
            elif 'api' in parts:
                return 'export_api'
            else:
                return 'export_reports'
        
        return 'temp_processing'  # Default
    
    def should_archive(self, file_path: Path) -> bool:
        """Check if file should be archived"""
        category = self.get_file_category(file_path)
        retention_days = self.retention_policies.get(category, 30)
        
        # Permanent files never archive
        if retention_days == -1:
            return False
        
        file_age = self.get_file_age_days(file_path)
        return file_age > retention_days
    
    def should_delete(self, file_path: Path) -> bool:
        """Check if file should be deleted (temp files only)"""
        category = self.get_file_category(file_path)
        
        # Only delete temp files
        if not category.startswith('temp_'):
            return False
        
        retention_days = self.retention_policies.get(category, 7)
        file_age = self.get_file_age_days(file_path)
        
        return file_age > retention_days
    
    def archive_file(self, file_path: Path) -> bool:
        """Archive a file to archive directory"""
        try:
            # Create archive path maintaining structure
            relative_path = file_path.relative_to(self.base_path / 'data' / 'active')
            archive_path = self.base_path / 'data' / 'archive' / relative_path
            
            # Create archive directory
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file to archive
            shutil.move(str(file_path), str(archive_path))
            
            self.logger.info(f"Archived: {file_path} -> {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to archive {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: Path) -> bool:
        """Delete a file"""
        try:
            file_path.unlink()
            self.logger.info(f"Deleted: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            return False
    
    def cleanup_empty_directories(self, directory: Path):
        """Remove empty directories"""
        try:
            for dirpath in directory.rglob('*'):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    self.logger.info(f"Removed empty directory: {dirpath}")
        except Exception as e:
            self.logger.error(f"Error cleaning empty directories: {e}")
    
    def run_lifecycle_management(self, dry_run: bool = True) -> Dict:
        """Run data lifecycle management"""
        
        results = {
            'archived': [],
            'deleted': [],
            'errors': [],
            'total_processed': 0,
            'space_freed_mb': 0
        }
        
        self.logger.info(f"Starting data lifecycle management (dry_run={dry_run})")
        
        # Process all JSON files in data directory
        data_dir = self.base_path / 'data'
        
        for json_file in data_dir.rglob('*.json'):
            results['total_processed'] += 1
            
            try:
                # Get file size for space calculation
                file_size = json_file.stat().st_size / (1024 * 1024)  # MB
                
                # Check if should delete (temp files)
                if self.should_delete(json_file):
                    if not dry_run:
                        if self.delete_file(json_file):
                            results['deleted'].append(str(json_file))
                            results['space_freed_mb'] += file_size
                    else:
                        results['deleted'].append(f"[DRY RUN] {json_file}")
                        results['space_freed_mb'] += file_size
                
                # Check if should archive
                elif self.should_archive(json_file):
                    if not dry_run:
                        if self.archive_file(json_file):
                            results['archived'].append(str(json_file))
                    else:
                        results['archived'].append(f"[DRY RUN] {json_file}")
                
            except Exception as e:
                error_msg = f"Error processing {json_file}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        # Clean up empty directories
        if not dry_run:
            self.cleanup_empty_directories(data_dir / 'active')
            self.cleanup_empty_directories(data_dir / 'temp')
        
        # Log summary
        self.logger.info(f"Lifecycle management complete:")
        self.logger.info(f"  Total processed: {results['total_processed']}")
        self.logger.info(f"  Archived: {len(results['archived'])}")
        self.logger.info(f"  Deleted: {len(results['deleted'])}")
        self.logger.info(f"  Errors: {len(results['errors'])}")
        self.logger.info(f"  Space freed: {results['space_freed_mb']:.2f} MB")
        
        return results
    
    def generate_retention_report(self) -> Dict:
        """Generate report on file retention status"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'categories': {},
            'total_files': 0,
            'total_size_mb': 0,
            'files_near_expiry': []  # Files expiring within 7 days
        }
        
        data_dir = self.base_path / 'data'
        
        for json_file in data_dir.rglob('*.json'):
            try:
                category = self.get_file_category(json_file)
                file_age = self.get_file_age_days(json_file)
                file_size = json_file.stat().st_size / (1024 * 1024)  # MB
                retention_days = self.retention_policies.get(category, 30)
                
                # Initialize category if not exists
                if category not in report['categories']:
                    report['categories'][category] = {
                        'count': 0,
                        'total_size_mb': 0,
                        'retention_days': retention_days,
                        'oldest_file_days': 0,
                        'newest_file_days': float('inf')
                    }
                
                # Update category stats
                cat_stats = report['categories'][category]
                cat_stats['count'] += 1
                cat_stats['total_size_mb'] += file_size
                cat_stats['oldest_file_days'] = max(cat_stats['oldest_file_days'], file_age)
                cat_stats['newest_file_days'] = min(cat_stats['newest_file_days'], file_age)
                
                # Update totals
                report['total_files'] += 1
                report['total_size_mb'] += file_size
                
                # Check if near expiry (within 7 days)
                if retention_days > 0:  # Not permanent
                    days_until_expiry = retention_days - file_age
                    if 0 <= days_until_expiry <= 7:
                        report['files_near_expiry'].append({
                            'file': str(json_file),
                            'category': category,
                            'age_days': file_age,
                            'days_until_expiry': days_until_expiry
                        })
                
            except Exception as e:
                self.logger.error(f"Error processing {json_file} for report: {e}")
        
        return report
    
    def save_retention_report(self) -> str:
        """Save retention report to file"""
        
        report = self.generate_retention_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.base_path / 'data' / 'config' / 'system' / f'retention_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Retention report saved to: {report_file}")
        return str(report_file)

def main():
    base_path = "/Users/chongraktanaka/Documents/Project/ris data scrap"
    manager = DataLifecycleManager(base_path)
    
    print("Data Lifecycle Management")
    print("=" * 40)
    
    # Generate retention report
    print("\\nGenerating retention report...")
    report_file = manager.save_retention_report()
    
    # Run dry run first
    print("\\nRunning lifecycle management (dry run)...")
    results = manager.run_lifecycle_management(dry_run=True)
    
    print(f"\\nDry run results:")
    print(f"  Files to archive: {len(results['archived'])}")
    print(f"  Files to delete: {len(results['deleted'])}")
    print(f"  Potential space freed: {results['space_freed_mb']:.2f} MB")
    
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"    - {error}")
    
    # Ask for confirmation to run actual cleanup
    response = input("\\nRun actual cleanup? (y/N): ")
    if response.lower() == 'y':
        print("\\nRunning actual lifecycle management...")
        actual_results = manager.run_lifecycle_management(dry_run=False)
        print(f"\\nActual results:")
        print(f"  Files archived: {len(actual_results['archived'])}")
        print(f"  Files deleted: {len(actual_results['deleted'])}")
        print(f"  Space freed: {actual_results['space_freed_mb']:.2f} MB")

if __name__ == "__main__":
    main()