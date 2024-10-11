from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from general import db_dependency, JWTBearer, decode_jwt
from models import UsersModel, PostsModel, PostLikesModel

likes = APIRouter(prefix='/likes', tags=['Likes'])

@likes.get('/my-liked-posts', status_code=status.HTTP_200_OK)
async def user_liked_posts(db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    liked_posts = db.query(PostLikesModel).filter(PostLikesModel.user_id == db_user.id).all()
    return liked_posts

@likes.post('/like/{post_id}', status_code=status.HTTP_200_OK)
async def like_post(post_id: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id'])
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if not post:
        raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
    try:
        like = PostLikesModel(
            user_id=db_user.id,
            post_id=post.id
        )
        db.add(like)
        return {'msg': 'Successfully liked'}
    except:
        return {'msg': 'Was liked'}

@likes.delete('/unlike/{post_id}', status_code=status.HTTP_200_OK)
async def unlike_post(post_id: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    user_id = decode_jwt(user)['user_id']
    is_liked = db.query(PostLikesModel).filter(PostLikesModel.user_id == user_id, PostLikesModel.post_id == post_id).first()
    if not is_liked:
        raise HTTPException(detail='Liked post not found', status_code=status.HTTP_404_NOT_FOUND)
    db.delete(is_liked)
    db.commit()
    return {'msg': 'Liked post deleted'}