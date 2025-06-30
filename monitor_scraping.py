#!/usr/bin/env python3
"""
Real-time monitoring dashboard for HomePro scraping progress
"""
import asyncio
import argparse
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.services.supabase_service import SupabaseService

class ScrapingMonitor:
    """Real-time monitoring for scraping operations"""
    
    def __init__(self, refresh_interval: int = 10):
        self.supabase = SupabaseService()
        self.refresh_interval = refresh_interval
        self.last_stats = None
        
    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics"""
        try:
            # Get job statistics
            jobs = await self.supabase.get_scrape_jobs(limit=100)
            
            # Get product count
            products = await self.supabase.search_products(limit=1)
            total_products = products.get('total', 0)
            
            # Calculate job stats
            total_jobs = len(jobs)
            active_jobs = len([j for j in jobs if j['status'] in ['pending', 'running']])
            completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
            failed_jobs = len([j for j in jobs if j['status'] == 'failed'])
            
            # Calculate success metrics
            total_discovered = sum(j.get('total_items', 0) for j in jobs if j.get('total_items'))
            total_scraped = sum(j.get('success_items', 0) for j in jobs if j.get('success_items'))
            total_failed = sum(j.get('failed_items', 0) for j in jobs if j.get('failed_items'))
            
            success_rate = (total_scraped / total_discovered * 100) if total_discovered > 0 else 0
            
            # Get recent activity (last 24 hours)
            recent_jobs = [j for j in jobs if self._is_recent(j.get('created_at'))]
            recent_success = sum(j.get('success_items', 0) for j in recent_jobs)
            recent_failed = sum(j.get('failed_items', 0) for j in recent_jobs)
            
            # Calculate rates
            rates = self._calculate_rates(jobs)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'completed': completed_jobs,
                    'failed': failed_jobs
                },
                'products': {
                    'total_stored': total_products,
                    'total_discovered': total_discovered,
                    'total_scraped': total_scraped,
                    'total_failed': total_failed,
                    'success_rate': success_rate
                },
                'recent_24h': {
                    'jobs': len(recent_jobs),
                    'success': recent_success,
                    'failed': recent_failed
                },
                'rates': rates,
                'running_jobs': [j for j in jobs if j['status'] == 'running']
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _is_recent(self, timestamp_str: str) -> bool:
        """Check if timestamp is within last 24 hours"""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return datetime.now().replace(tzinfo=timestamp.tzinfo) - timestamp < timedelta(hours=24)
        except:
            return False
    
    def _calculate_rates(self, jobs: list) -> Dict[str, float]:
        """Calculate scraping rates"""
        try:
            completed_jobs = [j for j in jobs if j['status'] == 'completed' and j.get('started_at') and j.get('completed_at')]
            
            if not completed_jobs:
                return {'avg_job_duration_minutes': 0, 'avg_products_per_minute': 0}
            
            total_duration = 0
            total_products = 0
            
            for job in completed_jobs:
                try:
                    started = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(job['completed_at'].replace('Z', '+00:00'))
                    duration = (completed - started).total_seconds() / 60  # minutes
                    
                    if duration > 0:
                        total_duration += duration
                        total_products += job.get('success_items', 0)
                except:
                    continue
            
            avg_duration = total_duration / len(completed_jobs) if completed_jobs else 0
            avg_rate = total_products / total_duration if total_duration > 0 else 0
            
            return {
                'avg_job_duration_minutes': round(avg_duration, 1),
                'avg_products_per_minute': round(avg_rate, 2)
            }
        except:
            return {'avg_job_duration_minutes': 0, 'avg_products_per_minute': 0}
    
    def print_dashboard(self, stats: Dict[str, Any]):
        """Print formatted dashboard"""
        # Clear screen
        print("\033[2J\033[H")
        
        # Header
        print("🏠 HomePro Scraping Monitor")
        print("=" * 80)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        # Jobs Overview
        jobs = stats['jobs']
        print("📋 JOBS OVERVIEW")
        print("-" * 40)
        print(f"Total Jobs:      {jobs['total']:,}")
        print(f"Active Jobs:     {jobs['active']:,} ({'🟢 RUNNING' if jobs['active'] > 0 else '⏸️  IDLE'})")
        print(f"Completed Jobs:  {jobs['completed']:,}")
        print(f"Failed Jobs:     {jobs['failed']:,}")
        print()
        
        # Products Overview
        products = stats['products']
        print("📦 PRODUCTS OVERVIEW")
        print("-" * 40)
        print(f"Stored in DB:    {products['total_stored']:,}")
        print(f"Total Discovered: {products['total_discovered']:,}")
        print(f"Successfully Scraped: {products['total_scraped']:,}")
        print(f"Failed:          {products['total_failed']:,}")
        print(f"Success Rate:    {products['success_rate']:.1f}%")
        print()
        
        # Recent Activity
        recent = stats['recent_24h']
        print("⏱️  LAST 24 HOURS")
        print("-" * 40)
        print(f"Jobs Run:        {recent['jobs']:,}")
        print(f"Products Scraped: {recent['success']:,}")
        print(f"Failed:          {recent['failed']:,}")
        print()
        
        # Performance
        rates = stats['rates']
        print("⚡ PERFORMANCE")
        print("-" * 40)
        print(f"Avg Job Duration: {rates['avg_job_duration_minutes']} minutes")
        print(f"Avg Rate:        {rates['avg_products_per_minute']} products/minute")
        print()
        
        # Running Jobs
        running_jobs = stats['running_jobs']
        if running_jobs:
            print("🔄 CURRENTLY RUNNING JOBS")
            print("-" * 40)
            for job in running_jobs[:5]:  # Show max 5
                job_type = job.get('job_type', 'unknown')
                total = job.get('total_items', 0)
                processed = job.get('processed_items', 0)
                success = job.get('success_items', 0)
                progress = (processed / total * 100) if total > 0 else 0
                
                print(f"Job {job['id'][:8]}... ({job_type})")
                print(f"  Progress: {processed:,}/{total:,} ({progress:.1f}%) | Success: {success:,}")
                
                if job.get('started_at'):
                    try:
                        started = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00'))
                        elapsed = datetime.now().replace(tzinfo=started.tzinfo) - started
                        print(f"  Running for: {elapsed}")
                    except:
                        pass
                print()
        else:
            print("🔄 CURRENTLY RUNNING JOBS")
            print("-" * 40)
            print("No jobs currently running")
            print()
        
        # Progress indicators
        if self.last_stats:
            self._print_changes(stats)
        
        self.last_stats = stats
        
        print("-" * 80)
        print(f"Auto-refresh in {self.refresh_interval}s | Press Ctrl+C to exit")
    
    def _print_changes(self, current_stats: Dict[str, Any]):
        """Print changes since last update"""
        try:
            last_products = self.last_stats['products']['total_stored']
            current_products = current_stats['products']['total_stored']
            
            if current_products > last_products:
                diff = current_products - last_products
                print(f"📈 NEW: +{diff:,} products added since last update")
                print()
        except:
            pass
    
    async def run_monitor(self):
        """Run continuous monitoring"""
        print("Starting HomePro Scraping Monitor...")
        print("Press Ctrl+C to exit")
        
        try:
            while True:
                stats = await self.get_current_stats()
                self.print_dashboard(stats)
                await asyncio.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")

async def show_summary():
    """Show one-time summary"""
    monitor = ScrapingMonitor()
    stats = await monitor.get_current_stats()
    monitor.print_dashboard(stats)

async def show_jobs():
    """Show detailed job information"""
    supabase = SupabaseService()
    jobs = await supabase.get_scrape_jobs(limit=20)
    
    print("📋 Recent Scraping Jobs")
    print("=" * 100)
    print(f"{'Job ID':<12} {'Type':<10} {'Status':<12} {'Items':<8} {'Success':<8} {'Failed':<8} {'Rate':<8} {'Created':<20}")
    print("-" * 100)
    
    for job in jobs:
        job_id = job['id'][:8] + "..."
        job_type = job.get('job_type', 'unknown')
        status = job['status']
        total = job.get('total_items', 0)
        success = job.get('success_items', 0)
        failed = job.get('failed_items', 0)
        rate = f"{(success/total*100):.1f}%" if total > 0 else "N/A"
        created = job['created_at'][:19] if job.get('created_at') else 'N/A'
        
        # Color coding
        status_color = {
            'completed': '✅',
            'running': '🔄',
            'failed': '❌',
            'pending': '⏳'
        }.get(status, '❓')
        
        print(f"{job_id:<12} {job_type:<10} {status_color} {status:<10} {total:<8} {success:<8} {failed:<8} {rate:<8} {created:<20}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='HomePro Scraping Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run continuous monitoring (refreshes every 10 seconds)
  python monitor_scraping.py watch
  
  # Run with custom refresh interval
  python monitor_scraping.py watch --interval 30
  
  # Show one-time summary
  python monitor_scraping.py summary
  
  # Show detailed job list
  python monitor_scraping.py jobs
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Continuous monitoring')
    watch_parser.add_argument('--interval', type=int, default=10, help='Refresh interval in seconds')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='One-time summary')
    
    # Jobs command
    jobs_parser = subparsers.add_parser('jobs', help='Show detailed job list')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'watch':
            monitor = ScrapingMonitor(refresh_interval=args.interval)
            asyncio.run(monitor.run_monitor())
        elif args.command == 'summary':
            asyncio.run(show_summary())
        elif args.command == 'jobs':
            asyncio.run(show_jobs())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()