#!/usr/bin/env python3
"""
Master script to scrape all HomePro categories systematically
"""
import asyncio
import argparse
import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.scraper import HomeProScraper
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scrape_all_categories.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HomePro category definitions - Complete coverage of all 23 categories
HOMEPRO_CATEGORIES = {
    "LIG": {
        "name": "โคมไฟและหลอดไฟ (Lighting)",
        "url": "https://www.homepro.co.th/c/LIG",
        "priority": 1,  # Start with smaller category
        "estimated_products": 500
    },
    "PAI": {
        "name": "สีและอุปกรณ์ทาสี (Paint)",
        "url": "https://www.homepro.co.th/c/PAI", 
        "priority": 2,
        "estimated_products": 800
    },
    "BAT": {
        "name": "ห้องน้ำ (Bathroom)",
        "url": "https://www.homepro.co.th/c/BAT",
        "priority": 3,
        "estimated_products": 1200
    },
    "PLU": {
        "name": "งานระบบประปา (Plumbing)",
        "url": "https://www.homepro.co.th/c/PLU",
        "priority": 4,
        "estimated_products": 1500
    },
    "KIT": {
        "name": "ห้องครัวและอุปกรณ์ (Kitchen)",
        "url": "https://www.homepro.co.th/c/KIT",
        "priority": 5,
        "estimated_products": 2000
    },
    "SMA": {
        "name": "เครื่องใช้ไฟฟ้าขนาดเล็ก (Small Appliances)",
        "url": "https://www.homepro.co.th/c/SMA",
        "priority": 6,
        "estimated_products": 3000
    },
    "HHP": {
        "name": "จัดเก็บและของใช้ในบ้าน (Storage & Household)",
        "url": "https://www.homepro.co.th/c/HHP",
        "priority": 7,
        "estimated_products": 4000
    },
    "TVA": {
        "name": "ทีวี เครื่องเสียง เกม (TV, Audio, Gaming)",
        "url": "https://www.homepro.co.th/c/TVA",
        "priority": 8,
        "estimated_products": 5000
    },
    "FLO": {
        "name": "วัสดุปูพื้นและผนัง (Floor & Wall)",
        "url": "https://www.homepro.co.th/c/FLO",
        "priority": 9,
        "estimated_products": 6000
    },
    "FUR": {
        "name": "เฟอร์นิเจอร์และของแต่งบ้าน (Furniture & Decor)",
        "url": "https://www.homepro.co.th/c/FUR",
        "priority": 10,
        "estimated_products": 8000
    },
    "APP": {
        "name": "เครื่องใช้ไฟฟ้า (Appliances)",
        "url": "https://www.homepro.co.th/c/APP",
        "priority": 11,
        "estimated_products": 10000
    },
    # Additional 12 categories for complete coverage
    "CON": {
        "name": "วัสดุก่อสร้าง (Construction Materials)",
        "url": "https://www.homepro.co.th/c/CON",
        "priority": 12,
        "estimated_products": 3500
    },
    "ELT": {
        "name": "ระบบไฟฟ้าและความปลอดภัย (Electrical & Safety)",
        "url": "https://www.homepro.co.th/c/ELT",
        "priority": 13,
        "estimated_products": 2500
    },
    "DOW": {
        "name": "ประตูและหน้าต่าง (Doors & Windows)",
        "url": "https://www.homepro.co.th/c/DOW",
        "priority": 14,
        "estimated_products": 2000
    },
    "TOO": {
        "name": "เครื่องมือและฮาร์ดแวร์ (Tools & Hardware)",
        "url": "https://www.homepro.co.th/c/TOO",
        "priority": 15,
        "estimated_products": 4000
    },
    "OUT": {
        "name": "เฟอร์นิเจอร์นอกบ้านและสวน (Outdoor & Garden)",
        "url": "https://www.homepro.co.th/c/OUT",
        "priority": 16,
        "estimated_products": 2500
    },
    "BED": {
        "name": "ห้องนอนและเครื่องนอน (Bedroom & Bedding)",
        "url": "https://www.homepro.co.th/c/BED",
        "priority": 17,
        "estimated_products": 3000
    },
    "SPO": {
        "name": "กีฬาและการเดินทาง (Sports & Travel)",
        "url": "https://www.homepro.co.th/c/SPO",
        "priority": 18,
        "estimated_products": 1500
    },
    "BEA": {
        "name": "ความงามและดูแลตัว (Beauty & Personal Care)",
        "url": "https://www.homepro.co.th/c/BEA",
        "priority": 19,
        "estimated_products": 2000
    },
    "MOM": {
        "name": "แม่และเด็ก (Mother & Baby)",
        "url": "https://www.homepro.co.th/c/MOM",
        "priority": 20,
        "estimated_products": 1800
    },
    "HEA": {
        "name": "สุขภาพ (Health)",
        "url": "https://www.homepro.co.th/c/HEA",
        "priority": 21,
        "estimated_products": 1200
    },
    "PET": {
        "name": "อุปกรณ์สัตว์เลี้ยง (Pet Supplies)",
        "url": "https://www.homepro.co.th/c/PET",
        "priority": 22,
        "estimated_products": 1000
    },
    "ATM": {
        "name": "ยานยนต์ (Automotive)",
        "url": "https://www.homepro.co.th/c/ATM",
        "priority": 23,
        "estimated_products": 1500
    }
}

class ScrapingProgress:
    """Track scraping progress across all categories"""
    
    def __init__(self, save_file: str = "scraping_progress.json"):
        self.save_file = save_file
        self.progress = self.load_progress()
        
    def load_progress(self) -> Dict:
        """Load progress from file"""
        try:
            if Path(self.save_file).exists():
                with open(self.save_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load progress file: {e}")
        
        return {
            "started_at": None,
            "completed_categories": [],
            "current_category": None,
            "total_discovered": 0,
            "total_scraped": 0,
            "total_failed": 0,
            "category_results": {}
        }
    
    def save_progress(self):
        """Save progress to file"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.progress, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    def start_scraping(self):
        """Mark scraping as started"""
        self.progress["started_at"] = datetime.now().isoformat()
        self.save_progress()
    
    def start_category(self, category_code: str):
        """Mark category as started"""
        self.progress["current_category"] = category_code
        self.save_progress()
    
    def complete_category(self, category_code: str, results: Dict):
        """Mark category as completed"""
        self.progress["completed_categories"].append(category_code)
        self.progress["category_results"][category_code] = {
            **results,
            "completed_at": datetime.now().isoformat()
        }
        
        # Update totals
        self.progress["total_discovered"] += results.get("discovered", 0)
        self.progress["total_scraped"] += results.get("success", 0)
        self.progress["total_failed"] += results.get("failed", 0)
        
        if category_code == self.progress["current_category"]:
            self.progress["current_category"] = None
            
        self.save_progress()
    
    def get_remaining_categories(self) -> List[str]:
        """Get list of categories not yet completed"""
        completed = set(self.progress["completed_categories"])
        all_categories = set(HOMEPRO_CATEGORIES.keys())
        remaining = all_categories - completed
        
        # Sort by priority
        return sorted(remaining, key=lambda x: HOMEPRO_CATEGORIES[x]["priority"])
    
    def print_summary(self):
        """Print current progress summary"""
        total_categories = len(HOMEPRO_CATEGORIES)
        completed_categories = len(self.progress["completed_categories"])
        remaining = total_categories - completed_categories
        
        print(f"\n📊 SCRAPING PROGRESS SUMMARY")
        print(f"=" * 50)
        print(f"Categories: {completed_categories}/{total_categories} completed ({remaining} remaining)")
        print(f"Total Discovered: {self.progress['total_discovered']:,}")
        print(f"Total Scraped: {self.progress['total_scraped']:,}")
        print(f"Total Failed: {self.progress['total_failed']:,}")
        
        if self.progress['total_discovered'] > 0:
            success_rate = (self.progress['total_scraped'] / self.progress['total_discovered']) * 100
            print(f"Overall Success Rate: {success_rate:.1f}%")
        
        if self.progress["started_at"]:
            started = datetime.fromisoformat(self.progress["started_at"])
            elapsed = datetime.now() - started
            print(f"Elapsed Time: {elapsed}")
            
            if completed_categories > 0:
                avg_time_per_category = elapsed / completed_categories
                estimated_remaining = avg_time_per_category * remaining
                estimated_completion = datetime.now() + estimated_remaining
                print(f"Estimated Completion: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")

class CategoryScraper:
    """Enhanced category scraper with progress tracking"""
    
    def __init__(self, max_pages: int = 100, max_concurrent: int = 5, delay_between_categories: int = 30):
        self.scraper = HomeProScraper()
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.delay_between_categories = delay_between_categories
        self.progress = ScrapingProgress()
    
    async def scrape_single_category(self, category_code: str, category_info: Dict) -> Dict:
        """Scrape a single category with enhanced error handling"""
        print(f"\n🎯 Starting category: {category_info['name']}")
        print(f"   URL: {category_info['url']}")
        print(f"   Estimated products: {category_info['estimated_products']:,}")
        
        self.progress.start_category(category_code)
        
        start_time = time.time()
        
        try:
            # Scrape the category
            results = await self.scraper.scrape_category(
                category_url=category_info['url'],
                max_pages=self.max_pages,
                max_concurrent=self.max_concurrent
            )
            
            elapsed_time = time.time() - start_time
            results['elapsed_time_seconds'] = elapsed_time
            results['category_code'] = category_code
            results['category_name'] = category_info['name']
            
            # Log results
            print(f"\n✅ Category '{category_code}' completed!")
            print(f"   Discovered: {results['discovered']:,}")
            print(f"   Success: {results['success']:,}")
            print(f"   Failed: {results['failed']:,}")
            print(f"   Success Rate: {results['success_rate']:.1f}%")
            print(f"   Time: {elapsed_time/60:.1f} minutes")
            print(f"   Job ID: {results.get('job_id', 'N/A')}")
            
            self.progress.complete_category(category_code, results)
            return results
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_result = {
                'category_code': category_code,
                'category_name': category_info['name'],
                'discovered': 0,
                'success': 0,
                'failed': 0,
                'success_rate': 0,
                'elapsed_time_seconds': elapsed_time,
                'error': str(e)
            }
            
            logger.error(f"Category '{category_code}' failed: {str(e)}")
            print(f"\n❌ Category '{category_code}' failed: {str(e)}")
            
            self.progress.complete_category(category_code, error_result)
            return error_result
    
    async def scrape_all_categories(self, start_from: Optional[str] = None, categories: Optional[List[str]] = None):
        """Scrape all categories systematically"""
        print(f"\n🚀 Starting comprehensive HomePro scraping")
        print(f"Settings: max_pages={self.max_pages}, max_concurrent={self.max_concurrent}")
        
        self.progress.start_scraping()
        
        # Determine which categories to scrape
        if categories:
            remaining_categories = [cat for cat in categories if cat in HOMEPRO_CATEGORIES]
        else:
            remaining_categories = self.progress.get_remaining_categories()
        
        if start_from and start_from in remaining_categories:
            # Start from specific category
            start_index = remaining_categories.index(start_from)
            remaining_categories = remaining_categories[start_index:]
        
        print(f"Categories to scrape: {len(remaining_categories)}")
        for cat in remaining_categories:
            print(f"  - {cat}: {HOMEPRO_CATEGORIES[cat]['name']}")
        
        # Scrape each category
        all_results = []
        
        for i, category_code in enumerate(remaining_categories):
            category_info = HOMEPRO_CATEGORIES[category_code]
            
            print(f"\n" + "="*80)
            print(f"CATEGORY {i+1}/{len(remaining_categories)}: {category_code}")
            print(f"="*80)
            
            # Scrape the category
            result = await self.scrape_single_category(category_code, category_info)
            all_results.append(result)
            
            # Print current progress
            self.progress.print_summary()
            
            # Delay between categories (except for the last one)
            if i < len(remaining_categories) - 1:
                print(f"\n⏳ Waiting {self.delay_between_categories} seconds before next category...")
                await asyncio.sleep(self.delay_between_categories)
        
        # Final summary
        print(f"\n" + "="*80)
        print(f"🎉 ALL CATEGORIES COMPLETED!")
        print(f"="*80)
        self.progress.print_summary()
        
        return all_results

async def test_single_category(category_code: str = "LIG"):
    """Test scraping a single category"""
    if category_code not in HOMEPRO_CATEGORIES:
        print(f"❌ Invalid category code: {category_code}")
        print(f"Available categories: {list(HOMEPRO_CATEGORIES.keys())}")
        return
    
    scraper = CategoryScraper(max_pages=5, max_concurrent=3)  # Conservative settings for testing
    category_info = HOMEPRO_CATEGORIES[category_code]
    
    print(f"🧪 Testing single category scrape")
    result = await scraper.scrape_single_category(category_code, category_info)
    
    print(f"\n📋 Test Results:")
    print(json.dumps(result, indent=2, default=str))

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='HomePro Complete Category Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single category
  python scrape_all_categories.py test --category LIG
  
  # Scrape all categories (conservative)
  python scrape_all_categories.py all --max-pages 50 --max-concurrent 3
  
  # Scrape all categories (aggressive)
  python scrape_all_categories.py all --max-pages 200 --max-concurrent 8
  
  # Resume from specific category
  python scrape_all_categories.py all --start-from APP
  
  # Scrape specific categories only
  python scrape_all_categories.py all --categories LIG PAI BAT
  
  # Show current progress
  python scrape_all_categories.py progress
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test single category')
    test_parser.add_argument('--category', default='LIG', help='Category code to test')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Scrape all categories')
    all_parser.add_argument('--max-pages', type=int, default=100, help='Max pages per category')
    all_parser.add_argument('--max-concurrent', type=int, default=5, help='Max concurrent requests')
    all_parser.add_argument('--delay', type=int, default=30, help='Delay between categories (seconds)')
    all_parser.add_argument('--start-from', help='Start from specific category code')
    all_parser.add_argument('--categories', nargs='*', help='Scrape only specific categories')
    
    # Progress command
    progress_parser = subparsers.add_parser('progress', help='Show current progress')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'test':
            asyncio.run(test_single_category(args.category))
        elif args.command == 'all':
            scraper = CategoryScraper(
                max_pages=args.max_pages,
                max_concurrent=args.max_concurrent,
                delay_between_categories=args.delay
            )
            asyncio.run(scraper.scrape_all_categories(
                start_from=args.start_from,
                categories=args.categories
            ))
        elif args.command == 'progress':
            progress = ScrapingProgress()
            progress.print_summary()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Progress has been saved. Resume with: python scrape_all_categories.py all")
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()