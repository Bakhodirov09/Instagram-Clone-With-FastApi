import random
import smtplib
from uuid import UUID

import vonage
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from config import EMAIL_SENDER, EMAIL_SENDER_PASSWORD, VONAGE_KEY, VONAGE_SECRET, UPLOAD_FOLDER
from general import JWTBearer, db_dependency, decode_jwt, check_password
from models import UsersModel, CodesModel
from schemas import UpdateUserSchema, ChangePasswordSchema, ForgotPasswordSchema, UpdatePasswordSchema, \
    NewPasswordSchema
from werkzeug.security import check_password_hash, generate_password_hash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def save_logo(file: File(), user_id: UUID):
    file_location = f"{UPLOAD_FOLDER}/profile_pictures/{user_id}.{file.filename.split('.')[-1]}"
    with open(file_location, "wb") as file_object:
        file_object.write(file.file.read())
    return file_location

def send_code_to_email(email: str, code: str):
    sender_email = EMAIL_SENDER
    sender_password = EMAIL_SENDER_PASSWORD
    subject = "Password Reset Code"
    body = f"Your password reset code is: {code}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
    except Exception as e:
        raise HTTPException(detail=f"Error sending email: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

def send_code_to_phone(phone: str, code: str):
    client = vonage.Client(key=VONAGE_KEY, secret=VONAGE_SECRET)
    sms = vonage.Sms(client)
    responseData = sms.send_message(
        {
            "from": "Vonage APIs",
            "to": phone,
            "text": f"Your Password Reset Code: {code}",
        }
    )
    if responseData["messages"][0]["status"] == "0":
        return "Message sent successfully."
    else:
        return f"Message failed with error: {responseData['messages'][0]['error-text']}"

users = APIRouter(prefix='/users', tags=['Users'])

@users.get('/me', status_code=status.HTTP_200_OK)
async def user_account(db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)
    return db_user

@users.post('/change-password', status_code=status.HTTP_200_OK)
async def change_password(db: db_dependency, password_req: ChangePasswordSchema, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    user_id = decode_jwt(user)['user_id']
    db_user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)
    if not check_password_hash(db_user.password, password_req.last_password):
        raise HTTPException(detail='Password is not match', status_code=status.HTTP_400_BAD_REQUEST)
    db_user.password = generate_password_hash(password_req.new_password)
    db.commit()
    return {'msg': 'Successfully updated'}

@users.patch('/change-logo', status_code=status.HTTP_200_OK)
async def change_logo(db: db_dependency, user: str = Depends(JWTBearer()), new_logo: UploadFile = File(...)):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    user_id = decode_jwt(user)['user_id']
    db_user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)
    if new_logo.content_type not in ['image/png', 'image/jpg']:
        raise HTTPException(detail='File type is not image', status_code=status.HTTP_400_BAD_REQUEST)
    location = await save_logo(new_logo, db_user.id)
    db_user.avatar_picture = location
    db.commit()
    return {'msg': 'Successfully updated'}

@users.get('/forgot-password', status_code=status.HTTP_200_OK)
async def forgot_password(db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)

    user_id = decode_jwt(user)['user_id']
    db_user = db.query(UsersModel).filter(UsersModel.id == user_id).first()

    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)

    reset_code = ''.join([str(random.randint(0,9)) for i in range(6)])

    send_code_to_email(db_user.email, reset_code) if db_user.email else send_code_to_phone(db_user.phone_number,
                                                                                           reset_code)

    code = CodesModel(
        user_id=user_id,
        code=reset_code
    )
    db.add(code)
    db.commit()

    return {"msg": "Code was sent"}


@users.post('/check-code', status_code=status.HTTP_200_OK)
async def check_code(db: db_dependency, code_req: UpdatePasswordSchema, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)

    user_id = decode_jwt(user)['user_id']
    code = db.query(CodesModel).filter(CodesModel.code == code_req.code, CodesModel.user_id == user_id).first()
    if not code:
        raise HTTPException(detail='Code not found', status_code=status.HTTP_404_NOT_FOUND)
    return {'msg': 'Code is true', 'code_id': code.id}


@users.post('/update-password/{code_id}', status_code=status.HTTP_200_OK)
async def update_password(db: db_dependency, code_id: int, new_password: NewPasswordSchema, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)

    code = db.query(CodesModel).filter(CodesModel.id == code_id).first()

    if not code:
        raise HTTPException(detail='Code not found', status_code=status.HTTP_404_NOT_FOUND)

    user_id = decode_jwt(user)['user_id']
    db_user = db.query(UsersModel).filter(UsersModel.id == user_id).first()

    if not db_user:
        raise HTTPException(detail='User not found', status_code=status.HTTP_404_NOT_FOUND)
    if not check_password(new_password.new_password):
        raise HTTPException(detail='The password does not meet the requirement',
                            status_code=status.HTTP_400_BAD_REQUEST)
    db_user.password = generate_password_hash(new_password.new_password)
    db.delete(code)
    db.commit()

    return {'msg': 'Password successfully updated'}


@users.patch('/update', status_code=status.HTTP_200_OK)
async def update_user_data(db: db_dependency, user_req: UpdateUserSchema, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    user_id = decode_jwt(user)['user_id']
    try:
        db.query(UsersModel).filter_by(id=user_id).update(user_req.dict(exclude_unset=True))
        db.commit()
        return {'msg': 'Successfully updated.'}
    except Exception as e:
        raise HTTPException(detail=e, status_code=status.HTTP_400_BAD_REQUEST)
