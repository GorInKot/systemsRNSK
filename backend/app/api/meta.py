from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import DEV_USERS, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import User
from app.schemas import DevUserOut, MeOut, UserOut

router = APIRouter()


@router.get("/health", include_in_schema=False)
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    settings = get_settings()
    dev_users = None
    if settings.auth_mode == "dev":
        dev_users = [DevUserOut(login=login, full_name=name, is_admin=admin) for login, (name, _, _, admin) in DEV_USERS.items()]
    return MeOut(user=UserOut.model_validate(user), auth_mode=settings.auth_mode, dev_users=dev_users)
