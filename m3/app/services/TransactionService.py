from abc import ABC, abstractmethod
from app.services.UnitOfWork import UnitOfWork
from app.schemas.transaction import TransactionRead
import logging

logger = logging.getLogger(__name__)


class TransactionService(ABC):
    def __init__(self, uow: UnitOfWork, user_id: int, amount: float):
        self.transaction = None
        self.uow = uow
        self.user_id = user_id
        self.amount = amount

    def process(self) -> bool:
        if not self._validate():
            self._update_status("rejected")
            logger.warning(
                f"Validation failed for user_id={self.user_id}, amount={self.amount}"
            )
            return False

        self._apply_changes()
        self._update_status("approved")
        self.uow.commit()
        logger.info(
            f"Transaction approved for user_id={self.user_id}, amount={self.amount}"
        )
        return True

    @abstractmethod
    def _validate(self) -> bool:
        pass

    @abstractmethod
    def _apply_changes(self):
        pass

    def _update_status(self, status: str):
        if self.transaction is not None:
            self.uow.transactions.update_entity_status(self.transaction, status)


class DepositTransactionService(TransactionService):
    def _validate(self) -> bool:
        return self.amount > 0

    def _apply_changes(self):
        self.transaction = self.uow.transactions.create(
            user_id=self.user_id, amount=self.amount
        )
        self.uow.users.increase_balance(user_id=self.user_id, amount=self.amount)


class DebtTransactionService(TransactionService):
    def _validate(self) -> bool:
        balance = self.uow.users.get_balance(self.user_id)
        return balance >= self.amount > 0

    def _apply_changes(self):
        self.transaction = self.uow.transactions.create(
            user_id=self.user_id, amount=-self.amount
        )
        self.uow.users.decrease_balance(user_id=self.user_id, amount=self.amount)
