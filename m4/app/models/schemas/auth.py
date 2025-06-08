from sqlmodel import SQLModel


class UserSignIn(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str
