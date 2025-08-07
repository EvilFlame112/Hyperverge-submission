#!/usr/bin/env python3
"""
Test script to create and verify gamification tables in the database.
This script will add the new gamification tables to the existing database.
"""

import sys
import os
import sqlite3
import asyncio
import aiosqlite
from datetime import datetime, timedelta

# Add the src directory to Python path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'sensai-ai', 'src'))

from api.config import (
    sqlite_db_path,
    learning_sessions_table_name,
    weekly_quests_table_name, 
    quest_completions_table_name,
    grace_tokens_table_name,
    leaderboard_cache_table_name,
    users_table_name,
    tasks_table_name,
    questions_table_name,
    organizations_table_name,
    cohorts_table_name
)

async def create_gamification_tables():
    """Create the new gamification tables"""
    
    print(f"🗄️ Connecting to database: {sqlite_db_path}")
    
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        print("📋 Creating gamification tables...")
        
        # 1. Learning Sessions Table
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
        
        # Create indexes
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_user_id ON {learning_sessions_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_task_id ON {learning_sessions_table_name} (task_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_learning_sessions_date ON {learning_sessions_table_name} (session_start)")
        
        # 2. Weekly Quests Table
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
        
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_weekly_quests_week ON {weekly_quests_table_name} (week_start, week_end)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_weekly_quests_org ON {weekly_quests_table_name} (org_id)")
        
        # 3. Quest Completions Table
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
        
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_quest_completions_user_id ON {quest_completions_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_quest_completions_quest_id ON {quest_completions_table_name} (quest_id)")
        
        # 4. Grace Tokens Table
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
        
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_grace_tokens_user_id ON {grace_tokens_table_name} (user_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_grace_tokens_type ON {grace_tokens_table_name} (token_type)")
        
        # 5. Leaderboard Cache Table
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
        
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_type_scope ON {leaderboard_cache_table_name} (leaderboard_type, scope_id)")
        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_updated ON {leaderboard_cache_table_name} (last_updated)")
        
        await conn.commit()
        print("✅ All gamification tables created successfully!")


async def verify_tables():
    """Verify that all tables were created correctly"""
    
    print("\n🔍 Verifying table creation...")
    
    tables_to_check = [
        learning_sessions_table_name,
        weekly_quests_table_name,
        quest_completions_table_name,
        grace_tokens_table_name,
        leaderboard_cache_table_name
    ]
    
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        for table_name in tables_to_check:
            # Check if table exists
            await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            result = await cursor.fetchone()
            
            if result:
                print(f"  ✅ {table_name} - EXISTS")
                
                # Get table info to verify structure
                await cursor.execute(f"PRAGMA table_info({table_name})")
                columns = await cursor.fetchall()
                print(f"     📊 Columns: {len(columns)}")
                
                # Count rows (should be 0 for new tables)
                await cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = await cursor.fetchone()
                print(f"     📝 Rows: {count[0]}")
            else:
                print(f"  ❌ {table_name} - MISSING")


async def create_sample_quest():
    """Create a sample weekly quest for testing"""
    
    print("\n🎯 Creating sample weekly quest...")
    
    # Calculate this week's date range
    today = datetime.now().date()
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
    """Main function to run all tests"""
    
    print("🎮 SensAI Gamification Database Schema Test")
    print("=" * 50)
    
    try:
        # Check if database file exists
        if not os.path.exists(sqlite_db_path):
            print(f"❌ Database file not found: {sqlite_db_path}")
            print("   Make sure the backend Docker container is running!")
            return
        
        # Create tables
        await create_gamification_tables()
        
        # Verify tables
        await verify_tables()
        
        # Create sample quest
        await create_sample_quest()
        
        print("\n🎉 Database schema test completed successfully!")
        print("🚀 Gamification system ready for implementation!")
        
    except Exception as e:
        print(f"❌ Error during database schema test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
