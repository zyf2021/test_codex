# Focus Scenes (Python Desktop App)

Оффлайн-приложение для фокус-сессий с геймификацией в стиле Forest и тремя сценами прогресса.

## Текущая структура проекта

- `app/main.py` — вход в приложение
- `app/ui/` — UI слой (главное окно)
- `app/core/` — бизнес-логика (`timer.py`, `app_state.py`, `assets.py`)
- `app/scenes/` — сцены и рендер
- `app/data/storage.py` — SQLite слой + инициализация схемы
- `assets/` — опциональные ассеты (может быть пустой)
- `tests/` — unit-тесты

## Что важно

- Текущий Qt binding: **PyQt6**
- БД по умолчанию создаётся в корне проекта: `./app.db`
- Сцены работают без ассетов (fallback на `QPainter`), но при наличии файлов:
  - `assets/scenes/forest.png`
  - `assets/scenes/flight.png`
  - `assets/scenes/ice.png`
  они автоматически подхватятся.

## Запуск


```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```


## Тесты

```bash
pytest -q
```


## Сборка в EXE (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name FocusScenes app/main.py
```

Результат:
- Windows: `dist/FocusScenes.exe`
- Linux/macOS: `dist/FocusScenes`

