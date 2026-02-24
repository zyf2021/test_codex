from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def default_db_path() -> Path:
    return Path.home() / ".focus_scenes" / "focus_scenes.db"


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow(default_db_path())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
