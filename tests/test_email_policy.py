import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.parametrize("schema", [UserCreate, UserUpdate])
@pytest.mark.parametrize(
    "environment, enabled, allowed",
    [("dev", True, True), ("dev", False, False), ("prod", True, False), ("prod", False, False)],
)
def test_example_email_requires_development_mode_and_explicit_opt_in(
    monkeypatch, schema, environment, enabled, allowed
):
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    monkeypatch.setattr(settings, "ALLOW_LOCAL_TEST_EMAILS", enabled)
    payload = {"email": "driver@example.com"}
    if schema is UserCreate:
        payload.update(name="Local Driver", password="LocalDemo123!")

    if allowed:
        assert schema(**payload).email == payload["email"]
    else:
        with pytest.raises(ValidationError):
            schema(**payload)


def test_local_example_account_still_requires_email_activation(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
    monkeypatch.setattr(settings, "ALLOW_LOCAL_TEST_EMAILS", True)
    payload = {"name": "Local Passenger", "email": "passenger@example.com", "password": "LocalDemo123!"}

    registration = client.post("/auth/register", json=payload)
    assert registration.status_code == 201
    assert registration.json()["is_email_verified"] is False

    login = client.post("/auth/login", data={"username": payload["email"], "password": payload["password"]})
    assert login.status_code == 403
    assert login.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
