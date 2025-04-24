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
PAT_AUTHOR_BUILD = re.compile(
    r"[А-ЯЁ][а-яё]+(?:\s*[А-ЯЁ]\.)+"     # Фамилия И.О.
    r"|(?:[А-ЯЁ]\.\s*)+[А-ЯЁ][а-яё]+"    # И.О. Фамилия
)
TITLE_QUOTE = re.compile(r'(.+)')        # оставляем без изменений


def pdf_to_text(path: str) -> str:
    return extract_text(path)


def txt_to_text(path: str) -> str:
    if path.startswith(('http://', 'https://')):
        resp = requests.get(path)
        resp.raise_for_status()
        return resp.text
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def clean_title_from_authors(title: str, authors: list[str]) -> str:
    for auth in authors:
        pattern = rf"{re.escape(auth)}\s*,?\s*"
        title = re.sub(pattern, '', title)
    title = re.sub(r'\s{2,}', ' ', title)
    return title.strip(' ,;:-–—')


def split_authors_and_title(line: str) -> tuple[list[str], str]:
    authors = []
    pos = 0
    # основной проход: авторы подряд в начале строки
    while True:
        m = PAT_AUTHOR_BUILD.match(line, pos)
        if not m:
            break
        auth = ' '.join(m.group(0).split())
        authors.append(auth)
        pos = m.end()
        comma = re.match(r'\s*,\s*', line[pos:])
        if comma:
            pos += comma.end()
        else:
            break

    raw_title = line[pos:].strip()
    # если есть '/', берём первый автора из после '/' и обрезаем всё после него
    if '/' in raw_title:
        left, right = raw_title.split('/', 1)
        m2 = PAT_AUTHOR_BUILD.search(right)
        if m2:
            first_auth = ' '.join(m2.group(0).split())
            authors = [first_auth]
        title = left.strip(' ,;:-–—')
        return authors, title

    # fallback: если авторов не найдено, ищем до '/'
    if not authors:
        head = raw_title.split('/', 1)[0].strip()
        for m3 in PAT_AUTHOR_BUILD.finditer(head):
            auth2 = ' '.join(m3.group(0).split())
            if auth2 not in authors:
                authors.append(auth2)
        raw_title = head

    title = clean_title_from_authors(raw_title, authors)
    return authors, title


def parse_numbered_list(text: str) -> list[dict]:
    items = re.split(r'(?m)^\s*\d+\.\s*', text)[1:]
    result = []
    for item in items:
        if '//' in item or '«' not in item:
            continue
        first_line = next((ln for ln in item.splitlines() if ln.strip()), '').strip()
        if not first_line:
            continue

        raws = TITLE_QUOTE.findall(first_line)
        for raw in raws:
            authors, title = split_authors_and_title(raw)
            if title:
                result.append({'authors': authors, 'title': title})
    return result


def parse_references(text: str) -> list[dict]:
    return extract_references_from_string(text, is_only_references=False)


def build_from_raw(raw_refs: list[dict]) -> list[dict]:
    out = []
    for r in raw_refs:
        raw_list = r.get('raw_ref') or []
        if not raw_list:
            continue
        raw = raw_list[0].strip()
        main_part = re.sub(r'^\s*\d+\.\s*', '', raw)
        parts = re.split(r'\s*/{1,2}\s*', main_part, maxsplit=1)
        left = parts[0].strip()

        authors, title = split_authors_and_title(left)

        # если была правая часть после '/', обрабатываем как единый кейс в split
        if len(parts) > 1 and parts[1].strip():
            combined = f"{left} / {parts[1].strip()}"
            authors, title = split_authors_and_title(combined)

        if title:
            out.append({'authors': authors, 'title': title})
    return out


def deduplicate_references(refs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for r in refs:
        key = (tuple(r['authors']), r['title'].strip())
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="Извлечение ссылек из PDF или TXT: точный парсинг авторов и названий."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pdf', help="Путь к PDF-файлу")
    group.add_argument('--txt', help="Путь или URL к TXT-файлу")
    parser.add_argument('--output', '-o', default="refs_authors_titles.json",
                        help="Имя выходного JSON-файла")
    args = parser.parse_args()

    text = pdf_to_text(args.pdf) if args.pdf else txt_to_text(args.txt)

    list_items = parse_numbered_list(text)
    raw_refs = parse_references(text)
    academic_items = build_from_raw(raw_refs)

    result = deduplicate_references(list_items + academic_items)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {args.output} (обработано {len(result)} записей)")


if __name__ == '__main__':
    main()
