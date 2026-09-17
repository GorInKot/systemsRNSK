from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Office = Literal["head_office", "branch"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    full_name: str
    email: str | None
    department: str | None
    is_admin: bool


class DevUserOut(BaseModel):
    login: str
    full_name: str
    is_admin: bool


class MeOut(BaseModel):
    user: UserOut
    auth_mode: str
    dev_users: list[DevUserOut] | None = None


class SystemChoiceOut(BaseModel):
    field: str
    options: list[str]


class SystemOut(BaseModel):
    id: str
    title: str
    icon: str
    desc: str
    hl: bool
    ready: bool
    need: list[str]
    choice: SystemChoiceOut | None = None


class ProfileIn(BaseModel):
    """Анкета сотрудника. Все поля необязательны — форму можно сохранять частично заполненной;
    полнота, необходимая для конкретной заявки, проверяется отдельно при генерации файла."""

    office: Office = "head_office"
    full_name: str = ""
    position: str = ""
    phone: str = ""
    order_number: str | None = None
    order_date: date | None = None
    department: str = ""
    email: str | None = None
    no_email: bool = False
    account_name: str | None = None
    pkzi_name: str | None = None
    manager_full_name: str = ""
    manager_position: str = ""
    manager_phone: str = ""
    vkd_action: str | None = None
    vkd_rooms: list[str] = Field(default_factory=list)


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    updated_at: datetime


class EmployeeAdminIn(ProfileIn):
    id: int | None = None


class EmployeeAdminOut(ProfileOut):
    pass


class GenerateIn(BaseModel):
    choice: str | None = None


class GeneratedRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_profile_id: int
    employee_full_name: str
    system_id: str
    action: str | None
    file_name: str
    generated_by: str
    created_at: datetime


class EmployeePage(BaseModel):
    items: list[EmployeeAdminOut]
    total: int


class GeneratedRequestPage(BaseModel):
    items: list[GeneratedRequestOut]
    total: int
