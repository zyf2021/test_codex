from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ModuleNotFoundError:  # pragma: no cover - test fallback without Qt runtime
    class QObject:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:
            pass

    class _DummySignal:
        def connect(self, *_args, **_kwargs) -> None:
            pass

        def emit(self, *_args, **_kwargs) -> None:
            pass

    def pyqtSignal(*_args, **_kwargs):  # type: ignore[override]
        return _DummySignal()

from app.data.storage import Storage


THEME_ALIASES = {
    "forest": "forest",
    "flight": "flight",
    "ice": "ice",
    "hourglass": "hourglass",
    "Forest": "forest",
    "Flight": "flight",
    "Ice": "ice",
}


@dataclass
class SessionState:
    started_at: str
    duration_sec: int
    theme: str
    state: str = "idle"
    progress: float = 0.0


class AppState(QObject):
    state_changed = pyqtSignal()
    coins_changed = pyqtSignal(int)
    theme_changed = pyqtSignal(str)
    settings_changed = pyqtSignal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.current_session: SessionState | None = None
        self.selected_theme: str = "forest"
        self.settings: dict[str, Any] = {}
        self.coins_balance: int = 0
        self._storage: Storage | None = None

    def load_from_storage(self, storage: Storage) -> None:
        self._storage = storage
        saved_theme = storage.get_setting("selected_theme", "forest")
        self.selected_theme = self._normalize_theme(str(saved_theme))
        raw_settings = storage.get_setting("settings", {})
        self.settings = raw_settings if isinstance(raw_settings, dict) else {}
        self.coins_balance = storage.get_coins_balance()
        self.state_changed.emit()
        self.theme_changed.emit(self.selected_theme)
        self.coins_changed.emit(self.coins_balance)

    def save_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        if self._storage:
            self._storage.set_setting("settings", self.settings)
        self.settings_changed.emit(key, value)
        self.state_changed.emit()

    def set_theme(self, theme: str) -> None:
        normalized = self._normalize_theme(theme)
        self.selected_theme = normalized
        if self._storage:
            self._storage.set_setting("selected_theme", normalized)
        self.theme_changed.emit(normalized)
        self.state_changed.emit()

    def add_coins(self, amount: int, reason: str = "") -> None:
        self.coins_balance = max(0, self.coins_balance + amount)
        if self._storage:
            self._storage.set_coins_balance(self.coins_balance)
        self.coins_changed.emit(self.coins_balance)
        if reason:
            self.settings["last_coin_reason"] = reason
        self.state_changed.emit()

    def start_session(self, duration_sec: int, theme: str) -> None:
        self.current_session = SessionState(
            started_at=datetime.now().isoformat(timespec="seconds"),
            duration_sec=duration_sec,
            theme=self._normalize_theme(theme),
            state="focus_running",
            progress=0.0,
        )
        self.state_changed.emit()

    def update_session_state(self, state: str, progress: float) -> None:
        if not self.current_session:
            return
        self.current_session.state = state
        self.current_session.progress = max(0.0, min(1.0, progress))
        self.state_changed.emit()

    def finish_session(self, success: bool, coins_earned: int, duration_sec: int | None = None) -> None:
        if not self.current_session:
            return
        if self._storage:
            self._storage.insert_session(
                started_at=self.current_session.started_at,
                duration_sec=duration_sec if duration_sec is not None else self.current_session.duration_sec,
                theme=self.current_session.theme,
                success=success,
                coins_earned=coins_earned if success else 0,
            )
        if success and coins_earned:
            self.add_coins(coins_earned, reason="session_success")
        self.current_session = None
        self.state_changed.emit()

    def _normalize_theme(self, theme: str) -> str:
        return THEME_ALIASES.get(theme, "forest")
