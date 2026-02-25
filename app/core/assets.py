from __future__ import annotations

"""Загрузка графических ресурсов (ассетов) с кэшированием в памяти."""

from pathlib import Path

from PyQt6.QtGui import QPixmap


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_PIXMAP_CACHE: dict[str, QPixmap | None] = {}


def get_asset_path(relative: str) -> Path:
    """Преобразует относительный путь внутри `assets/` в абсолютный."""
    return ASSETS_DIR / relative


def asset_exists(relative: str) -> bool:
    """Проверяет, существует ли ассет на диске."""
    return get_asset_path(relative).exists()


def load_pixmap(relative: str) -> QPixmap | None:
    """Загружает `QPixmap` с кэшем; возвращает `None`, если файл невалиден."""
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
    """Загружает последовательность кадров; при ошибке возвращает пустой список."""
    pixmaps: list[QPixmap] = []
    for relative in relatives:
        pixmap = load_pixmap(relative)
        if pixmap is None:
            return []
        pixmaps.append(pixmap)
    return pixmaps
