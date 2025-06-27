"""
Test connections to Supabase and Firecrawl
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from supabase._async.client import create_client as create_async_client
from app.services.firecrawl_client import FirecrawlClient


async def test_supabase():
    """Test Supabase configuration"""
    print("\n🔍 Testing Supabase configuration...")
    try:
        settings = get_settings()
        if not settings.supabase_url:
            print("❌ SUPABASE_URL not configured")
            return False
        if not settings.supabase_anon_key:
            print("❌ SUPABASE_ANON_KEY not configured")
            return False
        if not settings.supabase_service_role_key:
            print("❌ SUPABASE_SERVICE_ROLE_KEY not configured")
            return False
            
        print(f"✅ Supabase configuration looks good!")
        print(f"   URL: {settings.supabase_url[:50]}...")
        print(f"   Keys configured: ✓")
        return True
    except Exception as e:
        print(f"❌ Supabase configuration error: {str(e)}")
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