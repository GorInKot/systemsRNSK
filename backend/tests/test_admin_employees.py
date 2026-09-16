from tests.conftest import FULL_PROFILE


def test_non_admin_is_forbidden(applicant):
    assert applicant.get("/api/admin/employees").status_code == 403
    assert applicant.post("/api/admin/employees", json={"full_name": "x"}).status_code == 403


def test_admin_can_list_search_and_sort(admin, applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    admin.post("/api/admin/employees", json={"full_name": "Аронова Алла Аркадьевна", "department": "Отдел кадров"})

    response = admin.get("/api/admin/employees", params={"sort": "full_name", "direction": "asc"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    names = [item["full_name"] for item in body["items"]]
    assert names == sorted(names)

    filtered = admin.get("/api/admin/employees", params={"search": "Иванов"})
    assert filtered.json()["total"] == 1


def test_admin_partial_update_does_not_wipe_other_fields(admin, applicant):
    # Диалог быстрого редактирования в реестре шлёт только часть полей анкеты (например,
    # только должность) — остальные данные сотрудника (ВКД, имя ключа ПКЗИ и т.д.) не должны стираться.
    applicant.put("/api/profile", json=FULL_PROFILE)
    employee_id = applicant.get("/api/profile").json()["id"]

    updated = admin.put(f"/api/admin/employees/{employee_id}", json={"position": "ведущий инженер"})
    assert updated.status_code == 200
    body = updated.json()
    assert body["position"] == "ведущий инженер"
    assert body["account_name"] == "ROSNEFT\\i.ivanov"
    assert body["pkzi_name"] == "StroyKontrol_IvanovII"
    assert body["vkd_rooms"] == ["РНСК", "РНСК КомНПЗ"]


def test_admin_create_update_delete_employee(admin):
    created = admin.post("/api/admin/employees", json={"full_name": "Новиков Никита Николаевич", "department": "АХО"})
    assert created.status_code == 201
    employee_id = created.json()["id"]
    assert created.json()["user_id"] is None  # заведён администратором заранее, ещё не входил

    updated = admin.put(f"/api/admin/employees/{employee_id}", json={"full_name": "Новиков Никита Николаевич", "position": "снабженец"})
    assert updated.status_code == 200
    assert updated.json()["position"] == "снабженец"

    assert admin.delete(f"/api/admin/employees/{employee_id}").status_code == 204
    assert admin.put(f"/api/admin/employees/{employee_id}", json={"full_name": "x"}).status_code == 404


def test_admin_export_returns_xlsx(admin, applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = admin.get("/api/admin/employees/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml")


def test_admin_import_creates_and_updates(admin, applicant):
    profile_id = applicant.get("/api/profile").json()["id"]
    result = admin.post(
        "/api/admin/employees/import",
        json=[
            {"id": profile_id, "full_name": "Иванов Иван Иванович (обновлён импортом)"},
            {"full_name": "Совсем Новый Сотрудник"},
        ],
    )
    assert result.status_code == 200
    assert result.json() == {"created": 1, "updated": 1}

    updated_profile = admin.get("/api/admin/employees", params={"search": "обновлён"}).json()
    assert updated_profile["total"] == 1


def test_generated_requests_are_logged_for_admin(admin, applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    applicant.post("/api/systems/account/generate", json={})

    log = admin.get("/api/admin/requests")
    assert log.status_code == 200
    body = log.json()
    assert body["total"] == 1
    assert body["items"][0]["system_id"] == "account"
    assert body["items"][0]["generated_by"] == "Иванов Иван Иванович"
