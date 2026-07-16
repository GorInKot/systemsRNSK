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


# ------------------------------------------------------------------ хелперы
def set_para(par, token):
    """Заменить весь текст абзаца на token, сохранив формат первого run."""
    if par.runs:
        par.runs[0].text = token
        for r in par.runs[1:]:
            r.text = ''
    else:
        par.add_run(token)


def repl_runs(par, start, end, token):
    """Заменить текст runs[start..end] на token (в первом), очистить остальные."""
    runs = par.runs
    runs[start].text = token
    for i in range(start + 1, end + 1):
        runs[i].text = ''


def preserve_space(par, run=0):
    """xml:space="preserve" на w:t run'а — чтобы Word не съедал пробелы,
    которыми браузер дополняет значение метки до фиксированной ширины."""
    from docx.oxml.ns import qn
    for t in par.runs[run]._element.findall(qn('w:t')):
        t.set(qn('xml:space'), 'preserve')


# ------------------------------------------------------------------ ПКЗИ
def build_pkzi():
    from docx import Document
    src = os.path.join(TYPES, '!Заявка на первичную генерацию ключевой информации.docx')
    doc = Document(src)
    t1 = doc.tables[1]

    # подразделение: «ООО «РН-СтройКонтроль», Группа …» → сохраняем префикс, метка вместо «Группа …»
    p = t1.rows[3].cells[1].paragraphs[0]
    repl_runs(p, 1, 2, '{{PODR}}')

    # руководитель СП: должность / ФИО / телефон
    ruk = t1.rows[4].cells[1]
    set_para(ruk.paragraphs[0], '{{RUK_POST}}')
    set_para(ruk.paragraphs[1], '{{RUK_FIO}}')
    repl_runs(ruk.paragraphs[3], 0, 3, '{{RUK_PHONE}}')   # телефон+доб.+номер, дата/подпись сохраняются
    preserve_space(ruk.paragraphs[3])                     # браузер дополняет телефон пробелами до 28 знаков

    # подключаемый пользователь: должность / ФИО / телефон / приказ
    usr = t1.rows[5].cells[1]
    set_para(usr.paragraphs[0], '{{USER_POST}}')
    set_para(usr.paragraphs[1], '{{USER_FIO}}')
    repl_runs(usr.paragraphs[3], 0, 2, '{{USER_PHONE}}')
    preserve_space(usr.paragraphs[3])                     # см. RUK_PHONE
    repl_runs(usr.paragraphs[6], 7, 8, '{{ORDER}}')       # «Приказ № {{ORDER}}»

    # имя сертификата (T1 r2 c2): «Имя сертификата:____» → метка вместо
    # прочерка, значение — с новой строки и подчёркнуто («на линии»);
    # пустое значение браузер заменяет линией «___» (см. mapValues в index.html)
    p = t1.rows[2].cells[2].paragraphs[0]
    p.runs[0].add_break()
    repl_runs(p, 1, 1, '{{CERT}}')
    p.runs[1].underline = True

    # e-mail (T2 r1 c1)
    set_para(doc.tables[2].rows[1].cells[1].paragraphs[0], '{{EMAIL}}')

    # срок использования — НЕ заполняем (оставляем «___» 202_ пустыми)

    tok = os.path.join(OUT, 'pkzi.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


# реестр сборщиков: id системы -> функция, возвращающая bytes mixed-zip
BUILDERS = {
    'ai_lab': build_ai_lab,
    'pkzi': build_pkzi,
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
