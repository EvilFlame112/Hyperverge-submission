#!/usr/bin/env python3

import sqlite3
import asyncio
import os

# Add the src directory to the path so we can import from api
import sys
sys.path.append('src')

from api.db import init_db, create_course_generation_jobs_table, create_task_generation_jobs_table
from api.utils.db import get_new_db_connection

async def check_and_fix_database():
    """Check what tables exist and create missing ones"""
    
    # Check current tables
    db_path = 'src/db/db.sqlite'
    if not os.path.exists(db_path):
        print("Database doesn't exist. Creating new database...")
        await init_db()
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print("Current tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Check for missing tables
    required_tables = {
        'course_generation_jobs': create_course_generation_jobs_table,
        'task_generation_jobs': create_task_generation_jobs_table,
    }
    
    missing_tables = []
    for table_name in required_tables:
        if table_name not in tables:
            missing_tables.append(table_name)
    
    if missing_tables:
        print(f"\nMissing tables: {missing_tables}")
        print("Creating missing tables...")
        
        # Create missing tables
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            
            for table_name in missing_tables:
                print(f"Creating {table_name}...")
                await required_tables[table_name](cursor)
            
            await conn.commit()
        
        print("✅ Database fixed!")
    else:
        print("\n✅ All required tables exist!")

if __name__ == "__main__":
    asyncio.run(check_and_fix_database())
