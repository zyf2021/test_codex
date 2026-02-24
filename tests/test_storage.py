from app.data.storage import Storage


def test_init_db_creates_tables(tmp_path) -> None:
    db = tmp_path / "app.db"
    storage = Storage(db)
    storage.init_db()
    assert db.exists()


def test_set_get_setting(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    storage.set_setting("volume", 0)
    assert storage.get_setting("volume") == 0
    assert storage.get_setting("missing", "x") == "x"


def test_insert_and_list_sessions(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    storage.insert_session("2026-01-01T10:00:00", 1500, "forest", True, 5)
    rows = storage.list_sessions()
    assert len(rows) == 1
    assert rows[0].theme == "forest"
    assert rows[0].coins_earned == 5


def test_task_add_and_toggle(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    task_id = storage.upsert_task("Write report")
    active = storage.list_tasks()
    assert len(active) == 1 and active[0].id == task_id

    storage.toggle_task(task_id, True)
    active_after = storage.list_tasks()
    assert active_after == []

    all_tasks = storage.list_tasks(include_done=True)
    assert all_tasks[0].is_done is True
