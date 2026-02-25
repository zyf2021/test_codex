from __future__ import annotations

from PyQt6.QtWidgets import QApplication


THEME_QSS = """
QWidget {
    background: #f4f1ee;
    color: #2f2a26;
    font-size: 13px;
}

QMainWindow {
    background: #f4f1ee;
}

QLabel, QCheckBox {
    background: transparent;
}

QToolTip {
    background-color: #fff9f3;
    color: #3d3732;
    border: none;
    border-radius: 8px;
    padding: 6px 8px;
}

QFrame#Panel, QFrame#Card, QFrame#SceneCard {
    background: #f6e4d6;
    border: none;
    border-radius: 16px;
}

QFrame#SceneCard {
    border-radius: 18px;
}

QLabel#Heading {
    font-size: 20px;
    font-weight: 700;
    color: #2a2521;
}

QLabel#SubtleTitle {
    font-size: 14px;
    font-weight: 600;
    color: #6f645b;
}

QLabel#TimerLabel {
    font-size: 58px;
    font-weight: 700;
    color: #2d2824;
}

QLabel#StatValue {
    font-size: 24px;
    font-weight: 700;
    color: #2d2824;
}

QLabel#MutedText {
    color: #867b71;
}

QPushButton {
    border: none;
    background: #f7eee6;
    border-radius: 16px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background: #f2e6dc;
}

QPushButton:pressed {
    background: #e8d8cc;
}

QPushButton:disabled {
    color: #b3a79b;
    background: #f5efea;
}

QPushButton#PrimaryButton {
    background: #eb8f60;
    color: #ffffff;
    border: none;
    border-radius: 22px;
    padding: 10px 24px;
    min-height: 24px;
    font-size: 14px;
}

QPushButton#PrimaryButton:hover {
    background: #de8050;
}

QPushButton#PrimaryButton:pressed {
    background: #cb6f40;
}

QPushButton#PrimaryButton:disabled {
    background: #efc2aa;
    color: #fff7f2;
}

QPushButton#SecondaryButton {
    border-radius: 22px;
    padding: 10px 18px;
    min-height: 24px;
    font-size: 14px;
}

QToolButton {
    border: none;
    background: #f8efe8;
    border-radius: 10px;
    padding: 2px 6px;
    min-width: 22px;
    color: #7a5742;
}

QToolButton:hover {
    background: #f2e4d9;
}

QLineEdit, QSpinBox, QComboBox {
    background: #fff7f1;
    border: none;
    border-radius: 16px;
    padding: 7px 10px;
    min-height: 22px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    background: #fff6ef;
}

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 16px;
    subcontrol-origin: border;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: transparent;
}

QSpinBox::up-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 7px solid #8b5e3c;
}

QSpinBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #8b5e3c;
}

QListWidget {
    background: #fff7f1;
    border: none;
    border-radius: 12px;
    padding: 6px;
}

QListWidget::item {
    border-radius: 10px;
    padding: 4px;
}

QListWidget::item:selected {
    background: #f5e9de;
    color: #2f2a26;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: none;
    background: #fff1e7;
}

QCheckBox::indicator:checked {
    background: #eb8f60;
}

QProgressBar {
    border: 0;
    border-radius: 4px;
    background: #eee4db;
    max-height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    border-radius: 4px;
    background: #eb8f60;
}

QSplitter::handle {
    background: transparent;
    width: 18px;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(THEME_QSS)
