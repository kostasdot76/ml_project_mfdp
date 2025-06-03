from fastapi import Request
from typing import Optional, List
from decimal import Decimal


class DepositForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List[str] = []
        self.amount: Decimal = None

    async def load_data(self):
        form = await self.request.form()
        self.amount = form.get("amount")

    async def is_valid(self):
        # Проверка наличия amount
        if not self.amount:
            self.errors.append("Amount is required")
            return False

        # Проверка, что amount является числом
        try:
            self.amount = Decimal(str(self.amount))
            if self.amount <= 0:
                self.errors.append("Amount must be positive")
        except:
            self.errors.append("Invalid amount format")

        return not self.errors
