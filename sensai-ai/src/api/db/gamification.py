"""
Database operations for the gamification system.
Handles sessions, quests, leaderboards, and grace tokens.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta, timezone
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    learning_sessions_table_name,
    weekly_quests_table_name,
    quest_completions_table_name,
    grace_tokens_table_name,
    leaderboard_cache_table_name,
    users_table_name,
    tasks_table_name,
    questions_table_name,
    organizations_table_name,
    cohorts_table_name,
    user_cohorts_table_name
)
from api.models_gamification import (
    LearningSession, WeeklyQuest, QuestCompletion, GraceToken, 
    LeaderboardData, SessionQuality, GraceTokenType, LeaderboardType, TimePeriod,
    QuestRequirements, QuestRewards, QuestProgress
)


# ================================
# Learning Session Operations
# ================================

async def create_learning_session(user_id: int, task_id: Optional[int] = None, question_id: Optional[int] = None) -> int:
    """Create a new learning session"""
    session_start = datetime.now(timezone.utc)
    
    session_id = await execute_db_operation(
        f"""
        INSERT INTO {learning_sessions_table_name} 
        (user_id, task_id, question_id, session_start)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, task_id, question_id, session_start),
        return_lastrowid=True
    )
    
    return session_id


async def update_learning_session(
    session_id: int,
    session_end: Optional[datetime] = None,
    total_minutes: Optional[int] = None,
    active_minutes: Optional[int] = None,
    interactions_count: Optional[int] = None,
    learning_velocity: Optional[float] = None,
    session_quality: Optional[SessionQuality] = None,
    is_completed: Optional[bool] = None
) -> bool:
    """Update an existing learning session"""
    
    # Build dynamic update query
    updates = []
    params = []
    
    if session_end is not None:
        updates.append("session_end = ?")
        params.append(session_end)
    
    if total_minutes is not None:
        updates.append("total_minutes = ?")
        params.append(total_minutes)
    
    if active_minutes is not None:
        updates.append("active_minutes = ?")
        params.append(active_minutes)
    
    if interactions_count is not None:
        updates.append("interactions_count = ?")
        params.append(interactions_count)
    
    if learning_velocity is not None:
        updates.append("learning_velocity = ?")
        params.append(learning_velocity)
    
    if session_quality is not None:
        updates.append("session_quality = ?")
        params.append(session_quality.value)
    
    if is_completed is not None:
        updates.append("is_completed = ?")
        params.append(is_completed)
    
    if not updates:
        return False
    
    params.append(session_id)
    
    await execute_db_operation(
        f"""
        UPDATE {learning_sessions_table_name} 
        SET {', '.join(updates)}
        WHERE id = ?
        """,
        params
    )
    
    return True


async def get_learning_session(session_id: int) -> Optional[LearningSession]:
    """Get a learning session by ID"""
    result = await execute_db_operation(
        f"""
        SELECT id, user_id, task_id, question_id, session_start, session_end,
               total_minutes, active_minutes, interactions_count, learning_velocity,
               session_quality, is_completed, created_at
        FROM {learning_sessions_table_name}
        WHERE id = ?
        """,
        (session_id,),
        fetch_one=True
    )
    
    if not result:
        return None
    
    return LearningSession(
        id=result[0],
        user_id=result[1],
        task_id=result[2],
        question_id=result[3],
        session_start=result[4],
        session_end=result[5],
        total_minutes=result[6],
        active_minutes=result[7],
        interactions_count=result[8],
        learning_velocity=result[9],
        session_quality=SessionQuality(result[10]),
        is_completed=bool(result[11]),
        created_at=result[12]
    )


async def get_user_active_sessions(user_id: int) -> List[LearningSession]:
    """Get all active (uncompleted) sessions for a user"""
    results = await execute_db_operation(
        f"""
        SELECT id, user_id, task_id, question_id, session_start, session_end,
               total_minutes, active_minutes, interactions_count, learning_velocity,
               session_quality, is_completed, created_at
        FROM {learning_sessions_table_name}
        WHERE user_id = ? AND is_completed = 0
        ORDER BY session_start DESC
        """,
        (user_id,),
        fetch_all=True
    )
    
    return [
        LearningSession(
            id=row[0], user_id=row[1], task_id=row[2], question_id=row[3],
            session_start=row[4], session_end=row[5], total_minutes=row[6],
            active_minutes=row[7], interactions_count=row[8], learning_velocity=row[9],
            session_quality=SessionQuality(row[10]), is_completed=bool(row[11]),
            created_at=row[12]
        ) for row in results
    ]


async def get_user_session_metrics(user_id: int, days: int = 7) -> Dict:
    """Get user's session metrics for the last N days"""
    since_date = datetime.now() - timedelta(days=days)
    
    results = await execute_db_operation(
        f"""
        SELECT 
            COUNT(*) as total_sessions,
            SUM(active_minutes) as total_active_minutes,
            AVG(learning_velocity) as avg_velocity,
            AVG(CASE 
                WHEN session_quality = 'high' THEN 3.0
                WHEN session_quality = 'medium' THEN 2.0
                WHEN session_quality = 'low' THEN 1.0
            END) as avg_quality_score,
            COUNT(CASE WHEN is_completed = 1 THEN 1 END) as completed_sessions
        FROM {learning_sessions_table_name}
        WHERE user_id = ? AND session_start >= ?
        """,
        (user_id, since_date),
        fetch_one=True
    )
    
    if not results:
        return {
            'total_sessions': 0,
            'total_active_minutes': 0,
            'avg_velocity': 0.0,
            'avg_quality_score': 0.0,
            'completed_sessions': 0
        }
    
    return {
        'total_sessions': results[0] or 0,
        'total_active_minutes': results[1] or 0,
        'avg_velocity': results[2] or 0.0,
        'avg_quality_score': results[3] or 0.0,
        'completed_sessions': results[4] or 0
    }


# ================================
# Weekly Quest Operations
# ================================

async def create_weekly_quest(
    quest_name: str,
    description: str,
    week_start: date,
    week_end: date,
    requirements: QuestRequirements,
    rewards: QuestRewards,
    org_id: Optional[int] = None,
    cohort_id: Optional[int] = None
) -> int:
    """Create a new weekly quest"""
    
    quest_id = await execute_db_operation(
        f"""
        INSERT INTO {weekly_quests_table_name}
        (quest_name, description, week_start, week_end, org_id, cohort_id, requirements, rewards)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            quest_name, description, week_start, week_end, org_id, cohort_id,
            json.dumps(requirements.dict()), json.dumps(rewards.dict())
        ),
        return_lastrowid=True
    )
    
    return quest_id


async def get_active_quests(org_id: Optional[int] = None, cohort_id: Optional[int] = None) -> List[WeeklyQuest]:
    """Get all active quests for current week"""
    today = date.today()
    
    # Build query based on scope
    where_clause = "WHERE is_active = 1 AND ? BETWEEN week_start AND week_end"
    params = [today]
    
    if org_id is not None:
        where_clause += " AND (org_id = ? OR org_id IS NULL)"
        params.append(org_id)
    
    if cohort_id is not None:
        where_clause += " AND (cohort_id = ? OR cohort_id IS NULL)"
        params.append(cohort_id)
    
    results = await execute_db_operation(
        f"""
        SELECT id, quest_name, description, week_start, week_end, org_id, cohort_id,
               requirements, rewards, is_active, created_at
        FROM {weekly_quests_table_name}
        {where_clause}
        ORDER BY created_at DESC
        """,
        params,
        fetch_all=True
    )
    
    quests = []
    for row in results:
        quests.append(WeeklyQuest(
            id=row[0],
            quest_name=row[1],
            description=row[2],
            week_start=row[3],
            week_end=row[4],
            org_id=row[5],
            cohort_id=row[6],
            requirements=QuestRequirements(**json.loads(row[7])),
            rewards=QuestRewards(**json.loads(row[8])),
            is_active=bool(row[9]),
            created_at=row[10]
        ))
    
    return quests


async def get_user_quest_progress(user_id: int, quest_id: int) -> Optional[QuestCompletion]:
    """Get user's progress on a specific quest"""
    result = await execute_db_operation(
        f"""
        SELECT id, user_id, quest_id, progress, is_completed, completed_at,
               points_earned, badges_earned, proof_data, created_at
        FROM {quest_completions_table_name}
        WHERE user_id = ? AND quest_id = ?
        """,
        (user_id, quest_id),
        fetch_one=True
    )
    
    if not result:
        return None
    
    return QuestCompletion(
        id=result[0],
        user_id=result[1],
        quest_id=result[2],
        progress=QuestProgress(**json.loads(result[3])),
        is_completed=bool(result[4]),
        completed_at=result[5],
        points_earned=result[6],
        badges_earned=json.loads(result[7]) if result[7] else [],
        proof_data=json.loads(result[8]) if result[8] else {},
        created_at=result[9]
    )


async def update_quest_progress(user_id: int, quest_id: int, progress: QuestProgress) -> bool:
    """Update user's quest progress"""
    
    # Check if progress record exists
    existing = await get_user_quest_progress(user_id, quest_id)
    
    if existing:
        # Update existing record
        await execute_db_operation(
            f"""
            UPDATE {quest_completions_table_name}
            SET progress = ?, completion_percentage = ?
            WHERE user_id = ? AND quest_id = ?
            """,
            (json.dumps(progress.dict()), progress.completion_percentage, user_id, quest_id)
        )
    else:
        # Create new record
        await execute_db_operation(
            f"""
            INSERT INTO {quest_completions_table_name}
            (user_id, quest_id, progress)
            VALUES (?, ?, ?)
            """,
            (user_id, quest_id, json.dumps(progress.dict()))
        )
    
    return True


async def calculate_quest_progress(user_id: int, quest: WeeklyQuest) -> QuestProgress:
    """Calculate user's current progress on a quest based on their activity"""
    
    # Get user's activity for the quest week
    week_start = datetime.combine(quest.week_start, datetime.min.time())
    week_end = datetime.combine(quest.week_end, datetime.max.time())
    
    # Get session metrics for the week
    session_metrics = await execute_db_operation(
        f"""
        SELECT 
            SUM(active_minutes) as total_active_minutes,
            AVG(CASE 
                WHEN session_quality = 'high' THEN 3.0
                WHEN session_quality = 'medium' THEN 2.0
                WHEN session_quality = 'low' THEN 1.0
            END) as avg_quality_score,
            COUNT(DISTINCT DATE(session_start)) as consistency_days,
            COUNT(*) as total_sessions
        FROM {learning_sessions_table_name}
        WHERE user_id = ? AND session_start BETWEEN ? AND ?
        """,
        (user_id, week_start, week_end),
        fetch_one=True
    )
    
    active_minutes = session_metrics[0] or 0
    avg_quality = (session_metrics[1] or 0) / 3.0  # Normalize to 0-1
    consistency_days = session_metrics[2] or 0
    
    # TODO: Calculate DP passes and peer reviews from other tables
    dp_passes = 0  # Placeholder
    peer_reviews = 0  # Placeholder
    
    # Calculate completion percentage
    req = quest.requirements
    progress_scores = [
        min(1.0, active_minutes / req.active_minutes),
        min(1.0, dp_passes / req.dp_passes) if req.dp_passes > 0 else 1.0,
        min(1.0, peer_reviews / req.peer_reviews) if req.peer_reviews > 0 else 1.0,
        min(1.0, avg_quality / req.session_quality) if req.session_quality > 0 else 1.0,
        min(1.0, consistency_days / req.consistency_days) if req.consistency_days > 0 else 1.0
    ]
    
    completion_percentage = sum(progress_scores) / len(progress_scores)
    
    return QuestProgress(
        active_minutes=active_minutes,
        dp_passes=dp_passes,
        peer_reviews=peer_reviews,
        avg_session_quality=avg_quality,
        consistency_days=consistency_days,
        completion_percentage=completion_percentage
    )


# ================================
# Grace Token Operations
# ================================

async def grant_grace_token(
    user_id: int,
    token_type: GraceTokenType,
    reason: str,
    quest_id: Optional[int] = None,
    session_id: Optional[int] = None,
    expires_days: int = 30
) -> int:
    """Grant a grace token to a user"""
    
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    token_id = await execute_db_operation(
        f"""
        INSERT INTO {grace_tokens_table_name}
        (user_id, token_type, reason, quest_id, session_id, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, token_type.value, reason, quest_id, session_id, expires_at),
        return_lastrowid=True
    )
    
    return token_id


async def get_user_grace_tokens(user_id: int, unused_only: bool = True) -> List[GraceToken]:
    """Get user's grace tokens"""
    
    where_clause = "WHERE user_id = ?"
    params = [user_id]
    
    if unused_only:
        where_clause += " AND is_used = 0 AND (expires_at IS NULL OR expires_at > ?)"
        params.append(datetime.now())
    
    results = await execute_db_operation(
        f"""
        SELECT id, user_id, token_type, granted_date, used_date, reason,
               quest_id, session_id, is_used, expires_at
        FROM {grace_tokens_table_name}
        {where_clause}
        ORDER BY granted_date DESC
        """,
        params,
        fetch_all=True
    )
    
    return [
        GraceToken(
            id=row[0], user_id=row[1], token_type=GraceTokenType(row[2]),
            granted_date=row[3], used_date=row[4], reason=row[5],
            quest_id=row[6], session_id=row[7], is_used=bool(row[8]),
            expires_at=row[9]
        ) for row in results
    ]


async def use_grace_token(token_id: int, usage_reason: str) -> bool:
    """Use a grace token"""
    
    # Check if token exists and is unused
    token = await execute_db_operation(
        f"""
        SELECT id, is_used, expires_at
        FROM {grace_tokens_table_name}
        WHERE id = ?
        """,
        (token_id,),
        fetch_one=True
    )
    
    if not token or token[1]:  # Token doesn't exist or already used
        return False
    
    if token[2] and datetime.fromisoformat(token[2]) < datetime.now():  # Token expired
        return False
    
    # Mark token as used
    await execute_db_operation(
        f"""
        UPDATE {grace_tokens_table_name}
        SET is_used = 1, used_date = ?
        WHERE id = ?
        """,
        (datetime.now(), token_id)
    )
    
    return True


# ================================
# Leaderboard Operations
# ================================

async def calculate_leaderboard(
    leaderboard_type: LeaderboardType,
    time_period: TimePeriod,
    scope_id: Optional[int] = None,
    limit: int = 100
) -> LeaderboardData:
    """Calculate leaderboard data for specified type and period"""
    
    # Define time period
    now = datetime.now()
    if time_period == TimePeriod.WEEKLY:
        start_date = now - timedelta(days=7)
    elif time_period == TimePeriod.MONTHLY:
        start_date = now - timedelta(days=30)
    else:  # ALL_TIME
        start_date = datetime.min
    
    # Build query based on leaderboard type
    if leaderboard_type == LeaderboardType.COHORT:
        user_filter = f"""
        AND u.id IN (
            SELECT user_id FROM {user_cohorts_table_name} 
            WHERE cohort_id = ? AND role = 'learner'
        )
        """
        params = [start_date, scope_id] if scope_id else [start_date]
    else:
        # For other types, we'll need to implement specific logic
        user_filter = ""
        params = [start_date]
    
    # Calculate leaderboard entries
    results = await execute_db_operation(
        f"""
        SELECT 
            u.id,
            COALESCE(u.first_name || ' ' || u.last_name, u.email) as user_name,
            u.email,
            COALESCE(SUM(ls.active_minutes), 0) as total_active_minutes,
            COUNT(DISTINCT ls.id) as total_sessions,
            AVG(CASE 
                WHEN ls.session_quality = 'high' THEN 3.0
                WHEN ls.session_quality = 'medium' THEN 2.0
                WHEN ls.session_quality = 'low' THEN 1.0
                ELSE 2.0
            END) as avg_quality_score,
            COUNT(DISTINCT qc.id) as quests_completed
        FROM {users_table_name} u
        LEFT JOIN {learning_sessions_table_name} ls ON u.id = ls.user_id 
            AND ls.session_start >= ?
        LEFT JOIN {quest_completions_table_name} qc ON u.id = qc.user_id 
            AND qc.is_completed = 1 AND qc.completed_at >= ?
        WHERE 1=1 {user_filter}
        GROUP BY u.id, u.first_name, u.last_name, u.email
        HAVING total_active_minutes > 0
        ORDER BY total_active_minutes DESC, avg_quality_score DESC
        LIMIT ?
        """,
        params + [start_date, limit],
        fetch_all=True
    )
    
    # TODO: Add streak calculation and badge logic
    
    entries = []
    for rank, row in enumerate(results, 1):
        entries.append({
            'user_id': row[0],
            'user_name': row[1],
            'user_email': row[2],
            'score': row[3],  # Using active minutes as primary score
            'rank': rank,
            'active_minutes': row[3],
            'quests_completed': row[6],
            'streak_count': 0,  # TODO: Calculate from existing streak system
            'session_quality_avg': row[5] / 3.0 if row[5] else 0.0,  # Normalize to 0-1
            'badges': []  # TODO: Calculate badges
        })
    
    return {
        'leaderboard_type': leaderboard_type,
        'scope_id': scope_id,
        'time_period': time_period,
        'entries': entries,
        'last_updated': now,
        'total_participants': len(entries),
        'metadata': {}
    }


async def cache_leaderboard(leaderboard_data: Dict, expires_hours: int = 1) -> int:
    """Cache leaderboard data for performance"""
    
    expires_at = datetime.now() + timedelta(hours=expires_hours)
    
    cache_id = await execute_db_operation(
        f"""
        INSERT OR REPLACE INTO {leaderboard_cache_table_name}
        (leaderboard_type, scope_id, time_period, leaderboard_data, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            leaderboard_data['leaderboard_type'],
            leaderboard_data.get('scope_id'),
            leaderboard_data['time_period'],
            json.dumps(leaderboard_data),
            expires_at
        ),
        return_lastrowid=True
    )
    
    return cache_id


async def get_cached_leaderboard(
    leaderboard_type: LeaderboardType,
    time_period: TimePeriod,
    scope_id: Optional[int] = None
) -> Optional[Dict]:
    """Get cached leaderboard if still valid"""
    
    result = await execute_db_operation(
        f"""
        SELECT leaderboard_data
        FROM {leaderboard_cache_table_name}
        WHERE leaderboard_type = ? AND time_period = ? AND scope_id = ?
            AND expires_at > ?
        """,
        (leaderboard_type.value, time_period.value, scope_id, datetime.now()),
        fetch_one=True
    )
    
    if result:
        return json.loads(result[0])
    
    return None
