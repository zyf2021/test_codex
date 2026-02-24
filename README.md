# Focus Scenes (Python Desktop App)

Оффлайн-приложение для фокус-сессий с геймификацией в стиле Forest и тремя сценами прогресса:

- **Forest** — растение растёт (при провале вянет),
- **Flight** — самолёт летит (при провале падает),
- **Ice** — айсберг тает (при провале трескается).

## Стек

- Python 3.11+
- PyQt6 (GUI)
- SQLite (`sqlite3` из stdlib)
- Pytest (юнит-тесты)

## Возможности MVP

- Таймер с режимами: **Pomodoro 25/5**, **Deep 50/10**, **Custom**.
- Кнопки: **Start / Pause / Resume / Stop**.
- При досрочном `Stop` — сессия считается **failed**.
- При завершении таймера — **success**.
- История сессий в SQLite: дата/время, длительность, сцена, успех/провал.
- Статистика:
  - успешных сессий за сегодня,
  - streak по дням (минимум 1 успешная сессия в день).
- Space как горячая клавиша для start/pause/resume.
- Подтверждение при закрытии окна во время активной сессии.

## Архитектура

- `app/main.py` — вход в приложение.
- `app/ui/main_window.py` — UI и orchestration.
- `app/core/timer.py` — бизнес-логика таймера (без UI).
- `app/core/storage.py` — SQLite слой.
- `app/scenes/base.py` — интерфейс сцены.
- `app/scenes/forest.py`, `flight.py`, `ice.py` — отрисовка сцен через `QPainter`.
- `tests/` — юнит-тесты для core-логики.

## Установка и запуск

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

База данных по умолчанию хранится в:

- Linux/macOS: `~/.focus_scenes/focus_scenes.db`
- Windows: `%USERPROFILE%\.focus_scenes\focus_scenes.db`

## Тесты

```bash
pytest -q
```

## Сборка в EXE через PyInstaller

> Необязательно для запуска из исходников. Ниже — рекомендуемые шаги.

1. Установить PyInstaller:

```bash
pip install pyinstaller
```

2. Собрать one-file бинарник:

```bash
pyinstaller --noconfirm --onefile --name FocusScenes app/main.py
```

3. Запуск артефакта:

- Windows: `dist/FocusScenes.exe`
- Linux/macOS: `dist/FocusScenes`

### Примечание

Приложение не зависит от внешних картинок: сцены рисуются примитивами `QPainter`, поэтому работает без `assets`.
