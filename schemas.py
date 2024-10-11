from typing import Optional, List, Union, Annotated, Dict
from uuid import UUID
from datetime import datetime, date
from fastapi import File
from pydantic import BaseModel, UUID4
from pydantic.v1 import root_validator


class RegisterSchema(BaseModel):
    full_name: str
    username: str
    phone_number: str | None = None
    email: str | None = None
    gender: str | None = None
    password: str

class LoginSchema(BaseModel):
    username_or_phone_number_or_email: str | None = None
    password: str | None = None

class ForgotPasswordSchema(BaseModel):
    username_or_phone_number_or_email: str | None

class UpdatePasswordSchema(BaseModel):
    code: int

class NewPasswordSchema(BaseModel):
    new_password: str

class CreatePostSchema(BaseModel):
    title: str
    access_to_views: bool
    access_to_comments: bool
    access_to_likes: bool

class UpdatePostSchema(BaseModel):
    title: str
    access_to_views: bool
    access_to_comments: bool
    access_to_likes: bool

class CommentReplySchema(BaseModel):
    id: UUID
    content: str
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ReplyCommentSchema(BaseModel):
    reply: str

class CommentSchema(BaseModel):
    id: UUID
    content: str
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PostSchema(BaseModel):
    id: UUID
    title: str
    post_file: str
    likes: Union[int, bool]
    views: Union[int, bool]
    comments: Union[int, bool]

    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    id: UUID
    username: str
    full_name: str
    day_of_birth: datetime | None = None
    bio: str | None = None
    gender: str
    avatar_pic: str
    posts: List[PostSchema] = []

    class Config:
        from_attributes = True

class AddCommentSchema(BaseModel):
    comment: str

class UpdateUserSchema(BaseModel):
    full_name: str
    username: str
    gender: str
    day_of_birth: date
    bio: str
    email: str
    phone_number: str

class ChangePasswordSchema(BaseModel):
    last_password: str
    new_password: str
