"""Каталог систем и правила заполнения бланков заявок.

Точный перенос ``SYSTEMS``/``ANKETA`` из прежнего клиентского прототипа (см. LOGIC.md
в корне репозитория) — та же бизнес-логика, тот же набор меток ``{{TOKEN}}`` в шаблонах
из ``app/data/templates``, только на Python и с данными из PostgreSQL вместо localStorage.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Callable

from app.models import EmployeeProfile

RU_MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

# Обоснование доступа — единый текст для заявок КСЭД и ВКД (как в прежнем прототипе).
ACCESS_REASON = "Исполнение служебных обязанностей, обмен информацией с филиалами"

# Действия бланка ПКЗИ (чекбоксы ☒/☐), поделены между карточками «ПКЗИ» и «VipNet / Деловая почта».
PKZI_ACTIONS = [
    "Первичная генерация ключевой информации",
    "Продление сертификата",
    "Создание абонентского пункта «VipNet»",
    "Добавление контактов «VipNet»",
]

# Действия бланка ВКД (☑ по одному пункту), порядок = чекбоксы C9/D9/E9/F9/H9 в шаблоне.
VKD_ACTIONS = [
    "Предоставление доступа Пользователям ВКД",
    "Изменение атрибутов УЗ Пользователей ВКД",
    "Прекращение (изъятие) доступа Пользователей ВКД",
    "Блокировка УЗ в ИС ВКД Пользователей ВКД",
    "Согласование полномочий, присвоенных ранее в экстренном порядке",
]

VKD_ROOMS = ["РНСК", "РНСК КомНПЗ", "РНСК Красноярск", "РНСК Тюмень", "РНСК Уфа"]

FIELD_LABELS = {
    "office": "Офис",
    "full_name": "Ф.И.О.",
    "position": "Должность",
    "phone": "Телефон",
    "order_number": "№ приказа",
    "order_date": "Дата приказа",
    "department": "Подразделение",
    "email": "E-mail",
    "account_name": "Имя учётной записи",
    "pkzi_name": "Имя ключа ПКЗИ",
    "manager_full_name": "ФИО руководителя",
    "manager_position": "Должность руководителя",
    "manager_phone": "Телефон руководителя",
    "vkd_action": "Действие ВКД",
    "vkd_rooms": "Наименование ВКД",
    "seid_role": "Роль в ИР СЭИД",
}

DOCX_PART = {"word/document.xml"}
XLSX_PART = {"xl/worksheets/sheet1.xml"}


def safe(value: str | None) -> str:
    text = value or "без_имени"
    text = re.sub(r"[^\wА-Яа-яЁё]+", "_", text)
    return text[:40]


def pad_to(value: str | None, width: int) -> str:
    """Дополняет пробелами до ``width`` знаков — выравнивание подписи «Телефон … Подпись» в бланке ПКЗИ."""
    return (value or "").ljust(width)


def order_fmt(order_number: str | None, order_date: dt.date | None) -> str:
    """«86-к» + 11.12.2020 → «86-к от 11.12.2020» (как раньше вводили строкой «86-к, 11.12.2020»)."""
    if not order_number:
        return ""
    if order_date:
        return f"{order_number} от {order_date.strftime('%d.%m.%Y')}"
    return order_number


def ru_date_of(day: dt.date) -> tuple[str, str, str]:
    """Дата → ('ДД', 'месяца', 'ГГ') для формулировки «ДД месяца 20ГГ г.»."""
    return f"{day.day:02d}", RU_MONTHS[day.month - 1], f"{day.year % 100:02d}"


def profile_to_dict(profile: EmployeeProfile) -> dict:
    return {
        "office": profile.office,
        "full_name": profile.full_name,
        "position": profile.position,
        "phone": profile.phone,
        "order_number": profile.order_number,
        "order_date": profile.order_date,
        "department": profile.department,
        "email": profile.email,
        "no_email": profile.no_email,
        "account_name": profile.account_name,
        "pkzi_name": profile.pkzi_name,
        "manager_full_name": profile.manager_full_name,
        "manager_position": profile.manager_position,
        "manager_phone": profile.manager_phone,
        "vkd_action": profile.vkd_action,
        "vkd_rooms": list(profile.vkd_rooms or []),
        "seid_role": profile.seid_role,
    }


def with_defaults(data: dict) -> dict:
    """Значения по умолчанию для полей-выборов — они считаются «всегда заполненными» (как в ANKETA)."""
    out = dict(data)
    out.setdefault("office", "head_office")
    if not out.get("office"):
        out["office"] = "head_office"
    if not out.get("vkd_action"):
        out["vkd_action"] = VKD_ACTIONS[0]
    out["vkd_rooms"] = out.get("vkd_rooms") or []
    return out


def _is_set(value) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def _join(*parts: str | None) -> str:
    return ", ".join(p for p in parts if p)


@dataclass
class System:
    id: str
    title: str
    icon: str
    desc: str
    need: list[str]
    hl: bool = False
    ready: bool = True
    text_parts: set[str] = field(default_factory=set)
    template: Callable[[dict], str] | str | None = None
    choice_field: str | None = None
    choice_options: list[str] | None = None
    file_name: Callable[[dict], str] | None = None
    map_values: Callable[[dict], dict] | None = None

    def template_key(self, data: dict) -> str | None:
        return self.template(data) if callable(self.template) else self.template

    def is_xlsx(self) -> bool:
        return any(part.startswith("xl/") for part in self.text_parts)

    def missing_fields(self, data: dict) -> list[str]:
        if not self.ready:
            return []
        resolved = with_defaults(data)
        return [key for key in self.need if not _is_set(resolved.get(key))]


def _make_pkzi(*, id: str, title: str, icon: str, desc: str, actions: list[str], action_field: str, hl: bool = False) -> System:
    def file_name(d: dict) -> str:
        suffix = {
            PKZI_ACTIONS[1]: "_Продление",
            PKZI_ACTIONS[2]: "_АП_VipNet",
            PKZI_ACTIONS[3]: "_Контакты_VipNet",
        }.get(d.get(action_field) or actions[0], "")
        return f"Заявка_ПКЗИ{suffix}_{safe(d.get('full_name'))}.docx"

    def map_values(d: dict) -> dict:
        box = lambda v: "☒" if v else "☐"  # noqa: E731
        act = d.get(action_field) or actions[0]
        today = dt.date.today()
        valid_to = today + dt.timedelta(days=365)
        d_from, m_from, y_from = ru_date_of(today)
        d_to, m_to, y_to = ru_date_of(valid_to)
        return {
            "CHK_GEN": box(act == PKZI_ACTIONS[0]),
            "CHK_PROLONG": box(act == PKZI_ACTIONS[1]),
            "CHK_AP": box(act == PKZI_ACTIONS[2]),
            "CHK_CONTACTS": box(act == PKZI_ACTIONS[3]),
            "D_FROM": d_from, "M_FROM": m_from, "Y_FROM": y_from,
            "D_TO": d_to, "M_TO": m_to, "Y_TO": y_to,
            "PODR": d.get("department") or "",
            "USER_POST": d.get("position") or "", "USER_FIO": d.get("full_name") or "", "USER_PHONE": pad_to(d.get("phone"), 28),
            "RUK_POST": d.get("manager_position") or "", "RUK_FIO": d.get("manager_full_name") or "", "RUK_PHONE": pad_to(d.get("manager_phone"), 28),
            "EMAIL": "в процессе оформления" if d.get("no_email") else (d.get("email") or ""),
            "CERT": d.get("pkzi_name") or "_____________________",
            "ORDER": order_fmt(d.get("order_number"), d.get("order_date")),
        }

    return System(
        id=id, title=title, icon=icon, desc=desc, hl=hl,
        need=["department", "full_name", "position", "manager_full_name", "manager_position"],
        text_parts=DOCX_PART, template="pkzi",
        choice_field=action_field, choice_options=actions,
        file_name=file_name, map_values=map_values,
    )


def _account_map_values(d: dict) -> dict:
    return {
        "FIO": d.get("full_name") or "", "POST": d.get("position") or "", "PHONE": d.get("phone") or "",
        "WORKER": _join(d.get("full_name"), d.get("position"), d.get("phone")),
        "PODR": d.get("department") or "", "ORDER": order_fmt(d.get("order_number"), d.get("order_date")),
    }


def _mail_map_values(d: dict) -> dict:
    return {
        "FIO": d.get("full_name") or "", "POST": d.get("position") or "", "PHONE": d.get("phone") or "",
        "SIZE": "1", "PODR": d.get("department") or "", "ACCOUNT": d.get("account_name") or "", "CERT": d.get("pkzi_name") or "",
        "RUK_FIO": d.get("manager_full_name") or "", "RUK_POST": d.get("manager_position") or "", "RUK_PHONE": d.get("manager_phone") or "",
    }


def _ksed_map_values(d: dict) -> dict:
    return {
        "FIO": d.get("full_name") or "", "ACCOUNT": d.get("account_name") or "", "EMAIL": d.get("email") or "",
        "CERT": d.get("pkzi_name") or "", "PODR": d.get("department") or "", "POST": d.get("position") or "", "REASON": ACCESS_REASON,
    }


def _vkd_map_values(d: dict) -> dict:
    box = lambda v: "☑" if v else "☐"  # noqa: E731
    act = d.get("vkd_action") or VKD_ACTIONS[0]
    rooms = d.get("vkd_rooms") or []
    return {
        "CHK_GRANT": box(act == VKD_ACTIONS[0]),
        "CHK_CHANGE": box(act == VKD_ACTIONS[1]),
        "CHK_REVOKE": box(act == VKD_ACTIONS[2]),
        "CHK_BLOCK": box(act == VKD_ACTIONS[3]),
        "CHK_APPROVE": box(act == VKD_ACTIONS[4]),
        "VDR": ", ".join(rooms),
        "FIO": d.get("full_name") or "", "EMAIL": d.get("email") or "", "PHONE": d.get("phone") or "",
        "ACCOUNT": d.get("account_name") or "", "KEY": d.get("pkzi_name") or "", "REASON": ACCESS_REASON,
    }


def _terminal_map_values(d: dict) -> dict:
    return {"FIO": d.get("full_name") or "", "KEY": d.get("pkzi_name") or ""}


def _tsus_map_values(d: dict) -> dict:
    return {
        "FIO": d.get("full_name") or "", "POST": d.get("position") or "", "EMAIL": d.get("email") or "",
        "ACCOUNT": d.get("account_name") or "", "CERT": d.get("pkzi_name") or "", "ROLE": d.get("seid_role") or "",
    }


def _sim_map_values(d: dict) -> dict:
    return {
        "FIO": d.get("full_name") or "", "PODR": d.get("department") or "", "POST": d.get("position") or "",
        "EMAIL": d.get("email") or "", "FIO_SIGN": d.get("full_name") or "",
        "RUK_POST": d.get("manager_position") or "", "RUK_FIO": d.get("manager_full_name") or "",
    }


def _sim_deduction_map_values(d: dict) -> dict:
    return {"POST": d.get("position") or "", "PODR": d.get("department") or "", "FIO": d.get("full_name") or ""}


def _ai_lab_map_values(d: dict) -> dict:
    today = dt.date.today()
    day = str(today.day)  # без ведущего нуля — как в прежнем шаблоне
    month = RU_MONTHS[today.month - 1]
    year_start = str(today.year)[-2:]
    year_end = str(today.year + 1)[-2:]
    return {
        "PODR": d.get("department") or "",
        "RAB": _join(d.get("full_name"), d.get("position"), d.get("phone")),
        "RUK": _join(d.get("manager_full_name"), d.get("manager_position"), d.get("manager_phone")),
        "KEY": d.get("pkzi_name") or "",
        "D_START": day, "M_START": month, "Y_START": year_start,
        "D_END": day, "M_END": month, "Y_END": year_end,
        "FIO_RAB_SIGN": d.get("full_name") or "", "D_SIGN": day, "M_SIGN": month, "Y_SIGN": year_start,
        "PODR_SIGN": d.get("department") or "", "FIO_RUK_SIGN": d.get("manager_full_name") or "",
    }


SYSTEMS: list[System] = [
    System(
        id="account", title="Учётная запись", icon="👤", hl=True,
        desc="Учётная запись в домене — отправная точка: без неё остальные доступы не оформить. У головного офиса создаётся вместе с почтовым ящиком.",
        need=["office", "full_name", "position", "department"],
        text_parts=XLSX_PART, template=lambda d: "account_fil" if d.get("office") == "branch" else "account",
        file_name=lambda d: f"Заявка_Учётная_запись_{safe(d.get('full_name'))}.xlsx",
        map_values=_account_map_values,
    ),
    System(
        id="mail", title="Почтовый ящик", icon="📧", hl=True,
        desc="Создание почтового ящика (филиал). У головного офиса ящик создаётся заявкой «Учётная запись».",
        need=["full_name", "position", "department", "account_name", "manager_full_name", "manager_position"],
        text_parts=XLSX_PART, template="mail_fil",
        file_name=lambda d: f"Заявка_Почтовый_ящик_{safe(d.get('full_name'))}.xlsx",
        map_values=_mail_map_values,
    ),
    _make_pkzi(
        id="pkzi", title="Ключевая информация ПКЗИ", icon="🔑", hl=True,
        desc="Генерация и продление ключевой информации ПКЗИ (действие — на карточке).",
        actions=PKZI_ACTIONS[:2], action_field="pkzi_action",
    ),
    _make_pkzi(
        id="vipnet", title="VipNet / Деловая почта", icon="✉️",
        desc="Создание абонентского пункта и добавление контактов «VipNet» (действие — на карточке).",
        actions=PKZI_ACTIONS[2:], action_field="vipnet_action",
    ),
    System(
        id="ksed", title="КСЭД", icon="📄",
        desc="Корпоративная система электронного документооборота: первоначальный доступ пользователя.",
        need=["full_name", "account_name", "department", "position"],
        text_parts=XLSX_PART, template="ksed",
        file_name=lambda d: f"Заявка_КСЭД_{safe(d.get('full_name'))}.xlsx",
        map_values=_ksed_map_values,
    ),
    System(
        id="tsus", title="ЦУС / СЭИД", icon="🏗️",
        desc="Добавление в группы ПКЗИ для работы в веб-приложении ИР СЭИД (Центр управления строительством).",
        need=["full_name", "position", "email", "account_name", "pkzi_name", "seid_role"],
        text_parts=XLSX_PART, template="tsus",
        file_name=lambda d: f"Заявка_ЦУС_{safe(d.get('full_name'))}.xlsx",
        map_values=_tsus_map_values,
    ),
    System(
        id="sim", title="SIM-карта", icon="📱",
        desc="Заявка на выдачу или переоформление корпоративной SIM-карты. Паспортные данные, адрес и параметры карты — заполняются от руки.",
        need=["full_name", "department", "position", "manager_full_name", "manager_position"],
        text_parts=DOCX_PART, template="sim",
        file_name=lambda d: f"Заявка_СИМ_{safe(d.get('full_name'))}.docx",
        map_values=_sim_map_values,
    ),
    System(
        id="sim_deduction", title="Удержание за перелимит связи", icon="💳",
        desc="Согласие на ежемесячное удержание из зарплаты суммы превышения лимита на телефонные переговоры.",
        need=["full_name", "department", "position"],
        text_parts=DOCX_PART, template="sim_deduction",
        file_name=lambda d: f"Заявление_Удержание_СИМ_{safe(d.get('full_name'))}.docx",
        map_values=_sim_deduction_map_values,
    ),
    System(id="sap", title="SAP", icon="📊", desc="Доступ к системе SAP.", need=[], ready=False),
    System(id="c1", title="1С", icon="🧮", desc="Доступ к системе «1С».", need=[], ready=False),
    System(
        id="vkd", title="ВКД", icon="🗄️",
        desc="Управление доступом к ИС «Виртуальные комнаты данных».",
        need=["vkd_action", "vkd_rooms", "full_name", "account_name"],
        text_parts=XLSX_PART, template="vkd",
        file_name=lambda d: f"Заявка_ВКД_{safe(d.get('full_name'))}.xlsx",
        map_values=_vkd_map_values,
    ),
    System(
        id="terminal", title="Терминальный сервер", icon="🖥️",
        desc="Доступ к терминальному серверу: добавление в группу «Пользователи АРМ» на МЭ.",
        need=["full_name", "pkzi_name"],
        text_parts=XLSX_PART, template="terminal",
        file_name=lambda d: f"Заявка_Терминальный_сервер_{safe(d.get('full_name'))}.xlsx",
        map_values=_terminal_map_values,
    ),
    System(
        id="ai_lab", title="Лаборатория ИИ", icon="🧪",
        desc="Управление доступом к стенду «Лаборатория искусственного интеллекта».",
        need=["department", "full_name", "position", "manager_full_name", "manager_position"],
        text_parts=DOCX_PART, template="ai_lab",
        file_name=lambda d: f"Заявка_ЛабИИ_{safe(d.get('full_name'))}.docx",
        map_values=_ai_lab_map_values,
    ),
]

SYSTEMS_BY_ID: dict[str, System] = {system.id: system for system in SYSTEMS}


def get_system(system_id: str) -> System | None:
    return SYSTEMS_BY_ID.get(system_id)
