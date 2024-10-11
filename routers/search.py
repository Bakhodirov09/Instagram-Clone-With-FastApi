from typing import List

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm.strategy_options import joinedload

from general import JWTBearer, db_dependency
from models import UsersModel, PostsModel, CommentsModel
from schemas import UserSchema

search = APIRouter(prefix='/search', tags=['Search'])


@search.get('/{username}', status_code=status.HTTP_200_OK, response_model=List[UserSchema])
async def search_user_by_username(username: str, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db_users = db.query(UsersModel).options(
        joinedload(UsersModel.posts)).filter(
        UsersModel.username.ilike(f'%{username}%')
    ).all()

    if not db_users:
        raise HTTPException(detail='No users found', status_code=status.HTTP_404_NOT_FOUND)

    return db_users
