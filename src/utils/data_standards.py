#!/usr/bin/env python3
"""
Data Standards and Naming Convention Utilities
Provides standardized naming, metadata, and validation for JSON data files
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

class DataStandards:
    """Utilities for data naming conventions and metadata standards"""
    
    # Valid category prefixes
    VALID_CATEGORIES = {
        'config': 'Configuration files',
        'analysis': 'Analysis results and reports',
        'scraping': 'Scraping outputs and results',
        'test': 'Test execution results',
        'backup': 'Backup files',
        'temp': 'Temporary processing files',
        'export': 'Export outputs'
    }
    
    # Valid subcategories
    VALID_SUBCATEGORIES = {
        'analysis': ['dataquality', 'performance', 'debugging'],
        'scraping': ['results', 'progress', 'validation'],
        'test': ['unit', 'integration', 'e2e'],
        'backup': ['daily', 'weekly', 'manual'],
        'temp': ['processing', 'debug', 'cache'],
        'export': ['csv', 'reports', 'api'],
        'config': ['retailers', 'scraping', 'system', 'application']
    }
    
    @staticmethod
    def generate_filename(category: str, subcategory: str, description: str, 
                         timestamp: Optional[str] = None, extension: str = 'json') -> str:
        """
        Generate standardized filename following naming convention
        
        Pattern: {category}_{subcategory}_{description}_{timestamp}.{extension}
        """
        
        # Validate inputs
        if category not in DataStandards.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        
        if subcategory not in DataStandards.VALID_SUBCATEGORIES.get(category, []):
            raise ValueError(f"Invalid subcategory '{subcategory}' for category '{category}'")
        
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Clean description (remove special chars, convert to lowercase)
        clean_description = re.sub(r'[^a-zA-Z0-9_]', '_', description.lower())
        clean_description = re.sub(r'_+', '_', clean_description).strip('_')
        
        # Construct filename
        filename = f"{category}_{subcategory}_{clean_description}_{timestamp}.{extension}"
        
        return filename
    
    @staticmethod
    def create_metadata(data_source: str, description: str, created_by: str,
                       file_type: str, retention_policy: str,
                       version: str = "1.0", 
                       related_files: Optional[List[str]] = None,
                       processing_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create standardized metadata structure
        """
        
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "file_type": file_type,
            "data_source": data_source,
            "retention_policy": retention_policy,
            "description": description,
            "version": version,
            "schema_version": "1.0",
            "last_modified": datetime.now(timezone.utc).isoformat(),
        }
        
        # Add optional fields
        if related_files:
            metadata["related_files"] = related_files
        
        if processing_params:
            metadata["processing_parameters"] = processing_params
        
        return metadata
    
    @staticmethod
    def create_data_file(data: Any, metadata: Dict[str, Any], 
                        calculate_checksum: bool = True) -> Dict[str, Any]:
        """
        Create complete data file structure with metadata and data
        """
        
        file_structure = {
            "metadata": metadata,
            "data": data
        }
        
        # Calculate checksum if requested
        if calculate_checksum:
            data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            checksum = hashlib.sha256(data_str.encode()).hexdigest()
            file_structure["metadata"]["checksum"] = checksum
        
        return file_structure
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename follows naming convention
        
        Pattern: {category}_{subcategory}_{description}_{timestamp}.{extension}
        """
        
        # Check basic pattern
        pattern = r'^([a-z]+)_([a-z]+)_([a-z0-9_]+)_(\d{8}_\d{6})\.(json|csv|txt)$'
        match = re.match(pattern, filename)
        
        if not match:
            return False
        
        category, subcategory, description, timestamp, extension = match.groups()
        
        # Validate category
        if category not in DataStandards.VALID_CATEGORIES:
            return False
        
        # Validate subcategory
        if subcategory not in DataStandards.VALID_SUBCATEGORIES.get(category, []):
            return False
        
        # Validate timestamp format
        try:
            datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        except ValueError:
            return False
        
        return True
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> List[str]:
        """
        Validate metadata structure and return list of issues
        """
        
        issues = []
        required_fields = [
            'created_at', 'created_by', 'file_type', 'data_source',
            'retention_policy', 'description', 'version', 'schema_version'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in metadata:
                issues.append(f"Missing required field: {field}")
        
        # Validate timestamp format
        if 'created_at' in metadata:
            try:
                datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
            except ValueError:
                issues.append("Invalid created_at timestamp format")
        
        # Validate retention policy format
        if 'retention_policy' in metadata:
            valid_policies = ['permanent', '7_days', '30_days', '90_days', '180_days', '365_days']
            if metadata['retention_policy'] not in valid_policies:
                issues.append(f"Invalid retention_policy: {metadata['retention_policy']}")
        
        return issues
    
    @staticmethod
    def validate_data_file(file_path: Path) -> Dict[str, Any]:
        """
        Validate complete data file structure and content
        """
        
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                validation_result['valid'] = False
                validation_result['issues'].append("File does not exist")
                return validation_result
            
            # Validate filename
            if not DataStandards.validate_filename(file_path.name):
                validation_result['warnings'].append("Filename does not follow naming convention")
            
            # Load and validate JSON structure
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check for required top-level structure
            if 'metadata' not in data:
                validation_result['valid'] = False
                validation_result['issues'].append("Missing metadata section")
            
            if 'data' not in data:
                validation_result['valid'] = False
                validation_result['issues'].append("Missing data section")
            
            # Validate metadata if present
            if 'metadata' in data:
                metadata_issues = DataStandards.validate_metadata(data['metadata'])
                validation_result['issues'].extend(metadata_issues)
                if metadata_issues:
                    validation_result['valid'] = False
            
            # Validate checksum if present
            if 'metadata' in data and 'checksum' in data['metadata']:
                data_str = json.dumps(data['data'], sort_keys=True, separators=(',', ':'))
                calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()
                stored_checksum = data['metadata']['checksum']
                
                if calculated_checksum != stored_checksum:
                    validation_result['valid'] = False
                    validation_result['issues'].append("Checksum mismatch - data may be corrupted")
        
        except json.JSONDecodeError as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Invalid JSON format: {e}")
        
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {e}")
        
        return validation_result

class DataFileGenerator:
    """Helper class to generate standardized data files"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def save_analysis_result(self, data: Any, description: str, 
                           data_source: str, subcategory: str = 'dataquality',
                           created_by: str = 'system') -> Path:
        """Save analysis result with proper structure and metadata"""
        
        # Generate filename
        filename = DataStandards.generate_filename('analysis', subcategory, description)
        
        # Create metadata
        metadata = DataStandards.create_metadata(
            data_source=data_source,
            description=description,
            created_by=created_by,
            file_type='analysis_result',
            retention_policy='90_days'
        )
        
        # Create complete file structure
        file_data = DataStandards.create_data_file(data, metadata)
        
        # Determine save path
        save_path = self.base_path / 'data' / 'active' / 'analysis' / subcategory / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(save_path, 'w') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        return save_path
    
    def save_scraping_result(self, data: Any, description: str,
                           retailer: str, subcategory: str = 'results',
                           created_by: str = 'scraping_service') -> Path:
        """Save scraping result with proper structure and metadata"""
        
        # Generate filename with retailer info
        desc_with_retailer = f"{retailer}_{description}"
        filename = DataStandards.generate_filename('scraping', subcategory, desc_with_retailer)
        
        # Create metadata
        metadata = DataStandards.create_metadata(
            data_source=f"{retailer}_website",
            description=f"Scraping result for {retailer}: {description}",
            created_by=created_by,
            file_type='scraping_result',
            retention_policy='180_days'
        )
        
        # Create complete file structure
        file_data = DataStandards.create_data_file(data, metadata)
        
        # Determine save path
        save_path = self.base_path / 'data' / 'active' / 'scraping' / subcategory / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(save_path, 'w') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        return save_path
    
    def save_test_result(self, data: Any, description: str, 
                        test_type: str = 'integration',
                        created_by: str = 'test_runner') -> Path:
        """Save test result with proper structure and metadata"""
        
        # Generate filename
        filename = DataStandards.generate_filename('test', test_type, description)
        
        # Create metadata
        metadata = DataStandards.create_metadata(
            data_source='test_execution',
            description=f"Test result: {description}",
            created_by=created_by,
            file_type='test_result',
            retention_policy='30_days'
        )
        
        # Create complete file structure
        file_data = DataStandards.create_data_file(data, metadata)
        
        # Determine save path
        save_path = self.base_path / 'data' / 'active' / 'testing' / test_type / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(save_path, 'w') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        return save_path

# Example usage functions
def example_create_analysis_file():
    """Example of creating a properly structured analysis file"""
    
    generator = DataFileGenerator("/Users/chongraktanaka/Documents/Project/ris data scrap")
    
    # Sample analysis data
    analysis_data = {
        "total_products": 1000,
        "by_retailer": {
            "HP": {"total": 741, "missing_brand": 2},
            "TWD": {"total": 259, "missing_brand": 3}
        },
        "quality_score": 0.95
    }
    
    # Save with proper structure
    file_path = generator.save_analysis_result(
        data=analysis_data,
        description="hp_twd_data_quality_check",
        data_source="supabase_products_table",
        subcategory="dataquality",
        created_by="quality_checker"
    )
    
    print(f"Analysis file saved: {file_path}")
    return file_path

def example_validate_file(file_path: str):
    """Example of validating a data file"""
    
    result = DataStandards.validate_data_file(Path(file_path))
    
    print(f"Validation result for {file_path}:")
    print(f"  Valid: {result['valid']}")
    
    if result['issues']:
        print("  Issues:")
        for issue in result['issues']:
            print(f"    - {issue}")
    
    if result['warnings']:
        print("  Warnings:")
        for warning in result['warnings']:
            print(f"    - {warning}")

if __name__ == "__main__":
    # Example usage
    print("Data Standards Example")
    print("=" * 30)
    
    # Create example file
    file_path = example_create_analysis_file()
    
    # Validate the file
    example_validate_file(str(file_path))