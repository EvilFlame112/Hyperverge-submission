"""
API routes for the gamification system.
Handles sessions, quests, leaderboards, and grace tokens.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import traceback

from api.models_gamification import (
    CreateSessionRequest, UpdateSessionRequest, SessionResponse,
    CreateQuestRequest, QuestResponse, LeaderboardResponse,
    GrantTokenRequest, UseTokenRequest, TokenResponse,
    GamificationStatsResponse, UserGamificationProfile,
    LeaderboardType, TimePeriod, SessionQuality, GraceTokenType,
    LearningSession, WeeklyQuest, QuestCompletion, GraceToken
)

from api.db.gamification import (
    create_learning_session, update_learning_session, get_learning_session,
    get_user_active_sessions, get_user_session_metrics,
    create_weekly_quest, get_active_quests, get_user_quest_progress,
    update_quest_progress, calculate_quest_progress,
    grant_grace_token, get_user_grace_tokens, use_grace_token,
    calculate_leaderboard, cache_leaderboard, get_cached_leaderboard
)

router = APIRouter()


# ================================
# Learning Session Endpoints
# ================================

@router.post("/sessions/", response_model=SessionResponse)
async def start_learning_session(request: CreateSessionRequest) -> SessionResponse:
    """Start a new learning session for a user"""
    try:
        session_id = await create_learning_session(
            request.user_id, request.task_id, request.question_id
        )
        
        session = await get_learning_session(session_id)
        
        return SessionResponse(
            session=session,
            metrics_updated=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: int, request: UpdateSessionRequest) -> SessionResponse:
    """Update an existing learning session"""
    try:
        success = await update_learning_session(
            session_id=session_id,
            session_end=request.session_end,
            total_minutes=request.total_minutes,
            active_minutes=request.active_minutes,
            interactions_count=request.interactions_count,
            learning_velocity=request.learning_velocity,
            session_quality=request.session_quality,
            is_completed=request.is_completed
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = await get_learning_session(session_id)
        
        return SessionResponse(
            session=session,
            metrics_updated=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}", response_model=LearningSession)
async def get_session(session_id: int) -> LearningSession:
    """Get a specific learning session"""
    session = await get_learning_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/users/{user_id}/sessions/active", response_model=List[LearningSession])
async def get_user_active_sessions_endpoint(user_id: int) -> List[LearningSession]:
    """Get all active sessions for a user"""
    return await get_user_active_sessions(user_id)


@router.get("/users/{user_id}/sessions/metrics")
async def get_user_session_metrics_endpoint(
    user_id: int, 
    days: int = Query(7, description="Number of days to look back")
) -> Dict:
    """Get user's session metrics for the last N days"""
    return await get_user_session_metrics(user_id, days)


# ================================
# Weekly Quest Endpoints
# ================================

@router.post("/quests/", response_model=WeeklyQuest)
async def create_quest(request: CreateQuestRequest) -> WeeklyQuest:
    """Create a new weekly quest"""
    try:
        quest_id = await create_weekly_quest(
            quest_name=request.quest_name,
            description=request.description,
            week_start=request.week_start,
            week_end=request.week_end,
            requirements=request.requirements,
            rewards=request.rewards,
            org_id=request.org_id,
            cohort_id=request.cohort_id
        )
        
        # Return the created quest (we'd need to implement get_quest_by_id)
        quest = WeeklyQuest(
            id=quest_id,
            quest_name=request.quest_name,
            description=request.description,
            week_start=request.week_start,
            week_end=request.week_end,
            requirements=request.requirements,
            rewards=request.rewards,
            org_id=request.org_id,
            cohort_id=request.cohort_id,
            created_at=datetime.now()
        )
        
        return quest
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quests/active", response_model=List[WeeklyQuest])
async def get_active_quests_endpoint(
    org_id: Optional[int] = Query(None, description="Organization ID filter"),
    cohort_id: Optional[int] = Query(None, description="Cohort ID filter")
) -> List[WeeklyQuest]:
    """Get all active quests for the current week"""
    return await get_active_quests(org_id, cohort_id)


@router.get("/users/{user_id}/quests/{quest_id}/progress", response_model=QuestCompletion)
async def get_quest_progress(user_id: int, quest_id: int) -> QuestCompletion:
    """Get user's progress on a specific quest"""
    progress = await get_user_quest_progress(user_id, quest_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Quest progress not found")
    
    return progress


@router.post("/users/{user_id}/quests/{quest_id}/update-progress")
async def update_user_quest_progress(user_id: int, quest_id: int) -> Dict:
    """Update user's quest progress based on their recent activity"""
    try:
        # Get the quest details
        active_quests = await get_active_quests()
        quest = next((q for q in active_quests if q.id == quest_id), None)
        
        if not quest:
            raise HTTPException(status_code=404, detail="Quest not found")
        
        # Calculate current progress
        progress = await calculate_quest_progress(user_id, quest)
        
        # Update progress in database
        await update_quest_progress(user_id, quest_id, progress)
        
        # Check if quest is completed
        is_completed = progress.completion_percentage >= 1.0
        
        return {
            "quest_id": quest_id,
            "user_id": user_id,
            "progress": progress.dict(),
            "is_completed": is_completed,
            "updated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================================
# Grace Token Endpoints
# ================================

@router.post("/grace-tokens/", response_model=TokenResponse)
async def grant_token(request: GrantTokenRequest) -> TokenResponse:
    """Grant a grace token to a user"""
    try:
        token_id = await grant_grace_token(
            user_id=request.user_id,
            token_type=request.token_type,
            reason=request.reason,
            quest_id=request.quest_id,
            session_id=request.session_id,
            expires_days=request.expires_days
        )
        
        # Get the granted token details
        tokens = await get_user_grace_tokens(request.user_id, unused_only=False)
        token = next((t for t in tokens if t.id == token_id), None)
        
        # Count remaining tokens
        remaining_tokens = len(await get_user_grace_tokens(request.user_id, unused_only=True))
        
        return TokenResponse(
            token=token,
            remaining_tokens=remaining_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/grace-tokens", response_model=List[GraceToken])
async def get_user_tokens(
    user_id: int,
    unused_only: bool = Query(True, description="Only return unused tokens")
) -> List[GraceToken]:
    """Get user's grace tokens"""
    return await get_user_grace_tokens(user_id, unused_only)


@router.post("/grace-tokens/{token_id}/use")
async def use_token(token_id: int, request: UseTokenRequest) -> Dict:
    """Use a grace token"""
    try:
        success = await use_grace_token(token_id, request.usage_reason)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Token not found, already used, or expired"
            )
        
        return {
            "token_id": token_id,
            "used": True,
            "used_at": datetime.now(),
            "usage_reason": request.usage_reason
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================================
# Leaderboard Endpoints
# ================================

@router.get("/leaderboards/{leaderboard_type}", response_model=LeaderboardResponse)
async def get_leaderboard(
    leaderboard_type: LeaderboardType,
    time_period: TimePeriod = Query(TimePeriod.WEEKLY),
    scope_id: Optional[int] = Query(None, description="Scope ID (cohort, course, etc.)"),
    user_id: Optional[int] = Query(None, description="User ID to highlight in results"),
    limit: int = Query(100, description="Maximum number of entries")
) -> LeaderboardResponse:
    """Get leaderboard data for specified type and period"""
    try:
        # Try to get cached leaderboard first
        cached_data = await get_cached_leaderboard(leaderboard_type, time_period, scope_id)
        
        if cached_data:
            leaderboard_data = cached_data
        else:
            # Calculate fresh leaderboard
            leaderboard_data = await calculate_leaderboard(
                leaderboard_type, time_period, scope_id, limit
            )
            
            # Cache the results
            await cache_leaderboard(leaderboard_data, expires_hours=1)
        
        # Find user's rank and entry if user_id provided
        user_rank = None
        user_entry = None
        
        if user_id:
            for entry in leaderboard_data['entries']:
                if entry['user_id'] == user_id:
                    user_rank = entry['rank']
                    user_entry = entry
                    break
        
        return LeaderboardResponse(
            leaderboard=leaderboard_data,
            user_rank=user_rank,
            user_entry=user_entry
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leaderboards/types", response_model=List[str])
async def get_leaderboard_types() -> List[str]:
    """Get available leaderboard types"""
    return [t.value for t in LeaderboardType]


# ================================
# User Profile & Analytics
# ================================

@router.get("/users/{user_id}/gamification-profile", response_model=GamificationStatsResponse)
async def get_user_gamification_profile(user_id: int) -> GamificationStatsResponse:
    """Get comprehensive gamification profile for a user"""
    try:
        # Get session metrics
        session_metrics = await get_user_session_metrics(user_id, days=30)
        
        # Get active quests
        active_quests = await get_active_quests()
        user_quests = []
        
        for quest in active_quests:
            progress = await get_user_quest_progress(user_id, quest.id)
            if progress:
                user_quests.append(progress)
        
        # Get grace tokens
        grace_tokens = await get_user_grace_tokens(user_id, unused_only=False)
        available_tokens = await get_user_grace_tokens(user_id, unused_only=True)
        
        # Get recent sessions
        recent_sessions = await get_user_active_sessions(user_id)
        
        # TODO: Calculate badges, total points, and leaderboard rankings
        
        profile = UserGamificationProfile(
            user_id=user_id,
            total_points=0,  # TODO: Calculate from quests completed
            badges_earned=[],  # TODO: Calculate badges
            active_learning_metrics={
                'total_active_minutes': session_metrics['total_active_minutes'],
                'avg_session_quality': session_metrics['avg_quality_score'],
                'total_sessions': session_metrics['total_sessions'],
                'completed_quests': len([q for q in user_quests if q.is_completed]),
                'current_streak': 0,  # TODO: Get from existing streak system
                'grace_tokens_used': len([t for t in grace_tokens if t.is_used]),
                'grace_tokens_available': len(available_tokens),
                'weekly_progress': user_quests[0].progress if user_quests else {},
                'leaderboard_rankings': {}  # TODO: Get user's ranks
            },
            current_quests=user_quests,
            grace_tokens=available_tokens,
            recent_sessions=recent_sessions[:5]  # Last 5 sessions
        )
        
        # Generate recommendations
        recommendations = []
        if session_metrics['total_active_minutes'] < 60:
            recommendations.append("Aim for at least 60 active learning minutes this week")
        if session_metrics['avg_quality_score'] < 2.0:
            recommendations.append("Focus on deeper engagement to improve session quality")
        if not user_quests:
            recommendations.append("Join this week's quest to earn rewards and compete!")
        
        # Calculate next milestones
        next_milestones = {}
        if user_quests:
            current_progress = user_quests[0].progress
            next_milestones['next_quest_completion'] = f"{current_progress.completion_percentage * 100:.1f}%"
        
        return GamificationStatsResponse(
            profile=profile,
            recommendations=recommendations,
            next_milestones=next_milestones
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================================
# Admin & Management Endpoints
# ================================

@router.post("/admin/refresh-leaderboards")
async def refresh_all_leaderboards() -> Dict:
    """Refresh all cached leaderboards (admin endpoint)"""
    try:
        # This would be an admin-only endpoint in production
        refresh_count = 0
        
        for leaderboard_type in LeaderboardType:
            for time_period in TimePeriod:
                # Calculate and cache fresh leaderboard
                leaderboard_data = await calculate_leaderboard(leaderboard_type, time_period)
                await cache_leaderboard(leaderboard_data, expires_hours=2)
                refresh_count += 1
        
        return {
            "refreshed_count": refresh_count,
            "refreshed_at": datetime.now(),
            "message": "All leaderboards refreshed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/stats")
async def get_gamification_stats() -> Dict:
    """Get overall gamification system statistics (admin endpoint)"""
    try:
        # This would include overall system metrics
        # For now, return basic placeholder data
        return {
            "total_active_sessions": 0,  # TODO: Calculate
            "total_quests_completed": 0,  # TODO: Calculate
            "total_grace_tokens_granted": 0,  # TODO: Calculate
            "avg_session_quality": 0.0,  # TODO: Calculate
            "leaderboard_cache_hit_rate": 0.0,  # TODO: Calculate
            "last_updated": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
