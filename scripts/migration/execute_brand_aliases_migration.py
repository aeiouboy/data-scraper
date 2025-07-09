#!/usr/bin/env python3
"""
Execute the brand aliases migration SQL script
"""
import sys
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def execute_migration():
    """Execute the brand aliases migration"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found in environment variables")
        return False
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Read the SQL script
    sql_file = "scripts/add_brand_aliases_table.sql"
    if not os.path.exists(sql_file):
        print(f"❌ Error: SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    print("🚀 Executing brand aliases migration...")
    print("=" * 60)
    
    # Split SQL into individual statements
    # Remove comments and empty lines
    lines = sql_content.split('\n')
    clean_lines = []
    for line in lines:
        # Skip comment lines
        if line.strip().startswith('--') or not line.strip():
            continue
        clean_lines.append(line)
    
    # Join back and split by semicolon
    clean_sql = '\n'.join(clean_lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    # Execute each statement
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        try:
            # Skip if it's just whitespace
            if not statement.strip():
                continue
                
            print(f"\n📝 Executing statement {i}/{len(statements)}...")
            
            # For CREATE TABLE statements, we need to use RPC
            if 'CREATE TABLE' in statement.upper():
                print("   Creating table...")
            elif 'CREATE INDEX' in statement.upper():
                print("   Creating index...")
            elif 'INSERT INTO' in statement.upper():
                print("   Inserting data...")
            elif 'CREATE OR REPLACE FUNCTION' in statement.upper():
                print("   Creating function...")
            elif 'GRANT' in statement.upper():
                print("   Granting permissions...")
            elif 'UPDATE' in statement.upper():
                print("   Updating data...")
            elif 'CREATE OR REPLACE VIEW' in statement.upper():
                print("   Creating view...")
            
            # Execute using RPC
            result = supabase.rpc('exec_sql', {'query': statement + ';'}).execute()
            print("   ✅ Success")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            error_count += 1
            # Continue with other statements
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully executed: {success_count} statements")
    if error_count > 0:
        print(f"❌ Failed: {error_count} statements")
    print("=" * 60)
    
    # Verify the migration
    print("\n🔍 Verifying migration...")
    
    try:
        # Check if brand_aliases table exists
        result = supabase.table('brand_aliases').select('count').execute()
        print(f"✅ brand_aliases table created successfully")
        
        # Check if product_models table exists
        result = supabase.table('product_models').select('count').execute()
        print(f"✅ product_models table created successfully")
        
        # Check if match_history table exists
        result = supabase.table('match_history').select('count').execute()
        print(f"✅ match_history table created successfully")
        
    except Exception as e:
        print(f"⚠️  Warning during verification: {str(e)}")
    
    return success_count > 0

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)