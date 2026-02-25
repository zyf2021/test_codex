from app.data.storage import MAX_TASKS, Storage


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


def test_create_task_limit_5(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()

    for i in range(MAX_TASKS):
        storage.create_task(f"Task {i}")

    assert len(storage.list_tasks(limit=MAX_TASKS, include_done=True)) == MAX_TASKS

    try:
        storage.create_task("Task overflow")
        assert False, "Expected ValueError when adding more than 5 tasks"
    except ValueError:
        pass


def test_reorder_tasks_persists_order(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    ids = [storage.create_task(f"Task {i}") for i in range(3)]

    storage.reorder_tasks([ids[2], ids[0], ids[1]])

    rows = storage.list_tasks(limit=MAX_TASKS, include_done=True)
    assert [row.id for row in rows] == [ids[2], ids[0], ids[1]]


def test_toggle_done_and_delete(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    task_id = storage.create_task("Write report")

    storage.set_task_done(task_id, True)
    rows = storage.list_tasks(limit=MAX_TASKS, include_done=True)
    assert rows[0].is_done is True

    storage.delete_task(task_id)
    assert storage.list_tasks(limit=MAX_TASKS, include_done=True) == []
