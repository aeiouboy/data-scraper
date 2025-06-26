"""
Test connections to Supabase and Firecrawl
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from supabase import create_client
from app.services.firecrawl_client import FirecrawlClient


async def test_supabase():
    """Test Supabase connection"""
    print("\n🔍 Testing Supabase connection...")
    try:
        settings = get_settings()
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        # Test query
        result = supabase.table("products").select("count", count="exact").execute()
        print(f"✅ Supabase connected! Products table has {result.count} records")
        return True
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return False


async def test_firecrawl():
    """Test Firecrawl API connection"""
    print("\n🔍 Testing Firecrawl API...")
    try:
        async with FirecrawlClient() as client:
            # Test with HomePro homepage
            result = await client.scrape("https://www.homepro.co.th")
            if result:
                print("✅ Firecrawl API connected and working!")
                return True
            else:
                print("⚠️  Firecrawl connected but no data returned")
                return False
    except Exception as e:
        print(f"❌ Firecrawl error: {str(e)}")
        return False


async def main():
    """Run all connection tests"""
    print("🚀 HomePro Scraper Connection Test")
    print("=" * 50)
    
    # Test Supabase
    supabase_ok = await test_supabase()
    
    # Test Firecrawl
    firecrawl_ok = await test_firecrawl()
    
    print("\n" + "=" * 50)
    if supabase_ok and firecrawl_ok:
        print("✅ All connections successful!")
        return 0
    else:
        print("❌ Some connections failed. Please check your .env file")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)