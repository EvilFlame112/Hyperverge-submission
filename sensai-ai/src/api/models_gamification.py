"""
Gamification models for the active learning tracking system.
These models handle sessions, quests, leaderboards, and grace tokens.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum


# ================================
# Session Quality and Tracking
# ================================

class SessionQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"


class LearningSession(BaseModel):
    id: Optional[int] = None
    user_id: int
    task_id: Optional[int] = None
    question_id: Optional[int] = None
    session_start: datetime
    session_end: Optional[datetime] = None
    total_minutes: int = 0
    active_minutes: int = 0
    interactions_count: int = 0
    learning_velocity: float = 0.0
    session_quality: SessionQuality = SessionQuality.MEDIUM
    is_completed: bool = False
    created_at: Optional[datetime] = None


class CreateSessionRequest(BaseModel):
    user_id: int
    task_id: Optional[int] = None
    question_id: Optional[int] = None


class UpdateSessionRequest(BaseModel):
    session_end: Optional[datetime] = None
    total_minutes: Optional[int] = None
    active_minutes: Optional[int] = None
    interactions_count: Optional[int] = None
    learning_velocity: Optional[float] = None
    session_quality: Optional[SessionQuality] = None
    is_completed: Optional[bool] = None


# ================================
# Quest System
# ================================

class QuestRequirements(BaseModel):
    active_minutes: int = 120
    dp_passes: int = 3
    peer_reviews: int = 1
    session_quality: float = 0.8  # Minimum average session quality
    consistency_days: int = 5     # Number of days to maintain activity


class QuestRewards(BaseModel):
    points: int = 500
    badges: List[str] = ["Active Learner"]
    grace_tokens: int = 2
    leaderboard_boost: float = 0.1  # 10% boost


class WeeklyQuest(BaseModel):
    id: Optional[int] = None
    quest_name: str
    description: str
    week_start: date
    week_end: date
    org_id: Optional[int] = None
    cohort_id: Optional[int] = None
    requirements: QuestRequirements
    rewards: QuestRewards
    is_active: bool = True
    created_at: Optional[datetime] = None


class CreateQuestRequest(BaseModel):
    quest_name: str
    description: str
    week_start: date
    week_end: date
    org_id: Optional[int] = None
    cohort_id: Optional[int] = None
    requirements: QuestRequirements
    rewards: QuestRewards


class QuestProgress(BaseModel):
    active_minutes: int = 0
    dp_passes: int = 0
    peer_reviews: int = 0
    avg_session_quality: float = 0.0
    consistency_days: int = 0
    completion_percentage: float = 0.0


class QuestCompletion(BaseModel):
    id: Optional[int] = None
    user_id: int
    quest_id: int
    progress: QuestProgress
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    points_earned: int = 0
    badges_earned: List[str] = []
    proof_data: Dict = {}
    created_at: Optional[datetime] = None


# ================================
# Grace Token System
# ================================

class GraceTokenType(str, Enum):
    SESSION_EXTENSION = "session_extension"
    QUEST_RETRY = "quest_retry"
    STREAK_SAVE = "streak_save"
    QUALITY_ADJUSTMENT = "quality_adjustment"


class GraceToken(BaseModel):
    id: Optional[int] = None
    user_id: int
    token_type: GraceTokenType
    granted_date: datetime
    used_date: Optional[datetime] = None
    reason: str
    quest_id: Optional[int] = None
    session_id: Optional[int] = None
    is_used: bool = False
    expires_at: Optional[datetime] = None


class GrantTokenRequest(BaseModel):
    user_id: int
    token_type: GraceTokenType
    reason: str
    quest_id: Optional[int] = None
    session_id: Optional[int] = None
    expires_days: int = 30


class UseTokenRequest(BaseModel):
    token_id: int
    usage_reason: str


# ================================
# Leaderboard System
# ================================

class LeaderboardType(str, Enum):
    COURSE = "course"
    COHORT = "cohort"
    TOPIC = "topic"
    CAMPUS = "campus"
    GLOBAL = "global"


class TimePeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class LeaderboardEntry(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    score: float
    rank: int
    active_minutes: int
    quests_completed: int
    streak_count: int
    session_quality_avg: float
    badges: List[str] = []


class LeaderboardData(BaseModel):
    leaderboard_type: LeaderboardType
    scope_id: Optional[int] = None
    time_period: TimePeriod
    entries: List[LeaderboardEntry]
    last_updated: datetime
    total_participants: int
    metadata: Dict = {}


class LeaderboardCache(BaseModel):
    id: Optional[int] = None
    leaderboard_type: LeaderboardType
    scope_id: Optional[int] = None
    time_period: TimePeriod
    leaderboard_data: LeaderboardData
    last_updated: datetime
    expires_at: datetime


# ================================
# Analytics and Metrics
# ================================

class ActiveLearningMetrics(BaseModel):
    total_active_minutes: int
    avg_session_quality: float
    total_sessions: int
    completed_quests: int
    current_streak: int
    grace_tokens_used: int
    grace_tokens_available: int
    weekly_progress: QuestProgress
    leaderboard_rankings: Dict[str, int] = {}  # leaderboard_type -> rank


class UserGamificationProfile(BaseModel):
    user_id: int
    total_points: int
    badges_earned: List[str]
    active_learning_metrics: ActiveLearningMetrics
    current_quests: List[QuestCompletion]
    grace_tokens: List[GraceToken]
    recent_sessions: List[LearningSession]


# ================================
# API Response Models
# ================================

class SessionResponse(BaseModel):
    session: LearningSession
    metrics_updated: bool = True


class QuestResponse(BaseModel):
    quest: WeeklyQuest
    user_progress: Optional[QuestCompletion] = None


class LeaderboardResponse(BaseModel):
    leaderboard: LeaderboardData
    user_rank: Optional[int] = None
    user_entry: Optional[LeaderboardEntry] = None


class TokenResponse(BaseModel):
    token: GraceToken
    remaining_tokens: int


class GamificationStatsResponse(BaseModel):
    profile: UserGamificationProfile
    recommendations: List[str] = []
    next_milestones: Dict[str, Union[str, int]] = {}


# ================================
# Anti-Cheat and Validation
# ================================

class InteractionQuality(BaseModel):
    content_length: int
    response_time_seconds: float
    interaction_type: str  # 'chat', 'code', 'navigation', 'completion'
    engagement_score: float  # 0.0 to 1.0
    suspicious_patterns: List[str] = []


class SessionValidation(BaseModel):
    session_id: int
    is_valid: bool
    quality_score: float
    flags: List[str] = []
    recommended_active_minutes: int
    time_adjustments: Dict[str, int] = {}


class AntiCheatAlert(BaseModel):
    user_id: int
    session_id: Optional[int] = None
    alert_type: str
    severity: str  # 'low', 'medium', 'high'
    description: str
    evidence: Dict = {}
    auto_resolved: bool = False
    review_required: bool = True
