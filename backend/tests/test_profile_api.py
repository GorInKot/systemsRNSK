import zipfile
from io import BytesIO

from tests.conftest import FULL_PROFILE


def test_profile_is_created_empty_on_first_access(applicant):
    response = applicant.get("/api/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Иванов Иван Иванович"  # подставлено из личности AD при автосоздании
    assert body["office"] == "head_office"
    assert body["vkd_rooms"] == []


def test_profile_is_saved_and_scoped_to_the_user(applicant, other_applicant):
    saved = applicant.put("/api/profile", json=FULL_PROFILE)
    assert saved.status_code == 200
    assert saved.json()["account_name"] == "ROSNEFT\\i.ivanov"

    # Анкета другого сотрудника не пересекается с этой.
    other = other_applicant.get("/api/profile")
    assert other.json()["account_name"] is None


def test_systems_catalog_lists_pkzi_with_choice(applicant):
    response = applicant.get("/api/systems")
    assert response.status_code == 200
    systems = {system["id"]: system for system in response.json()}
    assert systems["pkzi"]["choice"] == {
        "field": "pkzi_action",
        "options": ["Первичная генерация ключевой информации", "Продление сертификата"],
    }
    assert systems["sap"]["ready"] is False


def test_generate_requires_complete_profile(applicant):
    response = applicant.post("/api/systems/account/generate", json={})
    assert response.status_code == 422
    assert response.json()["code"] == "profile_incomplete"


def test_generate_account_fills_real_template(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/account/generate", json={})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml")
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in sheet
        assert "{{" not in sheet

    log = applicant.get("/api/admin/requests")
    assert log.status_code == 403  # заявитель не видит журнал — это раздел администратора


def test_generate_pkzi_marks_the_chosen_checkbox(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/pkzi/generate", json={"choice": "Продление сертификата"})
    assert response.status_code == 200
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "☒" in document


def test_generate_tsus_fills_real_template(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/tsus/generate", json={})
    assert response.status_code == 200
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "(Строительный контроль) - Инженер СК" in sheet
        assert "{{" not in sheet


def test_generate_sim_fills_real_template(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/sim/generate", json={})
    assert response.status_code == 200
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in document
        assert "{{" not in document


def test_generate_sim_deduction_fills_real_template(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/sim_deduction/generate", json={})
    assert response.status_code == 200
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Иванов Иван Иванович" in document
        assert "{{" not in document


def test_generate_unready_system_is_rejected(applicant):
    applicant.put("/api/profile", json=FULL_PROFILE)
    response = applicant.post("/api/systems/sap/generate", json={})
    assert response.status_code == 409


def test_generate_unknown_system_is_not_found(applicant):
    response = applicant.post("/api/systems/unknown/generate", json={})
    assert response.status_code == 404
