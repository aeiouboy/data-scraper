#!/usr/bin/env python3
"""
Monitor the progress of the import process
"""
import re
import time
from pathlib import Path

def monitor_import_progress():
    """Monitor import progress from log file"""
    log_file = Path("import_log.txt")
    
    if not log_file.exists():
        print("Import log file not found")
        return
    
    print("🔄 Monitoring import progress...")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_batch = 0
    start_time = None
    
    try:
        while True:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Find batch progress
            batch_matches = re.findall(r'Processing batch (\d+)/(\d+)', content)
            if batch_matches:
                current_batch, total_batches = batch_matches[-1]
                current_batch = int(current_batch)
                total_batches = int(total_batches)
                
                if current_batch > last_batch:
                    last_batch = current_batch
                    progress = (current_batch / total_batches) * 100
                    
                    print(f"📊 Batch {current_batch}/{total_batches} ({progress:.1f}%)")
            
            # Find successful imports
            success_matches = re.findall(r'Successfully upserted product:', content)
            success_count = len(success_matches)
            
            # Find batch completion messages
            batch_completed = re.findall(r'Batch \d+ completed: (\d+) imported, (\d+) updated, (\d+) failed', content)
            
            if batch_completed:
                imported = sum(int(match[0]) for match in batch_completed)
                updated = sum(int(match[1]) for match in batch_completed)
                failed = sum(int(match[2]) for match in batch_completed)
                total_processed = imported + updated + failed
                
                print(f"✅ Progress: {total_processed} processed ({imported} new, {updated} updated, {failed} failed)")
            
            # Check if import completed
            if "IMPORT COMPLETED" in content:
                print("\n🎉 Import completed successfully!")
                
                # Extract final statistics
                final_stats = re.search(r'Products imported: (\d+).*?Products updated: (\d+).*?Products failed: (\d+)', content, re.DOTALL)
                if final_stats:
                    imported, updated, failed = final_stats.groups()
                    total = int(imported) + int(updated) + int(failed)
                    success_rate = ((int(imported) + int(updated)) / total * 100) if total > 0 else 0
                    
                    print(f"📈 Final Results:")
                    print(f"   • Imported: {imported}")
                    print(f"   • Updated: {updated}")
                    print(f"   • Failed: {failed}")
                    print(f"   • Success Rate: {success_rate:.1f}%")
                break
            
            # Check for errors
            if "Import process failed" in content:
                print("\n❌ Import process failed!")
                break
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
        print(f"Last seen: Batch {last_batch} with {success_count} successful imports")

if __name__ == "__main__":
    monitor_import_progress()