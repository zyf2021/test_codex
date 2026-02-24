from __future__ import annotations

from abc import ABC, abstractmethod

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter

from app.core.timer import TimerState


class BaseScene(ABC):
    name: str

    @abstractmethod
    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        """Render scene in the provided rect."""

    def on_timer_state_changed(self, state: TimerState) -> None:
        """Hook for scene-specific state updates."""

    def advance_animation_frame(self, state: TimerState) -> bool:
        """Advance animation frame and return True if repaint is needed."""
        return False
