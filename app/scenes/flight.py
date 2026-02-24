from __future__ import annotations

from math import sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

from app.scenes.base import BaseScene


class FlightScene(BaseScene):
    name = "Flight"

    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        painter.fillRect(rect, QColor("#b3e5fc"))

        cloud_shift = (time_s * 25) % (rect.width() + 180)
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.PenStyle.NoPen)
        for i, y in enumerate([0.2, 0.32, 0.16]):
            x = rect.left() + ((i * 280 + cloud_shift) % (rect.width() + 180)) - 90
            cy = rect.top() + rect.height() * y
            painter.drawEllipse(QRectF(x, cy, 120, 40))
            painter.drawEllipse(QRectF(x + 35, cy - 15, 90, 40))

        x = rect.left() + rect.width() * (0.08 + 0.84 * progress)
        y = rect.top() + rect.height() * (0.55 - 0.25 * progress)
        if failed:
            y += min(rect.height() * 0.4, (1.0 - progress) * rect.height() * 0.6 + time_s * 140)

        body = QPolygonF([
            QPointF(x - 35, y),
            QPointF(x + 28, y - 8),
            QPointF(x + 40, y),
            QPointF(x + 28, y + 8),
        ])
        wing = QPolygonF([
            QPointF(x - 5, y),
            QPointF(x - 25, y + 20),
            QPointF(x + 15, y + 7),
        ])

        plane_color = QColor("#1e88e5") if not failed else QColor("#455a64")
        painter.setBrush(QBrush(plane_color))
        painter.setPen(QPen(QColor("#0d47a1"), 2))
        painter.drawPolygon(body)
        painter.drawPolygon(wing)

        if not failed:
            trail_y = y + sin(time_s * 6) * 2
            painter.setPen(QPen(QColor(255, 255, 255, 180), 2, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x - 120, trail_y), QPointF(x - 40, trail_y))
