from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmployeeProfile, User
from app.schemas import ProfileIn


def get_or_create_own_profile(db: Session, user: User) -> EmployeeProfile:
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    if profile is not None:
        return profile
    profile = EmployeeProfile(user_id=user.id, full_name=user.full_name, department=user.department or "", email=user.email)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def apply_profile_input(profile: EmployeeProfile, payload: ProfileIn) -> None:
    """Применяет только поля, явно присланные клиентом (``exclude_unset``).

    Анкета сотрудника (``PUT /profile``) всегда шлёт полностью заполненную форму — для неё
    это равносильно полной замене. А вот админский диалог быстрого редактирования в реестре
    отправляет только часть полей анкеты: без ``exclude_unset`` остальные поля (офис, ВКД,
    имена учётной записи и ключа ПКЗИ) затирались бы значениями по умолчанию.
    """
    data = payload.model_dump(exclude_unset=True)
    data.pop("id", None)  # EmployeeAdminIn несёт id для upsert — это не поле анкеты
    for field, value in data.items():
        setattr(profile, field, value)
