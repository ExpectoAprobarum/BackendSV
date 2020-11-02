import json
from pony.orm import db_session, commit
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from pydantic import BaseModel
from src.models import db,User
from src.services import manager

router = APIRouter()

class UserM(BaseModel):
    username: str
    email: str
    password: str

@router.post("/")
async def new_user(inputGame: UserM):
    with db_session:
        user = User.get(username=inputGame.username)
        newUser = None
        if not user:
            user = User.get(email=inputGame.email)
            if not user:
                newUser = User(username= inputGame.username, email=inputGame.email, password=inputGame.password)
            else:
                raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already registered")
        commit()
        return {"id": newUser.id, "message": "User created succesfully"}

@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        users = User.select()[:]
        result = {'data': [{"id":u.id,"email":u.email,"username":u.username} for u in users]}
        return result