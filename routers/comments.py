from fastapi import APIRouter, status, Depends, HTTPException
from uuid import UUID

from general import db_dependency, JWTBearer, decode_jwt
from models import PostsModel, CommentsModel, UsersModel, CommentLikesModel, CommentRepliesModel
from schemas import AddCommentSchema, ReplyCommentSchema

comments = APIRouter(prefix='/comments', tags=['Comments'])

@comments.get('/{post_id}', status_code=status.HTTP_200_OK)
async def get_post_comments(post_id: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if post is None:
        raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
    return post.comments

@comments.post('/like/{comment_uid}', status_code=status.HTTP_200_OK)
async def like_comment(comment_uid: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    comment = db.query(CommentsModel).filter(CommentsModel.id == comment_uid).first()
    if not comment:
        comment = db.query(CommentRepliesModel).filter(CommentRepliesModel.id == comment_uid).first()
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    if not comment:
        raise HTTPException(detail='Comment not found', status_code=status.HTTP_404_NOT_FOUND)
    like = CommentLikesModel(
        user_id=db_user.id,
        comment_id=comment.id,
        user=db_user,
        comment=comment
    )
    db.add(like)
    db.commit()
    return {'msg': 'Liked to comment'}

@comments.post('/add-comment/{post_id}', status_code=status.HTTP_201_CREATED)
async def write_comment(post_id: UUID, db: db_dependency, comment_req: AddCommentSchema, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    user_about = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)['user_id']).first()
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if post is None:
        raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
    comment = CommentsModel(
        content=comment_req.comment,
        post_id=post.id,
        user_id=user_about.id,
        post=post,
        user=user_about
    )
    db.add(comment)
    db.commit()
    post_comments = db.query(CommentsModel).filter(CommentsModel.post_id == post_id).count()
    return {'message': 'Comment wrote', 'count': post_comments}

@comments.post('/reply/{comment_id}', status_code=status.HTTP_201_CREATED)
async def reply_to_comment(comment_uid: UUID, reply_req: ReplyCommentSchema, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    comment = db.query(CommentsModel).filter(CommentsModel.id == comment_uid).first()
    db_user = db.query(UsersModel).filter(UsersModel.id == decode_jwt(user)).first()
    if not comment:
        raise HTTPException(detail='Comment not found', status_code=status.HTTP_404_NOT_FOUND)
    reply = CommentRepliesModel(
        content=reply_req.reply,
        comment_id=comment.id,
        user_id=db_user.id,
        comment=comment,
        user=db_user
    )
    db.add(reply)
    db.commit()
    return {'msg': 'Replied'}

@comments.delete('/delete/{comment_uid}', status_code=status.HTTP_200_OK)
async def delete_comment(comment_uid: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if user is None:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    comment = db.query(CommentsModel).filter(CommentsModel.id == comment_uid).first()
    if not comment:
        comment = db.query(CommentRepliesModel).filter(CommentRepliesModel.id == comment_uid).first()
    about_user = decode_jwt(user)
    if not comment.user_id == about_user['user_id']:
        raise HTTPException(detail="You don't have permission to delete comment!", status_code=status.HTTP_400_BAD_REQUEST)
    db.delete(comment)
    db.commit()
    return {'message': 'Successfully deleted'}

@comments.patch('/update/{comment_id}', status_code=status.HTTP_200_OK)
async def update_comment(comment_uid: UUID, db: db_dependency, comment_req: AddCommentSchema, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    comment = db.query(CommentsModel).filter(CommentsModel.id == comment_uid).first()
    if not comment:
        comment = db.query(CommentRepliesModel).filter(CommentRepliesModel.id == comment_uid).first()
    about_user = decode_jwt(user)
    if not comment.user_id == about_user['user_id']:
        raise HTTPException(detail="You don't have permission to delete comment!", status_code=status.HTTP_400_BAD_REQUEST)
    comment.content = comment_req.comment
    db.commit()
    return {'msg': 'Successfully updated.'}
