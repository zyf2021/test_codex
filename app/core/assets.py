from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QPixmap


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def get_asset_path(relative: str) -> str:
    return str(ASSETS_DIR / relative)


def asset_exists(path: str) -> bool:
    return Path(path).exists()


def load_pixmap(relative: str) -> QPixmap | None:
    path = Path(get_asset_path(relative))
    if not path.exists():
        return None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return pixmap
