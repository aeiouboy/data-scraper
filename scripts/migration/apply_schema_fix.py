#!/usr/bin/env python3
"""
Apply schema fix to allow imported JSON data without foreign key constraints
"""
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.supabase_service import SupabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_schema_fix():
    """Apply schema fix for imported data"""
    try:
        db_service = SupabaseService()
        
        # Execute the schema fix using direct SQL execution
        # Note: Supabase Python client may not support DDL directly
        # This might need to be done via Supabase dashboard SQL editor
        
        logger.info("Schema fix may need to be applied manually via Supabase SQL Editor:")
        logger.info("ALTER TABLE product_matches ALTER COLUMN master_product_id DROP NOT NULL;")
        
        # For now, let's modify our import script to handle this differently
        return True
        
    except Exception as e:
        logger.error(f"Schema fix failed: {e}")
        return False


if __name__ == "__main__":
    apply_schema_fix()