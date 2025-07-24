#!/usr/bin/env python3
"""Minimal test of Firecrawl API with new API key"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.services.firecrawl_client import FirecrawlClient

async def test_minimal_scrape():
    """Test basic Firecrawl functionality with a simple URL"""
    print("Testing Firecrawl with new API key...")
    
    # Initialize client
    client = FirecrawlClient()
    print(f"✓ Client initialized")
    print(f"  API Key: {os.getenv('FIRECRAWL_API_KEY')[:10]}...")
    
    # Test with a simple, fast-loading page
    test_url = "https://www.thaiwatsadu.com/th"
    print(f"\nTesting with URL: {test_url}")
    
    try:
        # Scrape with the async method
        result = await client.scrape(test_url)
        
        if result:
            print("✓ Scraping successful!")
            
            # Show basic info
            if 'markdown' in result:
                content_length = len(result['markdown'])
                print(f"✓ Markdown content received: {content_length} characters")
                
                # Show first 500 characters
                preview = result['markdown'][:500]
                print(f"\nContent preview:\n{preview}...")
            
            if 'metadata' in result:
                print(f"\n✓ Metadata received:")
                metadata = result['metadata']
                for key in ['title', 'description', 'language', 'statusCode']:
                    if key in metadata:
                        print(f"  - {key}: {metadata[key]}")
                        
            # Check for links
            if 'links' in result:
                print(f"\n✓ Links found: {len(result['links'])}")
        else:
            print("✗ Scraping failed - no result returned")
            
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(test_minimal_scrape())