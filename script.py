import re
import json
import argparse

# Для обработки PDF
from pdfminer.high_level import extract_text
# Для извлечения ссылок академического формата
from refextract import extract_references_from_string
# Для загрузки удалённых txt-файлов по URL
import requests

# Паттерны для авторов и заголовков
PAT_AUTHOR1 = re.compile(r"[А-ЯЁ][а-яё]+(?:\s*[А-ЯЁ]\.)+")       # Фамилия И.О.
PAT_AUTHOR2 = re.compile(r"(?:[А-ЯЁ]\.\s*)+[А-ЯЁ][а-яё]+")        # И.О. Фамилия
PAT_AUTHOR_BUILD = re.compile(
    r"[А-ЯЁ][а-яё]+(?:\s*[А-ЯЁ]\.)+"     # Фамилия И.И.
    r"|(?:[А-ЯЁ]\.\s*)+[А-ЯЁ][а-яё]+"    # И.И. Фамилия
)
TITLE_QUOTE = re.compile(r'«([^»]+)»')                                # Названия в «»


def pdf_to_text(path: str) -> str:
    """
    Извлекает весь текст из PDF-файла.
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
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_numbered_list(text: str) -> list[dict]:
    """
    Парсит нумерованный список чистых заголовков (списки книг, пункты без '//').
    """
    items = re.split(r'(?m)^\s*\d+\.\s*', text)[1:]
    result = []
    for item in items:
        if '//' in item:
            continue
        if '«' not in item:
            continue
        lines = [ln for ln in item.splitlines() if ln.strip()]
        if not lines:
            continue
        line = lines[0].strip()
        # авторы
        authors = []
        for pat in (PAT_AUTHOR1, PAT_AUTHOR2):
            authors += pat.findall(line)
        authors = [' '.join(a.split()) for a in authors]
        # заголовки
        titles = TITLE_QUOTE.findall(line)
        for t in titles:
            result.append({'authors': authors, 'title': t.strip()})
    return result


def parse_references(text: str) -> list[dict]:
    """
    Извлекает сырые академические ссылки из текста (пункты с '//').
    """
    return extract_references_from_string(text, is_only_references=False)


def build_from_raw(raw_refs: list[dict]) -> list[dict]:
    """
    Пост-обработка академических ссылок: парсинг авторов по позиции и заголовков.
    """
    out = []
    for r in raw_refs:
        raw_list = r.get('raw_ref') or []
        if not raw_list:
            continue
        raw = raw_list[0].strip()
        # удаляем нумерацию
        main_part = re.sub(r'^\s*\d+\.\s*', '', raw)
        # убираем всё после '//' для академических ссылок
        parts = main_part.split('//', 1)
        main_part = parts[0].strip()

        # извлечение авторов по позиции
        authors = []
        pos = 0
        while True:
            m = PAT_AUTHOR_BUILD.match(main_part, pos)
            if not m:
                break
            auth = ' '.join(m.group(0).split())
            authors.append(auth)
            pos = m.end()
            comma = re.match(r'\s*,\s*', main_part[pos:])
            if comma:
                pos += comma.end()
            else:
                break

        # поиск заголовков
        titles = TITLE_QUOTE.findall(main_part)
        if titles:
            for t in titles:
                out.append({'authors': authors, 'title': t.strip()})
        else:
            # fallback: текст после списка авторов
            tail = main_part[pos:].lstrip(' ,.—:').rstrip('.')
            if tail:
                out.append({'authors': authors, 'title': tail.strip()})
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Извлечение ссылок из PDF или TXT: точный парсинг авторов и названий."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pdf', help="Путь к PDF-файлу")
    group.add_argument('--txt', help="Путь или URL к TXT-файлу")
    parser.add_argument('--output', '-o', default="refs_authors_titles.json",
                        help="Имя выходного JSON-файла")
    args = parser.parse_args()

    text = pdf_to_text(args.pdf) if args.pdf else txt_to_text(args.txt)

    # пункты без '//' — нумерованные списки книг
    list_items = parse_numbered_list(text)
    # академические ссылки с '//'
    raw_refs = parse_references(text)
    academic_items = build_from_raw(raw_refs)

    # объединяем и сохраняем
    result = list_items + academic_items
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {args.output} (обработано {len(result)} записей)")

if __name__ == '__main__':
    main()
