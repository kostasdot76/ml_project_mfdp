from fastapi.testclient import TestClient


def test_home_request(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Главная страница!" in response.text
