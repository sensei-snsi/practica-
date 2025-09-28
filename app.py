from flask import Flask, request, jsonify   # подключаем Flask и функции для работы с HTTP-запросами и JSON-ответами
from werkzeug.utils import secure_filename  # безопасная обработка имён файлов
import os, tempfile                         # работа с файловой системой и временными файлами
from pathlib import Path                    # удобная работа с путями

from log_analyzer import analyze            # импортируем функцию анализа логов из другого модуля

app = Flask(__name__)                       # создаём экземпляр приложения Flask

# Определяем кросс-платформенную временную папку (поддержка Windows/Linux/Mac)
TMP_DIR = Path(tempfile.gettempdir())
TMP_DIR.mkdir(parents=True, exist_ok=True)  # создаём папку, если её нет

def analyze_text_via_tempfile(text: str, top: int):
    """Функция: записывает переданный текст во временный файл и передаёт путь в analyze()."""
    fd, temp_path = tempfile.mkstemp(prefix="log_", suffix=".log", dir=TMP_DIR)  
    os.close(fd)  # закрываем файловый дескриптор, будем писать через open()
    try:
        with open(temp_path, "w", encoding="utf-8") as tmp:
            tmp.write(text)  # записываем весь текст логов
        return analyze(temp_path, topn=int(top))  # вызываем анализатор по пути к файлу
    finally:
        try:
            os.remove(temp_path)  # обязательно удаляем временный файл
        except Exception:
            pass

@app.get("/health")
def health():
    """Простой эндпоинт: проверка, что сервис запущен."""
    return jsonify(status="ok")

@app.post("/analyze")
def analyze_endpoint():
    """
    Основной эндпоинт анализа логов.
    Поддерживает три варианта входа:
      1) multipart/form-data (файл логов в поле file)
      2) text/plain (сырой текст в теле запроса)
      3) application/json (ключ log со строкой логов)
    Параметр top (int) — число записей в «топе» отчёта.
    """
    # Пытаемся взять top из query (?top=10), из формы или JSON. Если нет — значение 5 по умолчанию.
    top = (
        request.args.get("top", type=int)
        or request.form.get("top", type=int)
        or ((request.get_json(silent=True) or {}).get("top") if request.is_json else None)
        or 5
    )

    # Вариант 1: файл в form-data
    if "file" in request.files:
        f = request.files["file"]
        filename = secure_filename(f.filename) or "uploaded.log"  # нормализуем имя файла
        fd, temp_path = tempfile.mkstemp(prefix="upload_", suffix="_" + filename, dir=TMP_DIR)
        os.close(fd)
        try:
            f.save(temp_path)  # сохраняем загруженный файл во временную папку
            report = analyze(temp_path, topn=int(top))  # анализируем
            return jsonify(report=report)
        finally:
            try:
                os.remove(temp_path)  # удаляем временный файл
            except Exception:
                pass

    # Вариант 2: сырой текст в теле запроса (text/plain)
    if request.data and request.content_type and request.content_type.startswith("text/plain"):
        raw_text = request.data.decode("utf-8", errors="ignore")  # декодируем байты в строку
        report = analyze_text_via_tempfile(raw_text, top)
        return jsonify(report=report)

    # Вариант 3: JSON с ключом log
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        if isinstance(payload.get("log"), str):  # проверяем, что log — строка
            report = analyze_text_via_tempfile(payload["log"], top)
            return jsonify(report=report)

    # Если ничего не подошло — возвращаем ошибку 400 и подсказку
    return jsonify(
        error="Дайте логи как 'file' (multipart/form-data), как raw text/plain, или JSON с полем 'log' (string).",
        hint="Пример: POST /analyze?top=5 c form-data: file=@sample_log.txt",
    ), 400

if __name__ == "__main__":
    # Запуск приложения Flask на локальном сервере
    app.run(host="0.0.0.0", port=8000, debug=True)
