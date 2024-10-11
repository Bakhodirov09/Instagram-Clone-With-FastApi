from fastapi import FastAPI
from routers.authentication import router
from routers.comments import comments
from routers.posts import posts
from routers.saves import saves
from routers.users import users
from routers.search import search
from database import Base, engine

app = FastAPI()

Base.metadata.create_all(engine)

app.include_router(router)
app.include_router(posts)
app.include_router(search)
app.include_router(comments)
app.include_router(saves)
app.include_router(users)