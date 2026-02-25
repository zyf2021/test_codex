from __future__ import annotations

"""Сцена Flight: полет самолета и анимация пропеллера."""

from math import sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QPolygonF

from app.core.assets import load_pixmap, load_pixmap_sequence
from app.core.timer import TimerState
from app.scenes.base import BaseScene


class FlightScene(BaseScene):
    """Визуализация авиа-темы; поддерживает покадровую анимацию."""
    name = "Flight"

    def __init__(self) -> None:
        self._pixmap = load_pixmap("scenes/flight.png")
        self._plane_frame_paths = [
            "plane/plane_fly_01.png",
            "plane/plane_fly_02.png",
            "plane/plane_fly_03.png",
            "plane/plane_fly_04.png",
        ]
        self._plane_frames = load_pixmap_sequence(self._plane_frame_paths)
        self._use_sprite_plane = len(self._plane_frames) == 4
        self._frame_index = 0

    def on_timer_state_changed(self, state: TimerState) -> None:
        if state in {TimerState.IDLE, TimerState.FINISHED, TimerState.FAILED}:
            self._frame_index = 0

    def advance_animation_frame(self, state: TimerState) -> bool:
        if not self._use_sprite_plane:
            return False
        if state not in {TimerState.FOCUS_RUNNING, TimerState.BREAK_RUNNING}:
            return False

        self._frame_index = (self._frame_index + 1) % len(self._plane_frames)
        return True

    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        if self._pixmap is not None:
            painter.drawPixmap(rect.toRect(), self._pixmap)
        else:
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

        if self._use_sprite_plane:
            self._draw_sprite_plane(painter, rect, x, y, time_s)
        else:
            self._draw_fallback_plane(painter, x, y, failed, time_s)

    def _draw_sprite_plane(self, painter: QPainter, rect: QRectF, x: float, y: float, time_s: float) -> None:
        frame = self._plane_frames[self._frame_index]
        self._draw_fitted_plane_frame(painter, rect, frame, x, y, time_s)

    def _draw_fallback_plane(self, painter: QPainter, x: float, y: float, failed: bool, time_s: float) -> None:
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

    def _draw_fitted_plane_frame(
        self,
        painter: QPainter,
        rect: QRectF,
        frame: QPixmap,
        x: float,
        y: float,
        time_s: float,
    ) -> None:
        max_w = rect.width() * 0.28
        max_h = rect.height() * 0.28
        scale = min(max_w / frame.width(), max_h / frame.height())
        draw_w = frame.width() * scale
        draw_h = frame.height() * scale
        wobble_y = sin(time_s * 4.0) * 3.0
        target = QRectF(x - draw_w * 0.55, y - draw_h * 0.5 + wobble_y, draw_w, draw_h)
        painter.drawPixmap(target, frame, QRectF(frame.rect()))
