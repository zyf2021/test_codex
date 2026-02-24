from app.core.timer import FocusTimer, TimerState


def test_focus_to_break_transition_with_auto_cycle() -> None:
    timer = FocusTimer()
    timer.configure(focus_seconds=2, break_seconds=2, auto_cycle=True)
    timer.start(now=100.0)

    timer.tick(100.0)
    snapshot = timer.tick(102.1)

    assert snapshot.state == TimerState.BREAK_RUNNING
    assert timer.completed_focus_sessions == 1


def test_pause_resume_keeps_elapsed_stable() -> None:
    timer = FocusTimer()
    timer.configure(focus_seconds=10, break_seconds=5, auto_cycle=False)
    timer.start(now=10.0)

    timer.tick(10.0)
    timer.pause(now=15.0)
    paused = timer.snapshot(15.0)
    frozen = timer.snapshot(16.0)
    timer.resume(now=16.0)
    timer.tick(18.0)
    resumed = timer.snapshot(18.0)

    assert paused.elapsed_seconds == 5
    assert frozen.elapsed_seconds == 5
    assert resumed.elapsed_seconds == 7


def test_stop_focus_marks_failed() -> None:
    timer = FocusTimer()
    timer.configure(focus_seconds=10, break_seconds=5, auto_cycle=False)
    timer.start(now=0.0)
    timer.tick(5.0)

    success = timer.stop(now=5.0)

    assert success is False
    assert timer.state == TimerState.FAILED
