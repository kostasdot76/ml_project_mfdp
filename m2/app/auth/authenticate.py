from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth.jwt_handler import verify_access_token
from database.database import get_session
from services.auth.cookieauth import OAuth2PasswordBearerWithCookie
from services.crud.UserRepository import UserRepository
from models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/signin")


async def authenticate(token: str = Depends(oauth2_scheme)) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sign in for access"
        )
    decoded_token = verify_access_token(token)
    return decoded_token["user"]


oauth2_scheme_cookie = OAuth2PasswordBearerWithCookie(tokenUrl="/home/token")


async def authenticate_cookie(token: str = Depends(oauth2_scheme_cookie)) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sign in for access"
        )
    token = token.removeprefix("Bearer ")
    decoded_token = verify_access_token(token)
    return decoded_token["user"]


async def authenticate_cookie_admin(
    token: str = Depends(oauth2_scheme_cookie), session=Depends(get_session)
) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sign in for access"
        )
    token = token.removeprefix("Bearer ")
    decoded_token = verify_access_token(token)
    email = decoded_token["user"]

    user = UserRepository(session).get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.role == UserRole.ADMIN:
        return email
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
