"""fill_template — подстановка {{TOKEN}} в реальных бланках из app/data/templates."""

import io
import zipfile

from app.services.systems_catalog import DOCX_PART, XLSX_PART
from app.services.templates import fill_template

TOKEN_PATTERN = "{{"


def test_xlsx_tokens_are_replaced_and_rest_is_untouched():
    result = fill_template(
        "account",
        {"FIO": "Иванов Иван Иванович", "POST": "инженер", "PHONE": "", "WORKER": "", "PODR": "", "ORDER": ""},
        XLSX_PART,
    )
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in sheet
        assert "инженер" in sheet
        assert TOKEN_PATTERN not in sheet
        # остальные части архива читаются без ошибок (не тронуты подстановкой)
        assert "[Content_Types].xml" in archive.namelist()


def test_docx_tokens_are_replaced():
    values = {
        "PODR": "Группа сопровождения ИС", "RAB": "Иванов Иван Иванович, инженер, +7 900 000-11-22",
        "RUK": "Сидоров Сидор Сидорович, начальник отдела, +7 900 000-33-44", "KEY": "StroyKontrol_IvanovII",
        "D_START": "16", "M_START": "сентября", "Y_START": "26", "D_END": "16", "M_END": "сентября", "Y_END": "27",
        "FIO_RAB_SIGN": "Иванов Иван Иванович", "D_SIGN": "16", "M_SIGN": "сентября", "Y_SIGN": "26",
        "PODR_SIGN": "Группа сопровождения ИС", "FIO_RUK_SIGN": "Сидоров Сидор Сидорович",
    }
    result = fill_template("ai_lab", values, DOCX_PART)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "StroyKontrol_IvanovII" in document
        assert "{{KEY}}" not in document


def test_token_without_a_value_is_left_untouched():
    # Как и в прежнем клиентском движке: нет значения для метки — метка остаётся как есть
    # (используется для полей, оставляемых «от руки», если явно не передано пустое значение).
    result = fill_template("account", {"FIO": "Иванов Иван Иванович"}, XLSX_PART)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in sheet
        assert "{{PODR}}" in sheet


def test_tsus_tokens_are_replaced():
    values = {
        "FIO": "Иванов Иван Иванович", "POST": "инженер", "EMAIL": "i.ivanov@rnsk.rosneft.ru",
        "ACCOUNT": "ROSNEFT\\i.ivanov", "CERT": "StroyKontrol_IvanovII", "ROLE": "(Строительный контроль) - Инженер СК",
    }
    result = fill_template("tsus", values, XLSX_PART)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "StroyKontrol_IvanovII" in sheet
        assert TOKEN_PATTERN not in sheet


def test_sim_tokens_are_replaced():
    values = {
        "FIO": "Иванов Иван Иванович", "PODR": "Группа сопровождения ИС", "POST": "инженер",
        "EMAIL": "i.ivanov@rnsk.rosneft.ru", "FIO_SIGN": "Иванов Иван Иванович",
        "RUK_POST": "начальник отдела", "RUK_FIO": "Сидоров Сидор Сидорович",
    }
    result = fill_template("sim", values, DOCX_PART)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Сидоров Сидор Сидорович" in document
        assert TOKEN_PATTERN not in document


def test_sim_deduction_tokens_are_replaced():
    values = {"POST": "инженер", "PODR": "Группа сопровождения ИС", "FIO": "Иванов Иван Иванович"}
    result = fill_template("sim_deduction", values, DOCX_PART)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in document
        assert TOKEN_PATTERN not in document
