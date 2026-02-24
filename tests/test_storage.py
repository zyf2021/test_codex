from datetime import date, timedelta

from app.core.storage import Storage


def test_storage_write_read(tmp_path) -> None:
    storage = Storage(tmp_path / "test.db")
    storage.add_session(1500, "Forest", True, created_at="2026-01-10T10:00:00")
    rows = storage.recent_sessions()
    assert len(rows) == 1
    assert rows[0].scene == "Forest"
    assert rows[0].success is True


def test_streak_calculation(tmp_path) -> None:
    storage = Storage(tmp_path / "streak.db")
    today = date.today()
    storage.add_session(100, "Forest", True, created_at=f"{today.isoformat()}T09:00:00")
    storage.add_session(100, "Ice", True, created_at=f"{(today - timedelta(days=1)).isoformat()}T09:00:00")
    storage.add_session(100, "Flight", True, created_at=f"{(today - timedelta(days=2)).isoformat()}T09:00:00")
    assert storage.current_streak_days() == 3
