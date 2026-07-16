#!/usr/bin/env python3
"""
Сборка встраиваемых шаблонов заявок.

Для каждого шаблона:
  1) токенизируем — заменяем заполняемые ячейки на метки {{TOKEN}};
  2) пересобираем в ZIP, где document.xml (для xlsx — sharedStrings/лист) хранится
     БЕЗ сжатия (STORED), а прочие части остаются сжатыми (DEFLATE);
  3) base64 и вставляем в index.html между маркерами TEMPLATES.

Браузеру не нужен deflate/inflate: он лишь меняет метки в несжатой части и
копирует остальные части «как есть» (см. zip-движок в index.html).

Зависимости (только для сборки, не для итогового файла): python-docx.
Запуск:  python3 build/build.py
"""
import base64, io, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = os.path.join(ROOT, 'types')
INDEX = os.path.join(ROOT, 'index.html')
OUT = os.path.join(ROOT, 'build', 'tokenized')

# части, которые остаются несжатыми (в них браузер меняет метки)
DOCX_TEXT_PARTS = {'word/document.xml'}


def mixed_zip(docx_path, text_parts):
    """Пересобрать docx: text_parts -> STORED, остальное -> DEFLATE."""
    zin = zipfile.ZipFile(docx_path)
    buf = io.BytesIO()
    zout = zipfile.ZipFile(buf, 'w')
    for it in zin.infolist():
        data = zin.read(it.filename)
        ct = zipfile.ZIP_STORED if it.filename in text_parts else zipfile.ZIP_DEFLATED
        zi = zipfile.ZipInfo(it.filename, date_time=it.date_time)
        zi.compress_type = ct
        zi.external_attr = it.external_attr
        zout.writestr(zi, data)
    zout.close()
    return buf.getvalue()


# ------------------------------------------------------------------ Лаб ИИ
def build_ai_lab():
    from docx import Document
    src = os.path.join(TYPES, 'Заявка Лаборатория ИИ.DOCX')
    doc = Document(src)

    # --- основная таблица: подразделение, работник, руководитель, ключ ---
    t0 = doc.tables[0]
    t0.rows[5].cells[1].text = '{{PODR}}'
    t0.rows[6].cells[1].text = '{{RAB}}'   # ФИО, должность, телефон работника
    t0.rows[7].cells[1].text = '{{RUK}}'   # ФИО, должность, телефон руководителя
    t0.rows[8].cells[1].text = '{{KEY}}'   # имя ключа ПКЗИ

    # --- роль фиксирована: Пользователь (без выбора) ---
    doc.tables[1].rows[0].cells[0].text = ''    # Администратор — пусто
    doc.tables[1].rows[1].cells[0].text = 'X'   # Пользователь — отмечено

    # --- срок действия: «ДД» МЕСЯЦ 20ГГ г. по «ДД» МЕСЯЦ 20ГГ г. (таблица 3) ---
    t3 = doc.tables[3]
    t3.rows[0].cells[1].text  = '{{D_START}}'
    t3.rows[0].cells[3].text  = '{{M_START}}'
    t3.rows[0].cells[6].text  = '{{Y_START}}'
    t3.rows[0].cells[8].text  = '{{D_END}}'
    t3.rows[0].cells[10].text = '{{M_END}}'
    t3.rows[0].cells[12].text = '{{Y_END}}'

    # --- «Ознакомлен с правилами…»: ФИО работника + дата (таблица 5) ---
    t5 = doc.tables[5]
    t5.rows[0].cells[0].text = '{{FIO_RAB_SIGN}}'
    t5.rows[0].cells[5].text = '{{D_SIGN}}'
    t5.rows[0].cells[7].text = '{{M_SIGN}}'
    t5.rows[0].cells[9].text = '{{Y_SIGN}}'

    # --- «Согласовано: руководитель СП»: подразделение + ФИО руководителя (таблица 6) ---
    t6 = doc.tables[6]
    t6.rows[0].cells[1].text = '{{PODR_SIGN}}'
    t6.rows[2].cells[0].text = '{{FIO_RUK_SIGN}}'

    tok = os.path.join(OUT, 'ai_lab.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


# реестр сборщиков: id системы -> функция, возвращающая bytes mixed-zip
BUILDERS = {
    'ai_lab': build_ai_lab,
}


def inject(templates):
    with open(INDEX, encoding='utf-8') as f:
        html = f.read()
    lines = ['window.TEMPLATES = {']
    for key, data in templates.items():
        b64 = base64.b64encode(data).decode('ascii')
        lines.append(f'  "{key}": "{b64}",')
    lines.append('};')
    block = '<script>\n' + '\n'.join(lines) + '\n</script>'
    new = re.sub(
        r'<!--TEMPLATES:START-->.*?<!--TEMPLATES:END-->',
        '<!--TEMPLATES:START-->\n' + block + '\n<!--TEMPLATES:END-->',
        html, flags=re.S)
    if new == html and '<!--TEMPLATES:START-->' not in html:
        raise SystemExit('Маркеры <!--TEMPLATES:START/END--> не найдены в index.html')
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write(new)


def main():
    os.makedirs(OUT, exist_ok=True)
    templates = {}
    for key, fn in BUILDERS.items():
        data = fn()
        templates[key] = data
        print(f'{key}: {len(data)} байт (base64 {len(base64.b64encode(data))})')
    inject(templates)
    print('index.html обновлён.')


if __name__ == '__main__':
    main()
