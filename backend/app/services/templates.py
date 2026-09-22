"""Заполнение реальных бланков (.docx/.xlsx): подстановка меток {{TOKEN}} в XML-часть архива.

Шаблоны в ``app/data/templates`` уже токенизированы сборкой ``build/build.py`` (см. корень
репозитория) — заполняемые ячейки/абзацы там заменены на ``{{TOKEN}}``, остальное содержимое
бланка (вёрстка, подписи, зашитый текст) оставлено как есть. Раньше подстановку делал
самодельный ZIP-движок в браузере (без доступа к inflate/deflate); на сервере это делает
стандартный ``zipfile`` — читает и перезаписывает архив любого метода сжатия сам.

Эта функция и есть та единственная логика, которую нужно перенести на портал для заявок
ЦУС/SIM/1С:ПБиОТ — подробности и таблицы токенов см. в ``PORTING.md`` в корне репозитория.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Iterable

from app.errors import AppError

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "data" / "templates"

TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def template_path(key: str) -> Path:
    for extension in (".xlsx", ".docx"):
        path = TEMPLATES_DIR / f"{key}{extension}"
        if path.exists():
            return path
    raise AppError(500, f"Шаблон «{key}» не найден на сервере", code="template_missing")


def fill_template(key: str, values: dict[str, str], text_parts: Iterable[str]) -> bytes:
    parts = set(text_parts)
    path = template_path(key)
    buffer = io.BytesIO()
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename in parts:
                text = data.decode("utf-8")
                text = TOKEN_RE.sub(lambda m: _xml_escape(str(values.get(m.group(1), m.group(0)))), text)
                data = text.encode("utf-8")
            dst.writestr(item, data)
    return buffer.getvalue()
