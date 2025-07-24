#!/usr/bin/env python3
"""
Audit existing matches for false positives similar to the CARRIER issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.services.supabase_service import SupabaseService
import json
import re

def audit_false_matches():
    """Audit existing match groups for false positives"""
    
    # Initialize services
    supabase_service = SupabaseService()
    
    print("=== AUDITING EXISTING MATCHES FOR FALSE POSITIVES ===\n")
    
    try:
        # Get all match groups
        match_groups_query = supabase_service.client.table('match_groups').select('*').execute()
        
        print(f"Total match groups to audit: {len(match_groups_query.data)}")
        
        false_positives = []
        
        for i, match_group in enumerate(match_groups_query.data):
            match_group_id = match_group['id']
            
            print(f"\nAuditing match group {i+1}/{len(match_groups_query.data)}: {match_group_id}")
            
            # Get all products in this match group
            mapping_query = supabase_service.client.table('product_match_mapping').select('*').eq('match_group_id', match_group_id).execute()
            
            if len(mapping_query.data) < 2:
                continue  # Skip single product groups
            
            products = []
            for mapping in mapping_query.data:
                product_query = supabase_service.client.table('products').select('*').eq('id', mapping['product_id']).execute()
                if product_query.data:
                    products.append(product_query.data[0])
            
            if len(products) < 2:
                continue
            
            # Analyze BTU variance for air conditioners
            btus = []
            for product in products:
                name = product.get('name', '')
                # Look for BTU in the name
                btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                if btu_match:
                    btu = int(btu_match.group(1).replace(',', '').replace('.', ''))
                    btus.append(btu)
            
            # Check if this is an air conditioner match with BTU variance
            if len(btus) >= 2:
                min_btu = min(btus)
                max_btu = max(btus)
                btu_variance = ((max_btu - min_btu) / min_btu) * 100 if min_btu > 0 else 0
                
                if btu_variance > 10:  # More than 10% BTU variance
                    print(f"  ❌ POTENTIAL FALSE POSITIVE: BTU variance {btu_variance:.1f}%")
                    
                    # Get confidence scores
                    confidence_query = supabase_service.client.table('match_confidence').select('*').eq('match_group_id', match_group_id).execute()
                    confidence_score = confidence_query.data[0].get('overall_score', 0) if confidence_query.data else 0
                    
                    false_positive = {
                        'match_group_id': match_group_id,
                        'canonical_name': match_group.get('canonical_name', ''),
                        'brand': match_group.get('canonical_brand', ''),
                        'confidence_score': confidence_score,
                        'btu_variance': btu_variance,
                        'btu_range': f"{min_btu} - {max_btu}",
                        'products': []
                    }
                    
                    for product in products:
                        name = product.get('name', '')
                        btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                        btu = int(btu_match.group(1).replace(',', '').replace('.', '')) if btu_match else None
                        
                        false_positive['products'].append({
                            'name': name,
                            'retailer': product.get('retailer_code', ''),
                            'btu': btu,
                            'price': product.get('price', 0)
                        })
                    
                    false_positives.append(false_positive)
                    
                    print(f"    Products:")
                    for product in products:
                        name = product.get('name', '')
                        retailer = product.get('retailer_code', '')
                        price = product.get('price', 0)
                        btu_match = re.search(r'(\d{1,3}[,.]?\d{3})\s*BTU', name, re.IGNORECASE)
                        btu = int(btu_match.group(1).replace(',', '').replace('.', '')) if btu_match else 'N/A'
                        print(f"      {retailer}: {name[:80]}... BTU: {btu}, Price: ฿{price}")
                
                else:
                    print(f"  ✅ BTU variance acceptable: {btu_variance:.1f}%")
            
            # Analyze model number differences
            models = []
            for product in products:
                name = product.get('name', '')
                # Extract model numbers using various patterns
                model_patterns = [
                    r'([A-Z0-9]+[A-Z][A-Z0-9]+)',
                    r'([0-9]+[A-Z]+[0-9]+[A-Z]*[0-9]*)',
                    r'(\d{2}[A-Z]{2,4}\d{3}[A-Z]*\d*[A-Z]*)'
                ]
                
                model_found = None
                for pattern in model_patterns:
                    match = re.search(pattern, name.upper())
                    if match:
                        model_found = match.group(1)
                        break
                
                if model_found:
                    models.append(model_found)
            
            unique_models = set(models)
            if len(unique_models) > 1 and len(btus) >= 2:
                print(f"  ⚠️  Multiple models in same match group: {list(unique_models)}")
        
        print(f"\n=== AUDIT SUMMARY ===")
        print(f"Total match groups audited: {len(match_groups_query.data)}")
        print(f"False positives found: {len(false_positives)}")
        
        if false_positives:
            print(f"\n=== TOP FALSE POSITIVES ===")
            # Sort by BTU variance
            false_positives.sort(key=lambda x: x['btu_variance'], reverse=True)
            
            for i, fp in enumerate(false_positives[:5]):  # Show top 5
                print(f"\n{i+1}. Match Group: {fp['match_group_id']}")
                print(f"   Brand: {fp['brand']}")
                print(f"   Confidence: {fp['confidence_score']}")
                print(f"   BTU Variance: {fp['btu_variance']:.1f}%")
                print(f"   BTU Range: {fp['btu_range']}")
                print(f"   Products:")
                for product in fp['products']:
                    print(f"     - {product['retailer']}: BTU {product['btu']}, ฿{product['price']}")
        
        # Save detailed report
        report_file = '/Users/chongraktanaka/Documents/Project/ris data scrap/false_positives_audit.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(false_positives, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    audit_false_matches()