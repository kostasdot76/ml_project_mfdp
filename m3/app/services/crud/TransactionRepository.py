### TransactionRepository.py — example/app/services/crud/TransactionRepository.py
from datetime import datetime
from app.models.transaction import Transaction, TransactionStatus
from .BaseRepository import BaseRepository
from sqlmodel import select


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session):
        super().__init__(session, Transaction)

    def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: str,
        status: str = TransactionStatus.PENDING,
    ) -> Transaction:
        return self.create_entity(
            user_id=user_id,
            amount=amount,
            type=type,
            timestamp=datetime.now(),
            status=status,
        )

    def get_all_transactions(self) -> list[Transaction]:
        return self.session.exec(select(Transaction)).all()
