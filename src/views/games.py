import datetime
import json
from pony.orm import db_session, commit
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from pydantic import BaseModel
from src.models import db,Game,Board,User,Player
from src.services import manager,defineBoard,newDeck,assignRoles,reasignMinister
from random import randrange

router = APIRouter()

class GameM(BaseModel):
    name: str
    player_amount: int

class PlayerM(BaseModel):
    id: str

class VoteM(BaseModel):
    vote: bool

class ProcM(BaseModel):
    card: str

@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        games = Game.select()[:]
        result = {'data': [g.to_dict() for g in games if not g.started]}
    return result
    
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

@router.get("/{gameId}")
async def get_specific_game(gameId: int,user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        result = game.to_dict()
    return result

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
        }
        
        commit()

        status = {'board_id': newBoard.id, 'message': 'Game started succesfully'}
    return status

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
        status = game.status.copy()
        return status

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

@router.get("/{gameId}/deck")
async def get_deck(gameId: int, user=Depends(manager)):
    status = {}
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        return game.board.deck

@router.get("/{gameId}/deck")
async def get_deck(gameId: int, user=Depends(manager)):
    status = {}
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        return game.board.deck

@router.post("/{gameId}/choosehm")
async def choose_headmaster(headmaster: PlayerM, gameId: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        status = game.status
        player = Player.get(id=status["minister"])
        if status["phase"] != "propose":
            raise HTTPException(status_code=400, detail="The headmaster only can be elected in the propose phase")
        if player.user.id != user["id"]:
            raise HTTPException(status_code=400, detail="Only the minister can propose a headmaster")
        newHM = Player.get(id=headmaster.id)
        if newHM is None:
            raise HTTPException(status_code=400, detail="The selected player does not exist")
        if newHM.id == status["minister"]:
            raise HTTPException(status_code=400, detail="The minister can not be the headmaster")
        if newHM.game.id != gameId:
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        status["headmaster"] = headmaster.id
        ########### PASS THE TURN ###########
        status["phase"] = "vote"
        #####################################
        game.status = status
        newHM.current_position = "headmaster"
        return {"message": f'The player number {newHM.id}: {newHM.user.username} was proposed as headmaster'}
        
@router.post("/{gameId}/vote")
async def vote(vote: VoteM, gameId: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status["phase"] != "vote":
            raise HTTPException(status_code=400, detail="It is not the vote phase")

        playerQuery = Player.select(lambda p: user["id"]==p.user.id and p.game.id == gameId)
        currentPlayerArray = [p.to_dict() for p in playerQuery]
        if (currentPlayerArray == []):
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        
        currentPlayer = currentPlayerArray[0]
        voteArr = [{"player": currentPlayer["id"] , "user": user["id"], "username": user["username"], "vote": vote.vote}]
        if 'votes' in game.status.keys():
            for v in game.status["votes"]:
                if v["user"] == user["id"]:
                    raise HTTPException(status_code=400, detail="This player already voted")
            game.status["votes"] = game.status["votes"] + voteArr
        else:
            game.status["votes"] = voteArr
        
        pid = currentPlayer["id"]
        username = user["username"]
        playerMsg = f"Player: {pid} ({username}) succesfully voted"
        generalMsg = "election in progress"
        if len(game.status["votes"]) == game.players.count():
            noxVotes = 0
            lumosVotes = 0
            for v in game.status["votes"]:
                if v["vote"]:
                    lumosVotes += 1
                else:
                    noxVotes += 1
            if lumosVotes > noxVotes:
                ########### PASS THE TURN ###########
                game.status["phase"] = "minister play"
                generalMsg = "election succed"
                #####################################
            else:
                ########### PASS THE TURN ###########
                game.board.caos = game.board.caos + 1
                generalMsg = "election failed"
                reasignMinister(Player, game)
                #WRITE ACTIONS TO DO IF CAOS IS EQUAL TO 5
                #####################################
            del game.status["votes"]
        return {"vote":playerMsg,"election":generalMsg}
       
@router.get("/{gameId}/proclamations")
async def get_proclamations(gameId: int, user=Depends(manager)):
   with db_session:
        game = Game.get(id=gameId)
        data = {}
        
        playerQuery = Player.select(lambda p: user["id"]==p.user.id and p.game.id == gameId)
        currentPlayerArray = [p.to_dict() for p in playerQuery]
        if (currentPlayerArray == []):
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        currentPlayer = currentPlayerArray[0]

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status["phase"] == "minister play":
            if currentPlayer["current_position"] != "minister":
                raise HTTPException(status_code=404, detail="This player is not the minister")
            cards = game.board.deck.split(',')[:3]
            data = {"data": cards}
        elif game.status["phase"] == "headmaster play":
            if currentPlayer["current_position"] != "headmaster":
                raise HTTPException(status_code=404, detail="This player is not the headmaster")
            cards = game.board.deck.split(',')[:2]
            data = {"data": cards}
        else:
            raise HTTPException(status_code=400, detail="It is not a phase for geting a proclamation")
        return data

@router.post("/{gameId}/proclamations")
async def play(proc: ProcM, gameId: int, user=Depends(manager)):
   with db_session:
        game = Game.get(id=gameId)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        playerQuery = Player.select(lambda p: user["id"]==p.user.id and p.game.id == gameId)
        currentPlayerArray = [p.to_dict() for p in playerQuery]
        if (currentPlayerArray == []):
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        currentPlayer = currentPlayerArray[0]

        cards = []
        msg = ''
        if game.status["phase"] == "minister play":
            if currentPlayer["current_position"]!= "minister":
                raise HTTPException(status_code=404, detail="This player is not the minister")
            cards = game.board.deck.split(',')[:3]
            if proc.card in cards:
                cards = game.board.deck.split(',')
                cards.remove(proc.card)
                game.board.deck = ','.join(cards)
            else:
                raise HTTPException(status_code=400, detail="The input card was not one of the options") 
            msg = f'{proc.card} card discarded successfully'
            ########### PASS THE TURN ###########
            game.status["phase"] = "headmaster play"
            #####################################

        elif game.status["phase"] == "headmaster play":
            if currentPlayer["current_position"] != "headmaster":
                raise HTTPException(status_code=404, detail="This player is not the headmaster")
            cards = game.board.deck.split(',')[:2]
            if proc.card in cards:
                cards = game.board.deck.split(',')[2:]
                game.board.deck = ','.join(cards)
                if proc.card == 'phoenix':
                    game.board.po_proc += 1
                else:
                    game.board.de_proc += 1
                #IMPORTANT! HERE GOES THE LOGIC FOR SPELL ACTIVATION
                ########### PASS THE TURN ###########
                reasignMinister(Player, game)
                #####################################
                msg = f'{proc.card} card played successfully'
            else:
                raise HTTPException(status_code=400, detail="The input card was not one of the options") 

        else:
            raise HTTPException(status_code=400, detail="It is not a phase for playing a proclamation")

        return {"message": msg}
        
@router.delete("/{gameId}/delete")
async def end_game(gameId: int, user=Depends(manager)):
    status = {}
    with db_session:
        currentGame=Game.get(id=gameId)
        if currentGame is None:
            raise HTTPException(status_code=404, detail="The game does not exist")
        if currentGame.created_by != user["id"]:
            raise HTTPException(status_code=403, detail="The game does not belong to the current user")
        gName = currentGame.name
        currentGame.delete()
    return {"message": f"The game {gameId} ({gName}) was deleted"}








