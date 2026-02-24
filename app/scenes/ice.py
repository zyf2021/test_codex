from __future__ import annotations

from math import sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

from app.core.assets import load_pixmap
from app.scenes.base import BaseScene


class IceScene(BaseScene):
    name = "Ice"
    def __init__(self) -> None:
        self._pixmap = load_pixmap("scenes/ice.png")

    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        if self._pixmap is not None:
            painter.drawPixmap(rect.toRect(), self._pixmap)
            return


        painter.fillRect(rect, QColor("#e1f5fe"))
        water_top = rect.bottom() - rect.height() * 0.28
        painter.fillRect(QRectF(rect.left(), water_top, rect.width(), rect.height() * 0.28), QColor("#4fc3f7"))

        melt_scale = 1.0 - 0.65 * progress
        w = rect.width() * 0.35 * melt_scale
        h = rect.height() * 0.45 * melt_scale
        cx = rect.center().x()
        base_y = water_top + 10

        iceberg = QPolygonF([
            QPointF(cx - w * 0.7, base_y),
            QPointF(cx - w * 0.45, base_y - h * 0.75),
            QPointF(cx - w * 0.1, base_y - h),
            QPointF(cx + w * 0.45, base_y - h * 0.8),
            QPointF(cx + w * 0.7, base_y),
        ])
        painter.setBrush(QBrush(QColor("#b3e5fc") if not failed else QColor("#90a4ae")))
        painter.setPen(QPen(QColor("#81d4fa"), 2))
        painter.drawPolygon(iceberg)

        drop_count = int(progress * 5)
        painter.setBrush(QBrush(QColor("#29b6f6")))
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(drop_count):
            dx = -40 + i * 20
            dy = sin(time_s * 4 + i) * 5
            painter.drawEllipse(QRectF(cx + dx, water_top - 20 + dy, 8, 12))

        if failed:
            painter.setPen(QPen(QColor("#37474f"), 3))
            painter.drawLine(QPointF(cx - w * 0.2, base_y - h * 0.9), QPointF(cx + w * 0.1, base_y - h * 0.3))
            painter.drawLine(QPointF(cx + w * 0.15, base_y - h * 0.85), QPointF(cx - w * 0.2, base_y - h * 0.2))
            painter.drawLine(QPointF(cx + w * 0.4, base_y - h * 0.7), QPointF(cx + w * 0.1, base_y - h * 0.1))
