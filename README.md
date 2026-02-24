# Focus Scenes (Python Desktop App)

Оффлайн-приложение для фокус-сессий с геймификацией в стиле Forest и тремя сценами прогресса.

## Текущая структура проекта

- `app/main.py` — вход в приложение
- `app/ui/` — UI слой (главное окно)
- `app/core/` — бизнес-логика (`timer.py`, `app_state.py`, `assets.py`)
- `app/scenes/` — сцены и рендер
- `app/data/storage.py` — SQLite слой + инициализация схемы
- `tests/` — unit-тесты

## Pomodoro-возможности

- Строгие состояния таймера: `IDLE`, `FOCUS_RUNNING`, `FOCUS_PAUSED`, `BREAK_RUNNING`, `BREAK_PAUSED`, `FINISHED`, `FAILED`.
- Команды `Start/Pause/Resume/Stop` с точным временем на `time.monotonic()`.
- Пресеты:
  - `Pomodoro 25/5`
  - `Deep 50/10`
  - `TEST 1:00/0:30`
  - `Custom` (через spinbox `Focus/Break`)
- Быстрая правка фокуса: `+5 min` / `-5 min` (минимум 1 минута).
- Настройка **Авто-цикл**: после фокуса автоматически запускается break и следующий focus.
- Сохранение настроек таймера в SQLite settings:
  - выбранный preset
  - focus/break минуты
  - auto_cycle
- История последних сессий (до 50 записей): дата/время, длительность `MM:SS`, успех/провал, тема.

### Горячие клавиши

- `Space` — pause/resume (только если сессия уже активна)
- `Ctrl+Enter` — start из idle/finished/failed

### Логирование сессий

Запись идет в таблицу `sessions(id, started_at, duration_sec, theme, success, coins_earned)`:

- Успешный focus: `success=1`, `duration_sec` фактический (для полной сессии равен длительности фокуса).
- Stop во время focus: `success=0`, `duration_sec` фактически прошедшее время, `coins_earned=0`.
- Stop во время break: не создает fail фокус-сессии.

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
