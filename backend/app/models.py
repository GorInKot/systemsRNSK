from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(TimestampMixin, Base):
    """Сотрудник. Создаётся и обновляется автоматически по данным из AD при каждом входе через портал."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    login: Mapped[str] = mapped_column(String(256), unique=True)
    full_name: Mapped[str] = mapped_column(String(256))
    email: Mapped[str | None] = mapped_column(String(320))
    department: Mapped[str | None] = mapped_column(String(256))
    is_admin: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeeProfile(TimestampMixin, Base):
    """Анкета сотрудника: единый набор данных, из которого собираются все заявки на доступы.

    ``user_id`` заполняется, когда сотрудник сам открыл систему через портал; NULL — запись
    завёл администратор заранее (сотрудник ещё не входил, например до выхода на работу).
    """

    __tablename__ = "employee_profiles"
    __table_args__ = (CheckConstraint("office IN ('head_office', 'branch')", name="office_valid"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)

    office: Mapped[str] = mapped_column(String(16), server_default=text("'head_office'"))
    full_name: Mapped[str] = mapped_column(String(256), server_default=text("''"))
    position: Mapped[str] = mapped_column(String(256), server_default=text("''"))
    phone: Mapped[str] = mapped_column(String(64), server_default=text("''"))

    # «Приказ о приёме»: № и дата отдельными полями (в бланке заявки собираются обратно во фразу «№ от ДД.ММ.ГГГГ»).
    order_number: Mapped[str | None] = mapped_column(String(64))
    order_date: Mapped[date | None] = mapped_column(Date)

    department: Mapped[str] = mapped_column(String(256), server_default=text("''"))

    email: Mapped[str | None] = mapped_column(String(320))
    no_email: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    account_name: Mapped[str | None] = mapped_column(String(256))
    pkzi_name: Mapped[str | None] = mapped_column(String(256))

    manager_full_name: Mapped[str] = mapped_column(String(256), server_default=text("''"))
    manager_position: Mapped[str] = mapped_column(String(256), server_default=text("''"))
    manager_phone: Mapped[str] = mapped_column(String(64), server_default=text("''"))

    # Действие ВКД и наименования ВКД — часть анкеты (в отличие от действий ПКЗИ/VipNet,
    # которые выбираются прямо на карточке заявки и не хранятся в анкете).
    vkd_action: Mapped[str | None] = mapped_column(String(256))
    vkd_rooms: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))

    # Роль в ИР СЭИД — для заявки ЦУС (добавление в группы ПКЗИ).
    seid_role: Mapped[str | None] = mapped_column(String(256))

    user: Mapped[User | None] = relationship()
    generated_requests: Mapped[list[GeneratedRequest]] = relationship(back_populates="employee_profile", order_by="GeneratedRequest.created_at.desc()")


class GeneratedRequest(Base):
    """Журнал аудита: какие файлы заявок и когда были сформированы, для кого и кем."""

    __tablename__ = "generated_requests"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    employee_profile_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id", ondelete="CASCADE"), index=True)
    system_id: Mapped[str] = mapped_column(String(32))
    action: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(256))
    generated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee_profile: Mapped[EmployeeProfile] = relationship(back_populates="generated_requests")
    generated_by: Mapped[User] = relationship()
