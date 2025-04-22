import re
import json
import argparse
from pdfminer.high_level import extract_text
from refextract import extract_references_from_string

def pdf_to_text(path: str) -> str:
    """
    Извлекает весь текст из PDF-файла по заданному пути.
    Требуется установка: pip install pdfminer.six
    """
    return extract_text(path)

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
    parser = argparse.ArgumentParser(description="Извлечение ссылок из PDF и формирование JSON.")
    parser.add_argument('--pdf', required=True, help="Путь к PDF-файлу")
    args = parser.parse_args()

    # Извлечение текста из PDF
    pdf_path = args.pdf
    txt = pdf_to_text(pdf_path)
    refs = parse_references(txt)
    authors_titles = build_authors_titles(refs)

    # Вывод в консоль
    # print(json.dumps(authors_titles, ensure_ascii=False, indent=2))

    # Сохранение в файл
    with open("refs_authors_titles.json", "w", encoding="utf-8") as f:
        json.dump(authors_titles, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: refs_authors_titles.json")

if __name__ == "__main__":
    main()