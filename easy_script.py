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
    # Паттерн для извлечения записей
    entry_pattern = re.compile(r'^\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.|\Z))', re.S | re.M)
    entries = entry_pattern.findall(text)
    results = []
    expected_num = 1

    # Шаблон авторов: фамилия с возможным дефисом + пробел + инициалы (1-2)
    author_pattern = r'[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)*\s+[А-Я]\.(?:[А-Я]\.)?'
    # Полный шаблон списка авторов
    authors_list_pattern = re.compile(rf'^({author_pattern}(?:,\s*{author_pattern})*)[ ,]')

    for num_str, body in entries:
        # num = int(num_str)
        # # Проверяем последовательность
        # if num != expected_num:
        #     # пропускаем ломанные номера, но не сбрасываем expected_num
        #     continue
        # expected_num += 1

        # Обрезаем номер и лишние пробелы
        entry_text = body.strip().replace('\n', ' ')

        # Ищем авторов
        m_auth = authors_list_pattern.match(entry_text)
        if not m_auth:
            # не соответствует ГОСТ-авторам
            continue
        authors = m_auth.group(1)
        rest = entry_text[m_auth.end():].strip()

        # Разделяем по маркеру ' // ' или ' / '
        # split = re.split(r'\s//\s|\s/\s', rest, maxsplit=1)
        split = re.split(r'\s*//\s*|\s*/\s*', rest, maxsplit=1)
        title = split[0].strip().rstrip('.')

        results.append({
            # "number": num,
            "authors": authors,
            "title": title
        })

    return results

if __name__ == "__main__":
    # пример использования:
    with open("files/__doc1.txt", encoding="utf-8") as f:
        text = f.read()
    sources = extract_sources(text)
    print(json.dumps(sources, ensure_ascii=False, indent=2))
