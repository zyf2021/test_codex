from __future__ import annotations

from abc import ABC, abstractmethod

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter


class BaseScene(ABC):
    name: str

    @abstractmethod
    def render(self, painter: QPainter, rect: QRectF, progress: float, failed: bool, time_s: float) -> None:
        """Render scene in the provided rect."""
