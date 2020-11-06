from pony.orm import db_session, commit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models import User
from src.services import manager

router = APIRouter()


class UserM(BaseModel):
    username: str
    email: str
    password: str


@router.post("/")
async def new_user(input_game: UserM):
    with db_session:
        user = User.get(username=input_game.username)
        if not user:
            user = User.get(email=input_game.email)
            if not user:
                curr_user = User(username=input_game.username, email=input_game.email, password=input_game.password)
            else:
                raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already registered")
        commit()
        return {"id": curr_user.id, "message": "User created successfully"}


@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        users = User.select()[:]
        result = {'data': [{"id": u.id, "email": u.email, "username": u.username} for u in users]}
        return result


@router.get("/me")
async def get_games(user=Depends(manager)):
    return {"id": user["id"], "username": user["username"], "email": user["email"]}
