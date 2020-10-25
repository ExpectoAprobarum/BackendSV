import datetime
import json
from pony.orm import db_session
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from src.models import db,Game

router = APIRouter()

class GameM(BaseModel):
    name: str
    player_amount: int

@router.post("/")
def create_game(inputGame: GameM):
    status = {}
    with db_session:
        newGame = Game(name=inputGame.name, creation_date=datetime.datetime.now(), player_amount=inputGame.player_amount, status={})
        print(newGame)
        status = {'id': newGame.id, 'message': 'Game created succesfully'}
    return status

@router.get("/")
def get_game():
    with db_session:
        persons = Game.select()[:]
        result = {'data': [p.to_dict() for p in persons]}
    return result
