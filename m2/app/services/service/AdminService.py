from models.tables import User, Transaction
from models.enums import UserRole
from services.service.UnitOfWork import UnitOfWork
from services.service.TransactionService import DepositTransactionService
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


class AdminService:
    def __init__(self, admin_user: User, uow: UnitOfWork):
        if admin_user.role != UserRole.ADMIN:
            raise PermissionError("Требуются права администратора")

        self.admin = admin_user
        self.uow = uow

    def deposit_to_user(self, target_user_id: int, amount: float) -> bool:
        """Пополнение баланса пользователя администратором"""
        target_user = self.uow.users.get_user_by_id(target_user_id)

        if not target_user:
            logging.info("Пользователь не найден")
            return False

        # Создаем транзакцию
        deposit = DepositTransactionService(target_user, self.uow, amount)

        # logging.info(f"Админ {self.admin.email} внес пользовтелю: {target_user.email}  депозит {amount}")

        if deposit.process():
            self.uow.session.commit()
            self.uow.session.refresh(target_user)
            return True
        else:
            return False

    def get_all_transactions(self) -> list[Transaction]:
        """Получение всех транзакций в системе"""
        return self.uow.transactions.get_all_transactions()
