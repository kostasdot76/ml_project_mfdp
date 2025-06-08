import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_create_prediction(client: TestClient):
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

    response = client.post(
        "/balance/deposit",
        data={"amount": 100},
        follow_redirects=False,
    )

    data = {
        "fixed_acidity": 7.4,
        "volatile_acidity": 0.7,
        "citric_acid": 0.24,
        "residual_sugar": 1.9,
        "chlorides": 0.076,
        "free_sulfur_dioxide": 11,
        "total_sulfur_dioxide": 34,
        "density": 0.99777,
        "pH": 3.51,
        "sulphates": 0.56,
        "alcohol": 9.4,
    }

    test_data = {
        "model_type": "classification",
        "data": json.dumps(data),
    }

    # мокирование всех вызовов rabbitmq
    with patch("pika.BlockingConnection") as mock_connection:
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        response = client.post(
            "/predict",
            data=test_data,
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "/predict/status/" in response.headers["Location"]


def test_prediction_history(client: TestClient):
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

    response = client.get(
        "/predict/history",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "История прогнозов" in response.text
