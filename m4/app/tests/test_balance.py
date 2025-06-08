from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models.tables import User
from services.service import UnitOfWork, DebtTransaction
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


def test_deposit_balance(client: TestClient, session: Session):
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
    assert response.status_code == 302

    response = client.get(
        "/balance",
        follow_redirects=False,
    )

    logging.info(f"header {response.headers}")

    statement = select(User).where(User.email == test_email)
    user = session.exec(statement).first()
    assert user.balance == 100


def test_debt_balance(client: TestClient, session: Session):
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

    with UnitOfWork(session) as uow:

        # Создаем транзакцию на списание
        user = uow.users.get_user_by_email(test_email)

        transaction = DebtTransaction(user=user, uow=uow, amount=10)

        new_balance = 0
        if transaction.process():
            new_balance = uow.users.get_user_balance(user.id)

    assert new_balance == 90


def test_debt_balance_when_zero(client: TestClient, session: Session):
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

    try:
        with UnitOfWork(session) as uow:

            # Создаем транзакцию на списание
            user = uow.users.get_user_by_email(test_email)

            transaction = DebtTransaction(user=user, uow=uow, amount=10)

            if transaction.process():
                return False
            else:
                return True
    except:
        return True


def test_balance_page_unauthorized(client: TestClient):
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
    client.cookies.clear()
    response = client.get(
        "/balance",
        follow_redirects=False,
    )
    assert response.status_code == 401
