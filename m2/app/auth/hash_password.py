from passlib.context import CryptContext


class HashPassword:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_hash(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
