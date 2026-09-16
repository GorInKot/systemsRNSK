"""Демонстрационные данные для разработки и показа.

    python -m app.seed           наполнить базу, если анкеты ещё нет
    python -m app.seed --reset   удалить все анкеты и создать демо-набор заново
"""

import argparse
import sys
from datetime import date

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from app.auth import DEV_USERS
from app.config import get_settings
from app.db import SessionLocal
from app.models import EmployeeProfile, User
from app.services.systems_catalog import VKD_ACTIONS


def ensure_users(db) -> dict[str, User]:
    for login, (full_name, email, department, is_admin) in DEV_USERS.items():
        values = {"login": login, "full_name": full_name, "email": email, "department": department, "is_admin": is_admin}
        db.execute(insert(User).values(**values).on_conflict_do_update(index_elements=[User.login], set_=values))
    db.commit()
    return {user.login: user for user in db.scalars(select(User).where(User.login.in_(DEV_USERS)))}


def seed(reset: bool) -> None:
    settings = get_settings()
    if settings.environment == "production":
        sys.exit("Демо-данные нельзя загружать при ENVIRONMENT=production.")

    with SessionLocal() as db:
        existing = db.scalar(select(func.count()).select_from(EmployeeProfile))
        if existing and not reset:
            print(f"В базе уже есть анкеты ({existing}). Для пересоздания запустите с --reset.")
            return
        if reset:
            db.execute(text("TRUNCATE generated_requests, employee_profiles RESTART IDENTITY CASCADE"))
            db.commit()

        users = ensure_users(db)

        # Собственная анкета сотрудника — заполнена полностью, все заявки можно сформировать.
        ivanov = users["i.ivanov"]
        db.add(EmployeeProfile(
            user_id=ivanov.id, office="head_office", full_name=ivanov.full_name, position="инженер",
            phone="+7 900 000-11-22", order_number="86-к", order_date=date(2020, 12, 11),
            department=ivanov.department, email=ivanov.email, account_name="ROSNEFT\\i.ivanov",
            pkzi_name="StroyKontrol_IvanovII", manager_full_name="Сидоров Сидор Сидорович",
            manager_position="начальник отдела", manager_phone="+7 900 000-33-44",
            vkd_action=VKD_ACTIONS[0], vkd_rooms=["РНСК", "РНСК КомНПЗ"],
        ))

        # Сотрудница филиала, анкета пока не заполнена (только что вошла в систему первый раз).
        sidorova = users["s.sidorova"]
        db.add(EmployeeProfile(user_id=sidorova.id, office="branch", full_name=sidorova.full_name, department=sidorova.department, email=sidorova.email))

        # Запись, которую администратор завёл заранее — сотрудник ещё ни разу не входил в портал.
        db.add(EmployeeProfile(
            office="head_office", full_name="Кузнецова Мария Андреевна", position="экономист",
            phone="+7 900 222-33-44", department="Отдел экономики и планирования",
            manager_full_name="Сидоров Сидор Сидорович", manager_position="начальник отдела",
        ))

        db.commit()
        total = db.scalar(select(func.count()).select_from(EmployeeProfile))
        print(f"Создано анкет: {total}. Пользователи для входа в режиме dev: {', '.join(DEV_USERS)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="удалить существующие анкеты и создать демо-набор заново")
    seed(parser.parse_args().reset)
