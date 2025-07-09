#!/usr/bin/env python3
"""
Check the structure of existing product matches
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_structure():
    """Check structure of existing matches"""
    supabase = SupabaseService()
    
    # Get one sample match
    result = supabase.client.table('product_matches')\
        .select('*')\
        .limit(1)\
        .execute()
    
    if result.data:
        match = result.data[0]
        logger.info("Sample product match structure:")
        logger.info(json.dumps(match, indent=2, ensure_ascii=False))
        
        logger.info("\nColumns found:")
        for key in match.keys():
            logger.info(f"  - {key}: {type(match[key]).__name__}")
    else:
        logger.info("No matches found")

async def main():
    await check_structure()

if __name__ == "__main__":
    asyncio.run(main())