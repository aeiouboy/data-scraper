#!/usr/bin/env python3
"""
Debug script to understand the match_groups table schema and find CARRIER matches
"""

import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

from src.services.supabase_service import SupabaseService
import json

def debug_match_schema():
    """Debug the match_groups table schema"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    print("=== DEBUGGING MATCH_GROUPS TABLE SCHEMA ===\n")
    
    try:
        # First, let's get all tables to understand the schema
        print("Getting match_groups table structure...")
        
        # Try to get a few records to understand the schema
        match_query = supabase_service.client.table('match_groups').select('*').limit(5).execute()
        
        if match_query.data:
            print(f"Found {len(match_query.data)} match groups")
            print("\nSample match group structure:")
            for i, match in enumerate(match_query.data):
                print(f"\n--- Match {i+1} ---")
                for key, value in match.items():
                    print(f"  {key}: {value}")
                print()
                
        # Check product_match_mapping table
        print("\n=== CHECKING PRODUCT_MATCH_MAPPING TABLE ===")
        mapping_query = supabase_service.client.table('product_match_mapping').select('*').limit(5).execute()
        
        if mapping_query.data:
            print(f"Found {len(mapping_query.data)} product mappings")
            print("\nSample mapping structure:")
            for i, mapping in enumerate(mapping_query.data):
                print(f"\n--- Mapping {i+1} ---")
                for key, value in mapping.items():
                    print(f"  {key}: {value}")
                print()
        
        # Look for CARRIER products directly in products table
        print("\n=== SEARCHING FOR CARRIER PRODUCTS ===")
        carrier_query = supabase_service.client.table('products').select('*').ilike('name', '%CARRIER%').limit(10).execute()
        
        if carrier_query.data:
            print(f"Found {len(carrier_query.data)} CARRIER products")
            for i, product in enumerate(carrier_query.data):
                print(f"\n--- CARRIER Product {i+1} ---")
                print(f"  ID: {product.get('id', 'N/A')}")
                print(f"  Name: {product.get('name', 'N/A')}")
                print(f"  Brand: {product.get('brand', 'N/A')}")
                print(f"  Price: ฿{product.get('price', 'N/A')}")
                print(f"  Retailer: {product.get('retailer_code', 'N/A')}")
                
                # Check if this product is in any match group
                mapping_check = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', product['id']).execute()
                if mapping_check.data:
                    print(f"  Match Group ID: {mapping_check.data[0].get('match_group_id', 'N/A')}")
                else:
                    print(f"  Match Group ID: None")
                
                # Extract BTU from name
                import re
                name = product.get('name', '')
                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                if btu_match:
                    btu = btu_match.group(1).replace(',', '').replace('.', '')
                    print(f"  BTU: {btu}")
                
        # Look for specific CARRIER models mentioned in the question
        print("\n=== SEARCHING FOR SPECIFIC CARRIER MODELS ===")
        
        # Search for the TWD model
        twd_query = supabase_service.client.table('products').select('*').ilike('name', '%38TVEA028A42TVEA028A%').execute()
        if twd_query.data:
            print(f"Found TWD CARRIER product: {twd_query.data[0].get('name', 'N/A')}")
            twd_product = twd_query.data[0]
            print(f"  ID: {twd_product.get('id', 'N/A')}")
            print(f"  Price: ฿{twd_product.get('price', 'N/A')}")
            
            # Check match group
            mapping_check = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', twd_product['id']).execute()
            if mapping_check.data:
                match_group_id = mapping_check.data[0].get('match_group_id')
                print(f"  Match Group ID: {match_group_id}")
                
                # Get other products in this match group
                other_mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
                if other_mappings.data:
                    print(f"  Other products in this match group:")
                    for mapping in other_mappings.data:
                        if mapping['product_id'] != twd_product['id']:
                            other_product = supabase_service.client.table('products').select('*').eq('id', mapping['product_id']).execute()
                            if other_product.data:
                                op = other_product.data[0]
                                print(f"    - {op.get('name', 'N/A')} (₿{op.get('price', 'N/A')}) - {op.get('retailer_code', 'N/A')}")
                                
                                # Extract BTU
                                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', op.get('name', ''), re.IGNORECASE)
                                if btu_match:
                                    btu = btu_match.group(1).replace(',', '').replace('.', '')
                                    print(f"      BTU: {btu}")
            else:
                print(f"  Match Group ID: None")
        
        # Search for the HP model
        hp_query = supabase_service.client.table('products').select('*').ilike('name', '%42TVAB013ABI%').execute()
        if hp_query.data:
            print(f"Found HP CARRIER product: {hp_query.data[0].get('name', 'N/A')}")
            hp_product = hp_query.data[0]
            print(f"  ID: {hp_product.get('id', 'N/A')}")
            print(f"  Price: ฿{hp_product.get('price', 'N/A')}")
            
            # Check match group
            mapping_check = supabase_service.client.table('product_match_mapping').select('*').eq('product_id', hp_product['id']).execute()
            if mapping_check.data:
                match_group_id = mapping_check.data[0].get('match_group_id')
                print(f"  Match Group ID: {match_group_id}")
                
                # Get other products in this match group
                other_mappings = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
                if other_mappings.data:
                    print(f"  Other products in this match group:")
                    for mapping in other_mappings.data:
                        if mapping['product_id'] != hp_product['id']:
                            other_product = supabase_service.client.table('products').select('*').eq('id', mapping['product_id']).execute()
                            if other_product.data:
                                op = other_product.data[0]
                                print(f"    - {op.get('name', 'N/A')} (₿{op.get('price', 'N/A')}) - {op.get('retailer_code', 'N/A')}")
                                
                                # Extract BTU
                                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', op.get('name', ''), re.IGNORECASE)
                                if btu_match:
                                    btu = btu_match.group(1).replace(',', '').replace('.', '')
                                    print(f"      BTU: {btu}")
            else:
                print(f"  Match Group ID: None")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_match_schema()