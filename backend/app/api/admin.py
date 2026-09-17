from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.db import get_db
from app.errors import not_found
from app.models import EmployeeProfile, GeneratedRequest, User
from app.schemas import EmployeeAdminIn, EmployeeAdminOut, EmployeePage, GeneratedRequestOut, GeneratedRequestPage
from app.services.profiles import apply_profile_input

router = APIRouter(prefix="/admin", tags=["Администрирование"])

SORT_COLUMNS = {
    "full_name": EmployeeProfile.full_name,
    "department": EmployeeProfile.department,
    "position": EmployeeProfile.position,
    "updated_at": EmployeeProfile.updated_at,
}


@router.get("/employees", response_model=EmployeePage)
def list_employees(
    search: str = Query("", max_length=200),
    sort: str = Query("full_name"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EmployeePage:
    stmt = select(EmployeeProfile)
    if search:
        like = f"%{search}%"
        stmt = stmt.where((EmployeeProfile.full_name.ilike(like)) | (EmployeeProfile.department.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    column = SORT_COLUMNS.get(sort, EmployeeProfile.full_name)
    stmt = stmt.order_by(column.desc() if direction == "desc" else column.asc()).limit(limit).offset(offset)
    items = list(db.scalars(stmt))
    return EmployeePage(items=[EmployeeAdminOut.model_validate(item) for item in items], total=total or 0)


@router.post("/employees", response_model=EmployeeAdminOut, status_code=201)
def create_employee(payload: EmployeeAdminIn, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> EmployeeProfile:
    profile = EmployeeProfile()
    apply_profile_input(profile, payload)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/employees/{employee_id}", response_model=EmployeeAdminOut)
def update_employee(employee_id: int, payload: EmployeeAdminIn, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> EmployeeProfile:
    profile = db.get(EmployeeProfile, employee_id)
    if profile is None:
        raise not_found("Сотрудник не найден")
    apply_profile_input(profile, payload)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> Response:
    profile = db.get(EmployeeProfile, employee_id)
    if profile is not None:
        db.delete(profile)
        db.commit()
    return Response(status_code=204)


@router.get("/requests", response_model=GeneratedRequestPage)
def list_requests(
    employee_id: int | None = Query(None),
    system_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GeneratedRequestPage:
    stmt = select(GeneratedRequest).options(selectinload(GeneratedRequest.employee_profile), selectinload(GeneratedRequest.generated_by))
    if employee_id is not None:
        stmt = stmt.where(GeneratedRequest.employee_profile_id == employee_id)
    if system_id is not None:
        stmt = stmt.where(GeneratedRequest.system_id == system_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.order_by(GeneratedRequest.created_at.desc()).limit(limit).offset(offset)
    rows = list(db.scalars(stmt))
    items = [
        GeneratedRequestOut(
            id=row.id, employee_profile_id=row.employee_profile_id, employee_full_name=row.employee_profile.full_name,
            system_id=row.system_id, action=row.action, file_name=row.file_name,
            generated_by=row.generated_by.full_name, created_at=row.created_at,
        )
        for row in rows
    ]
    return GeneratedRequestPage(items=items, total=total or 0)
