#!/usr/bin/env python3
"""
Migration script to add merge tracking fields to jobs table
Run this on PythonAnywhere to update the database schema
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/boykomobil2000/pythonanywherededuplicatoin')

from src.settings import DB
from src.queue_db import get_conn

def run_migration():
    """Run the database migration"""
    print("🔄 Running migration: add_merge_tracking.sql")
    
    try:
        conn = get_conn(DB)
        
        # Read the migration SQL
        with open('scripts/add_merge_tracking.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        with conn.cursor() as cur:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                print(f"   Executing: {statement[:50]}...")
                cur.execute(statement)
        
        conn.close()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Database schema updated!")
        print("   - Added initial_found_record_ids column")
        print("   - Added new_merged_record_id column")
        print("   - Added merge_count column")
        print("   - Added index for unique_identifier")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
