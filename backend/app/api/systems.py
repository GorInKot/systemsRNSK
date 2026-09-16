from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.errors import AppError, not_found
from app.models import GeneratedRequest, User
from app.schemas import GenerateIn, SystemChoiceOut, SystemOut
from app.services.profiles import get_or_create_own_profile
from app.services.systems_catalog import FIELD_LABELS, SYSTEMS, get_system, profile_to_dict, with_defaults
from app.services.templates import fill_template

router = APIRouter(tags=["Заявки"])

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.get("/systems", response_model=list[SystemOut])
def list_systems(_: User = Depends(get_current_user)) -> list[SystemOut]:
    return [
        SystemOut(
            id=system.id, title=system.title, icon=system.icon, desc=system.desc,
            hl=system.hl, ready=system.ready, need=system.need,
            choice=SystemChoiceOut(field=system.choice_field, options=system.choice_options) if system.choice_field else None,
        )
        for system in SYSTEMS
    ]


@router.post("/systems/{system_id}/generate")
def generate(system_id: str, payload: GenerateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    system = get_system(system_id)
    if system is None:
        raise not_found("Система не найдена")
    if not system.ready:
        raise AppError(409, "Шаблон для этой заявки ещё не подключён", code="not_ready")

    profile = get_or_create_own_profile(db, user)
    data = with_defaults(profile_to_dict(profile))

    chosen: str | None = None
    if system.choice_field:
        options = system.choice_options or []
        chosen = payload.choice if payload.choice in options else options[0]
        data[system.choice_field] = chosen

    missing = system.missing_fields(data)
    if missing:
        labels = [FIELD_LABELS.get(key, key) for key in missing]
        raise AppError(
            422,
            f"Дозаполните анкету: {', '.join(labels)}",
            code="profile_incomplete",
            errors=[{"path": key, "message": "Заполните поле в анкете"} for key in missing],
        )

    template_key = system.template_key(data)
    values = system.map_values(data)
    file_bytes = fill_template(template_key, values, system.text_parts)
    file_name = system.file_name(data)

    db.add(GeneratedRequest(employee_profile_id=profile.id, system_id=system.id, action=chosen, file_name=file_name, generated_by_id=user.id))
    db.commit()

    media_type = XLSX_MIME if system.is_xlsx() else DOCX_MIME
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"}
    return Response(content=file_bytes, media_type=media_type, headers=headers)
