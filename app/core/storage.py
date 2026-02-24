from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class SessionRecord:
    created_at: str
    duration_seconds: int
    scene: str
    success: bool


class Storage:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    scene TEXT NOT NULL,
                    success INTEGER NOT NULL CHECK(success IN (0, 1))
                )
                """
            )

    def add_session(self, duration_seconds: int, scene: str, success: bool, created_at: str | None = None) -> None:
        created_at = created_at or datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (created_at, duration_seconds, scene, success) VALUES (?, ?, ?, ?)",
                (created_at, duration_seconds, scene, int(success)),
            )

    def recent_sessions(self, limit: int = 50) -> list[SessionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, duration_seconds, scene, success
                FROM sessions
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            SessionRecord(
                created_at=row["created_at"],
                duration_seconds=row["duration_seconds"],
                scene=row["scene"],
                success=bool(row["success"]),
            )
            for row in rows
        ]

    def successful_sessions_today(self) -> int:
        today = date.today().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM sessions
                WHERE success = 1 AND date(created_at) = ?
                """,
                (today,),
            ).fetchone()
        return int(row["c"] if row else 0)

    def current_streak_days(self) -> int:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT date(created_at) AS d
                FROM sessions
                WHERE success = 1
                ORDER BY d DESC
                """
            ).fetchall()
        if not rows:
            return 0

        success_days = {datetime.fromisoformat(row["d"]).date() for row in rows}
        cursor = date.today()
        streak = 0
        while cursor in success_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak
