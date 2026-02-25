from __future__ import annotations

import time
from datetime import date, datetime, timedelta

from PyQt6.QtCore import QRect, QTimer, Qt
from PyQt6.QtGui import QColor, QKeySequence, QPainter, QPen, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.app_state import AppState
from app.core.timer import FocusTimer, TimerState
from app.data.storage import MAX_TASKS, SessionRow, Storage, TaskRow
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

    def set_timer_state(self, state: TimerState) -> None:
        self._scene.on_timer_state_changed(state)

    def advance_animation_frame(self, state: TimerState) -> bool:
        return self._scene.advance_animation_frame(state)

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
        x = rect.left() + 16
        y = rect.top() + 16
        circle_rect = QRect(x, y, diameter, diameter)

        painter.setPen(QPen(QColor(255, 255, 255, 180), 8))
        painter.drawEllipse(circle_rect)
        painter.setPen(QPen(QColor("#ffca28"), 8))
        span = int(-360 * 16 * self._progress)
        painter.drawArc(circle_rect, 90 * 16, span)

        painter.setPen(QColor("#263238"))
        painter.setFont(self.font())
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, self._remaining_text)


class MainWindow(QMainWindow):
    PRESETS: dict[str, tuple[int, int]] = {
        "Pomodoro 25/5": (25, 5),
        "Deep 50/10": (50, 10),
        "TEST 1:00/0:30": (1, 1),
        "Custom": (25, 5),
    }

    def __init__(self, storage: Storage, app_state: AppState) -> None:
        super().__init__()
        self.setWindowTitle("Focus Scenes")
        self.resize(1200, 740)
        self.storage = storage
        self.app_state = app_state
        self.timer = FocusTimer()
        self.failed_animation = False

        self.scenes: dict[str, BaseScene] = {
            "Forest": ForestScene(),
            "Flight": FlightScene(),
            "Ice": IceScene(),
        }
        self.theme_to_ui = {"forest": "Forest", "flight": "Flight", "ice": "Ice"}
        self.ui_to_theme = {v: k for k, v in self.theme_to_ui.items()}

        self._build_ui()
        self._load_timer_settings()
        self._connect_signals()
        self._sync_theme_from_state()

        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(250)
        self.frame_timer.timeout.connect(self._on_frame)
        self.frame_timer.start()

        self.repaint_timer = QTimer(self)
        self.repaint_timer.setInterval(33)
        self.repaint_timer.timeout.connect(self.scene_widget.update)
        self.repaint_timer.start()

        self.scene_animation_timer = QTimer(self)
        self.scene_animation_timer.setInterval(100)
        self.scene_animation_timer.timeout.connect(self._on_scene_animation_frame)
        self.scene_animation_timer.start()

        self.scene_widget.set_timer_state(self.timer.state)
        self.refresh_stats()
        self._refresh_tasks_panel()
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
        split.setStretchFactor(1, 2)

        root_layout = QHBoxLayout(central)
        root_layout.addWidget(split, 1)

        left_layout = QVBoxLayout(left)
        top_grid = QGridLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.PRESETS.keys()))

        self.focus_minutes = QSpinBox()
        self.focus_minutes.setRange(1, 240)
        self.break_minutes = QSpinBox()
        self.break_minutes.setRange(1, 120)
        self.auto_cycle_checkbox = QCheckBox("Авто-цикл")

        self.focus_plus_btn = QPushButton("+5 min")
        self.focus_minus_btn = QPushButton("-5 min")

        self.scene_combo = QComboBox()
        self.scene_combo.addItems(list(self.scenes.keys()))

        top_grid.addWidget(QLabel("Preset:"), 0, 0)
        top_grid.addWidget(self.preset_combo, 0, 1)
        top_grid.addWidget(self.auto_cycle_checkbox, 0, 2)
        top_grid.addWidget(QLabel("Focus (min):"), 1, 0)
        top_grid.addWidget(self.focus_minutes, 1, 1)
        top_grid.addWidget(self.focus_plus_btn, 1, 2)
        top_grid.addWidget(QLabel("Break (min):"), 2, 0)
        top_grid.addWidget(self.break_minutes, 2, 1)
        top_grid.addWidget(self.focus_minus_btn, 2, 2)
        top_grid.addWidget(QLabel("Scene:"), 3, 0)
        top_grid.addWidget(self.scene_combo, 3, 1)

        left_layout.addLayout(top_grid)

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
        self.cycles_label = QLabel("0")
        stats_form.addRow("Coins:", self.coins_label)
        stats_form.addRow("Success today:", self.today_success_label)
        stats_form.addRow("Current streak:", self.streak_label)
        stats_form.addRow("Completed cycles:", self.cycles_label)

        self.history_list = QListWidget()
        right_layout.addWidget(QLabel("Statistics"))
        right_layout.addWidget(stats_box)

        self.tasks_panel = QWidget()
        self.tasks_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        tasks_layout = QVBoxLayout(self.tasks_panel)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_title = QLabel(f"Задачи (0/{MAX_TASKS})")
        tasks_layout.addWidget(self.tasks_title)

        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Добавить задачу…")
        self.add_task_btn = QPushButton("+")
        self.add_task_btn.setFixedWidth(36)
        input_row.addWidget(self.task_input, 1)
        input_row.addWidget(self.add_task_btn)
        tasks_layout.addLayout(input_row)

        self.max_tasks_label = QLabel("Максимум 5 задач")
        self.max_tasks_label.setVisible(False)
        tasks_layout.addWidget(self.max_tasks_label)

        self.tasks_list = QListWidget()
        tasks_layout.addWidget(self.tasks_list, 1)

        right_layout.addWidget(self.tasks_panel, 1)
        right_layout.addWidget(QLabel("Recent sessions"))
        right_layout.addWidget(self.history_list, 1)

        self.tasks_panel = QWidget()
        self.tasks_panel.setFixedWidth(290)
        self.tasks_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        tasks_layout = QVBoxLayout(self.tasks_panel)
        self.tasks_title = QLabel(f"Задачи (0/{MAX_TASKS})")
        tasks_layout.addWidget(self.tasks_title)

        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Добавить задачу…")
        self.add_task_btn = QPushButton("+")
        self.add_task_btn.setFixedWidth(36)
        input_row.addWidget(self.task_input, 1)
        input_row.addWidget(self.add_task_btn)
        tasks_layout.addLayout(input_row)

        self.max_tasks_label = QLabel("Максимум 5 задач")
        self.max_tasks_label.setVisible(False)
        tasks_layout.addWidget(self.max_tasks_label)

        self.tasks_list = QListWidget()
        tasks_layout.addWidget(self.tasks_list, 1)

        root_layout.addWidget(self.tasks_panel)

        QShortcut(QKeySequence("Space"), self, activated=self._space_toggle)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.start_session)

    def _connect_signals(self) -> None:
        self.start_btn.clicked.connect(self.start_session)
        self.pause_btn.clicked.connect(self.pause_session)
        self.resume_btn.clicked.connect(self.resume_session)
        self.stop_btn.clicked.connect(self.stop_session)

        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        self.focus_minutes.valueChanged.connect(self._on_manual_duration_changed)
        self.break_minutes.valueChanged.connect(self._on_manual_duration_changed)
        self.auto_cycle_checkbox.toggled.connect(self._save_timer_settings)
        self.focus_plus_btn.clicked.connect(lambda: self._adjust_focus_minutes(5))
        self.focus_minus_btn.clicked.connect(lambda: self._adjust_focus_minutes(-5))

        self.scene_combo.currentTextChanged.connect(self._on_scene_changed)
        self.app_state.theme_changed.connect(self._sync_theme_from_state)
        self.app_state.coins_changed.connect(lambda _coins: self.refresh_stats())
        self.app_state.tasks_changed.connect(self._refresh_tasks_panel)

        self.add_task_btn.clicked.connect(self._on_add_task)
        self.task_input.returnPressed.connect(self._on_add_task)

    def _refresh_tasks_panel(self) -> None:
        self.tasks_list.clear()
        tasks = self.app_state.tasks
        for index, task in enumerate(tasks):
            item = QListWidgetItem(self.tasks_list)
            row_widget = self._build_task_row(task, index, len(tasks))
            item.setSizeHint(row_widget.sizeHint())
            self.tasks_list.addItem(item)
            self.tasks_list.setItemWidget(item, row_widget)

        done_count = sum(1 for task in tasks if task.is_done)
        self.tasks_title.setText(f"Задачи ({done_count}/{MAX_TASKS})")
        limit_reached = len(tasks) >= MAX_TASKS
        self.add_task_btn.setEnabled(not limit_reached)
        self.task_input.setToolTip("Максимум 5 задач" if limit_reached else "")
        self.max_tasks_label.setVisible(limit_reached)

    def _build_task_row(self, task: TaskRow, index: int, total: int) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 2, 4, 2)

        done_checkbox = QCheckBox()
        done_checkbox.setChecked(task.is_done)
        done_checkbox.toggled.connect(lambda checked, task_id=task.id: self.app_state.toggle_task_done(task_id, checked))

        title = QLabel(task.title)
        title.setWordWrap(True)

        up_btn = QToolButton()
        up_btn.setText("↑")
        up_btn.setEnabled(index > 0)
        up_btn.clicked.connect(lambda _checked=False, task_id=task.id: self.app_state.move_task_up(task_id))

        down_btn = QToolButton()
        down_btn.setText("↓")
        down_btn.setEnabled(index < total - 1)
        down_btn.clicked.connect(lambda _checked=False, task_id=task.id: self.app_state.move_task_down(task_id))

        delete_btn = QToolButton()
        delete_btn.setText("×")
        delete_btn.clicked.connect(lambda _checked=False, task_id=task.id: self.app_state.remove_task(task_id))

        layout.addWidget(done_checkbox)
        layout.addWidget(title, 1)
        layout.addWidget(up_btn)
        layout.addWidget(down_btn)
        layout.addWidget(delete_btn)
        return row

    def _on_add_task(self) -> None:
        if len(self.app_state.tasks) >= MAX_TASKS:
            self.max_tasks_label.setVisible(True)
            self.task_input.setFocus()
            return
        if self.app_state.add_task(self.task_input.text()):
            self.task_input.clear()
        self.task_input.setFocus()

    def _load_timer_settings(self) -> None:
        settings = self.app_state.settings
        self.preset_combo.setCurrentText(str(settings.get("preset", "Pomodoro 25/5")))
        self.focus_minutes.setValue(int(settings.get("focus_minutes", 25)))
        self.break_minutes.setValue(int(settings.get("break_minutes", 5)))
        self.auto_cycle_checkbox.setChecked(bool(settings.get("auto_cycle", False)))
        self._apply_preset()

    def _save_timer_settings(self) -> None:
        self.app_state.save_setting("preset", self.preset_combo.currentText())
        self.app_state.save_setting("focus_minutes", self.focus_minutes.value())
        self.app_state.save_setting("break_minutes", self.break_minutes.value())
        self.app_state.save_setting("auto_cycle", self.auto_cycle_checkbox.isChecked())

    def _sync_theme_from_state(self, *_args) -> None:
        ui_theme = self.theme_to_ui.get(self.app_state.selected_theme, "Forest")
        self.scene_combo.setCurrentText(ui_theme)
        self.scene_widget.set_scene(self.scenes[ui_theme])
        self.scene_widget.set_timer_state(self.timer.state)

    def _apply_preset(self, *_args) -> None:
        text = self.preset_combo.currentText()
        focus_min, break_min = self.PRESETS.get(text, (25, 5))

        custom = text == "Custom"
        self.focus_minutes.setEnabled(custom)
        self.break_minutes.setEnabled(custom)
        self.focus_plus_btn.setEnabled(custom)
        self.focus_minus_btn.setEnabled(custom)

        if text == "TEST 1:00/0:30":
            # 1 minute focus and 30 sec break for quick verification.
            self.timer.configure(focus_seconds=60, break_seconds=30, auto_cycle=self.auto_cycle_checkbox.isChecked())
        elif not custom:
            self.focus_minutes.blockSignals(True)
            self.break_minutes.blockSignals(True)
            self.focus_minutes.setValue(focus_min)
            self.break_minutes.setValue(break_min)
            self.focus_minutes.blockSignals(False)
            self.break_minutes.blockSignals(False)
            self.timer.configure(
                focus_seconds=focus_min * 60,
                break_seconds=break_min * 60,
                auto_cycle=self.auto_cycle_checkbox.isChecked(),
            )
        else:
            self._on_manual_duration_changed()
        self._save_timer_settings()

    def _on_manual_duration_changed(self) -> None:
        self.timer.configure(
            focus_seconds=self.focus_minutes.value() * 60,
            break_seconds=self.break_minutes.value() * 60,
            auto_cycle=self.auto_cycle_checkbox.isChecked(),
        )
        self._save_timer_settings()

    def _adjust_focus_minutes(self, delta: int) -> None:
        self.focus_minutes.setValue(max(1, self.focus_minutes.value() + delta))

    def _on_scene_changed(self) -> None:
        ui_theme = self.scene_combo.currentText()
        self.scene_widget.set_scene(self.scenes[ui_theme])
        self.scene_widget.set_timer_state(self.timer.state)
        self.app_state.set_theme(self.ui_to_theme.get(ui_theme, "forest"))

    def _space_toggle(self) -> None:
        if self.timer.state in {TimerState.FOCUS_RUNNING, TimerState.BREAK_RUNNING}:
            self.pause_session()
        elif self.timer.state in {TimerState.FOCUS_PAUSED, TimerState.BREAK_PAUSED}:
            self.resume_session()

    def start_session(self) -> None:
        if self.timer.state not in {TimerState.IDLE, TimerState.FINISHED, TimerState.FAILED}:
            return
        self._apply_preset()
        self.timer.start()
        self.app_state.start_session(self.timer.focus_duration_sec, self.ui_to_theme.get(self.scene_combo.currentText(), "forest"))
        self.failed_animation = False
        self.scene_widget.set_timer_state(self.timer.state)
        self._update_buttons()

    def pause_session(self) -> None:
        self.timer.pause()
        self.scene_widget.set_timer_state(self.timer.state)
        self._update_buttons()

    def resume_session(self) -> None:
        self.timer.resume()
        self.scene_widget.set_timer_state(self.timer.state)
        self._update_buttons()

    def stop_session(self) -> None:
        state_before_stop = self.timer.state
        success_stop = self.timer.stop()

        if state_before_stop in {TimerState.FOCUS_RUNNING, TimerState.FOCUS_PAUSED}:
            snapshot = self.timer.snapshot()
            self.app_state.finish_session(success=False, coins_earned=0, duration_sec=snapshot.elapsed_seconds)
            self.failed_animation = True
            QMessageBox.warning(self, "Session failed", "Session stopped early and was not counted.")
            self.refresh_stats()
            self._reset_after_finish()
            return

        if state_before_stop in {TimerState.BREAK_RUNNING, TimerState.BREAK_PAUSED}:
            self._reset_after_finish()
            return

        if success_stop:
            self._reset_after_finish()

    def _handle_focus_success(self, elapsed_seconds: int) -> None:
        coins_earned = max(1, self.timer.focus_duration_sec // 300)
        self.app_state.finish_session(success=True, coins_earned=coins_earned, duration_sec=elapsed_seconds)
        self.refresh_stats()
        if not self.auto_cycle_checkbox.isChecked():
            QMessageBox.information(self, "Session completed", f"Great job! +{coins_earned} coins")
            self._reset_after_finish()

    def _reset_after_finish(self) -> None:
        self.timer.reset()
        self.failed_animation = False
        self.scene_widget.set_timer_state(self.timer.state)
        self._update_buttons()

    def _on_frame(self) -> None:
        now = time.monotonic()
        prev_state = self.timer.state
        snapshot = self.timer.tick(now)

        if prev_state == TimerState.FOCUS_RUNNING and snapshot.state in {TimerState.BREAK_RUNNING, TimerState.FINISHED}:
            self._handle_focus_success(self.timer.focus_duration_sec)
            if snapshot.state == TimerState.FINISHED:
                return
            snapshot = self.timer.snapshot(now)

        self.app_state.update_session_state(snapshot.state.value, snapshot.progress)
        self.scene_widget.set_timer_state(snapshot.state)
        self.cycles_label.setText(str(self.timer.completed_focus_sessions))

        remaining_text = f"{snapshot.remaining_seconds // 60:02d}:{snapshot.remaining_seconds % 60:02d}"
        self.scene_widget.set_state(snapshot.progress, self.failed_animation, now, remaining_text)
        self._update_buttons()


    def _on_scene_animation_frame(self) -> None:
        if self.scene_widget.advance_animation_frame(self.timer.state):
            self.scene_widget.update()

    def _update_buttons(self) -> None:
        state = self.timer.state
        self.start_btn.setEnabled(state in {TimerState.IDLE, TimerState.FAILED, TimerState.FINISHED})
        self.pause_btn.setEnabled(state in {TimerState.FOCUS_RUNNING, TimerState.BREAK_RUNNING})
        self.resume_btn.setEnabled(state in {TimerState.FOCUS_PAUSED, TimerState.BREAK_PAUSED})
        self.stop_btn.setEnabled(state in {TimerState.FOCUS_RUNNING, TimerState.FOCUS_PAUSED, TimerState.BREAK_RUNNING, TimerState.BREAK_PAUSED})

    def _success_today(self, rows: list[SessionRow]) -> int:
        today = date.today().isoformat()
        return sum(1 for r in rows if r.success and r.started_at.startswith(today))

    def _streak_days(self, rows: list[SessionRow]) -> int:
        success_days = {datetime.fromisoformat(r.started_at).date() for r in rows if r.success}
        cursor = date.today()
        streak = 0
        while cursor in success_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def refresh_stats(self) -> None:
        rows = self.storage.list_sessions(limit=50)
        self.coins_label.setText(str(self.app_state.coins_balance))
        self.today_success_label.setText(str(self._success_today(rows)))
        self.streak_label.setText(str(self._streak_days(rows)))
        self.history_list.clear()
        for row in rows:
            status = "✅" if row.success else "❌"
            duration_text = f"{row.duration_sec // 60:02d}:{row.duration_sec % 60:02d}"
            item_text = f"{status} {row.started_at} · {duration_text} · {row.theme}"
            QListWidgetItem(item_text, self.history_list)

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self.timer.is_active:
            event.accept()
            return

        answer = QMessageBox.question(
            self,
            "Exit",
            "Сессия активна. Закрыть приложение? (это прервет сессию)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        if self.timer.state in {TimerState.FOCUS_RUNNING, TimerState.FOCUS_PAUSED}:
            self.stop_session()
        else:
            self.timer.stop()
        event.accept()
