# PDF Reference Extractor

Этот скрипт предназначен для извлечения ссылок на литературу из PDF и TXT файлов, а также формирования JSON-вывода с полями `authors` и `title`. Он использует библиотеки:

- `pdfminer.six` для извлечения текста из PDF
- `refextract` для парсинга ссылок
- `requests` (опционально) для загрузки TXT-файлов по URL

## Требования

Перед использованием убедитесь, что у вас установлены следующие зависимости:

- Python 3.10 или выше
- Poetry для управления зависимостями и виртуальными окружениями

## Установка

1. Установите Python 3.10 (или выше), если он ещё не установлен.
2. Установите Poetry:

    ```bash
    curl -sSL https://install.python-poetry.org | python3
    ```

3. Клонируйте этот репозиторий или скачайте код:

    ```bash
    git clone https://github.com/your-repository/pdf-reference-extractor.git
    cd pdf-reference-extractor
    ```

4. Установите зависимости:

    ```bash
    poetry install
    ```

## Использование

После установки зависимостей скрипт можно запустить для обработки PDF и TXT:

```bash
# Из PDF-файла
poetry run python script.py --pdf /путь/к/файлу.pdf

# Из локального TXT-файла
poetry run python script.py --txt /путь/к/файлу.txt

# Из удалённого TXT-файла по URL
poetry run python script.py --txt https://example.com/file.txt

# Указать имя выходного файла JSON
poetry run python script.py --pdf /путь/к/файлу.pdf --output output.json
```

После выполнения скрипт извлечёт все ссылки на литературу и сохранит результат в JSON-файл.

### Пример вывода

```json
[
  {
    "authors": [
      "Bishop C.M."
    ],
    "title": "Pattern Recognition and Machine Learning"
  },
  {
    "authors": [
      "Hastie T.", "Tibshirani R.", "Friedman J."
    ],
    "title": "The Elements of Statistical Learning"
  }
]
```

## Параметры командной строки

- `--pdf <path>` — путь к PDF-файлу для обработки.
- `--txt <path_or_url>` — путь к локальному TXT-файлу или URL для загрузки и обработки.
- `-o, --output <file>` — (опционально) имя выходного JSON-файла (по умолчанию `refs_authors_titles.json`).
