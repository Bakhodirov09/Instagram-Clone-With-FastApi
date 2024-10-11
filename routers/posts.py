from uuid import UUID
from fastapi import APIRouter, HTTPException, status, File, UploadFile, Depends
from sqlalchemy.orm import joinedload
from general import JWTBearer, db_dependency, decode_jwt
from models import UsersModel, PostsModel, CommentsModel, PostViewsModel, PostLikesModel
from schemas import CreatePostSchema, PostSchema, UpdatePostSchema
from config import UPLOAD_FOLDER

posts = APIRouter(prefix='/posts', tags=['Posts'])

async def save_post(file: File(), post_uid: UUID):
    file_location = f"{UPLOAD_FOLDER}/posts/{post_uid}.{file.filename.split('.')[-1]}"
    with open(file_location, "wb") as file_object:
        file_object.write(file.file.read())
    return file_location

@posts.post('/new-post', status_code=status.HTTP_201_CREATED)
async def add_new_post(db: db_dependency, post_request: CreatePostSchema, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)

    user_about = decode_jwt(token=user)
    owner = db.query(UsersModel).filter(UsersModel.id == user_about['user_id']).first()

    new_post = PostsModel(
        title=post_request.title,
        access_to_views=post_request.access_to_views,
        access_to_comments=post_request.access_to_comments,
        access_to_likes=post_request.access_to_likes,
        owner_id=user_about['user_id'],
        owner=owner
    )
    db.add(new_post)
    db.commit()
    return {"message": "Post created successfully!", "post_id": new_post.id}

@posts.post('/upload-post-file/{post_id}', status_code=status.HTTP_200_OK)
async def upload_post_file(db: db_dependency, post_id: UUID, file: UploadFile = File(...)):
    try:
        post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
        if not post:
            raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
        post.post_file = await save_post(file, post_uid=post.id)
        db.commit()
        return {'message': 'Successfully created.'}
    except Exception as e:
        raise HTTPException(detail=e, status_code=status.HTTP_400_BAD_REQUEST)

@posts.get('/get-my-posts', status_code=status.HTTP_200_OK)
async def get_my_posts(db: db_dependency, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)

    about_user = decode_jwt(user)

    try:
        user_posts = db.query(PostsModel).filter_by(owner_id=about_user['user_id']).all()
    except Exception as e:
        raise HTTPException(detail=e, status_code=status.HTTP_400_BAD_REQUEST)

    return user_posts

@posts.get('/{post_uuid}', response_model=PostSchema)
async def get_post(post_uuid: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    try:
        view = PostViewsModel(
            user_id=decode_jwt(user)['user_id'],
            post_id=post_uuid
        )
        db.add(view)
        db.commit()
    except Exception as e:
        raise HTTPException(detail=e, status_code=status.HTTP_400_BAD_REQUEST)
    post = db.query(PostsModel).filter(PostsModel.id == post_uuid).first()
    if not post:
        raise HTTPException(detail='Post not found', status_code=status.HTTP_404_NOT_FOUND)
    comments_count = db.query(CommentsModel).filter(CommentsModel.post_id == post_uuid).count()
    post_data = {
        "id": post.id,
        "title": post.title,
        "post_file": post.post_file,
        "likes": post.likes if post.access_to_likes else False,
        "views": post.views if post.access_to_views else False,
        "comments": comments_count if post.access_to_comments else False
    }
    post_schema = PostSchema(**post_data)

    return post_schema


@posts.put('/update/{post_uuid}', status_code=status.HTTP_200_OK)
async def update_post(post_uuid: UUID, db: db_dependency, update_req: UpdatePostSchema, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    about_owner = decode_jwt(user)
    post = db.query(PostsModel).filter(PostsModel.id == post_uuid).first()
    if str(post.owner_id) != str(about_owner['user_id']):
        raise HTTPException(detail="You don't have permission to update this post", status_code=status.HTTP_403_FORBIDDEN)
    post.title = update_req.title,
    post.access_to_views = bool(update_req.access_to_views)
    post.access_to_likes = bool(update_req.access_to_likes)
    post.access_to_comments = bool(update_req.access_to_comments)
    db.commit()
    return {'message': 'Successfully updated'}

@posts.delete('/delete/{post_uuid}', status_code=status.HTTP_200_OK)
async def delete_post(post_uuid: UUID, db: db_dependency, user: str = Depends(JWTBearer())):
    if not user:
        raise HTTPException(detail='User is not authenticated', status_code=status.HTTP_403_FORBIDDEN)
    db.query(PostsModel).filter_by(id=post_uuid).delete()
    db.commit()
    return {'message': "Post successfully deleted"}