import datetime
import json
from pony.orm import db_session, commit
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from pydantic import BaseModel
from src.models import db,Game,Board,User,Player
from src.services import manager,defineBoard,newDeck,assignRoles
from random import randrange

router = APIRouter()

class GameM(BaseModel):
    name: str
    player_amount: int

@router.post("/")
async def create_game(inputGame: GameM, user=Depends(manager)):
    status = {}
    with db_session:
        newGame = Game(name=inputGame.name, created_by = user["id"], started=False, creation_date=datetime.datetime.now(), player_amount=inputGame.player_amount, status={})
        newPlayer = Player(choosable=True, current_position = '', role = '', is_voldemort = False, alive = True, user = User[user["id"]])
        newGame.players.add(newPlayer)
        newPlayer.game = newGame
        commit()
        status = {'id': newGame.id, 'message': 'Game created succesfully'}
    return status

@router.post("/{gameId}/start")
async def start_game(gameId: int, user=Depends(manager)):
    status = {}
    with db_session:
        currentGame=Game.get(id=gameId)
        #IMPORTANT!!!:
        #Currently this is not checking that the game is full before continue (for testing purposes)

        if currentGame is None:
            raise HTTPException(status_code=404, detail="The game does not exist")
        if currentGame.started:
            raise HTTPException(status_code=400, detail="The game was already started")
        if currentGame.created_by != user["id"]:
            raise HTTPException(status_code=403, detail="The game does not belong to the current user")
        
        #spell board and random deck
        spellFields = ','.join(defineBoard(currentGame.player_amount))
        randomDeck = ','.join(newDeck(15))

        newBoard = Board(de_proc=0,po_proc=0,spell_fields=spellFields,caos=0, game=currentGame, deck = randomDeck)
        currentGame.started = True
        currentGame.board = newBoard

        #Role choosing
        roleInfo = assignRoles(currentGame.players, Player)

        currentGame.status = {
            "round": 1,
            "phase": 'propose',
            "minister": roleInfo,
            "headmaster": '',
        }
        
        commit()

        status = {'board_id': newBoard.id, 'message': 'Game started succesfully'}
    return status

@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        games = Game.select()[:]
        result = {'data': [g.to_dict() for g in games if not g.started]}
    return result

@router.get("/{gameId}")
async def get_specific_game(gameId: int,user=Depends(manager)):
    with db_session:
        game = Game[gameId]
        result = game.to_dict()
    return result

@router.post("/{gameId}/join")
async def join_game(gameId: int,user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        newPlayer = Player(choosable=True, current_position = '', role = '', is_voldemort = False, alive = True, user = User[user["id"]])
        if game.players.count() == game.player_amount:
            raise HTTPException(status_code=403, detail="The game is full")
        newPlayer = Player(choosable=True, current_position = '', role = '', is_voldemort = False, alive = True, user = User[user["id"]])
        newPlayer.game = game
        game.players.add(newPlayer)
    return {"message": 'joined succesfully'}

@router.get("/{gameId}/players")
async def list_players(gameId: int,user=Depends(manager)):
    status = {}
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        players = game.players
        status = {'data': [p.to_dict() for p in players]}
        for p in status['data']:
            user = User.get(id=p['user']).to_dict()
            user.pop("password")
            user.pop("email")
            p.update(user=user)
    return status
    
@router.get("/{gameId}/status")
async def get_status(gameId: int,user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return game.status

@router.get("/{gameId}/board")
async def get_board(gameId: int,user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        board = game.board.to_dict().copy()
        spell_fields = board["spell_fields"]
        board["spell_fields"] = spell_fields.split(",")
        return board

