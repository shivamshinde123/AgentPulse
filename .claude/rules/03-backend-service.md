# Backend Service (Python FastAPI)

## Overview

The backend service exposes REST APIs that the frontend dashboard consumes. It reads from the SQLite database (populated by monitor) and computes aggregated analytics.

**Location**: `backend/` directory  
**Language**: Python 3.9+  
**Framework**: FastAPI (async, high performance)  
**Server**: Uvicorn  
**Port**: 8000 (localhost:8000)

## Responsibilities

1. **Expose REST APIs** for sessions, metrics, and timeline data
2. **Perform aggregations** (acceptance rates, error statistics, trends)
3. **Enable filtering** (by date, language, session status)
4. **Compute quality scores** from raw code metrics
5. **Handle CORS** for frontend (localhost:5173)

## Architecture

```
main.py (FastAPI app init, CORS, health check)
├── api/
│   ├── sessions.py       (GET /api/sessions, /api/sessions/{id})
│   ├── metrics.py        (GET /api/metrics/quality, /metrics/errors, /metrics/acceptance)
│   └── timeline.py       (GET /api/timeline/session, /timeline/historical)
├── db/
│   ├── models.py         (SQLAlchemy ORM models - shared with monitor)
│   └── queries.py        (Database query functions)
└── utils/
    └── aggregations.py   (Statistical calculations, quality scoring)
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "claude-code-analyzer-backend"
version = "0.1.0"
description = "FastAPI backend for analytics"
requires-python = ">=3.9"

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

## Module Details

### 1. main.py - FastAPI App

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import sessions, metrics, timeline
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Claude Code Analyzer API",
    version="0.1.0",
    description="Analytics for Claude Code sessions"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# Include API routers
app.include_router(sessions.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
```

**Startup**:
```bash
cd backend && uv sync && uv run python src/main.py
# OR
cd backend && uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 2. api/sessions.py - Session Endpoints

```python
from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from db.queries import (
    get_all_sessions, get_session_with_interactions, 
    get_session_stats
)

router = APIRouter()

# Pydantic schemas
class SessionResponse(BaseModel):
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    language: str
    project_name: Optional[str]
    file_path: Optional[str]
    acceptance_rate: Optional[float]
    status: str
    interaction_count: int
    error_count: int

class InteractionResponse(BaseModel):
    id: str
    sequence_number: int
    timestamp: datetime
    human_prompt: str
    claude_response: str
    was_accepted: bool
    was_modified: bool
    modification_count: Optional[int]
    interaction_type: str

class SessionDetailResponse(SessionResponse):
    interactions: List[InteractionResponse]
    errors: List[dict]  # Error details

class SessionStatsResponse(BaseModel):
    total_sessions: int
    total_interactions: int
    avg_acceptance_rate: float
    languages: dict  # {python: 10, javascript: 5, ...}
    session_statuses: dict  # {completed: 8, abandoned: 2, ...}

# Endpoints

@router.get("/sessions", response_model=dict)
async def list_sessions(
    language: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),  # ISO format
    end_date: Optional[str] = Query(None),    # ISO format
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List all sessions with optional filtering.
    
    Query params:
    - language: filter by programming language (python, javascript, etc)
    - status: filter by status (completed, abandoned, in_progress)
    - start_date: ISO format (2025-01-15)
    - end_date: ISO format (2025-01-20)
    - limit: items per page (default 50, max 500)
    - offset: pagination offset (default 0)
    
    Returns:
    {
        "sessions": [SessionResponse, ...],
        "total_count": 100,
        "has_more": true
    }
    """
    filters = {
        "language": language,
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
    }
    
    sessions, total_count = get_all_sessions(filters, limit, offset)
    
    return {
        "sessions": [SessionResponse.from_orm(s) for s in sessions],
        "total_count": total_count,
        "has_more": offset + limit < total_count
    }

@router.get("/sessions/{session_id}", response_model=dict)
async def get_session_detail(session_id: str):
    """
    Get full details for a specific session.
    
    Includes:
    - Session metadata
    - All interactions
    - All errors
    - Code metrics summary
    
    Returns:
    {
        "session": SessionDetailResponse,
        "summary": {
            "total_interactions": 5,
            "acceptance_rate": 0.8,
            "error_count": 1,
            "avg_tokens_per_interaction": 150
        }
    }
    """
    session = get_session_with_interactions(session_id)
    
    if not session:
        return {"error": "Session not found"}, 404
    
    return {
        "session": SessionDetailResponse.from_orm(session),
        "summary": {
            "total_interactions": len(session.interactions),
            "acceptance_rate": session.acceptance_rate,
            "error_count": len(session.errors),
            "avg_tokens_per_interaction": calculate_avg_tokens(session)
        }
    }

@router.get("/sessions/stats/summary", response_model=SessionStatsResponse)
async def get_session_stats():
    """
    Get high-level statistics across all sessions.
    
    Returns:
    {
        "total_sessions": 25,
        "total_interactions": 120,
        "avg_acceptance_rate": 0.78,
        "languages": {"python": 15, "javascript": 8, "typescript": 2},
        "session_statuses": {"completed": 20, "abandoned": 3, "in_progress": 2}
    }
    """
    stats = get_session_stats()
    return stats
```

---

### 3. api/metrics.py - Metrics Endpoints

```python
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from db.queries import (
    get_quality_metrics, get_error_analysis, 
    get_acceptance_metrics
)
from utils.aggregations import (
    calculate_quality_score, detect_error_patterns,
    compute_rolling_average
)

router = APIRouter()

class MetricPoint(BaseModel):
    timestamp: datetime
    value: float

class QualityMetricsResponse(BaseModel):
    metrics: List[dict]  # [{timestamp, complexity, loc, quality_score, ...}]
    average_quality_score: float
    trend: str  # "improving", "declining", "stable"

class ErrorAnalysisResponse(BaseModel):
    error_distribution: Dict[str, int]  # {syntax: 10, runtime: 5, ...}
    most_common_error: str
    average_recovery_iterations: float
    recovery_rate: float  # % of errors resolved

class AcceptanceMetricsResponse(BaseModel):
    acceptance_rate: float
    by_language: Dict[str, float]
    by_interaction_type: Dict[str, float]
    trend: List[MetricPoint]  # Daily or weekly trend

# Endpoints

@router.get("/metrics/quality", response_model=QualityMetricsResponse)
async def get_quality_metrics(
    session_id: Optional[str] = Query(None),
    granularity: str = Query("interaction")  # interaction or session
):
    """
    Get code quality metrics over time.
    
    Query params:
    - session_id: filter to specific session (or all if not provided)
    - granularity: "interaction" (point per interaction) or "session" (point per session)
    
    Returns quality scores, complexity trends, etc.
    """
    metrics = get_quality_metrics(session_id, granularity)
    
    return QualityMetricsResponse(
        metrics=metrics,
        average_quality_score=calculate_average(metrics),
        trend=detect_trend(metrics)
    )

@router.get("/metrics/errors", response_model=ErrorAnalysisResponse)
async def get_error_metrics(
    session_id: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None)
):
    """
    Analyze errors across sessions.
    
    Query params:
    - session_id: filter to specific session
    - error_type: filter by error type (syntax, runtime, type, logic)
    - language: filter by language
    
    Returns error distribution, patterns, recovery stats.
    """
    errors = get_error_analysis(session_id, error_type, language)
    patterns = detect_error_patterns(errors)
    
    return ErrorAnalysisResponse(
        error_distribution=patterns["distribution"],
        most_common_error=patterns["most_common"],
        average_recovery_iterations=patterns["avg_recovery"],
        recovery_rate=patterns["recovery_rate"]
    )

@router.get("/metrics/acceptance", response_model=AcceptanceMetricsResponse)
async def get_acceptance_metrics(
    language: Optional[str] = Query(None),
    time_period: str = Query("all_time")  # last_7_days, last_30_days, all_time
):
    """
    Analyze acceptance rates.
    
    Query params:
    - language: filter by language
    - time_period: "last_7_days", "last_30_days", "all_time"
    
    Returns overall rate, breakdown by language/type, trends over time.
    """
    metrics = get_acceptance_metrics(language, time_period)
    trend = compute_rolling_average(metrics["daily_rates"], window=7)
    
    return AcceptanceMetricsResponse(
        acceptance_rate=metrics["overall"],
        by_language=metrics["by_language"],
        by_interaction_type=metrics["by_interaction_type"],
        trend=[MetricPoint(timestamp=t, value=v) for t, v in trend]
    )
```

---

### 4. api/timeline.py - Timeline Endpoints

```python
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime
from db.queries import (
    get_session_timeline, get_historical_timeline
)

router = APIRouter()

class TimelinePoint(BaseModel):
    sequence_number: int  # For session timeline
    timestamp: datetime
    interaction_type: str
    quality_score: Optional[float]
    error_count: int
    was_accepted: bool
    duration_ms: Optional[int]

class HistoricalPoint(BaseModel):
    date: str
    session_count: int
    avg_duration: int  # seconds
    avg_acceptance_rate: float
    error_count: int

# Endpoints

@router.get("/timeline/session/{session_id}", response_model=dict)
async def get_session_timeline(session_id: str):
    """
    Get interaction-by-interaction timeline for a specific session.
    
    Shows progression: when did quality improve/degrade, where did errors occur.
    
    Returns:
    {
        "timeline": [
            {
                "sequence_number": 1,
                "timestamp": "2025-01-15T10:30:00",
                "quality_score": 0.8,
                "error_count": 0,
                "was_accepted": true
            },
            ...
        ]
    }
    """
    timeline = get_session_timeline(session_id)
    
    return {
        "timeline": [TimelinePoint.from_orm(t) for t in timeline]
    }

@router.get("/timeline/historical", response_model=dict)
async def get_historical_timeline(
    granularity: str = Query("day"),  # day, week, month
    language: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Get historical timeline of sessions over time.
    
    Query params:
    - granularity: "day", "week", or "month"
    - language: filter by language
    - start_date, end_date: ISO format
    
    Shows trends: session count, avg duration, acceptance rate, errors per day.
    
    Returns:
    {
        "timeline": [
            {
                "date": "2025-01-15",
                "session_count": 3,
                "avg_duration": 1200,
                "avg_acceptance_rate": 0.82
            },
            ...
        ]
    }
    """
    timeline = get_historical_timeline(granularity, language, start_date, end_date)
    
    return {
        "timeline": [HistoricalPoint.from_orm(t) for t in timeline]
    }
```

---

### 5. db/queries.py - Database Queries

```python
from sqlalchemy import create_engine, select, func, and_
from sqlalchemy.orm import Session as SQLSession
from db.models import SessionModel, InteractionModel, ErrorModel, CodeMetricsModel
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict

class QueryManager:
    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
    
    def get_all_sessions(
        self, 
        filters: Dict, 
        limit: int = 50, 
        offset: int = 0
    ) -> Tuple[List[SessionModel], int]:
        """Get paginated sessions with filters."""
        with SQLSession(self.engine) as session:
            query = select(SessionModel)
            
            if filters.get("language"):
                query = query.where(SessionModel.language == filters["language"])
            if filters.get("status"):
                query = query.where(SessionModel.status == filters["status"])
            if filters.get("start_date"):
                start = datetime.fromisoformat(filters["start_date"])
                query = query.where(SessionModel.start_time >= start)
            if filters.get("end_date"):
                end = datetime.fromisoformat(filters["end_date"])
                query = query.where(SessionModel.start_time < end)
            
            total = session.query(func.count(SessionModel.id)).scalar()
            results = session.execute(query.offset(offset).limit(limit))
            sessions = results.scalars().all()
            
            return sessions, total
    
    def get_session_with_interactions(self, session_id: str) -> Optional[SessionModel]:
        """Get session with all interactions and errors eagerly loaded."""
        with SQLSession(self.engine) as session:
            result = session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            return result.scalar_one_or_none()
    
    def get_quality_metrics(
        self, 
        session_id: Optional[str], 
        granularity: str
    ) -> List[Dict]:
        """Get code quality metrics over time."""
        with SQLSession(self.engine) as session:
            query = select(CodeMetricsModel)
            
            if session_id:
                query = query.join(InteractionModel).where(
                    InteractionModel.session_id == session_id
                )
            
            results = session.execute(query)
            metrics = results.scalars().all()
            
            return [
                {
                    "timestamp": m.interaction.timestamp,
                    "complexity": m.cyclomatic_complexity,
                    "loc": m.lines_of_code,
                    "quality_score": m.code_quality_score
                }
                for m in metrics if m
            ]
    
    def get_error_analysis(
        self,
        session_id: Optional[str],
        error_type: Optional[str],
        language: Optional[str]
    ) -> List[ErrorModel]:
        """Get errors with optional filters."""
        with SQLSession(self.engine) as session:
            query = select(ErrorModel)
            
            if session_id:
                query = query.where(ErrorModel.session_id == session_id)
            if error_type:
                query = query.where(ErrorModel.error_type == error_type)
            if language:
                query = query.where(ErrorModel.language == language)
            
            results = session.execute(query)
            return results.scalars().all()
    
    def get_acceptance_metrics(
        self,
        language: Optional[str],
        time_period: str
    ) -> Dict:
        """Get acceptance rate metrics."""
        with SQLSession(self.engine) as session:
            query = select(InteractionModel)
            
            if language:
                query = query.join(SessionModel).where(SessionModel.language == language)
            
            if time_period == "last_7_days":
                cutoff = datetime.utcnow() - timedelta(days=7)
                query = query.where(InteractionModel.timestamp >= cutoff)
            elif time_period == "last_30_days":
                cutoff = datetime.utcnow() - timedelta(days=30)
                query = query.where(InteractionModel.timestamp >= cutoff)
            
            interactions = session.execute(query).scalars().all()
            
            if not interactions:
                return {
                    "overall": 0.0,
                    "by_language": {},
                    "by_interaction_type": {}
                }
            
            accepted = sum(1 for i in interactions if i.was_accepted)
            overall_rate = accepted / len(interactions) if interactions else 0
            
            # Group by language
            by_language = {}
            for language_group in set(i.session.language for i in interactions):
                lang_interactions = [i for i in interactions if i.session.language == language_group]
                lang_accepted = sum(1 for i in lang_interactions if i.was_accepted)
                by_language[language_group] = lang_accepted / len(lang_interactions)
            
            # Group by interaction type
            by_type = {}
            for type_group in set(i.interaction_type for i in interactions):
                type_interactions = [i for i in interactions if i.interaction_type == type_group]
                type_accepted = sum(1 for i in type_interactions if i.was_accepted)
                by_type[type_group] = type_accepted / len(type_interactions)
            
            return {
                "overall": overall_rate,
                "by_language": by_language,
                "by_interaction_type": by_type
            }
```

---

### 6. utils/aggregations.py - Statistical Functions

```python
from typing import List, Dict, Tuple
import statistics

def calculate_quality_score(
    cyclomatic_complexity: Optional[float],
    lines_of_code: Optional[int],
    has_type_hints: Optional[bool]
) -> float:
    """
    Calculate a 0-1 code quality score.
    
    Factors:
    - Lower complexity: better (1 - min(complexity, 10) / 10) * 0.4
    - Type hints present: +0.3
    - Shallow nesting: +0.3
    """
    score = 0.0
    
    if cyclomatic_complexity is not None:
        complexity_score = (1 - min(cyclomatic_complexity, 10) / 10) * 0.4
        score += complexity_score
    
    if has_type_hints:
        score += 0.3
    else:
        score += 0.1
    
    # Clamp to [0, 1]
    return max(0, min(1, score))

def detect_error_patterns(errors: List[Dict]) -> Dict:
    """
    Analyze error patterns.
    
    Returns:
    {
        "distribution": {syntax: 10, runtime: 5, ...},
        "most_common": "syntax",
        "avg_recovery": 2.3,
        "recovery_rate": 0.85
    }
    """
    if not errors:
        return {
            "distribution": {},
            "most_common": None,
            "avg_recovery": 0,
            "recovery_rate": 0
        }
    
    distribution = {}
    for error in errors:
        error_type = error.error_type
        distribution[error_type] = distribution.get(error_type, 0) + 1
    
    most_common = max(distribution, key=distribution.get) if distribution else None
    
    avg_recovery = statistics.mean([e.recovery_interactions_count for e in errors if e.recovery_interactions_count])
    recovery_rate = sum(1 for e in errors if e.was_resolved_in_next_interaction) / len(errors)
    
    return {
        "distribution": distribution,
        "most_common": most_common,
        "avg_recovery": avg_recovery,
        "recovery_rate": recovery_rate
    }

def compute_rolling_average(
    data: List[Tuple[datetime, float]],
    window: int = 5
) -> List[Tuple[datetime, float]]:
    """
    Compute rolling average of time-series data.
    
    Smooths trends over a window size.
    """
    if len(data) < window:
        return data
    
    result = []
    for i in range(len(data) - window + 1):
        window_values = [v for _, v in data[i:i+window]]
        avg = statistics.mean(window_values)
        result.append((data[i+window-1][0], avg))
    
    return result
```

---

## Running the Backend

```bash
cd backend
uv sync
uv run python src/main.py

# Or with auto-reload:
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

API will be available at `http://localhost:8000`  
API docs: `http://localhost:8000/docs` (Swagger UI)

---

## Environment Variables

Create `.env` file:
```
DATABASE_PATH=../data/sessions.db
API_PORT=8000
API_HOST=127.0.0.1
FRONTEND_ORIGIN=http://localhost:5173
```

---

## Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List all sessions
curl http://localhost:8000/api/sessions

# Get specific session
curl http://localhost:8000/api/sessions/{session_id}

# Get quality metrics
curl "http://localhost:8000/api/metrics/quality?session_id={session_id}"

# Get error analysis
curl http://localhost:8000/api/metrics/errors

# Get acceptance metrics
curl http://localhost:8000/api/metrics/acceptance
```
