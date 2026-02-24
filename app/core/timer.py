from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class TimerState(str, Enum):
    IDLE = "idle"
    FOCUS_RUNNING = "focus_running"
    FOCUS_PAUSED = "focus_paused"
    BREAK_RUNNING = "break_running"
    BREAK_PAUSED = "break_paused"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass(frozen=True)
class TimerSnapshot:
    total_seconds: int
    remaining_seconds: int
    elapsed_seconds: int
    progress: float
    state: TimerState
    is_focus: bool
    completed_focus_sessions: int


class FocusTimer:
    """Monotonic pomodoro engine detached from UI framework."""

    def __init__(self) -> None:
        self._focus_duration_sec = 25 * 60
        self._break_duration_sec = 5 * 60
        self._auto_cycle = False
        self._state = TimerState.IDLE
        self._phase_total_sec = 0.0
        self._phase_elapsed_before_pause_sec = 0.0
        self._phase_started_monotonic: float | None = None
        self._completed_focus_sessions = 0

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in {
            TimerState.FOCUS_RUNNING,
            TimerState.FOCUS_PAUSED,
            TimerState.BREAK_RUNNING,
            TimerState.BREAK_PAUSED,
        }

    @property
    def focus_duration_sec(self) -> int:
        return self._focus_duration_sec

    @property
    def break_duration_sec(self) -> int:
        return self._break_duration_sec

    @property
    def completed_focus_sessions(self) -> int:
        return self._completed_focus_sessions

    @property
    def auto_cycle(self) -> bool:
        return self._auto_cycle

    def configure(self, focus_seconds: int, break_seconds: int, auto_cycle: bool) -> None:
        if focus_seconds <= 0 or break_seconds <= 0:
            raise ValueError("Durations must be positive")
        self._focus_duration_sec = focus_seconds
        self._break_duration_sec = break_seconds
        self._auto_cycle = auto_cycle

    def start(self, now: float | None = None) -> None:
        if self._state in {
            TimerState.FOCUS_RUNNING,
            TimerState.FOCUS_PAUSED,
            TimerState.BREAK_RUNNING,
            TimerState.BREAK_PAUSED,
        }:
            return
        if now is None:
            now = time.monotonic()
        self._start_phase(TimerState.FOCUS_RUNNING, self._focus_duration_sec, now)

    def pause(self, now: float | None = None) -> None:
        if now is None:
            now = time.monotonic()
        if self._state == TimerState.FOCUS_RUNNING:
            self._phase_elapsed_before_pause_sec = self._current_elapsed(now)
            self._phase_started_monotonic = None
            self._state = TimerState.FOCUS_PAUSED
            return
        if self._state == TimerState.BREAK_RUNNING:
            self._phase_elapsed_before_pause_sec = self._current_elapsed(now)
            self._phase_started_monotonic = None
            self._state = TimerState.BREAK_PAUSED

    def resume(self, now: float | None = None) -> None:
        if now is None:
            now = time.monotonic()
        if self._state == TimerState.FOCUS_PAUSED:
            self._phase_started_monotonic = now
            self._state = TimerState.FOCUS_RUNNING
            return
        if self._state == TimerState.BREAK_PAUSED:
            self._phase_started_monotonic = now
            self._state = TimerState.BREAK_RUNNING

    def stop(self, now: float | None = None) -> bool:
        if now is None:
            now = time.monotonic()
        if self._state in {TimerState.FOCUS_RUNNING, TimerState.FOCUS_PAUSED}:
            self._state = TimerState.FAILED
            self._phase_elapsed_before_pause_sec = min(self._phase_total_sec, self._current_elapsed(now))
            self._phase_started_monotonic = None
            return False
        if self._state in {TimerState.BREAK_RUNNING, TimerState.BREAK_PAUSED}:
            self.reset()
            return True
        if self._state == TimerState.FINISHED:
            return True
        return False

    def reset(self) -> None:
        self._phase_total_sec = 0.0
        self._phase_elapsed_before_pause_sec = 0.0
        self._phase_started_monotonic = None
        self._state = TimerState.IDLE

    def tick(self, now: float | None = None) -> TimerSnapshot:
        if now is None:
            now = time.monotonic()

        if self._state not in {TimerState.FOCUS_RUNNING, TimerState.BREAK_RUNNING}:
            return self.snapshot(now)

        elapsed = self._current_elapsed(now)
        if elapsed >= self._phase_total_sec:
            overflow = elapsed - self._phase_total_sec
            if self._state == TimerState.FOCUS_RUNNING:
                self._completed_focus_sessions += 1
                if self._auto_cycle:
                    self._start_phase(TimerState.BREAK_RUNNING, self._break_duration_sec, now - overflow)
                else:
                    self._phase_elapsed_before_pause_sec = self._phase_total_sec
                    self._phase_started_monotonic = None
                    self._state = TimerState.FINISHED
            elif self._state == TimerState.BREAK_RUNNING:
                if self._auto_cycle:
                    self._start_phase(TimerState.FOCUS_RUNNING, self._focus_duration_sec, now - overflow)
                else:
                    self._phase_elapsed_before_pause_sec = self._phase_total_sec
                    self._phase_started_monotonic = None
                    self._state = TimerState.FINISHED
        return self.snapshot(now)

    def snapshot(self, now: float | None = None) -> TimerSnapshot:
        if now is None:
            now = time.monotonic()
        elapsed = self._current_elapsed(now)
        total = max(0, int(round(self._phase_total_sec)))
        elapsed_seconds = min(total, max(0, int(elapsed)))
        remaining_seconds = max(0, total - elapsed_seconds)
        progress = (elapsed / self._phase_total_sec) if self._phase_total_sec > 0 else 0.0
        is_focus = self._state in {TimerState.FOCUS_RUNNING, TimerState.FOCUS_PAUSED, TimerState.FAILED, TimerState.FINISHED, TimerState.IDLE}
        return TimerSnapshot(
            total_seconds=total,
            remaining_seconds=remaining_seconds,
            elapsed_seconds=elapsed_seconds,
            progress=max(0.0, min(1.0, progress)),
            state=self._state,
            is_focus=is_focus,
            completed_focus_sessions=self._completed_focus_sessions,
        )

    def _start_phase(self, state: TimerState, total_seconds: int, started_at_monotonic: float) -> None:
        self._state = state
        self._phase_total_sec = float(total_seconds)
        self._phase_elapsed_before_pause_sec = 0.0
        self._phase_started_monotonic = started_at_monotonic

    def _current_elapsed(self, now: float) -> float:
        elapsed = self._phase_elapsed_before_pause_sec
        if self._phase_started_monotonic is not None:
            elapsed += max(0.0, now - self._phase_started_monotonic)
        return min(self._phase_total_sec, elapsed)
