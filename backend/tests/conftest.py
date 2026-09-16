import os

# Настройки читаются при импорте приложения, поэтому окружение задаётся до любых импортов app.*
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://dostup:dostup@localhost:5433/dostup_test")
os.environ["ENVIRONMENT"] = "test"
os.environ["AUTH_MODE"] = "dev"

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import engine
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    # Схема пересоздаётся с нуля: база могла остаться заполненной после прерванного запуска.
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(config, "head")
    yield


@pytest.fixture(autouse=True)
def clean_database(migrated_database):
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE generated_requests, employee_profiles, users RESTART IDENTITY CASCADE"))
    yield


class Api:
    def __init__(self, client: TestClient, login: str):
        self.client = client
        self.login = login

    def headers(self, extra: dict | None = None) -> dict:
        return {"X-Dev-User": self.login, "X-Requested-With": "dostup", **(extra or {})}

    def get(self, url: str, **kwargs):
        return self.client.get(url, headers=self.headers(kwargs.pop("headers", None)), **kwargs)

    def post(self, url: str, **kwargs):
        return self.client.post(url, headers=self.headers(kwargs.pop("headers", None)), **kwargs)

    def put(self, url: str, **kwargs):
        return self.client.put(url, headers=self.headers(kwargs.pop("headers", None)), **kwargs)

    def delete(self, url: str, **kwargs):
        return self.client.delete(url, headers=self.headers(kwargs.pop("headers", None)), **kwargs)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def as_user(client):
    return lambda login: Api(client, login)


@pytest.fixture
def applicant(as_user) -> Api:
    return as_user("i.ivanov")


@pytest.fixture
def other_applicant(as_user) -> Api:
    return as_user("s.sidorova")


@pytest.fixture
def admin(as_user) -> Api:
    return as_user("a.orlova")


FULL_PROFILE = {
    "office": "head_office",
    "full_name": "Иванов Иван Иванович",
    "position": "инженер",
    "phone": "+7 900 000-11-22",
    "order_number": "86-к",
    "order_date": "2020-12-11",
    "department": "Группа сопровождения ИС",
    "email": "i.ivanov@rnsk.rosneft.ru",
    "no_email": False,
    "account_name": "ROSNEFT\\i.ivanov",
    "pkzi_name": "StroyKontrol_IvanovII",
    "manager_full_name": "Сидоров Сидор Сидорович",
    "manager_position": "начальник отдела",
    "manager_phone": "+7 900 000-33-44",
    "vkd_action": "Предоставление доступа Пользователям ВКД",
    "vkd_rooms": ["РНСК", "РНСК КомНПЗ"],
}
