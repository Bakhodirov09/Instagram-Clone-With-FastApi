import random
from uuid import UUID
from datetime import datetime, timedelta
from config import SECRET_KEYS, ALGORITHM, tashkent, ACCESS_TOKEN_TIME, REFRESH_TOKEN_TIME
from fastapi import APIRouter, status, HTTPException
from general import db_dependency, detect_user_input, decode_jwt
from models import UsersModel, CodesModel
from routers.users import send_code_to_email, send_code_to_phone
from schemas import RegisterSchema, LoginSchema, ForgotPasswordSchema, UpdatePasswordSchema, NewPasswordSchema
from jose import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from general import check_password

router = APIRouter(prefix='/auth', tags=['Auth'])


def create_tokens(username: str, user_id):
    def create_token(token_type: str, exp_duration: timedelta):
        encode = {"sub": username, "user_id": str(user_id), 'token_type': token_type}
        expires = datetime.now(tz=tashkent) + exp_duration
        encode.update({"exp": expires})

        return jwt.encode(encode, SECRET_KEYS, algorithm=ALGORITHM)

    access_token = create_token("access", timedelta(hours=ACCESS_TOKEN_TIME))
    refresh_token = create_token("refresh", timedelta(hours=REFRESH_TOKEN_TIME))

    return access_token, refresh_token

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def registration(user_request: RegisterSchema, db: db_dependency):
    password = check_password(user_request.password)
    if not password:
        raise HTTPException(detail='The password does not meet the requirement', status_code=status.HTTP_400_BAD_REQUEST)
    user = UsersModel(
        username=user_request.username,
        password=password,
        full_name=user_request.full_name,
        gender=user_request.gender,
        email=user_request.email,
        phone_number=user_request.phone_number
    )
    try:
        db.add(user)
        db.commit()
        access_token, refresh_token = create_tokens(user_request.username, user_id=user.id)
        return {'access_token': access_token, 'refresh_token': refresh_token, 'message': 'Successfully registered', 'status': True}
    except Exception as e:
        raise HTTPException(detail=f"Change username {e}", status_code=status.HTTP_400_BAD_REQUEST)

@router.post('/login', status_code=status.HTTP_200_OK)
async def sign_in(user_request: LoginSchema, db: db_dependency):
    user_input = await detect_user_input(user_request.username_or_phone_number_or_email)
    user = db.query(UsersModel).filter(
        (UsersModel.username == user_request.username_or_phone_number_or_email) if user_input == 'username' else
        (UsersModel.phone_number == user_request.username_or_phone_number_or_email) if user_input == 'phone_number' else
        (UsersModel.email == user_request.username_or_phone_number_or_email)
    ).first()

    if user is None or not check_password_hash(user.password, user_request.password):
        raise HTTPException(detail='Username or password is incorrect', status_code=status.HTTP_400_BAD_REQUEST)

    access_token, refresh_token = create_tokens(user.username, user.id)
    return {'access_token': access_token, 'refresh_token': refresh_token}

@router.post('/forgot-password', status_code=status.HTTP_200_OK)
async def forgot_password(user_req: ForgotPasswordSchema, db: db_dependency):
    user_input = await detect_user_input(user_req.username_or_phone_number_or_email)
    code = ''.join([str(random.randint(0,9)) for i in range(6)])
    user = db.query(UsersModel).filter(
        (UsersModel.username == user_req.username_or_phone_number_or_email) if user_input == 'username' else
        (UsersModel.email == user_req.username_or_phone_number_or_email) if user_input == 'email' else
        (UsersModel.phone_number == user_req.username_or_phone_number_or_email)
    ).first()
    print(code)
    db_code =CodesModel(
        user_id=user.id,
        code=int(code)
    )
    db.add(db_code)
    db.commit()
    send_code_to_email(user.email, code) if user.email else send_code_to_phone(user.phone_number, code)
    return {'msg': 'Code sent', 'user_id': user.id}

@router.post('/check-code/{code}/{user_id}', status_code=status.HTTP_200_OK)
async def check_code(user_id: UUID, code: int, db: db_dependency, update_req: NewPasswordSchema):
    db_code = db.query(CodesModel).filter(CodesModel.code == code, CodesModel.user_id == user_id).first()
    if not db_code:
        raise HTTPException(detail='Code not found', status_code=status.HTTP_404_NOT_FOUND)
    db_user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)
    if not check_password(update_req.new_password):
        raise HTTPException(detail='The password does not meet the requirement', status_code=status.HTTP_400_BAD_REQUEST)
    db_user.password = generate_password_hash(update_req.new_password)
    db.delete(db_code)
    db.commit()
    return {'msg': 'Updated'}


