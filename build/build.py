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


def underline_token(par, prefix, token, suffix=''):
    """Заменить первый run параграфа на prefix + token + suffix: token выходит
    подчёркнутым (имитирует заполненную «___» линию бланка), prefix/suffix — обычным
    начертанием исходного run (шрифт/размер копируются в новые runs). Остальные runs
    параграфа (если есть) не трогаем — они остаются сразу после вставленных.

    ``paragraph.add_run`` всегда добавляет run в конец параграфа, поэтому новые runs
    сперва создаются там, а затем переставляются на место первого run через
    ``addnext`` (в обратном порядке — suffix, потом token, — чтобы после каждой
    перестановки порядок token→suffix не ломался)."""
    import copy
    from docx.oxml.ns import qn
    template = par.runs[0]
    rpr = template._element.find(qn('w:rPr'))
    template.text = prefix
    token_run = par.add_run(token)
    if rpr is not None:
        token_run._element.insert(0, copy.deepcopy(rpr))
    token_run.underline = True
    suffix_run = None
    if suffix:
        suffix_run = par.add_run(suffix)
        if rpr is not None:
            suffix_run._element.insert(0, copy.deepcopy(rpr))
    if suffix_run is not None:
        template._element.addnext(suffix_run._element)
    template._element.addnext(token_run._element)


def preserve_space(par, run=0):
    """xml:space="preserve" на w:t run'а — чтобы Word не съедал пробелы,
    которыми браузер дополняет значение метки до фиксированной ширины."""
    from docx.oxml.ns import qn
    for t in par.runs[run]._element.findall(qn('w:t')):
        t.set(qn('xml:space'), 'preserve')


def unwrap_sdt(sdt):
    """Заменить content control (w:sdt) его содержимым (w:sdtContent).
    Чекбокс перестаёт быть интерактивным — остаётся простой текст ☒/☐,
    который никто случайно не перещёлкнет в Word."""
    from docx.oxml.ns import qn
    parent = sdt.getparent()
    idx = list(parent).index(sdt)
    for child in reversed(list(sdt.find(qn('w:sdtContent')))):
        parent.insert(idx, child)
    parent.remove(sdt)


def sym_to_token(run, token):
    """Заменить run-чекбокс, отрисованный шрифтовым символом (``<w:sym w:font="Wingdings"
    .../>`` — пустой квадрат, без интерактивности и без пары «отмеченный» символ в этом же
    шрифте), обычным текстовым токеном. На сервере он подставится реальным ☒/☐ (Arial),
    как везде в остальных бланках."""
    from docx.oxml.ns import qn
    sym = run._element.find(qn('w:sym'))
    if sym is not None:
        run._element.remove(sym)
    run.text = token


# ------------------------------------------------------------------ ПКЗИ
def build_pkzi():
    from docx import Document
    from docx.oxml.ns import qn
    src = os.path.join(TYPES, '!Заявка на первичную генерацию ключевой информации.docx')
    doc = Document(src)
    t1 = doc.tables[1]

    # действие (T1 r1 c2): чекбоксы w14:checkbox → метки ☒/☐ из формы.
    # Порядок в ячейке: генерация, продление, АП VipNet, контакты VipNet,
    # переименование (последний не токенизируем — остаётся пустым ☐).
    tc = t1.rows[1].cells[2]._tc
    boxes = [t for t in tc.iter(qn('w:t')) if t.text in ('☒', '☐')]
    assert len(boxes) == 5, f'ожидалось 5 чекбоксов действий, найдено {len(boxes)}'
    for t, tok in zip(boxes, ['{{CHK_GEN}}', '{{CHK_PROLONG}}',
                              '{{CHK_AP}}', '{{CHK_CONTACTS}}']):
        t.text = tok
        unwrap_sdt(next(t.iterancestors(qn('w:sdt'))))

    # срок использования (абзац 4 тела): с «___» ______ 202_ г. до «___» … —
    # день/месяц/год обоих дат; пустые значения браузер заменяет прочерками
    # и пробелами исходного бланка (см. mapValues в index.html)
    p = doc.paragraphs[4]
    repl_runs(p, 2, 4, '{{D_FROM}}')     # «___» день
    repl_runs(p, 6, 7, '{{M_FROM}}')     # месяц (пустое место бланка)
    repl_runs(p, 9, 9, '{{Y_FROM}}')     # «202_» → 20{{Y_FROM}}
    repl_runs(p, 14, 15, '{{D_TO}}')
    repl_runs(p, 17, 17, '{{M_TO}}')
    repl_runs(p, 19, 19, '{{Y_TO}}')
    for i in (2, 6, 9, 14, 17, 19):
        preserve_space(p, i)

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

    # Жёлтая подсветка в исходном бланке отмечает места для ручного заполнения.
    # В автоматически заполненной заявке она не нужна — убираем её со всех
    # фрагментов, не затрагивая остальное форматирование текста.
    for highlight in list(doc.element.iter(qn('w:highlight'))):
        if highlight.get(qn('w:val')) == 'yellow':
            highlight.getparent().remove(highlight)

    # срок использования — НЕ заполняем (оставляем «___» 202_ пустыми)

    tok = os.path.join(OUT, 'pkzi.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


# --------------------------------------------------- листы ШаблонОбщий.xlsx
def build_sheet(sheet, cells, out_name, merges=()):
    """Оставить в ШаблонОбщий.xlsx один лист `sheet`, вписать метки `cells`
    ({coord: '{{TOKEN}}'}), пересобрать. openpyxl пишет строки inline (без
    sharedStrings) → текстовая часть для замены — xl/worksheets/sheet1.xml.
    № заявки/даты/подписи бланка — от руки."""
    import openpyxl
    src = os.path.join(TYPES, 'ШаблонОбщий.xlsx')
    wb = openpyxl.load_workbook(src)
    for name in list(wb.sheetnames):
        if name != sheet:
            del wb[name]
    ws = wb[sheet]
    for cell_range in merges:
        ws.merge_cells(cell_range)
    for coord, val in cells.items():
        ws[coord] = val
    tok = os.path.join(OUT, out_name)
    wb.save(tok)
    return mixed_zip(tok, {'xl/worksheets/sheet1.xml'})


# ------------------------------------------------------- Терминальный сервер
def build_terminal():
    """Лист «6.Терминальный сервер»: заявка на изменение правил МЭ (группа
    AD_RNSK_TRM_Users_WS). Коллективная таблица на одного человека:
    D14 — ФИО, E14 — наименование ПКЗИ."""
    return build_sheet('6.Терминальный сервер',
                       {'D14': '{{FIO}}', 'E14': '{{KEY}}'}, 'terminal.xlsx')


# --------------------------------------------------------- Учётная запись
def build_account():
    """Лист «2.УЗ» (головной офис): создание учётной записи в домене
    rosneft.ru. Бланк заодно просит создать почтовый ящик (E12 — фикс. текст),
    поэтому у головного отдельной заявки на почту нет. Коллективная таблица
    на одного: B12 — ФИО, B13 — должность, B14 — телефон,
    D12:D14 — объединённое основание (приказ),
    D16 — подразделение. C1 — подписант «Подразделение ИТ» (Еременко А.С.)."""
    return build_sheet('2.УЗ', {
        'C1': 'Еременко А.С.',
        'B12': '{{FIO}}',
        'B13': '{{POST}}',
        'B14': '{{PHONE}}',
        'D12': 'Приказ о приеме на работу {{ORDER}}',
        'D16': '{{PODR}}',
    }, 'account.xlsx', merges=('D12:D14',))


def build_account_fil():
    """Лист «УЗ (Филиал)»: создание учётной записи через ООО ИК «СИБИНТЕК»
    (группа PKZI_EKTS_EX_Clients_CDC). На одного: B16 — ФИО/должность/телефон,
    C16 — Общество Группы, D16 — подразделение."""
    return build_sheet('УЗ (Филиал)', {
        'B16': '{{WORKER}}',
        'C16': 'ООО «РН-СтройКонтроль»',
        'D16': '{{PODR}}',
    }, 'account_fil.xlsx')


def build_ksed():
    """Лист «4.КСЭД»: заявка «Управление доступом к КСЭД», тип «Первоначальный
    доступ пользователя к ИР» (зашит в бланке, как и ДЕЙСТВИЕ/ПРОФИЛЬ/СРОК).
    Таблица сотрудников на одного (строка 13): B — ФИО, C — УЗ, D — e-mail,
    E — ПКЗИ, F — СП, G — должность, J — обоснование. Колонки «принимающий
    права» (K/L) — для передачи прав, при первичном доступе пусты."""
    return build_sheet('4.КСЭД', {
        'B13': '{{FIO}}',
        'C13': '{{ACCOUNT}}',
        'D13': '{{EMAIL}}',
        'E13': '{{CERT}}',
        'F13': '{{PODR}}',
        'G13': '{{POST}}',
        'J13': '{{REASON}}',
    }, 'ksed.xlsx')


def build_mail_fil():
    """Лист «ПЯ (Филиал)»: создание почтового ящика в домене rosneft.ru
    (филиал). C13 — ФИО, C14 — должность, C15 — телефон,
    C16 — объём ящика (Гб),
    C18 — подразделение, C19 — имя УЗ в домене, C20 — имя сертификата ПКЗИ,
    C21 — ФИО руководителя, C22 — его должность, C23 — телефон."""
    return build_sheet('ПЯ (Филиал)', {
        'C13': '{{FIO}}',
        'C14': '{{POST}}',
        'C15': '{{PHONE}}',
        'C16': '{{SIZE}}',
        'C18': '{{PODR}}',
        'C19': '{{ACCOUNT}}',
        'C20': '{{CERT}}',
        'C21': '{{RUK_FIO}}',
        'C22': '{{RUK_POST}}',
        'C23': '{{RUK_PHONE}}',
    }, 'mail_fil.xlsx')


# ------------------------------------------------------------------ ЦУС
def build_tsus():
    """Файл «Заявка ЦУС.xlsx» (добавление в группы ПКЗИ для доступа к ИР СЭИД),
    один лист «ЗаявкаЦУС». Строка 9 — пример сотрудника; ОГ (D9) — фиксированный
    текст (сотрудники «РН-СтройКонтроль»), не трогаем."""
    import openpyxl
    src = os.path.join(TYPES, 'Заявка ЦУС.xlsx')
    wb = openpyxl.load_workbook(src)
    ws = wb.active
    ws['E9'] = '{{FIO}}'
    ws['F9'] = '{{POST}}'
    ws['G9'] = '{{EMAIL}}'
    ws['H9'] = '{{ACCOUNT}}'
    ws['I9'] = '{{CERT}}'
    ws['J9'] = '{{ROLE}}'
    tok = os.path.join(OUT, 'tsus.xlsx')
    wb.save(tok)
    return mixed_zip(tok, {'xl/worksheets/sheet1.xml'})


# ------------------------------------------------------------------ СИМ
def build_sim():
    """Файл «Заявка СИМ-карта.docx» (выдача/переоформление SIM-карты). Тип/размер
    SIM и переоформление на физ.лицо/ООО — отмечаются от руки (в бланке нет
    чекбокс-символов, только подписи вариантов через «Нужное отметить»),
    паспортные данные, дата рождения, адрес, Госуслуги — тоже от руки
    (персональные данные, которых нет в анкете)."""
    from docx import Document
    src = os.path.join(TYPES, 'Заявка СИМ-карта.docx')
    doc = Document(src)
    t0 = doc.tables[0]
    t0.rows[0].cells[1].text = '{{FIO}}'
    t0.rows[1].cells[1].text = '{{PODR}}'
    t0.rows[2].cells[1].text = '{{POST}}'
    t0.rows[5].cells[1].text = '{{EMAIL}}'

    # подпись работника (согласие на обработку ПДн): «/_____/» → «/{{FIO_SIGN}}/»
    doc.paragraphs[11].runs[0].text = '/{{FIO_SIGN}}/'
    # «Согласовано»: должность руководителя (подчёркнутая — как заполненная линия бланка) и ФИО
    underline_token(doc.paragraphs[18], '', '{{RUK_POST}}')
    doc.paragraphs[21].runs[0].text = '/{{RUK_FIO}}/'

    # поле «Подпись» в обоих блоках (работник и руководитель) — удлиняем линию
    # на 8 подчёркиваний (было 14, стало 22): после подстановки ФИО в те же
    # строки места под реальную подпись остаётся визуально меньше, чем в
    # исходном пустом бланке.
    for idx in (11, 21):
        signature_run = doc.paragraphs[idx].runs[1]
        signature_run.text = signature_run.text.replace('______________', '______________' + '________', 1)

    tok = os.path.join(OUT, 'sim.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


def build_sim_deduction():
    """Файл «Заявление об удержании СИМ.docx» (согласие на удержание из
    зарплаты суммы превышения лимита связи). Три строки данных заявителя —
    значения подчёркнуты, как заполненная от руки линия бланка; номер
    телефона и подпись/дата — от руки."""
    from docx import Document
    src = os.path.join(TYPES, 'Заявление об удержании СИМ.docx')
    doc = Document(src)
    underline_token(doc.paragraphs[3], 'от  ', '{{POST}}')
    underline_token(doc.paragraphs[4], '', '{{PODR}}')
    underline_token(doc.paragraphs[5], '', '{{FIO}}', '  (Должность/')

    tok = os.path.join(OUT, 'sim_deduction.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


# ------------------------------------------------------------------ 1С:ПБиОТ
def build_c1_pbiot():
    """Файл «Заявка 1С ПБиОТ.docx» (управление доступом к ИР 1С:ПБиОТ — охрана
    труда). Таблица пользователя (табл. 2) содержит ДВА примера сотрудников
    (строки 4–5) — заполняем первый, второй вычищаем. Чекбоксы действия
    («предоставить полномочия» / «прекратить доступ», строка 1) в исходнике —
    не текст ☐/☒, а шрифтовый символ Wingdings (``<w:sym>``): переводим в
    обычный текстовый токен через sym_to_token. Список ролей (24 пункта,
    табл. 3) и тип подключения ЕКТС/не ЕКТС — вообще без чекбоксов, отмечаются
    от руки — таблицу ролей не трогаем."""
    from docx import Document
    src = os.path.join(TYPES, 'Заявка 1С ПБиОТ.docx')
    doc = Document(src)

    t2 = doc.tables[2]
    t2.rows[0].cells[1].text = 'ООО «РН-СтройКонтроль»'

    action_runs = t2.rows[1].cells[0].paragraphs[0].runs
    sym_to_token(action_runs[2], '{{CHK_GRANT}}')
    sym_to_token(action_runs[7], '{{CHK_REVOKE}}')

    data = t2.rows[4].cells
    data[0].text = '{{FIO}}'
    data[1].text = '{{PODR_POST}}'
    data[2].text = '{{RUK}}'
    data[3].text = '{{EMAIL}}'
    data[4].text = '{{PHONE}}'         # столбцы 4–5 объединены (телефон)
    data[6].text = ''                  # «рабочее место» — нет такого поля в анкете
    data[7].text = '{{ACCOUNT}}'
    data[8].text = '{{CERT}}'
    data[9].text = 'Нет'               # «ограничения доступа к данным» — по умолчанию нет
    data[10].text = ''                 # «подпись работника» — от руки
    for cell in t2.rows[5].cells:      # второй сотрудник-пример — вычищаем
        cell.text = ''

    doc.tables[6].rows[0].cells[0].text = '{{RUK_FIO_SIGN}}'

    tok = os.path.join(OUT, 'c1_pbiot.docx')
    doc.save(tok)
    return mixed_zip(tok, DOCX_TEXT_PARTS)


# ------------------------------------------------------------------ ВКД
def build_vkd():
    """Файл «Заявка ВКД.xlsx» (ИС «Виртуальные комнаты данных»), один лист.
    Блок «Действия с учётной записью» — чекбоксы ☑/☐ (выбор одного пункта,
    как в ПКЗИ) → метки на месте символа. Таблица пользователей (4 блока по
    6 строк) в исходнике содержит ТРИ реальных сотрудника-примера — их
    вычищаем; заполняем первый блок (строки 15–20) на одного человека,
    блоки 2–4 очищаем."""
    import openpyxl
    src = os.path.join(TYPES, 'Заявка ВКД.xlsx')
    wb = openpyxl.load_workbook(src)
    ws = wb.active

    # действие: заменяем символ ☑/☐ в начале строки на метку, текст сохраняем
    actions = {'C9': '{{CHK_GRANT}}', 'D9': '{{CHK_CHANGE}}',
               'E9': '{{CHK_REVOKE}}', 'F9': '{{CHK_BLOCK}}', 'H9': '{{CHK_APPROVE}}'}
    for coord, tok in actions.items():
        cur = ws[coord].value
        ws[coord] = tok + cur[1:]   # cur[0] — символ ☑/☐

    # первый блок пользователя (строки 15–20): D17 «Компания» и E15 «☑До срока
    # действия ВКД» оставляем как есть (значения по умолчанию бланка)
    ws['B15'] = '{{VDR}}'       # наименование ВКД
    ws['D15'] = '{{FIO}}'
    ws['D16'] = '{{EMAIL}}'
    ws['D20'] = '{{PHONE}}'     # моб. телефон для SMS-кода
    ws['F15'] = '{{ACCOUNT}}'   # имя учётной записи
    ws['G15'] = '{{KEY}}'       # имя ключа ПКЗИ-КТ
    ws['H15'] = '{{REASON}}'    # основание предоставления доступа

    # очищаем блоки 2–4 от данных сотрудников-примеров (оставляем только метки-
    # подписи столбцов C: «ФИО:», «E-mail:» и т.п.)
    for start in (21, 27, 33):
        for col in ('B', 'D', 'F', 'G', 'H', 'E'):
            ws[f'{col}{start}'] = None
        ws[f'D{start+1}'] = None   # e-mail
        ws[f'D{start+2}'] = None   # компания

    tok = os.path.join(OUT, 'vkd.xlsx')
    wb.save(tok)
    return mixed_zip(tok, {'xl/worksheets/sheet1.xml'})


# реестр сборщиков: id системы -> функция, возвращающая bytes mixed-zip
BUILDERS = {
    'ai_lab': build_ai_lab,
    'pkzi': build_pkzi,
    'terminal': build_terminal,
    'account': build_account,
    'account_fil': build_account_fil,
    'mail_fil': build_mail_fil,
    'ksed': build_ksed,
    'vkd': build_vkd,
    'tsus': build_tsus,
    'sim': build_sim,
    'sim_deduction': build_sim_deduction,
    'c1_pbiot': build_c1_pbiot,
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
