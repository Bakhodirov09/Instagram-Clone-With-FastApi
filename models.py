from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID


class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsersModel(BaseModel):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(Text, nullable=False)
    full_name = Column(String(50))
    gender = Column(String(10))
    day_of_birth = Column(DateTime)
    bio = Column(Text)
    avatar_pic = Column(String, default='media/profile_pictures/default.png')
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)

    posts = relationship('PostsModel', back_populates='owner', cascade="all, delete")
    comments = relationship('CommentsModel', back_populates='user', cascade="all, delete")
    replies = relationship('CommentRepliesModel', back_populates='user', cascade="all, delete")
    post_views = relationship('PostViewsModel', back_populates='user', cascade="all, delete")
    comment_likes = relationship('CommentLikesModel', back_populates='user', cascade="all, delete")
    saves = relationship('SavesModel', back_populates='user', cascade='all, delete')


class MusicsModel(BaseModel):
    __tablename__ = 'musics'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    singer = Column(String(100), nullable=False)

    posts = relationship('PostsModel', back_populates='music', cascade="all, delete")

class PostLikesModel(BaseModel):
    __tablename__ = 'post_likes'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
    post_id = Column(UUID, ForeignKey('posts.id', ondelete='CASCADE'))

    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_post_like_uc'),)

class PostsModel(BaseModel):
    __tablename__ = 'posts'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    post_file = Column(Text, nullable=True)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    access_to_views = Column(Boolean, default=True)
    access_to_likes = Column(Boolean, default=True)
    access_to_comments = Column(Boolean, default=True)

    owner_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    music_id = Column(UUID, ForeignKey('musics.id', ondelete='SET NULL'))

    owner = relationship('UsersModel', back_populates='posts')
    music = relationship('MusicsModel', back_populates='posts')
    comments = relationship('CommentsModel', back_populates='post', cascade="all, delete")
    post_views = relationship('PostViewsModel', back_populates='post', cascade='all, delete')
    saves = relationship('SavesModel', back_populates='post', cascade='all, delete')


class CommentsModel(BaseModel):
    __tablename__ = 'comments'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)

    post_id = Column(UUID, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    post = relationship('PostsModel', back_populates='comments')
    user = relationship('UsersModel', back_populates='comments')
    replies = relationship('CommentRepliesModel', back_populates='comment', cascade="all, delete")
    comment_likes = relationship('CommentLikesModel', back_populates='comment', cascade="all, delete")


class CommentRepliesModel(BaseModel):
    __tablename__ = 'comment_replies'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)

    comment_id = Column(UUID, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    comment = relationship('CommentsModel', back_populates='replies')
    user = relationship('UsersModel', back_populates='replies')


class CommentLikesModel(BaseModel):
    __tablename__ = 'comment_likes'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
    comment_id = Column(UUID, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True)
    comment_reply_id = Column(UUID, ForeignKey('comment_replies.id', ondelete='CASCADE'), nullable=True)

    __table_args__ = (UniqueConstraint('user_id', 'comment_id', name='_user_comment_like_uc'),)

    user = relationship("UsersModel", back_populates="comment_likes")
    comment = relationship("CommentsModel", back_populates="comment_likes")

class CodesModel(BaseModel):
    __tablename__ = "codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    code = Column(Integer)

class PostViewsModel(BaseModel):
    __tablename__ = 'post_views'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
    post_id = Column(UUID, ForeignKey('posts.id', ondelete='CASCADE'))

    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_post_uc'),)

    user = relationship("UsersModel", back_populates="post_views")
    post = relationship("PostsModel", back_populates="post_views")


class SavesModel(BaseModel):
    __tablename__ = 'saves'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
    post_id = Column(UUID, ForeignKey('posts.id', ondelete='CASCADE'))

    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_save_uc'),)

    user = relationship("UsersModel", back_populates="saves")
    post = relationship("PostsModel", back_populates='saves')

# Biron postni save qilinganda Collection larga saqlash uchun Model. Hali tayyor emas.

# class SaveCollections(BaseModel):
#     __tablename__ = "save_collections"
#
#     id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     owner_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
#     post_id = Column(UUID, ForeignKey('posts.id', ondelete='CASCADE'))

