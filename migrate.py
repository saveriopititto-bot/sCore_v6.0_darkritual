#!/usr/bin/env python3
"""
Migration Runner for sCore Database
Executes pending SQL migrations to fix schema issues
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from supabase import create_client
    from config import Config
    import logging
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Execute the v4.2 fix migration"""
    
    # Get Supabase credentials
    supabase_creds = Config.get_supabase_creds()
    if not supabase_creds.get('url') or not supabase_creds.get('key'):
        logger.error("❌ Supabase credentials not found in secrets")
        return False
    
    # Initialize Supabase client
    client = create_client(supabase_creds['url'], supabase_creds['key'])
    
    # Read migration SQL
    migration_path = Path(__file__).parent / "migrations" / "v4_2_fix_missing_columns.sql"
    if not migration_path.exists():
        logger.error(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    logger.info("🚀 Executing migration v4.2_fix_missing_columns...")
    
    try:
        # Execute SQL using Supabase RPC
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll need to use the REST API or create a SQL function
        
        # For now, let's try using raw SQL through postgrest
        response = client.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        logger.info("✅ Migration executed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        
        # Alternative: Try executing individual statements
        logger.info("🔄 Attempting to execute statements individually...")
        
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for stmt in statements:
            if stmt and not stmt.startswith('--'):
                try:
                    logger.info(f"Executing: {stmt[:100]}...")
                    # This would need to be adapted based on actual Supabase capabilities
                    # client.postgrest.rpc('exec_sql', {'sql': stmt}).execute()
                except Exception as stmt_e:
                    logger.error(f"Failed statement: {stmt_e}")
        
        return False

def check_schema():
    """Check current database schema"""
    
    supabase_creds = Config.get_supabase_creds()
    client = create_client(supabase_creds['url'], supabase_creds['key'])
    
    # Check runs table columns
    try:
        logger.info("🔍 Checking runs table schema...")
        runs_response = client.table('runs').select('*').limit(1).execute()
        if runs_response.data:
            columns = list(runs_response.data[0].keys())
            logger.info(f"Runs table columns: {columns}")
            
            if 'name' not in columns:
                logger.warning("❌ 'name' column missing from runs table")
            else:
                logger.info("✅ 'name' column exists in runs table")
        
    except Exception as e:
        logger.error(f"Error checking runs table: {e}")
    
    # Check athlete_baselines table columns  
    try:
        logger.info("🔍 Checking athlete_baselines table schema...")
        baselines_response = client.table('athlete_baselines').select('*').limit(1).execute()
        if baselines_response.data:
            columns = list(baselines_response.data[0].keys())
            logger.info(f"Athlete_baselines table columns: {columns}")
            
            if 'updated_at' not in columns:
                logger.warning("❌ 'updated_at' column missing from athlete_baselines table")
            else:
                logger.info("✅ 'updated_at' column exists in athlete_baselines table")
                
    except Exception as e:
        logger.error(f"Error checking athlete_baselines table: {e}")

if __name__ == "__main__":
    print("🔧 sCore Database Migration Runner")
    print("=" * 40)
    
    # First check current schema
    check_schema()
    
    # Then run migration
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        # Check schema again
        check_schema()
    else:
        print("\n❌ Migration failed. Please check the logs above.")
        sys.exit(1)