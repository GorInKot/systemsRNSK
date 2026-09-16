from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import ProfileIn, ProfileOut
from app.services.profiles import apply_profile_input, get_or_create_own_profile

router = APIRouter(tags=["Анкета"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_create_own_profile(db, user)


@router.put("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_or_create_own_profile(db, user)
    apply_profile_input(profile, payload)
    db.commit()
    db.refresh(profile)
    return profile
