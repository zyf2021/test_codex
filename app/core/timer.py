from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TimerState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class TimerSnapshot:
    total_seconds: int
    remaining_seconds: int
    elapsed_seconds: int
    progress: float
    state: TimerState


class FocusTimer:
    """Pure business timer logic detached from UI frameworks."""

    def __init__(self) -> None:
        self._total_ms = 0
        self._remaining_ms = 0
        self._state = TimerState.IDLE

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in {TimerState.RUNNING, TimerState.PAUSED}

    def start(self, duration_seconds: int) -> None:
        if duration_seconds <= 0:
            raise ValueError("Duration must be positive")
        if self._state == TimerState.RUNNING:
            raise RuntimeError("Timer already running")
        self._total_ms = duration_seconds * 1000
        self._remaining_ms = self._total_ms
        self._state = TimerState.RUNNING

    def pause(self) -> None:
        if self._state != TimerState.RUNNING:
            raise RuntimeError("Pause is only available while running")
        self._state = TimerState.PAUSED

    def resume(self) -> None:
        if self._state != TimerState.PAUSED:
            raise RuntimeError("Resume is only available while paused")
        self._state = TimerState.RUNNING

    def stop(self) -> bool:
        """Stop session; returns True on success completion and False on fail."""
        if self._state not in {TimerState.RUNNING, TimerState.PAUSED, TimerState.COMPLETED}:
            raise RuntimeError("Stop is unavailable in current state")
        succeeded = self._state == TimerState.COMPLETED
        self._state = TimerState.COMPLETED if succeeded else TimerState.FAILED
        return succeeded

    def reset(self) -> None:
        self._total_ms = 0
        self._remaining_ms = 0
        self._state = TimerState.IDLE

    def tick(self, dt_seconds: float) -> TimerSnapshot:
        if self._state != TimerState.RUNNING:
            return self.snapshot()
        delta_ms = max(0, int(dt_seconds * 1000))
        self._remaining_ms = max(0, self._remaining_ms - delta_ms)
        if self._remaining_ms == 0:
            self._state = TimerState.COMPLETED
        return self.snapshot()

    def snapshot(self) -> TimerSnapshot:
        total_seconds = self._total_ms // 1000
        remaining_seconds = (self._remaining_ms + 999) // 1000 if self._remaining_ms else 0
        elapsed_seconds = max(0, total_seconds - remaining_seconds)
        progress = (elapsed_seconds / total_seconds) if total_seconds else 0.0
        return TimerSnapshot(
            total_seconds=total_seconds,
            remaining_seconds=remaining_seconds,
            elapsed_seconds=elapsed_seconds,
            progress=max(0.0, min(1.0, progress)),
            state=self._state,
        )
