from fastapi import FastAPI
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.middleware.cors import CORSMiddleware
from src.views import games, users
from src.services import manager, load_user
from pydantic import BaseModel
from datetime import timedelta

app = FastAPI()


class UserM(BaseModel):
    username: str
    password: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def index():
    return {'app_name': 'Secret Voldemort', 'version': '1.0'}


@app.post('/auth/token')
async def login(data: UserM):
    user = data.username
    password = data.password

    user = load_user(user)  # authentication file function

    if not user:
        raise InvalidCredentialsException  # Default credential exeption
    elif password != user['password']:
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data=dict(sub=user), expires_delta=timedelta(hours=4)
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


app.include_router(games.router, prefix="/games")
app.include_router(users.router, prefix="/users")
