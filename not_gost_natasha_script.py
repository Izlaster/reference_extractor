import re
import json
from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc

# Инициализация компонентов Natasha
segmenter = Segmenter()
emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)

def remove_repeated_punct(text: str) -> str:
    """
    Убирает повторения одного и того же знака препинания, оставляя только один экземпляр.
    """
    import re
    punctuation_chars = re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")
    pattern = re.compile(rf'([{punctuation_chars}])\1+')
    return pattern.sub(r'\1', text)

def extract_authors(text):
    """Извлечение имен авторов из текста с помощью Natasha."""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)
    authors = [span.text for span in doc.spans if span.type == 'PER']
    return ', '.join(authors)

def extract_sources(text):
    """
    Извлекает ссылки из нумерованного списка с учетом заданных форматов.
    Использует Natasha для улучшенного извлечения имен авторов.
    """
    text = remove_repeated_punct(text)

    # Регулярное выражение для разделения текста на отдельные записи
    entry_pattern = re.compile(r'^\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.|\Z))', re.S | re.M)
    entries = entry_pattern.findall(text)
    results = []

    for num_str, body in entries:
        entry_text = body.strip().replace('\n', ' ')

        # ВАРИАНТ A: Авторы перед кавычками, например "С. Востоков «Фрося Коровина»"
        if m_q := re.search(r'«', entry_text):
            authors_part = entry_text[:m_q.start()].strip()
            authors = extract_authors(authors_part)
            m_title = re.search(r'«(.+?)»', entry_text)
            title = m_title.group(1).strip() if m_title else ""
            if authors and title:
                results.append({
                    "number": int(num_str),
                    "authors": authors,
                    "title": title
                })
                continue

        # ВАРИАНТ B: Авторы перед слешем, например "Иванов А.Б. Название / ..."
        authors_list_pattern_slash = re.compile(
            r'^([А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)*\s+[A-ZА-ЯЁ]\.(?:[A-ZА-ЯЁ]\.)?(?:,\s*[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)*\s+[A-ZА-ЯЁ]\.(?:[A-ZА-ЯЁ]\.)?)*)[ ,]'
        )
        m_s = authors_list_pattern_slash.match(entry_text)
        if m_s:
            authors_part = m_s.group(1)
            authors = extract_authors(authors_part)
            rest = entry_text[m_s.end():].strip()
            split = re.split(r'\s*//\s*|\s*/\s*', rest, maxsplit=1)
            title = split[0].strip().rstrip('.')
            if authors and title:
                results.append({
                    "number": int(num_str),
                    "authors": authors,
                    "title": title
                })
                continue

        # ВАРИАНТ C: Название перед слешем, авторы после, например "Название / T.Ю. Игнатов"
        parts = re.split(r'\s*//\s*|\s*/\s*', entry_text, maxsplit=1)
        if len(parts) == 2:
            title = parts[0].strip().rstrip('.')
            authors_part = parts[1]
            authors = extract_authors(authors_part)
            if authors and title:
                results.append({
                    "number": int(num_str),
                    "authors": authors,
                    "title": title
                })
                continue

    return results

if __name__ == "__main__":
    # Пример использования: чтение текста из файла
    with open("files/__doc2.txt", encoding="utf-8") as f:
        text = f.read()
    sources = extract_sources(text)
    print(json.dumps(sources, ensure_ascii=False, indent=2))