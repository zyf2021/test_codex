from __future__ import annotations

"""SQLite-слой хранения с CRUD-операциями сессий, задач и настроек."""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
MAX_TASKS = 5


@dataclass(frozen=True)
class SessionRow:
    id: int
    started_at: str
    duration_sec: int
    theme: str
    success: bool
    coins_earned: int


@dataclass(frozen=True)
class TaskRow:
    id: int
    title: str
    is_done: bool
    sort_order: int
    created_at: str


@dataclass(frozen=True)
class InventoryRow:
    id: int
    type: str
    code: str
    is_unlocked: bool
    unlocked_at: str | None


class Storage:
    """Инкапсулирует подключение к SQLite и транзакционные операции."""
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.DatabaseError:
            pass
        return conn

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Создает все таблицы приложения при первом запуске."""
        with self._transaction() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if not row:
                conn.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT,
                    duration_sec INTEGER,
                    theme TEXT,
                    success INTEGER,
                    coins_earned INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    is_done INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    code TEXT NOT NULL,
                    is_unlocked INTEGER NOT NULL DEFAULT 0,
                    unlocked_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings(
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_tasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    task_title TEXT NOT NULL,
                    is_done INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        raw = row["value"]
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return raw

    def set_setting(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, payload),
            )

    def get_coins_balance(self) -> int:
        return int(self.get_setting("coins_balance", 0) or 0)

    def set_coins_balance(self, value: int) -> None:
        self.set_setting("coins_balance", int(value))

    def insert_session(
        self,
        started_at: str,
        duration_sec: int,
        theme: str,
        success: bool,
        coins_earned: int,
    ) -> int:
        with self._transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO sessions(started_at, duration_sec, theme, success, coins_earned)
                VALUES (?, ?, ?, ?, ?)
                """,
                (started_at, duration_sec, theme, int(success), coins_earned),
            )
            return int(cursor.lastrowid)

    def list_sessions(self, limit: int = 100) -> list[SessionRow]:
        """Возвращает последние сессии в обратном хронологическом порядке."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, started_at, duration_sec, theme, success, coins_earned FROM sessions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            SessionRow(
                id=row["id"],
                started_at=row["started_at"],
                duration_sec=row["duration_sec"],
                theme=row["theme"],
                success=bool(row["success"]),
                coins_earned=row["coins_earned"],
            )
            for row in rows
        ]

    def list_tasks(self, limit: int = MAX_TASKS, include_done: bool = True) -> list[TaskRow]:
        """Возвращает задачи с сортировкой по ручному порядку."""
        query = "SELECT id, title, is_done, sort_order, created_at FROM tasks"
        params: tuple[Any, ...]
        if include_done:
            query += " ORDER BY sort_order ASC, created_at ASC LIMIT ?"
            params = (limit,)
        else:
            query += " WHERE is_done = 0 ORDER BY sort_order ASC, created_at ASC LIMIT ?"
            params = (limit,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            TaskRow(
                id=row["id"],
                title=row["title"],
                is_done=bool(row["is_done"]),
                sort_order=row["sort_order"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def create_task(self, title: str) -> int:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty")
        with self._transaction() as conn:
            count = conn.execute("SELECT COUNT(*) AS cnt FROM tasks").fetchone()["cnt"]
            if count >= MAX_TASKS:
                raise ValueError("Task limit reached")
            next_order_row = conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM tasks").fetchone()
            next_order = int(next_order_row["next_order"])
            created_at = datetime.now().isoformat(timespec="seconds")
            cursor = conn.execute(
                "INSERT INTO tasks(title, is_done, sort_order, created_at) VALUES (?, 0, ?, ?)",
                (clean_title, next_order, created_at),
            )
            return int(cursor.lastrowid)

    def delete_task(self, task_id: int) -> None:
        with self._transaction() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def set_task_done(self, task_id: int, is_done: bool) -> None:
        with self._transaction() as conn:
            conn.execute("UPDATE tasks SET is_done = ? WHERE id = ?", (int(is_done), task_id))

    def reorder_tasks(self, task_ids_in_order: list[int]) -> None:
        with self._transaction() as conn:
            for sort_order, task_id in enumerate(task_ids_in_order):
                conn.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (sort_order, task_id))

    def insert_session_tasks_snapshot(self, session_id: int, tasks: list[TaskRow]) -> None:
        with self._transaction() as conn:
            for sort_order, task in enumerate(tasks[:MAX_TASKS]):
                conn.execute(
                    """
                    INSERT INTO session_tasks(session_id, task_title, is_done, sort_order)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, task.title, int(task.is_done), sort_order),
                )

    # Backward-compatible wrappers
    def upsert_task(
        self,
        title: str,
        is_done: bool = False,
        sort_order: int = 0,
        task_id: int | None = None,
    ) -> int:
        if task_id is None:
            return self.create_task(title)
        with self._transaction() as conn:
            conn.execute(
                "UPDATE tasks SET title = ?, is_done = ?, sort_order = ? WHERE id = ?",
                (title, int(is_done), sort_order, task_id),
            )
        return task_id

    def toggle_task(self, task_id: int, is_done: bool) -> None:
        self.set_task_done(task_id, is_done)

    def list_inventory(self, type: str | None = None) -> list[InventoryRow]:
        with self._connect() as conn:
            if type is None:
                rows = conn.execute(
                    "SELECT id, type, code, is_unlocked, unlocked_at FROM inventory ORDER BY id ASC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, type, code, is_unlocked, unlocked_at FROM inventory WHERE type = ? ORDER BY id ASC",
                    (type,),
                ).fetchall()
        return [
            InventoryRow(
                id=row["id"],
                type=row["type"],
                code=row["code"],
                is_unlocked=bool(row["is_unlocked"]),
                unlocked_at=row["unlocked_at"],
            )
            for row in rows
        ]

    def unlock_item(self, type: str, code: str) -> None:
        unlocked_at = datetime.now().isoformat(timespec="seconds")
        with self._transaction() as conn:
            row = conn.execute("SELECT id FROM inventory WHERE type = ? AND code = ?", (type, code)).fetchone()
            if row:
                conn.execute(
                    "UPDATE inventory SET is_unlocked = 1, unlocked_at = ? WHERE id = ?",
                    (unlocked_at, row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO inventory(type, code, is_unlocked, unlocked_at) VALUES (?, ?, 1, ?)",
                    (type, code, unlocked_at),
                )
