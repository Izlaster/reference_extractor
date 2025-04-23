import re
import json
import argparse

# Для обработки PDF
from pdfminer.high_level import extract_text
# Для извлечения ссылок
from refextract import extract_references_from_string

# Для загрузки удалённых txt-файлов по URL
import requests

def pdf_to_text(path: str) -> str:
    """
    Извлекает весь текст из PDF-файла по заданному пути.
    Требуется установка: pip install pdfminer.six
    """
    return extract_text(path)

def txt_to_text(path: str) -> str:
    """
    Получает текст из локального .txt-файла или по HTTP(S)-ссылке.
    Требуется установка (для URL): pip install requests
    """
    if path.startswith(('http://', 'https://')):
        resp = requests.get(path)
        resp.raise_for_status()
        return resp.text
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

def parse_references(text: str) -> list[dict]:
    """
    Извлекает сырые ссылки из текста и возвращает список словарей refextract.
    """
    return extract_references_from_string(text, is_only_references=False)

def build_authors_titles(references: list[dict]) -> list[dict]:
    """
    Из списка словарей refextract формирует новый список с полями:
      - authors: список строк
      - title: строка
    """
    out = []
    split_re = re.compile(r'(.+\.)\s+(.+)')
    for r in references:
        raw_authors = r.get("author", [])
        extra_titles = []
        cleaned_authors = []

        for a in raw_authors:
            m = split_re.match(a)
            if m:
                cleaned_authors.append(m.group(1).strip())
                extra_titles.append(m.group(2).strip())
            else:
                cleaned_authors.append(a.strip())

        misc = r.get("misc", [""])[0].strip().rstrip('.')
        title = " ".join(extra_titles + ([misc] if misc else []))

        # отсекаем всё после '//' (например: // Int. J)
        title = re.split(r'\s*//', title)[0]
        # отсекаем всё после вида 'X.:' (например: 'М.')
        title = re.split(r'\s*[A-Za-zА-ЯЁ]\.:', title)[0]
        title = title.strip().rstrip('.')
        # ===============================================

        out.append({
            "authors": cleaned_authors,
            "title": title
        })
    return out

def main():
    # Настроим парсер аргументов
    parser = argparse.ArgumentParser(
        description="Извлечение ссылок из PDF или TXT и формирование JSON."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pdf', help="Путь к PDF-файлу")
    group.add_argument('--txt', help="Путь или URL к TXT-файлу")
    parser.add_argument('--output', '-o', default="refs_authors_titles.json",
                        help="Имя выходного JSON-файла")
    args = parser.parse_args()

    # Чтение исходного текста
    if args.pdf:
        text = pdf_to_text(args.pdf)
    else:
        text = txt_to_text(args.txt)

    # Извлечение и обработка ссылок
    refs = parse_references(text)
    authors_titles = build_authors_titles(refs)

    # Сохранение в файл
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(authors_titles, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {args.output}")

if __name__ == "__main__":
    main()
