#!/usr/bin/env python3
"""
Complete database setup script for SensAI with gamification system.
This script ensures ALL tables are created, including the new gamification tables.
"""

import sys
import os
import sqlite3
import asyncio
import aiosqlite
from datetime import datetime, timedelta, date

# Add the src directory to Python path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'sensai-ai', 'src'))

from api.config import (
    sqlite_db_path,
    # Existing tables
    users_table_name,
    organizations_table_name,
    user_organizations_table_name,
    milestones_table_name,
    cohorts_table_name,
    user_cohorts_table_name,
    courses_table_name,
    course_cohorts_table_name,
    tasks_table_name,
    questions_table_name,
    course_tasks_table_name,
    course_milestones_table_name,
    scorecards_table_name,
    question_scorecards_table_name,
    chat_history_table_name,
    task_completions_table_name,
    course_generation_jobs_table_name,
    task_generation_jobs_table_name,
    org_api_keys_table_name,
    code_drafts_table_name,
    # New gamification tables
    learning_sessions_table_name,
    weekly_quests_table_name,
    quest_completions_table_name,
    grace_tokens_table_name,
    leaderboard_cache_table_name,
)

async def create_all_tables_force():
    """Force create all tables including gamification ones"""
    
    print(f"🗄️ Connecting to database: {sqlite_db_path}")
    
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        print("📋 Creating ALL database tables (including gamification)...")
        
        # 1. Organizations table
        print("  🏢 Creating organizations table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {organizations_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Org API Keys table
        print("  🔐 Creating org_api_keys table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {org_api_keys_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                api_key_name TEXT NOT NULL,
                encrypted_api_key TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                UNIQUE(org_id, api_key_name)
            )
        """)
        
        # 3. Users table
        print("  👤 Creating users table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {users_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                default_dp_color TEXT DEFAULT '#3B82F6',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. User Organizations table
        print("  🔗 Creating user_organizations table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {user_organizations_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                UNIQUE(user_id, org_id)
            )
        """)
        
        # 5. Milestones table
        print("  🎯 Creating milestones table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {milestones_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#3B82F6',
                org_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 6. Cohorts table
        print("  👥 Creating cohorts table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                org_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 7. User Cohorts table
        print("  🔗 Creating user_cohorts table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {user_cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cohort_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'learner',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE,
                UNIQUE(user_id, cohort_id)
            )
        """)
        
        # 8. Courses table
        print("  📚 Creating courses table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {courses_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                org_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 9. Course Cohorts table
        print("  🔗 Creating course_cohorts table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {course_cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                cohort_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE,
                UNIQUE(course_id, cohort_id)
            )
        """)
        
        # 10. Tasks table
        print("  📝 Creating tasks table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {tasks_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                org_id INTEGER NOT NULL,
                milestone_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (milestone_id) REFERENCES {milestones_table_name}(id) ON DELETE SET NULL
            )
        """)
        
        # 11. Questions table
        print("  ❓ Creating questions table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {questions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 12. Course Tasks table
        print("  🔗 Creating course_tasks table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {course_tasks_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                task_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                UNIQUE(course_id, task_id)
            )
        """)
        
        # 13. Course Milestones table
        print("  🔗 Creating course_milestones table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {course_milestones_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                milestone_id INTEGER NOT NULL,
                milestone_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (milestone_id) REFERENCES {milestones_table_name}(id) ON DELETE CASCADE,
                UNIQUE(course_id, milestone_id)
            )
        """)
        
        # 14. Scorecards table
        print("  📊 Creating scorecards table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {scorecards_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                org_id INTEGER NOT NULL,
                criteria TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 15. Question Scorecards table
        print("  🔗 Creating question_scorecards table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {question_scorecards_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                scorecard_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (scorecard_id) REFERENCES {scorecards_table_name}(id) ON DELETE CASCADE,
                UNIQUE(question_id, scorecard_id)
            )
        """)
        
        # 16. Chat History table
        print("  💬 Creating chat_history table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {chat_history_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                response_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_solved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 17. Task Completions table
        print("  ✅ Creating task_completions table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {task_completions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                question_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE,
                UNIQUE(user_id, task_id),
                UNIQUE(user_id, question_id)
            )
        """)
        
        # 18. Course Generation Jobs table (MISSING!)
        print("  🤖 Creating course_generation_jobs table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {course_generation_jobs_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                error_message TEXT,
                result_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 19. Task Generation Jobs table (MISSING!)
        print("  🤖 Creating task_generation_jobs table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {task_generation_jobs_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                error_message TEXT,
                result_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 20. Code Drafts table
        print("  💻 Creating code_drafts table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {code_drafts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # === NEW GAMIFICATION TABLES ===
        
        # 21. Learning Sessions table (NEW)
        print("  ⏱️ Creating learning_sessions table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {learning_sessions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                question_id INTEGER,
                session_start DATETIME NOT NULL,
                session_end DATETIME,
                total_minutes INTEGER DEFAULT 0,
                active_minutes INTEGER DEFAULT 0,
                interactions_count INTEGER DEFAULT 0,
                learning_velocity REAL DEFAULT 0.0,
                session_quality TEXT CHECK(session_quality IN ('high', 'medium', 'low')) DEFAULT 'medium',
                is_completed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 22. Weekly Quests table (NEW)
        print("  🎯 Creating weekly_quests table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {weekly_quests_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest_name TEXT NOT NULL,
                description TEXT NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                org_id INTEGER,
                cohort_id INTEGER,
                requirements TEXT NOT NULL,
                rewards TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 23. Quest Completions table (NEW)
        print("  ✅ Creating quest_completions table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {quest_completions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                progress TEXT NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at DATETIME,
                points_earned INTEGER DEFAULT 0,
                badges_earned TEXT,
                proof_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, quest_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (quest_id) REFERENCES {weekly_quests_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 24. Grace Tokens table (NEW)
        print("  🎫 Creating grace_tokens table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {grace_tokens_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_type TEXT NOT NULL CHECK(token_type IN ('session_extension', 'quest_retry', 'streak_save', 'quality_adjustment')),
                granted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                used_date DATETIME,
                reason TEXT NOT NULL,
                quest_id INTEGER,
                session_id INTEGER,
                is_used BOOLEAN DEFAULT FALSE,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (quest_id) REFERENCES {weekly_quests_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES {learning_sessions_table_name}(id) ON DELETE CASCADE
            )
        """)
        
        # 25. Leaderboard Cache table (NEW)
        print("  🏆 Creating leaderboard_cache table...")
        await cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {leaderboard_cache_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leaderboard_type TEXT NOT NULL CHECK(leaderboard_type IN ('course', 'cohort', 'topic', 'campus', 'global')),
                scope_id INTEGER,
                time_period TEXT NOT NULL CHECK(time_period IN ('weekly', 'monthly', 'all_time')),
                leaderboard_data TEXT NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                UNIQUE(leaderboard_type, scope_id, time_period)
            )
        """)
        
        # Create all indexes
        print("  📊 Creating indexes for performance...")
        
        # Learning sessions indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_user_id ON {learning_sessions_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_task_id ON {learning_sessions_table_name} (task_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_date ON {learning_sessions_table_name} (session_start)")
        
        # Weekly quests indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_weekly_quests_week ON {weekly_quests_table_name} (week_start, week_end)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_weekly_quests_org ON {weekly_quests_table_name} (org_id)")
        
        # Quest completions indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_quest_completions_user_id ON {quest_completions_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_quest_completions_quest_id ON {quest_completions_table_name} (quest_id)")
        
        # Grace tokens indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_grace_tokens_user_id ON {grace_tokens_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_grace_tokens_type ON {grace_tokens_table_name} (token_type)")
        
        # Leaderboard cache indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_type_scope ON {leaderboard_cache_table_name} (leaderboard_type, scope_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_updated ON {leaderboard_cache_table_name} (last_updated)")
        
        # Other important indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON {chat_history_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_chat_history_question_id ON {chat_history_table_name} (question_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_task_completions_user_id ON {task_completions_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_task_completions_task_id ON {task_completions_table_name} (task_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_code_drafts_user_id ON {code_drafts_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_code_drafts_question_id ON {code_drafts_table_name} (question_id)")
        
        await conn.commit()
        print("✅ All 25 tables created successfully!")


async def verify_all_tables():
    """Verify that all tables were created correctly"""
    
    print("\n🔍 Verifying all table creation...")
    
    all_tables = [
        # Existing tables
        organizations_table_name,
        org_api_keys_table_name,
        users_table_name,
        user_organizations_table_name,
        milestones_table_name,
        cohorts_table_name,
        user_cohorts_table_name,
        courses_table_name,
        course_cohorts_table_name,
        tasks_table_name,
        questions_table_name,
        course_tasks_table_name,
        course_milestones_table_name,
        scorecards_table_name,
        question_scorecards_table_name,
        chat_history_table_name,
        task_completions_table_name,
        course_generation_jobs_table_name,  # This was missing!
        task_generation_jobs_table_name,    # This was missing!
        code_drafts_table_name,
        # New gamification tables
        learning_sessions_table_name,
        weekly_quests_table_name,
        quest_completions_table_name,
        grace_tokens_table_name,
        leaderboard_cache_table_name
    ]
    
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        missing_tables = []
        existing_tables = []
        
        for table_name in all_tables:
            # Check if table exists
            await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            result = await cursor.fetchone()
            
            if result:
                existing_tables.append(table_name)
                print(f"  ✅ {table_name}")
            else:
                missing_tables.append(table_name)
                print(f"  ❌ {table_name} - MISSING")
        
        print(f"\n📊 Summary:")
        print(f"  ✅ Existing tables: {len(existing_tables)}")
        print(f"  ❌ Missing tables: {len(missing_tables)}")
        
        if missing_tables:
            print(f"  Missing: {', '.join(missing_tables)}")
        
        return len(missing_tables) == 0


async def create_sample_quest():
    """Create a sample weekly quest for testing"""
    
    print("\n🎯 Creating sample weekly quest...")
    
    # Calculate this week's date range
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    quest_data = {
        'quest_name': 'Active Learner Challenge',
        'description': 'Complete 120 active learning minutes, 3 DP passes, and 1 peer review',
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'org_id': None,  # Global quest
        'cohort_id': None,  # Global quest
        'requirements': '{"active_minutes": 120, "dp_passes": 3, "peer_reviews": 1, "session_quality": 0.8}',
        'rewards': '{"points": 500, "badges": ["Active Learner"], "grace_tokens": 2, "leaderboard_boost": 0.1}'
    }
    
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        # Check if quest already exists for this week
        await cursor.execute(f"""
            SELECT id FROM {weekly_quests_table_name} 
            WHERE week_start = ? AND week_end = ? AND quest_name = ?
        """, (quest_data['week_start'], quest_data['week_end'], quest_data['quest_name']))
        
        existing = await cursor.fetchone()
        
        if existing:
            print(f"  ℹ️ Quest already exists for this week (ID: {existing[0]})")
        else:
            await cursor.execute(f"""
                INSERT INTO {weekly_quests_table_name} 
                (quest_name, description, week_start, week_end, org_id, cohort_id, requirements, rewards)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quest_data['quest_name'],
                quest_data['description'], 
                quest_data['week_start'],
                quest_data['week_end'],
                quest_data['org_id'],
                quest_data['cohort_id'],
                quest_data['requirements'],
                quest_data['rewards']
            ))
            
            await conn.commit()
            quest_id = cursor.lastrowid
            print(f"  ✅ Sample quest created with ID: {quest_id}")
            print(f"     📅 Week: {quest_data['week_start']} to {quest_data['week_end']}")


async def main():
    """Main function to set up complete database"""
    
    print("🎮 SensAI Complete Database Setup (Including Gamification)")
    print("=" * 60)
    
    try:
        # Check if database file exists
        if not os.path.exists(sqlite_db_path):
            print(f"❌ Database file not found: {sqlite_db_path}")
            print("   Make sure the backend Docker container is running!")
            return
        
        # Force create all tables
        await create_all_tables_force()
        
        # Verify all tables
        all_created = await verify_all_tables()
        
        if all_created:
            # Create sample quest
            await create_sample_quest()
            
            print("\n🎉 Complete database setup successful!")
            print("✅ All 25 tables created (20 existing + 5 gamification)")
            print("🚀 Backend should now start without errors!")
            print("🎯 Gamification system ready for testing!")
        else:
            print("\n❌ Some tables are still missing - check errors above")
        
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
