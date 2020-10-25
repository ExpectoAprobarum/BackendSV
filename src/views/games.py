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
        newGame = Game(name=inputGame.name, started=False, creation_date=datetime.datetime.now(), player_amount=inputGame.player_amount, status={})
        status = {'id': newGame.id, 'message': 'Game created succesfully'}
    return status

@router.post("/{gameId}/start")
def start_game(gameId: int):
    status = {}
    with db_session:
        Game[gameId].started = True
        status = {'message': 'Game started succesfully'}
    return status

@router.get("/")
def get_games():
    with db_session:
        games = Game.select()[:]
        result = {'data': [p.to_dict() for p in games if not p.started]}
    return result

@router.get("/{gameId}")
def get_specific_game(gameId: int):
    with db_session:
        game = Game[gameId]
        result = game.to_dict()
    return result


