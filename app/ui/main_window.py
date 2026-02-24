from __future__ import annotations

from datetime import date, datetime, timedelta

from PyQt6.QtCore import QElapsedTimer, QRect, QTimer, Qt
from PyQt6.QtGui import QAction, QColor, QKeySequence, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.app_state import AppState
from app.core.timer import FocusTimer, TimerState
from app.data.storage import SessionRow, Storage
from app.scenes.base import BaseScene
from app.scenes.flight import FlightScene
from app.scenes.forest import ForestScene
from app.scenes.ice import IceScene


class SceneWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(600, 420)
        self._scene: BaseScene = ForestScene()
        self._progress = 0.0
        self._failed = False
        self._time_s = 0.0
        self._remaining_text = "00:00"

    def set_scene(self, scene: BaseScene) -> None:
        self._scene = scene
        self.update()

    def set_state(self, progress: float, failed: bool, time_s: float, remaining_text: str) -> None:
        self._progress = progress
        self._failed = failed
        self._time_s = time_s
        self._remaining_text = remaining_text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        self._scene.render(painter, rect, self._progress, self._failed, self._time_s)

        diameter = int(min(rect.width(), rect.height()) * 0.35)
        circle_rect = QRect(rect.left() + 16, rect.top() + 16, diameter, diameter)

        painter.setPen(QPen(QColor(255, 255, 255, 180), 8))
        painter.drawEllipse(circle_rect)
        painter.setPen(QPen(QColor("#ffca28"), 8))
        span = int(-360 * 16 * self._progress)
        painter.drawArc(circle_rect, 90 * 16, span)

        painter.setPen(QColor("#263238"))
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_text)


class MainWindow(QMainWindow):
    def __init__(self, storage: Storage, app_state: AppState) -> None:
        super().__init__()
        self.setWindowTitle("Focus Scenes")
        self.resize(1100, 700)

        self.storage = storage
        self.app_state = app_state
        self.timer = FocusTimer()
        self.session_duration = 25 * 60
        self.failed_animation = False

        self.elapsed = QElapsedTimer()
        self.elapsed.start()
        self.last_ms = self.elapsed.elapsed()

        self.scenes: dict[str, BaseScene] = {
            "Forest": ForestScene(),
            "Flight": FlightScene(),
            "Ice": IceScene(),
        }
        self.theme_to_ui = {"forest": "Forest", "flight": "Flight", "ice": "Ice"}
        self.ui_to_theme = {v: k for k, v in self.theme_to_ui.items()}

        self._build_ui()
        self._connect_signals()
        self._sync_theme_from_state()

        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(33)
        self.frame_timer.timeout.connect(self._on_frame)
        self.frame_timer.start()

        self.refresh_stats()
        self._update_buttons()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        right = QWidget()
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)

        root_layout = QHBoxLayout(central)
        root_layout.addWidget(split)

        left_layout = QVBoxLayout(left)
        top_bar = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Pomodoro 25/5", "Deep 50/10", "Custom"])
        self.custom_minutes = QSpinBox()
        self.custom_minutes.setRange(1, 240)
        self.custom_minutes.setValue(30)
        self.custom_minutes.setEnabled(False)

        self.scene_combo = QComboBox()
        self.scene_combo.addItems(list(self.scenes.keys()))

        top_bar.addWidget(QLabel("Mode:"))
        top_bar.addWidget(self.preset_combo)
        top_bar.addWidget(QLabel("Custom min:"))
        top_bar.addWidget(self.custom_minutes)
        top_bar.addSpacing(20)
        top_bar.addWidget(QLabel("Scene:"))
        top_bar.addWidget(self.scene_combo)
        top_bar.addStretch()
        left_layout.addLayout(top_bar)

        self.scene_widget = SceneWidget()
        left_layout.addWidget(self.scene_widget, 1)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")
        controls.addWidget(self.start_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.resume_btn)
        controls.addWidget(self.stop_btn)
        controls.addStretch()
        left_layout.addLayout(controls)

        right_layout = QVBoxLayout(right)
        stats_box = QWidget()
        stats_form = QFormLayout(stats_box)
        self.coins_label = QLabel("0")
        self.today_success_label = QLabel("0")
        self.streak_label = QLabel("0")
        stats_form.addRow("Coins:", self.coins_label)
        stats_form.addRow("Success today:", self.today_success_label)
        stats_form.addRow("Current streak:", self.streak_label)

        self.history_list = QListWidget()
        right_layout.addWidget(QLabel("Statistics"))
        right_layout.addWidget(stats_box)
        right_layout.addWidget(QLabel("Recent sessions"))
        right_layout.addWidget(self.history_list, 1)

        space_action = QAction(self)
        space_action.setShortcut(QKeySequence(Qt.Key.Key_Space))
        space_action.triggered.connect(self._space_toggle)
        self.addAction(space_action)

    def _connect_signals(self) -> None:
        self.start_btn.clicked.connect(self.start_session)
        self.pause_btn.clicked.connect(self.pause_session)
        self.resume_btn.clicked.connect(self.resume_session)
        self.stop_btn.clicked.connect(self.stop_session)
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        self.custom_minutes.valueChanged.connect(self._apply_preset)
        self.scene_combo.currentTextChanged.connect(self._on_scene_changed)
        self.app_state.theme_changed.connect(self._sync_theme_from_state)
        self.app_state.coins_changed.connect(lambda _coins: self.refresh_stats())

    def _sync_theme_from_state(self, *_args) -> None:
        ui_theme = self.theme_to_ui.get(self.app_state.selected_theme, "Forest")
        self.scene_combo.setCurrentText(ui_theme)
        self.scene_widget.set_scene(self.scenes[ui_theme])

    def _apply_preset(self, *_args) -> None:
        text = self.preset_combo.currentText()
        self.custom_minutes.setEnabled(text == "Custom")
        if text.startswith("Pomodoro"):
            self.session_duration = 25 * 60
        elif text.startswith("Deep"):
            self.session_duration = 50 * 60
        else:
            self.session_duration = self.custom_minutes.value() * 60

    def _on_scene_changed(self) -> None:
        ui_theme = self.scene_combo.currentText()
        self.scene_widget.set_scene(self.scenes[ui_theme])
        self.app_state.set_theme(self.ui_to_theme.get(ui_theme, "forest"))

    def _space_toggle(self) -> None:
        if self.timer.state == TimerState.IDLE:
            self.start_session()
        elif self.timer.state == TimerState.RUNNING:
            self.pause_session()
        elif self.timer.state == TimerState.PAUSED:
            self.resume_session()

    def start_session(self) -> None:
        self._apply_preset()
        try:
            self.timer.start(self.session_duration)
        except RuntimeError:
            QMessageBox.information(self, "Timer", "Session is already running")
            return
        self.app_state.start_session(self.session_duration, self.ui_to_theme.get(self.scene_combo.currentText(), "forest"))
        self.failed_animation = False
        self._update_buttons()

    def pause_session(self) -> None:
        try:
            self.timer.pause()
            self._update_buttons()
        except RuntimeError:
            return

    def resume_session(self) -> None:
        try:
            self.timer.resume()
            self._update_buttons()
        except RuntimeError:
            return

    def stop_session(self) -> None:
        try:
            success = self.timer.stop()
        except RuntimeError:
            return

        snapshot = self.timer.snapshot()
        coins_earned = max(1, snapshot.total_seconds // 300) if success else 0
        self.app_state.finish_session(success=success, coins_earned=coins_earned)

        if success:
            QMessageBox.information(self, "Session completed", f"Great job! +{coins_earned} coins")
        else:
            self.failed_animation = True
            QMessageBox.warning(self, "Session failed", "Session stopped early and was not counted.")

        self.refresh_stats()
        QTimer.singleShot(900, self._reset_after_finish)

    def _reset_after_finish(self) -> None:
        self.timer.reset()
        self.failed_animation = False
        self._update_buttons()

    def _on_frame(self) -> None:
        now_ms = self.elapsed.elapsed()
        dt = max(0.0, (now_ms - self.last_ms) / 1000.0)
        self.last_ms = now_ms

        snapshot = self.timer.tick(dt)
        if snapshot.state == TimerState.COMPLETED:
            self.stop_session()
            return

        remaining_text = f"{snapshot.remaining_seconds // 60:02d}:{snapshot.remaining_seconds % 60:02d}"
        self.scene_widget.set_state(snapshot.progress, self.failed_animation, now_ms / 1000.0, remaining_text)

    def _update_buttons(self) -> None:
        state = self.timer.state
        self.start_btn.setEnabled(state in {TimerState.IDLE, TimerState.FAILED, TimerState.COMPLETED})
        self.pause_btn.setEnabled(state == TimerState.RUNNING)
        self.resume_btn.setEnabled(state == TimerState.PAUSED)
        self.stop_btn.setEnabled(state in {TimerState.RUNNING, TimerState.PAUSED})

    def _success_today(self, rows: list[SessionRow]) -> int:
        today = date.today().isoformat()
        return sum(1 for r in rows if r.success and r.started_at.startswith(today))

    def _streak_days(self, rows: list[SessionRow]) -> int:
        success_days = {
            datetime.fromisoformat(r.started_at).date()
            for r in rows
            if r.success
        }
        cursor = date.today()
        streak = 0
        while cursor in success_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def refresh_stats(self) -> None:
        rows = self.storage.list_sessions(limit=100)
        self.coins_label.setText(str(self.app_state.coins_balance))
        self.today_success_label.setText(str(self._success_today(rows)))
        self.streak_label.setText(str(self._streak_days(rows)))
        self.history_list.clear()
        for row in rows:
            status = "✅" if row.success else "❌"
            minutes = row.duration_sec // 60
            item_text = f"{status} {row.started_at} · {minutes}m · {row.theme} · +{row.coins_earned}"
            QListWidgetItem(item_text, self.history_list)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.timer.is_active:
            answer = QMessageBox.question(
                self,
                "Exit",
                "A focus session is active. Exit and mark it as failed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.stop_session()
                event.accept()
            else:
                event.ignore()
            return
        event.accept()
