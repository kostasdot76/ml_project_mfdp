from fastapi.testclient import TestClient
from database.config import get_settings
from sqlmodel import Session

settings = get_settings()


def test_signup_success(client: TestClient, session: Session):
    test_email = "test1@test.ru"
    test_password = "123"

    response = client.post(
        "/auth/signup",
        data={"email": test_email, "password": test_password},
        follow_redirects=False,
    )
    assert (
        response.status_code == 302
    ), f"Ожидался 302, получен {response.status_code}. Ответ: {response.text}"

    assert response.headers.get("location") == "/auth/login"


def test_login_success(client: TestClient):
    test_email = "test1@test.ru"
    test_password = "123"

    response = client.post(
        "/auth/signup",
        data={"email": test_email, "password": test_password},
        follow_redirects=False,
    )

    response = client.post(
        "/auth/login",
        data={"username": test_email, "password": test_password},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "Bearer" in client.cookies.get(settings.COOKIE_NAME)


def test_login_invalid(client: TestClient):
    test_email = "test1@test.ru"
    test_password = "123"

    response = client.post(
        "/auth/signup",
        data={"email": test_email, "password": test_password},
        follow_redirects=False,
    )

    response = client.post(
        "/auth/login",
        data={"username": test_email, "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Incorrect Email or Password" in response.text


def test_logout(client: TestClient):
    response = client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 302
    assert client.cookies.get(settings.COOKIE_NAME) is None
