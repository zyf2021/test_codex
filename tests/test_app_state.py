from app.core.app_state import AppState
from app.data.storage import Storage


def test_load_and_theme_persist(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()

    state = AppState()
    state.load_from_storage(storage)
    state.set_theme("Flight")

    again = AppState()
    again.load_from_storage(storage)
    assert again.selected_theme == "flight"


def test_finish_session_persists_and_adds_coins(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    state = AppState()
    state.load_from_storage(storage)

    state.start_session(1200, "forest")
    state.finish_session(success=True, coins_earned=4, duration_sec=1199)

    assert state.coins_balance == 4
    rows = storage.list_sessions()
    assert len(rows) == 1
    assert rows[0].success is True
    assert rows[0].coins_earned == 4
    assert rows[0].duration_sec == 1199


def test_finish_failed_session_persists_zero_coins(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    state = AppState()
    state.load_from_storage(storage)

    state.start_session(1500, "ice")
    state.finish_session(success=False, coins_earned=9, duration_sec=321)

    rows = storage.list_sessions()
    assert len(rows) == 1
    assert rows[0].success is False
    assert rows[0].coins_earned == 0
    assert rows[0].duration_sec == 321


def test_task_methods_and_snapshot_on_success(tmp_path) -> None:
    storage = Storage(tmp_path / "app.db")
    storage.init_db()
    state = AppState()
    state.load_from_storage(storage)

    assert state.add_task("Task A") is True
    assert state.add_task("Task B") is True
    first_id = state.tasks[0].id
    second_id = state.tasks[1].id

    state.toggle_task_done(second_id, True)
    state.move_task_up(second_id)
    assert [t.id for t in state.tasks] == [second_id, first_id]

    state.start_session(60, "forest")
    state.finish_session(success=True, coins_earned=1, duration_sec=60)

    with storage._connect() as conn:  # noqa: SLF001 - tests may inspect DB directly
        rows = conn.execute(
            "SELECT task_title, is_done, sort_order FROM session_tasks ORDER BY sort_order ASC"
        ).fetchall()
    assert [(r["task_title"], r["is_done"], r["sort_order"]) for r in rows] == [
        ("Task B", 1, 0),
        ("Task A", 0, 1),
    ]
