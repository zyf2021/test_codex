from __future__ import annotations

"""Сцена Forest: рост растения по мере прогресса фокуса."""

from math import sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from app.core.assets import load_pixmap
from app.scenes.base import BaseScene


class ForestScene(BaseScene):
    """Визуализация лесной темы: стебель, листья, цветок."""
    name = "Forest"


    def __init__(self) -> None:
        self._pixmap = load_pixmap("scenes/forest.png")

    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        if self._pixmap is not None:
            painter.drawPixmap(rect.toRect(), self._pixmap)
            return

        sky = QColor("#d9f6ff") if not failed else QColor("#c7c7c7")
        ground = QColor("#86c06c") if not failed else QColor("#6e6e6e")
        painter.fillRect(rect, sky)
        ground_rect = QRectF(rect.left(), rect.bottom() - rect.height() * 0.25, rect.width(), rect.height() * 0.25)
        painter.fillRect(ground_rect, ground)

        cx = rect.center().x()
        base_y = ground_rect.top() + 8
        stem_top = base_y - rect.height() * (0.08 + 0.35 * progress)
        stem_color = QColor("#2e7d32") if not failed else QColor("#424242")
        painter.setPen(QPen(stem_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, base_y), QPointF(cx, stem_top))

        leaf_progress = max(0.0, min(1.0, (progress - 0.2) / 0.4))
        if leaf_progress > 0:
            painter.setBrush(QBrush(QColor("#4caf50") if not failed else QColor("#555555")))
            painter.setPen(Qt.PenStyle.NoPen)
            drop_offset = 35 * max(0, progress - 0.9) if failed else 0
            size = 34 * leaf_progress
            painter.drawEllipse(QRectF(cx - 55, stem_top + 45 + drop_offset, size, size * 0.55))
            painter.drawEllipse(QRectF(cx + 20, stem_top + 60 + drop_offset, size, size * 0.55))

        flower_progress = max(0.0, min(1.0, (progress - 0.7) / 0.3))
        if flower_progress > 0:
            wobble = sin(time_s * 2.0) * 4
            center = QPointF(cx + wobble, stem_top - 12)
            petal_color = QColor("#ff80ab") if not failed else QColor("#607d8b")
            painter.setBrush(QBrush(petal_color))
            for dx, dy in [(-12, 0), (12, 0), (0, -12), (0, 12)]:
                painter.drawEllipse(QRectF(center.x() + dx - 8, center.y() + dy - 8, 16 * flower_progress, 16 * flower_progress))
            painter.setBrush(QBrush(QColor("#ffeb3b") if not failed else QColor("#455a64")))
            painter.drawEllipse(QRectF(center.x() - 7, center.y() - 7, 14, 14))
