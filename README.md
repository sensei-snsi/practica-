# README.md

## Назначение

Проект предоставляет простой и быстрый обработчик логов с двумя режимами работы:

1. **CLI** — разовый анализ локального файла с выводом сводки в консоль.  
2. **REST API (Flask)** — сервис с эндпоинтом `/analyze`, принимающий логи файлом, «сырым» текстом или JSON и возвращающий отчёт в формате JSON.

Подходит для учебных и прикладных задач: разбора смешанных текстовых журналов, первичной диагностики ошибок, подсчёта частот и поиска «медленных» операций.

## Возможности

- Поддержка двух форматов строк:
  - Apache-подобные: `IP [дата] "метод путь" статус размер`
  - ISO-строки: `YYYY-MM-DDTHH:MM:SS(.us)Z LEVEL IP - сообщение`
- Подсчёт:
  - по уровням (INFO/WARN/ERROR/OTHER),
  - по IP-адресам,
  - по сообщениям (топ N),
  - по HTTP-статусам (для Apache-логов),
  - ошибок по часам (группировка по UTC-часу),
  - «медленных» строк по `duration_ms`.
- Работа с повреждёнными строками и смешанной кодировкой (`errors="ignore"`).
- Безопасная обработка загружаемых файлов (временные файлы, `secure_filename`).

## Примеры форматов входных логов

```
127.0.0.1 - - [25/Sep/2025:10:15:32 +0000] "GET /api/v1/items HTTP/1.1" 200 123
10.0.0.5 - - [25/Sep/2025:10:16:01 +0000] "POST /login HTTP/1.1" 500 0
2025-09-26T06:32:14Z INFO 192.168.1.18 - DB timeout duration_ms=800
2025-09-26T06:35:55.123Z ERROR 10.1.2.3 - Payment failed order=42 duration_ms=1200
```

## Структура репозитория

```
.
├─ app.py                           # REST API (Flask): /health, /analyze
├─ log_analyzer.py                  # Логика анализа: parse_ts, analyze, CLI main
├─ requirements.txt                 # Зависимости (Flask)
├─ README.md                        # Этот файл
├─ Log Analyzer API.postman_collection.json   # Коллекция Postman
└─ sample_log.txt                   # Тестовый лог (пример)
```

## Установка

1) Python 3.11 (рекомендуется).  
2) Создать виртуальное окружение и установить зависимости:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

### 1) CLI-анализ

```bash
python log_analyzer.py sample_log.txt --top 10
```

### 2) REST API (Flask)

```bash
python app.py
```

Сервис поднимется на `http://localhost:8000`.

Эндпоинты:
- `GET /health` → `{"status":"ok"}`
- `POST /analyze` → `{"report": "<многострочный_текст_отчёта>"}`

## Примеры запросов к API

### Загрузка файла (multipart/form-data)
```bash
curl -X POST "http://localhost:8000/analyze?top=5"   -F "file=@sample_log.txt"
```

### Сырой текст (text/plain)
```bash
curl -X POST "http://localhost:8000/analyze?top=5"   -H "Content-Type: text/plain"   --data-binary @sample_log.txt
```

### JSON с полем `log`
```bash
curl -X POST "http://localhost:8000/analyze"   -H "Content-Type: application/json"   -d '{"top":7, "log":"2025-09-26T06:32:14Z INFO 192.168.1.18 - DB timeout duration_ms=800\n"}'
```

## Производительность

- Один проход O(n); память — пропорционально числу уникальных IP/сообщений.  
- На примере ~400 строк — менее 0.1 с на обычном ноутбуке.  

## Ограничения и планы

- Не поддерживаются структурированные JSON-логи «как есть».  
- Нет экспорта в CSV/JSON и визуализации.  
- Нет ограничения размера загружаемого файла.  

## Тестирование

- Коллекция Postman `Log Analyzer API.postman_collection.json` включает проверки для /health и /analyze.  
- Дополнительно можно использовать примеры curl выше.
