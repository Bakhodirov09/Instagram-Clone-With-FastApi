from fastapi import HTTPException, APIRouter, Depends, status
from general import JWTBearer, db_dependency, decode_jwt
from models import UsersModel, PostsModel, SavesModel
from uuid import UUID

saves = APIRouter(prefix='/saves', tags=['Saves'])

@saves.post('/add/{post_uid}', status_code=status.HTTP_201_CREATED)
async def save_post(post_uid: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    post = db.query(PostsModel).filter(PostsModel.id == post_uid).first()
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    if not post:
        raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
    save = SavesModel(
        user_id=db_user.id,
        post_id=post.id,
        user=db_user,
        post=post
    )
    db.add(save)
    db.commit()
    return {'msg': 'Saved'}

@saves.post('/unsave/{saved_post_id}', status_code=status.HTTP_200_OK)
async def un_save_post(db: db_dependency, saved_post_id: UUID, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    saved_post = db.query(SavesModel).filter(SavesModel.id == saved_post_id).first()
    if not saved_post:
        raise HTTPException(detail='Saved post not found', status_code=status.HTTP_404_NOT_FOUND)
    db.delete(saved_post)
    db.commit()
    return {'msg': 'Successfully deleted'}

@saves.get('/saved-posts', status_code=status.HTTP_200_OK)
async def user_saved_posts(db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    saved_posts = db.query(SavesModel).filter(SavesModel.user_id == db_user.id).all()
    return saved_posts
