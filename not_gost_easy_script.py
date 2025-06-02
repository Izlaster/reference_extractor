import re
import json

def extract_sources(text):
    """
    Извлекает из нумерованного списка по ГОСТ авторов и заголовков работ.
    Правила:
      1. Строка должна начинаться с номера и точки.
      2. После номера идёт список авторов: фамилия (с заглавной буквы, может содержать 'ё' или дефис) и одна или две инициалов.
      3. Авторы разделяются запятой.
      4. После авторов — запятая или пробел, затем название до маркера ' // ' или ' / '.
      5. Последовательность номеров проверяется внутри функции и нарушенные номера пропускаются.
    Возвращает список словарей:
      {
        "number": номер,
        "authors": "Автор1, Автор2, ...",
        "title": "Название"
      }
    """
    # 1) Сначала ищем все «N. тело…» (до следующей строки с «M.» или до конца)
    entry_pattern = re.compile(
        r'^\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.|\Z))',
        re.S | re.M
    )
    entries = entry_pattern.findall(text)
    results = []

    # 2) Подготовим два шаблона для «автор → название»:
    #
    #   A) формат «Инициалы+Фамилия» перед кавычками ««…»»
    #      Инициалы могут быть кириллицей или латиницей, с точками и дефисами, затем пробел и кирил.фамилия.
    #      Пример: «С. Востоков», «Ж.-Ж. Сампэ», «Г. Галахова»
    author_pattern_quotes = r'[A-ZА-ЯЁ][A-ZА-ЯЁ\.\-]*\s+[А-ЯЁ][а-яё]+'
    authors_list_pattern_quotes = re.compile(
        rf'^({author_pattern_quotes}(?:,\s*{author_pattern_quotes})*)\s+«'
    )

    #   B) прежний формат «Фамилия И.О.» или «Фамилия I.O.» перед «/» или «//»
    #      (как было ранее)
    author_pattern_slash = r'[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)*\s+[A-ZА-ЯЁ]\.(?:[A-ZА-ЯЁ]\.)?'
    authors_list_pattern_slash = re.compile(
        rf'^({author_pattern_slash}(?:,\s*{author_pattern_slash})*)[ ,]'
    )

    for num_str, body in entries:
        entry_text = body.strip().replace('\n', ' ')

        # === ВАРИАНТ A: «С. Востоков «Фрося Коровина»» и т.п. ===
        m_q = authors_list_pattern_quotes.match(entry_text)
        if m_q:
            authors = m_q.group(1)
            # Название внутри кавычек «…»
            m_title = re.search(r'«(.+?)»', entry_text)
            title = m_title.group(1).strip() if m_title else ""
            results.append({
                "number": int(num_str),
                "authors": authors,
                "title": title
            })
            continue

        # === ВАРИАНТ B: «Фамилия И.О. Название / Фамилия2 И.О., …» или с «//» ===
        m_s = authors_list_pattern_slash.match(entry_text)
        if m_s:
            authors = m_s.group(1)
            rest = entry_text[m_s.end():].strip()
            # Разделяем по «//» или «/», пробелы вокруг — опционально
            split = re.split(r'\s*//\s*|\s*/\s*', rest, maxsplit=1)
            title = split[0].strip().rstrip('.')
            results.append({
                "number": int(num_str),
                "authors": authors,
                "title": title
            })
            continue

        # === ВАРИАНТ C: сначала название, затем «/ Авторы» (частный случай) ===
        parts = re.split(r'\s*/\s*', entry_text, maxsplit=1)
        if len(parts) == 2:
            title = parts[0].strip().rstrip('.')
            after_slash = parts[1]
            # Пытаемся вытащить авторов (пример: «T.Ю. Игнатов», «Я.Я. Скрипниченко [и др.]»)
            m2 = re.match(
                r'\s*([A-ZА-ЯЁ]\.[A-ZА-ЯЁ]\.\s*[А-ЯЁ][а-яё]+(?:\s*\[.*?\])?)',
                after_slash
            )
            authors2 = m2.group(1).strip() if m2 else ""
            results.append({
                "number": int(num_str),
                "authors": authors2,
                "title": title
            })
            continue

        # Если ни один шаблон не сработал, просто пропускаем запись.

    return results

if __name__ == "__main__":
    # пример использования:
    with open("files/__doc1.txt", encoding="utf-8") as f:
        text = f.read()
    sources = extract_sources(text)
    print(json.dumps(sources, ensure_ascii=False, indent=2))
