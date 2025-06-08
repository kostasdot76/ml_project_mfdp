from abc import ABC, abstractmethod
from models.tables import User
from models.enums import TransactionStatus, TransactionType
from services.service.UnitOfWork import UnitOfWork
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


class TransactionService(ABC):
    def __init__(self, user: User, uow: UnitOfWork):
        self.user = user
        self.uow = uow
        self.transaction = None

    @abstractmethod
    def _validate(self) -> bool:
        """
        логика проверки
        """
        pass

    @abstractmethod
    def _apply_changes(self) -> None:
        """
        логика обработки
        """
        pass

    def process(self) -> bool:
        # проверка и ставим статус если не прошла
        if not self._validate():
            self.uow.transactions.update_entity_status(
                self.transaction, TransactionStatus.rejected
            )
            return False

        try:
            self._apply_changes()
            self.uow.transactions.update_entity_status(
                self.transaction, TransactionStatus.approved
            )
            return True
        except Exception:
            self.uow.transactions.update_entity_status(
                self.transaction, TransactionStatus.failed
            )
            raise


class DepositTransactionService(TransactionService):
    def __init__(self, user: User, uow: UnitOfWork, amount: float):
        super().__init__(user, uow)
        self.transaction = self.uow.transactions.create_transaction(
            user_id=user.id, amount=amount, type=TransactionType.deposit
        )

    def _validate(self) -> bool:
        return self.transaction.amount > 0

    def _apply_changes(self) -> None:
        self.user.balance += self.transaction.amount
        logging.info(f" депозит внесен")
        self.uow.users.update_user(self.user)


class DebtTransaction(TransactionService):
    def __init__(self, user: User, uow: UnitOfWork, amount: float):
        super().__init__(user, uow)
        self.transaction = self.uow.transactions.create_transaction(
            user_id=user.id, amount=amount, type=TransactionType.debt
        )

    def _validate(self) -> bool:
        return self.transaction.amount > 0

    def _apply_changes(self) -> None:
        self.user.balance -= self.transaction.amount
        self.uow.users.update_user(self.user)
