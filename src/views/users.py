from pony.orm import db_session, commit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models import User
from typing import Optional
from src.services import manager, simple_send, generate_confirmation_token, confirm_token

router = APIRouter()


class UserM(BaseModel):
    username: str
    useralias: str
    email: str
    password: str
    frontURL: str


class ConfM(BaseModel):
    code: str


class UserMod(BaseModel):
    useralias: Optional[str] = None
    oldpassword: Optional[str] = None
    newpassword: Optional[str] = None


@router.post("/")
async def new_user(input_game: UserM):
    with db_session:
        user = User.get(username=input_game.username)
        if not user:
            user = User.get(email=input_game.email)
            if not user:
                curr_user = User(
                    username=input_game.username,
                    useralias=input_game.useralias,
                    email=input_game.email,
                    password=input_game.password)
                commit()

                await simple_send([input_game.email],
                                  generate_confirmation_token(input_game.email),
                                  input_game.frontURL)
            else:
                raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already registered")
        return {"id": curr_user.id, "message": "User created successfully"}


@router.post("/confirm")
async def confirm(confirmation: ConfM):
    with db_session:
        decr_email = confirm_token(confirmation.code)
        if not decr_email:
            raise HTTPException(status_code=400, detail="invalid code")
        user = User.get(email=decr_email)
        if not user:
            raise HTTPException(status_code=400, detail="invalid code")
        user.verified = True
        return {"info": f'your account {user.username} has been activated!'}


@router.put("/")
async def new_user(input_game: UserMod, user=Depends(manager)):
    with db_session:
        user = User.get(id=user["id"])
        message = 'fields modified:'
        if input_game.useralias:
            user.useralias = input_game.useralias
            message += " -useralias"
        if input_game.newpassword:
            if input_game.oldpassword and user.password == input_game.oldpassword:
                user.password = input_game.newpassword
                message += " -password"
            else:
                raise HTTPException(status_code=400, detail="Old password dont match")

        return {message}


@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        users = User.select()[:]
        result = {'data': [{"id": u.id, "email": u.email, "username": u.username} for u in users]}
        return result


@router.get("/me")
async def get_games(curr_user=Depends(manager)):
    with db_session:
        user = User.get(id=curr_user["id"])
        return {"id": user.id, "username": user.username, "useralias": user.useralias, "email": user.email}
