from fastapi import Request
from typing import Optional, List


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: str = None
        self.password: str = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if (
            not self.username and not self.password
        ):  # проверку наличия @ делаем в login_for_access_token
            self.errors.append("Email and password are required")
        if not self.errors:
            return True
        return False
