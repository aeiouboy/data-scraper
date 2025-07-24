#!/usr/bin/env python3
"""
Import processed Excel data to Supabase database
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import os
from datetime import datetime

# Add project root to path
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

# Import project modules
from src.services.supabase_service import SupabaseService
from src.models.product import Product


class SupabaseImporter:
    """Import processed data to Supabase"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
    
    def import_products(self, products_data: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """Import products in batches"""
        
        total_products = len(products_data)
        successful_imports = 0
        failed_imports = 0
        errors = []
        
        print(f"Starting import of {total_products} products in batches of {batch_size}...")
        
        # Process in batches
        for i in range(0, total_products, batch_size):
            batch = products_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)...")
            
            try:
                # Convert to Product models for validation
                products = []
                for product_data in batch:
                    try:
                        product = Product(**product_data)
                        products.append(product)
                    except Exception as e:
                        failed_imports += 1
                        errors.append(f"Validation error for product {product_data.get('name', 'Unknown')}: {str(e)}")
                        continue
                
                # Insert batch to database
                if products:
                    inserted_products = self.supabase_service.insert_products(products)
                    successful_imports += len(inserted_products)
                    print(f"  ✅ Successfully imported {len(inserted_products)} products")
                else:
                    print(f"  ❌ No valid products in batch")
                    
            except Exception as e:
                failed_imports += len(batch)
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
        
        # Summary
        result = {
            'total_products': total_products,
            'successful_imports': successful_imports,
            'failed_imports': failed_imports,
            'success_rate': (successful_imports / total_products) * 100 if total_products > 0 else 0,
            'errors': errors
        }
        
        return result
    
    def check_existing_products(self, retailer_codes: List[str]) -> Dict[str, int]:
        """Check existing products in database"""
        existing_counts = {}
        
        for retailer_code in retailer_codes:
            try:
                # Query products by retailer
                response = self.supabase_service.supabase.table('products').select('id', count='exact').eq('retailer_code', retailer_code).execute()
                existing_counts[retailer_code] = response.count or 0
            except Exception as e:
                print(f"Error checking existing products for {retailer_code}: {str(e)}")
                existing_counts[retailer_code] = 0
        
        return existing_counts
    
    def backup_existing_data(self, retailer_codes: List[str]) -> str:
        """Backup existing data before import"""
        backup_data = {}
        
        for retailer_code in retailer_codes:
            try:
                response = self.supabase_service.supabase.table('products').select('*').eq('retailer_code', retailer_code).execute()
                backup_data[retailer_code] = response.data
                print(f"Backed up {len(response.data)} products for {retailer_code}")
            except Exception as e:
                print(f"Error backing up {retailer_code}: {str(e)}")
                backup_data[retailer_code] = []
        
        # Save backup to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"/Users/chongraktanaka/Documents/Project/ris data scrap/data/backup_{timestamp}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Backup saved to: {backup_file}")
        return backup_file
    
    def clear_existing_data(self, retailer_codes: List[str]) -> bool:
        """Clear existing data for specified retailers"""
        try:
            for retailer_code in retailer_codes:
                response = self.supabase_service.supabase.table('products').delete().eq('retailer_code', retailer_code).execute()
                print(f"Cleared existing data for {retailer_code}")
            return True
        except Exception as e:
            print(f"Error clearing existing data: {str(e)}")
            return False


def main():
    """Main import function"""
    
    # Load processed data
    data_file = Path("/Users/chongraktanaka/Documents/Project/ris data scrap/data/processed_import_data.json")
    
    if not data_file.exists():
        print("❌ Processed data file not found. Please run import_excel_data.py first.")
        sys.exit(1)
    
    # Load data
    with open(data_file, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    print(f"Loaded {len(products_data)} products from {data_file}")
    
    # Initialize importer
    importer = SupabaseImporter()
    
    # Check existing data
    retailer_codes = ['HP', 'TWD']
    existing_counts = importer.check_existing_products(retailer_codes)
    
    print("\nExisting products in database:")
    for retailer_code, count in existing_counts.items():
        print(f"  {retailer_code}: {count} products")
    
    # Ask for confirmation if data exists
    total_existing = sum(existing_counts.values())
    if total_existing > 0:
        print(f"\n⚠️  Warning: {total_existing} existing products will be replaced!")
        
        # Create backup
        backup_file = importer.backup_existing_data(retailer_codes)
        
        # Clear existing data
        if not importer.clear_existing_data(retailer_codes):
            print("❌ Failed to clear existing data. Aborting import.")
            sys.exit(1)
    
    # Import data
    print("\n" + "="*80)
    print("STARTING IMPORT")
    print("="*80)
    
    result = importer.import_products(products_data, batch_size=50)
    
    # Print results
    print("\n" + "="*80)
    print("IMPORT RESULTS")
    print("="*80)
    
    print(f"Total products processed: {result['total_products']}")
    print(f"Successful imports: {result['successful_imports']}")
    print(f"Failed imports: {result['failed_imports']}")
    print(f"Success rate: {result['success_rate']:.1f}%")
    
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])} total):")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(result['errors']) > 5:
            print(f"  ... and {len(result['errors']) - 5} more errors")
    
    # Verify import
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    final_counts = importer.check_existing_products(retailer_codes)
    print("Final product counts:")
    for retailer_code, count in final_counts.items():
        print(f"  {retailer_code}: {count} products")
    
    total_imported = sum(final_counts.values())
    print(f"\nTotal products in database: {total_imported}")
    
    if total_imported == result['successful_imports']:
        print("✅ Import verification successful!")
    else:
        print("❌ Import verification failed - count mismatch")
    
    print("\n🎉 Import process completed!")


if __name__ == "__main__":
    main()