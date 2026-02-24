import pytest

from app.core.timer import FocusTimer, TimerState


def test_timer_completes_after_ticks() -> None:
    timer = FocusTimer()
    timer.start(2)
    timer.tick(1.0)
    assert timer.snapshot().remaining_seconds == 1
    timer.tick(1.0)
    assert timer.state == TimerState.COMPLETED


def test_pause_resume_flow() -> None:
    timer = FocusTimer()
    timer.start(5)
    timer.pause()
    timer.tick(10)
    assert timer.snapshot().remaining_seconds == 5
    timer.resume()
    timer.tick(2)
    assert timer.snapshot().remaining_seconds == 3


def test_stop_marks_failed_if_early() -> None:
    timer = FocusTimer()
    timer.start(5)
    success = timer.stop()
    assert success is False
    assert timer.state == TimerState.FAILED


def test_invalid_double_start_raises() -> None:
    timer = FocusTimer()
    timer.start(3)
    with pytest.raises(RuntimeError):
        timer.start(2)
