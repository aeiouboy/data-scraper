#!/usr/bin/env python3
"""
Automated batch processor for fixing TWD category URLs
Runs multiple batches to fix all remaining products
"""

import json
import time
from fix_twd_category_url_extraction import TWDCategoryURLExtractor

def run_automated_batches(max_batches: int = 10, batch_size: int = 15):
    """Run multiple automated batches to fix TWD category URLs"""
    
    extractor = TWDCategoryURLExtractor()
    total_stats = {
        'batches_run': 0,
        'total_processed': 0,
        'total_fixed': 0,
        'total_failed': 0,
        'total_url_corrections': 0,
        'total_price_corrections': 0,
        'total_brand_corrections': 0,
        'total_category_corrections': 0,
        'batch_results': []
    }
    
    print("🔄 AUTOMATED TWD CATEGORY URL FIX")
    print("=" * 50)
    print(f"Target: Fix remaining TWD category URL products")
    print(f"Configuration: {max_batches} batches of {batch_size} products each")
    
    for batch_num in range(1, max_batches + 1):
        print(f"\n🔧 BATCH {batch_num}/{max_batches}")
        print("-" * 30)
        
        try:
            # Reset stats for this batch
            extractor.stats = {
                'processed': 0,
                'fixed': 0,
                'failed': 0,
                'url_corrections': 0,
                'price_corrections': 0,
                'brand_corrections': 0,
                'category_corrections': 0
            }
            
            # Run batch
            batch_results = extractor.fix_twd_category_products_batch(limit=batch_size)
            
            # Update totals
            total_stats['batches_run'] += 1
            total_stats['total_processed'] += batch_results['processed']
            total_stats['total_fixed'] += batch_results['fixed']
            total_stats['total_failed'] += batch_results['failed']
            total_stats['total_url_corrections'] += batch_results['url_corrections']
            total_stats['total_price_corrections'] += batch_results['price_corrections']
            total_stats['total_brand_corrections'] += batch_results['brand_corrections']
            total_stats['total_category_corrections'] += batch_results['category_corrections']
            
            # Store batch result
            batch_result = {
                'batch_number': batch_num,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': batch_results
            }
            total_stats['batch_results'].append(batch_result)
            
            # Display batch results
            success_rate = (batch_results['fixed'] / batch_results['processed'] * 100) if batch_results['processed'] > 0 else 0
            print(f"  Processed: {batch_results['processed']}")
            print(f"  ✅ Fixed: {batch_results['fixed']}")
            print(f"  ❌ Failed: {batch_results['failed']}")
            print(f"  📈 Success rate: {success_rate:.1f}%")
            print(f"  🔗 URL fixes: {batch_results['url_corrections']}")
            print(f"  💰 Price fixes: {batch_results['price_corrections']}")
            
            # Stop if no products were processed (all done)
            if batch_results['processed'] == 0:
                print(f"\n🎉 All products processed! No more TWD category URLs found.")
                break
            
            # Brief pause between batches
            if batch_num < max_batches:
                print(f"  ⏳ Waiting 3 seconds before next batch...")
                time.sleep(3)
                
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {str(e)}")
            break
    
    # Final summary
    print(f"\n📊 AUTOMATION SUMMARY:")
    print(f"  Batches completed: {total_stats['batches_run']}")
    print(f"  Total processed: {total_stats['total_processed']}")
    print(f"  ✅ Total fixed: {total_stats['total_fixed']}")
    print(f"  ❌ Total failed: {total_stats['total_failed']}")
    print(f"  🔗 URL corrections: {total_stats['total_url_corrections']}")
    print(f"  💰 Price corrections: {total_stats['total_price_corrections']}")
    print(f"  🏷️ Brand corrections: {total_stats['total_brand_corrections']}")
    print(f"  📂 Category corrections: {total_stats['total_category_corrections']}")
    
    overall_success_rate = (total_stats['total_fixed'] / total_stats['total_processed'] * 100) if total_stats['total_processed'] > 0 else 0
    print(f"  📈 Overall success rate: {overall_success_rate:.1f}%")
    
    # Save complete results
    with open('automated_twd_fix_results.json', 'w') as f:
        json.dump(total_stats, f, indent=2)
    
    print(f"\n📁 Complete results saved: automated_twd_fix_results.json")
    print(f"✅ Automated TWD category URL fix completed!")
    
    return total_stats

if __name__ == "__main__":
    # Run 10 batches of 15 products each (150 total products)
    results = run_automated_batches(max_batches=10, batch_size=15)
    
    # Show estimated remaining work
    if results['total_processed'] > 0:
        estimated_remaining = max(0, 2444 - results['total_fixed'])
        estimated_batches_needed = estimated_remaining // 15 + (1 if estimated_remaining % 15 else 0)
        print(f"\n🎯 NEXT STEPS:")
        print(f"  Estimated remaining products: ~{estimated_remaining}")
        print(f"  Estimated batches needed: ~{estimated_batches_needed}")
        print(f"  💡 Run this script again to continue fixing remaining products")