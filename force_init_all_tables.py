#!/usr/bin/env python3

import asyncio
import os
import sys
sys.path.append('sensai-ai/src')

from api.db import (
    create_organizations_table, create_users_table, create_user_organizations_table,
    create_cohort_tables, create_courses_table, create_course_cohorts_table,
    create_tasks_table, create_questions_table, create_chat_history_table,
    create_task_completion_table, create_course_tasks_table, 
    create_course_milestones_table, create_milestones_table,
    create_scorecards_table, create_question_scorecards_table,
    create_course_generation_jobs_table, create_task_generation_jobs_table,
    create_code_drafts_table, create_org_api_keys_table
)
from api.utils.db import get_new_db_connection
from api.config import sqlite_db_path

async def force_create_all_tables():
    """Force create all required tables"""
    
    # Remove incomplete database
    db_path = 'sensai-ai/src/db/db.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed incomplete database: {db_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create all tables
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        tables_to_create = [
            ("organizations", create_organizations_table),
            ("org_api_keys", create_org_api_keys_table),
            ("users", create_users_table),
            ("user_organizations", create_user_organizations_table),
            ("milestones", create_milestones_table),
            ("cohorts", create_cohort_tables),
            ("courses", create_courses_table),
            ("course_cohorts", create_course_cohorts_table),
            ("tasks", create_tasks_table),
            ("questions", create_questions_table),
            ("scorecards", create_scorecards_table),
            ("question_scorecards", create_question_scorecards_table),
            ("chat_history", create_chat_history_table),
            ("task_completion", create_task_completion_table),
            ("course_tasks", create_course_tasks_table),
            ("course_milestones", create_course_milestones_table),
            ("course_generation_jobs", create_course_generation_jobs_table),
            ("task_generation_jobs", create_task_generation_jobs_table),
            ("code_drafts", create_code_drafts_table),
        ]
        
        for table_name, create_func in tables_to_create:
            try:
                print(f"Creating {table_name} table...")
                await create_func(cursor)
            except Exception as e:
                print(f"Error creating {table_name}: {e}")
        
        await conn.commit()
        print("✅ All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(force_create_all_tables())
