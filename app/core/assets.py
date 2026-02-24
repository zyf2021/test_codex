from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QPixmap


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_PIXMAP_CACHE: dict[str, QPixmap | None] = {}


def get_asset_path(relative: str) -> Path:
    return ASSETS_DIR / relative


def asset_exists(relative: str) -> bool:
    return get_asset_path(relative).exists()


def load_pixmap(relative: str) -> QPixmap | None:
    if relative in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[relative]

    path = get_asset_path(relative)
    if not path.exists():
        _PIXMAP_CACHE[relative] = None
        return None

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        _PIXMAP_CACHE[relative] = None
        return None

    _PIXMAP_CACHE[relative] = pixmap
    return pixmap


def load_pixmap_sequence(relatives: list[str]) -> list[QPixmap]:
    pixmaps: list[QPixmap] = []
    for relative in relatives:
        pixmap = load_pixmap(relative)
        if pixmap is None:
            return []
        pixmaps.append(pixmap)
    return pixmaps
