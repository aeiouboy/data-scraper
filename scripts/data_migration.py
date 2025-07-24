#!/usr/bin/env python3
"""
Data Migration Script for JSON Data Organization
Moves existing JSON files to new organized structure
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import re

class DataMigrator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.migration_log = []
        
    def get_current_timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def categorize_file(self, filename, file_path):
        """Categorize files based on their names and content"""
        
        # Configuration files
        if filename in ['package.json', 'package-lock.json', 'tsconfig.json', 'manifest.json']:
            return 'config', 'application'
        
        # Test results
        if any(keyword in filename.lower() for keyword in ['test_', 'coverage', 'matcher_comparison', 'matching_comparison']):
            return 'testing', 'results'
        
        # Analysis files
        if any(keyword in filename.lower() for keyword in [
            'analysis', 'quality', 'missing_data', 'null_sku', 
            'investigation', 'audit', 'check_results'
        ]):
            return 'analysis', 'data-quality'
        
        # Scraping results
        if any(keyword in filename.lower() for keyword in [
            'scraping', 'categories', 'products', 'twd_', 'hp_', 
            'boonthavorn', 'extraction'
        ]):
            return 'scraping', 'results'
        
        # Fix/improvement results
        if any(keyword in filename.lower() for keyword in [
            'fix_results', 'improvement', 'rescraping'
        ]):
            return 'analysis', 'debugging'
        
        # Backup files
        if 'backup' in filename.lower():
            return 'backups', 'manual'
        
        # Progress tracking
        if 'progress' in filename.lower():
            return 'scraping', 'progress'
        
        # Default to temp for unknown files
        return 'temp', 'processing'
    
    def create_new_filename(self, old_filename, category, subcategory):
        """Create new filename following naming convention"""
        
        # Extract timestamp if exists
        timestamp_pattern = r'(\d{8}_\d{6}|\d{4}\d{2}\d{2}_\d{6})'
        timestamp_match = re.search(timestamp_pattern, old_filename)
        
        if timestamp_match:
            timestamp = timestamp_match.group(1)
        else:
            timestamp = self.get_current_timestamp()
        
        # Remove old timestamp and file extension
        base_name = re.sub(timestamp_pattern, '', old_filename)
        base_name = base_name.replace('.json', '').strip('_')
        
        # Create new filename
        if category == 'analysis':
            prefix = 'analysis'
        elif category == 'scraping':
            prefix = 'scraping'
        elif category == 'testing':
            prefix = 'test'
        elif category == 'backups':
            prefix = 'backup'
        elif category == 'config':
            prefix = 'config'
        else:
            prefix = 'temp'
        
        new_filename = f"{prefix}_{subcategory}_{base_name}_{timestamp}.json"
        
        # Clean up double underscores and other issues
        new_filename = re.sub(r'_+', '_', new_filename)
        new_filename = new_filename.strip('_')
        
        return new_filename
    
    def migrate_file(self, source_path, category, subcategory):
        """Migrate a single file to new location"""
        
        try:
            source_file = Path(source_path)
            
            # Determine destination directory
            if category == 'config':
                dest_dir = self.base_path / 'data' / 'config' / subcategory
            elif category == 'analysis':
                dest_dir = self.base_path / 'data' / 'active' / 'analysis' / subcategory
            elif category == 'scraping':
                dest_dir = self.base_path / 'data' / 'active' / 'scraping' / subcategory
            elif category == 'testing':
                dest_dir = self.base_path / 'data' / 'active' / 'testing' / subcategory
            elif category == 'backups':
                dest_dir = self.base_path / 'data' / 'backups' / subcategory
            else:
                dest_dir = self.base_path / 'data' / 'temp' / subcategory
            
            # Create destination directory
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Create new filename
            new_filename = self.create_new_filename(source_file.name, category, subcategory)
            dest_path = dest_dir / new_filename
            
            # Copy file (don't move yet, keep originals for safety)
            shutil.copy2(source_file, dest_path)
            
            self.migration_log.append({
                'source': str(source_file),
                'destination': str(dest_path),
                'category': category,
                'subcategory': subcategory,
                'status': 'copied',
                'timestamp': self.get_current_timestamp()
            })
            
            print(f"Migrated: {source_file.name} -> {dest_path}")
            return True
            
        except Exception as e:
            self.migration_log.append({
                'source': str(source_path),
                'destination': 'FAILED',
                'category': category,
                'subcategory': subcategory,
                'status': 'error',
                'error': str(e),
                'timestamp': self.get_current_timestamp()
            })
            print(f"Error migrating {source_path}: {e}")
            return False
    
    def migrate_root_json_files(self):
        """Migrate JSON files from project root"""
        
        root_json_files = [
            'automated_twd_fix_results.json',
            'brand_extraction_test_results.json',
            'brand_rescraping_results.json',
            'current_missing_data_analysis.json',
            'data_quality_analysis.json',
            'data_quality_improvement_plan.json',
            'false_positives_audit.json',
            'hp_price_extraction_test_results.json',
            'hp_price_improvements_results.json',
            'improvement_application_results.json',
            'missing_data_analysis.json',
            'null_sku_analysis.json',
            'problematic_products_samples.json',
            'quick_quality_check_results.json',
            'specific_products_fix_results.json',
            'twd_category_investigation_results.json',
            'twd_category_url_fix_results.json',
            'twd_extraction_fix_results.json',
            'twd_url_analysis.json',
            'url_and_price_issues_analysis.json'
        ]
        
        for filename in root_json_files:
            file_path = self.base_path / filename
            if file_path.exists():
                category, subcategory = self.categorize_file(filename, file_path)
                self.migrate_file(file_path, category, subcategory)
    
    def reorganize_existing_data_files(self):
        """Reorganize files already in data directory"""
        
        # Move files from existing structure to new structure
        moves = [
            # Analysis reports
            ('data/analysis_reports/', 'analysis', 'data-quality'),
            
            # Test results 
            ('data/test_results/', 'testing', 'integration'),
            
            # Current backups
            ('data/backups/', 'backups', 'manual'),
            
            # Results
            ('data/results/', 'analysis', 'data-quality'),
            
            # Keep scraping results in place but reorganize
            ('data/scraping_results/', 'scraping', 'results'),
        ]
        
        for source_dir, category, subcategory in moves:
            source_path = self.base_path / source_dir
            if source_path.exists():
                for json_file in source_path.glob('*.json'):
                    self.migrate_file(json_file, category, subcategory)
    
    def save_migration_log(self):
        """Save migration log to file"""
        
        log_file = self.base_path / 'data' / 'config' / 'system' / f'migration_log_{self.get_current_timestamp()}.json'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'w') as f:
            json.dump({
                'migration_date': datetime.now().isoformat(),
                'total_files': len(self.migration_log),
                'successful': len([log for log in self.migration_log if log['status'] == 'copied']),
                'failed': len([log for log in self.migration_log if log['status'] == 'error']),
                'files': self.migration_log
            }, f, indent=2)
        
        print(f"Migration log saved to: {log_file}")
    
    def run_migration(self):
        """Run complete migration process"""
        
        print("Starting JSON Data Migration...")
        print("=" * 50)
        
        # Migrate root directory JSON files
        print("\\nMigrating root directory JSON files...")
        self.migrate_root_json_files()
        
        # Reorganize existing data directory files
        print("\\nReorganizing existing data directory files...")
        self.reorganize_existing_data_files()
        
        # Save migration log
        print("\\nSaving migration log...")
        self.save_migration_log()
        
        # Print summary
        successful = len([log for log in self.migration_log if log['status'] == 'copied'])
        failed = len([log for log in self.migration_log if log['status'] == 'error'])
        
        print("\\n" + "=" * 50)
        print("Migration Summary:")
        print(f"Total files processed: {len(self.migration_log)}")
        print(f"Successfully migrated: {successful}")
        print(f"Failed migrations: {failed}")
        
        if failed > 0:
            print("\\nFailed files:")
            for log in self.migration_log:
                if log['status'] == 'error':
                    print(f"  - {log['source']}: {log['error']}")

if __name__ == "__main__":
    base_path = "/Users/chongraktanaka/Documents/Project/ris data scrap"
    migrator = DataMigrator(base_path)
    migrator.run_migration()