"""Database query functions for the backend API."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession, joinedload, sessionmaker

from .models import (
    CodeMetricsModel,
    ErrorModel,
    InteractionModel,
    SessionModel,
)


class QueryManager:
    """Encapsulates all read queries the backend needs."""

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    # ── Sessions ──────────────────────────────────────────────────────────

    def get_all_sessions(
        self,
        filters: Dict,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Return paginated sessions with optional filters.

        Returns (list_of_session_dicts, total_count).
        """
        with self._session_factory() as db:
            query = select(SessionModel)
            count_query = select(func.count(SessionModel.id))

            conditions = self._build_session_filters(filters)
            for cond in conditions:
                query = query.where(cond)
                count_query = count_query.where(cond)

            total = db.execute(count_query).scalar() or 0

            query = query.order_by(SessionModel.start_time.desc())
            query = query.offset(offset).limit(limit)
            sessions = db.execute(query).scalars().all()

            result = []
            for s in sessions:
                interaction_count = (
                    db.execute(
                        select(func.count(InteractionModel.id)).where(
                            InteractionModel.session_id == s.id
                        )
                    ).scalar()
                    or 0
                )
                error_count = (
                    db.execute(
                        select(func.count(ErrorModel.id)).where(
                            ErrorModel.session_id == s.id
                        )
                    ).scalar()
                    or 0
                )
                result.append(
                    {
                        "id": s.id,
                        "start_time": s.start_time.isoformat() if s.start_time else None,
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "duration_seconds": s.duration_seconds,
                        "language": s.language,
                        "project_name": s.project_name,
                        "file_path": s.file_path,
                        "total_tokens_used": s.total_tokens_used,
                        "acceptance_rate": s.acceptance_rate,
                        "status": s.status,
                        "interaction_count": interaction_count,
                        "error_count": error_count,
                    }
                )

            return result, total

    def get_session_detail(self, session_id: str) -> Optional[Dict]:
        """Return full session detail including interactions, errors, and metrics."""
        with self._session_factory() as db:
            session = (
                db.execute(
                    select(SessionModel)
                    .options(
                        joinedload(SessionModel.interactions)
                        .joinedload(InteractionModel.metrics),
                        joinedload(SessionModel.interactions)
                        .joinedload(InteractionModel.errors),
                        joinedload(SessionModel.errors),
                    )
                    .where(SessionModel.id == session_id)
                )
                .unique()
                .scalar_one_or_none()
            )

            if session is None:
                return None

            interactions = sorted(
                session.interactions, key=lambda i: i.sequence_number
            )

            interaction_dicts = []
            for i in interactions:
                interaction_dicts.append(
                    {
                        "id": i.id,
                        "sequence_number": i.sequence_number,
                        "timestamp": i.timestamp.isoformat() if i.timestamp else None,
                        "human_prompt": i.human_prompt,
                        "claude_response": i.claude_response,
                        "response_length": i.response_length,
                        "was_accepted": i.was_accepted,
                        "was_modified": i.was_modified,
                        "modification_count": i.modification_count,
                        "tokens_used": i.tokens_used,
                        "interaction_type": i.interaction_type,
                    }
                )

            error_dicts = [
                {
                    "id": e.id,
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "language": e.language,
                    "severity": e.severity,
                    "was_resolved_in_next_interaction": e.was_resolved_in_next_interaction,
                    "recovery_interactions_count": e.recovery_interactions_count,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                }
                for e in session.errors
            ]

            # Compute avg tokens per interaction
            token_values = [
                i.tokens_used for i in interactions if i.tokens_used is not None
            ]
            avg_tokens = (
                round(sum(token_values) / len(token_values), 1) if token_values else 0
            )

            return {
                "session": {
                    "id": session.id,
                    "start_time": session.start_time.isoformat() if session.start_time else None,
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "duration_seconds": session.duration_seconds,
                    "language": session.language,
                    "project_name": session.project_name,
                    "file_path": session.file_path,
                    "total_tokens_used": session.total_tokens_used,
                    "acceptance_rate": session.acceptance_rate,
                    "status": session.status,
                    "interaction_count": len(interactions),
                    "error_count": len(error_dicts),
                    "interactions": interaction_dicts,
                    "errors": error_dicts,
                },
                "summary": {
                    "total_interactions": len(interactions),
                    "acceptance_rate": session.acceptance_rate,
                    "error_count": len(error_dicts),
                    "avg_tokens_per_interaction": avg_tokens,
                },
            }

    def get_session_stats(self) -> Dict:
        """Return high-level statistics across all sessions."""
        with self._session_factory() as db:
            total_sessions = (
                db.execute(select(func.count(SessionModel.id))).scalar() or 0
            )
            total_interactions = (
                db.execute(select(func.count(InteractionModel.id))).scalar() or 0
            )

            avg_acceptance = (
                db.execute(
                    select(func.avg(SessionModel.acceptance_rate)).where(
                        SessionModel.acceptance_rate.isnot(None)
                    )
                ).scalar()
                or 0.0
            )

            # Language breakdown
            lang_rows = db.execute(
                select(SessionModel.language, func.count(SessionModel.id))
                .group_by(SessionModel.language)
            ).all()
            languages = {row[0]: row[1] for row in lang_rows}

            # Status breakdown
            status_rows = db.execute(
                select(SessionModel.status, func.count(SessionModel.id))
                .group_by(SessionModel.status)
            ).all()
            session_statuses = {row[0]: row[1] for row in status_rows}

            return {
                "total_sessions": total_sessions,
                "total_interactions": total_interactions,
                "avg_acceptance_rate": round(float(avg_acceptance), 4),
                "languages": languages,
                "session_statuses": session_statuses,
            }

    # ── Metrics ───────────────────────────────────────────────────────────

    def get_quality_metrics(
        self,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """Return code quality metrics, optionally scoped to a session."""
        with self._session_factory() as db:
            query = (
                select(CodeMetricsModel, InteractionModel.timestamp)
                .join(
                    InteractionModel,
                    CodeMetricsModel.interaction_id == InteractionModel.id,
                )
            )

            if session_id:
                query = query.where(InteractionModel.session_id == session_id)

            query = query.order_by(InteractionModel.timestamp)
            rows = db.execute(query).all()

            return [
                {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "cyclomatic_complexity": row.CodeMetricsModel.cyclomatic_complexity,
                    "lines_of_code": row.CodeMetricsModel.lines_of_code,
                    "function_count": row.CodeMetricsModel.function_count,
                    "class_count": row.CodeMetricsModel.class_count,
                    "max_nesting_depth": row.CodeMetricsModel.max_nesting_depth,
                    "has_type_hints": row.CodeMetricsModel.has_type_hints,
                    "code_quality_score": row.CodeMetricsModel.code_quality_score,
                    "language": row.CodeMetricsModel.language,
                }
                for row in rows
            ]

    def get_error_analysis(
        self,
        session_id: Optional[str] = None,
        error_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[Dict]:
        """Return errors with optional filters, as list of dicts."""
        with self._session_factory() as db:
            query = select(ErrorModel)

            if session_id:
                query = query.where(ErrorModel.session_id == session_id)
            if error_type:
                query = query.where(ErrorModel.error_type == error_type)
            if language:
                query = query.where(ErrorModel.language == language)

            query = query.order_by(ErrorModel.timestamp)
            errors = db.execute(query).scalars().all()

            return [
                {
                    "id": e.id,
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "language": e.language,
                    "severity": e.severity,
                    "was_resolved_in_next_interaction": e.was_resolved_in_next_interaction,
                    "recovery_interactions_count": e.recovery_interactions_count,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                }
                for e in errors
            ]

    def get_acceptance_metrics(
        self,
        language: Optional[str] = None,
        time_period: str = "all_time",
    ) -> Dict:
        """Compute acceptance rate metrics with breakdowns."""
        with self._session_factory() as db:
            query = (
                select(InteractionModel, SessionModel.language)
                .join(
                    SessionModel,
                    InteractionModel.session_id == SessionModel.id,
                )
            )

            if language:
                query = query.where(SessionModel.language == language)

            if time_period == "last_7_days":
                cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                query = query.where(InteractionModel.timestamp >= cutoff)
            elif time_period == "last_30_days":
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                query = query.where(InteractionModel.timestamp >= cutoff)

            rows = db.execute(query).all()

            if not rows:
                return {
                    "overall": 0.0,
                    "by_language": {},
                    "by_interaction_type": {},
                    "daily_rates": [],
                }

            interactions = [(row.InteractionModel, row.language) for row in rows]

            # Overall
            accepted = sum(1 for i, _ in interactions if i.was_accepted)
            overall = accepted / len(interactions)

            # By language
            by_language: Dict[str, List[bool]] = defaultdict(list)
            for i, lang in interactions:
                by_language[lang].append(i.was_accepted)
            by_language_rates = {
                lang: sum(vals) / len(vals)
                for lang, vals in by_language.items()
            }

            # By interaction type
            by_type: Dict[str, List[bool]] = defaultdict(list)
            for i, _ in interactions:
                by_type[i.interaction_type].append(i.was_accepted)
            by_type_rates = {
                t: sum(vals) / len(vals) for t, vals in by_type.items()
            }

            # Daily rates for trend chart
            daily: Dict[str, List[bool]] = defaultdict(list)
            for i, _ in interactions:
                if i.timestamp:
                    day = i.timestamp.strftime("%Y-%m-%d")
                    daily[day].append(i.was_accepted)
            daily_rates = sorted(
                [
                    (day, sum(vals) / len(vals))
                    for day, vals in daily.items()
                ]
            )

            return {
                "overall": round(overall, 4),
                "by_language": {k: round(v, 4) for k, v in by_language_rates.items()},
                "by_interaction_type": {k: round(v, 4) for k, v in by_type_rates.items()},
                "daily_rates": daily_rates,
            }

    # ── Timeline ──────────────────────────────────────────────────────────

    def get_session_timeline(self, session_id: str) -> List[Dict]:
        """Return interaction-by-interaction timeline for a session."""
        with self._session_factory() as db:
            interactions = (
                db.execute(
                    select(InteractionModel)
                    .options(
                        joinedload(InteractionModel.errors),
                        joinedload(InteractionModel.metrics),
                    )
                    .where(InteractionModel.session_id == session_id)
                    .order_by(InteractionModel.sequence_number)
                )
                .unique()
                .scalars()
                .all()
            )

            timeline = []
            for i in interactions:
                quality_score = None
                if i.metrics:
                    quality_score = i.metrics[0].code_quality_score

                timeline.append(
                    {
                        "sequence_number": i.sequence_number,
                        "timestamp": i.timestamp.isoformat() if i.timestamp else None,
                        "interaction_type": i.interaction_type,
                        "quality_score": quality_score,
                        "error_count": len(i.errors),
                        "was_accepted": i.was_accepted,
                        "tokens_used": i.tokens_used,
                    }
                )

            return timeline

    def get_historical_timeline(
        self,
        granularity: str = "day",
        language: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Return aggregated timeline of sessions over time."""
        with self._session_factory() as db:
            query = select(SessionModel)

            if language:
                query = query.where(SessionModel.language == language)
            if start_date:
                query = query.where(
                    SessionModel.start_time >= datetime.fromisoformat(start_date)
                )
            if end_date:
                query = query.where(
                    SessionModel.start_time < datetime.fromisoformat(end_date)
                )

            query = query.order_by(SessionModel.start_time)
            sessions = db.execute(query).scalars().all()

            if not sessions:
                return []

            # Group sessions by date bucket
            buckets: Dict[str, List[SessionModel]] = defaultdict(list)
            for s in sessions:
                if s.start_time is None:
                    continue
                if granularity == "week":
                    # ISO week start (Monday)
                    week_start = s.start_time - timedelta(
                        days=s.start_time.weekday()
                    )
                    key = week_start.strftime("%Y-%m-%d")
                elif granularity == "month":
                    key = s.start_time.strftime("%Y-%m-01")
                else:  # day
                    key = s.start_time.strftime("%Y-%m-%d")
                buckets[key].append(s)

            # Count errors per session
            error_counts: Dict[str, int] = {}
            session_ids = [s.id for s in sessions]
            if session_ids:
                rows = db.execute(
                    select(
                        ErrorModel.session_id,
                        func.count(ErrorModel.id),
                    )
                    .where(ErrorModel.session_id.in_(session_ids))
                    .group_by(ErrorModel.session_id)
                ).all()
                error_counts = {row[0]: row[1] for row in rows}

            timeline = []
            for date_key in sorted(buckets.keys()):
                bucket = buckets[date_key]
                durations = [
                    s.duration_seconds for s in bucket if s.duration_seconds is not None
                ]
                acceptance_rates = [
                    s.acceptance_rate for s in bucket if s.acceptance_rate is not None
                ]
                bucket_errors = sum(error_counts.get(s.id, 0) for s in bucket)

                timeline.append(
                    {
                        "date": date_key,
                        "session_count": len(bucket),
                        "avg_duration": (
                            round(sum(durations) / len(durations))
                            if durations
                            else 0
                        ),
                        "avg_acceptance_rate": (
                            round(
                                sum(acceptance_rates) / len(acceptance_rates), 4
                            )
                            if acceptance_rates
                            else 0.0
                        ),
                        "error_count": bucket_errors,
                    }
                )

            return timeline

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _build_session_filters(filters: Dict) -> list:
        """Convert a filter dict to a list of SQLAlchemy where-clauses."""
        conditions = []
        if filters.get("language"):
            conditions.append(SessionModel.language == filters["language"])
        if filters.get("status"):
            conditions.append(SessionModel.status == filters["status"])
        if filters.get("start_date"):
            conditions.append(
                SessionModel.start_time >= datetime.fromisoformat(filters["start_date"])
            )
        if filters.get("end_date"):
            conditions.append(
                SessionModel.start_time < datetime.fromisoformat(filters["end_date"])
            )
        return conditions
