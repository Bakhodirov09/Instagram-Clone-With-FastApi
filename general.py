import re
from werkzeug.security import generate_password_hash
from config import SECRET_KEYS, ALGORITHM
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import SessionLocal

USERNAME_REGEX = re.compile(r'^[a-z0-9_-]{3,15}$')
PHONE_NUMBER_REGEX = re.compile(r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$')
EMAIL_REGEX = re.compile(r'[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEYS, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return {}


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        token = self.verify_jwt(credentials.credentials)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not token:
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:

        try:
            payload = decode_jwt(jwtoken)
        except:
            payload = None

        return bool(payload)


async def detect_user_input(text):
    if re.fullmatch(USERNAME_REGEX, text):
        return 'username'
    elif re.fullmatch(PHONE_NUMBER_REGEX, text):
        return 'phone_number'
    elif re.fullmatch(EMAIL_REGEX, text):
        return 'email'

def check_password(password: str):
    if len(password) < 8:
        return False
    elif password.isdigit() or password.isalpha():
        return False
    elif not any(c.isalnum() for c in password):
        return False
    return generate_password_hash(password)
