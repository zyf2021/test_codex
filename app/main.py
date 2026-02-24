from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.core.app_state import AppState
from app.data.storage import Storage
from app.ui.main_window import MainWindow


def default_db_path() -> Path:
    return Path.cwd() / "app.db"


def main() -> int:
    app = QApplication(sys.argv)

    storage = Storage(default_db_path())
    storage.init_db()

    app_state = AppState()
    app_state.load_from_storage(storage)

    window = MainWindow(storage=storage, app_state=app_state)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
