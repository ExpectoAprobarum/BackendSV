import datetime
from pony.orm import db_session, commit, desc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models import Game, Board, User, Player, Message
from src.services import manager

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


class MessageM(BaseModel):
    content: str


@router.get("/")
async def get_games(user=Depends(manager)):
    with db_session:
        def parseGame(game):
            game_dict = game.to_dict()
            players = game.players.count()
            game_dict["joined_players"] = players
            return game_dict
        games = Game.select()[:]
        result = {'data': [parseGame(g) for g in games if not g.started]}
    return result


@router.post("/")
async def create_game(input_game: GameM, user=Depends(manager)):
    with db_session:
        new_game = Game(name=input_game.name, created_by=user["id"], started=False,
                        creation_date=datetime.datetime.now(),
                        player_amount=input_game.player_amount, status={})
        new_player = Player(choosable=True, current_position='', role='', is_voldemort=False, alive=True,
                            user=User[user["id"]])
        new_game.players.add(new_player)
        new_player.game = new_game
        commit()
        status = {'id': new_game.id, 'message': 'Game created successfully'}
    return status


@router.get("/{game_id}")
async def get_specific_game(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        result = game.to_dict()
    return result


@router.post("/{game_id}/start")
async def start_game(game_id: int, user=Depends(manager)):
    status = {}
    with db_session:
        current_game = Game.get(id=game_id)
        # IMPORTANT!!!:
        # Currently this is not checking that the game is full before continue (for testing purposes)

        if current_game is None:
            raise HTTPException(status_code=404, detail="The game does not exist")
        if current_game.started:
            raise HTTPException(status_code=400, detail="The game was already started")
        if current_game.created_by != user["id"]:
            raise HTTPException(status_code=403, detail="The game does not belong to the current user")

        # spell board and random deck
        spell_fields = ','.join(Board.define_board(current_game.player_amount))
        random_deck = ','.join(Board.new_deck(50))

        new_board = Board(de_proc=0, po_proc=0, spell_fields=spell_fields, caos=0, game=current_game, deck=random_deck)
        current_game.started = True
        current_game.board = new_board

        # Role choosing
        role_info = Player.assign_roles(current_game.players)

        current_game.status = {
            "round": 1,
            "phase": 'propose',
            "minister": role_info,
        }

        commit()

        status = {'board_id': new_board.id, 'message': 'Game started successfully'}
    return status


@router.post("/{game_id}/join")
async def join_game(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.players.count() == game.player_amount:
            raise HTTPException(status_code=403, detail="The game is full")
        new_player = Player(choosable=True, current_position='', role='', is_voldemort=False, alive=True,
                            user=User[user["id"]])
        new_player.game = game
        game.players.add(new_player)
    return {"message": 'joined successfully'}


@router.post("/{game_id}/exit")
async def left_game(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.started:
            raise HTTPException(status_code=400, detail="The Game is already started")

        current_player = Player.user_player(user, game_id)
        player_obj = Player.get(id=current_player["id"])
        player_obj.delete()

    return {"message": 'game left successfully'}


@router.get("/{game_id}/players")
async def list_players(game_id: int, user=Depends(manager)):
    status = {}
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        players = game.players
        parsed_players = [p.to_dict() for p in players]
        parsed_players.sort(key=lambda x: x.get('id'))
        for p in parsed_players:
            user = User.get(id=p['user']).to_dict()
            user.pop("password")
            user.pop("email")
            p.update(user=user)
    return {'data': parsed_players}


@router.get("/{game_id}/status")
async def get_status(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        status = game.status.copy()
        return status


@router.get("/{game_id}/board")
async def get_board(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        board = game.board.to_dict().copy()
        spell_fields = board["spell_fields"]
        board["spell_fields"] = spell_fields.split(",")
        return board


@router.get("/{game_id}/deck")
async def get_deck(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        return game.board.deck


@router.post("/{game_id}/choosehm")
async def choose_headmaster(headmaster: PlayerM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
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
        new_hm = Player.get(id=headmaster.id)
        if new_hm is None:
            raise HTTPException(status_code=400, detail="The selected player does not exist")
        if new_hm.id == status["minister"]:
            raise HTTPException(status_code=400, detail="The minister can not be the headmaster")
        if not new_hm.choosable:
            raise HTTPException(status_code=400, detail="The player has been headmaster in the previous round")
        if new_hm.game.id != game_id:
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        if not new_hm.alive:
            raise HTTPException(status_code=400, detail="The player cannot be headmaster because is dead")
        Player.reset_choosable()
        status["headmaster"] = int(headmaster.id)
        # PASS THE TURN ####################
        status["phase"] = "vote"
        #####################################
        game.status = status
        new_hm.current_position = "headmaster"
        new_hm.choosable = False
        return {"message": f'The player number {new_hm.id}: {new_hm.user.username} was proposed as headmaster'}


@router.post("/{game_id}/vote")
async def vote(in_vote: VoteM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status["phase"] != "vote":
            raise HTTPException(status_code=400, detail="It is not the vote phase")

        current_player = Player.user_player(user, game_id)
        vote_arr = [{"player": current_player["id"],
                     "user": user["id"],
                     "username": user["username"],
                     "vote": in_vote.vote}]

        if 'votes' in game.status.keys():
            for v in game.status["votes"]:
                if v["user"] == user["id"]:
                    raise HTTPException(status_code=400, detail="This player already voted")
            game.status["votes"] = game.status["votes"] + vote_arr
        else:
            game.status["votes"] = vote_arr

        pid = current_player["id"]
        username = user["username"]
        player_msg = f"Player: {pid} ({username}) successfully voted"
        general_msg = "election in progress"
        if len(game.status["votes"]) == game.players.select(lambda p: p.alive).count():
            nox_votes = 0
            lumos_votes = 0
            for v in game.status["votes"]:
                if v["vote"]:
                    lumos_votes += 1
                else:
                    nox_votes += 1
            if lumos_votes > nox_votes:
                # PASS THE TURN ######################
                game.status["phase"] = "minister play"
                general_msg = "election succeed"
                new_hm = Player.get(id=game.status["headmaster"])
                if new_hm and (game.player_amount == 5 or game.player_amount == 6)\
                        and game.board.de_proc > 3 and new_hm.is_voldemort:
                    game.status = {"info": "game ended", "winner": "Death Eaters", "detail": "voldemort headmaster"}
                    return {"vote": player_msg, "election": general_msg}
                ######################################
            else:
                # PASS THE TURN #####################
                game.board.caos = game.board.caos + 1
                general_msg = "election failed"
                Player.reassign_minister(game)
                # WRITE ACTIONS TO DO IF CAOS IS EQUAL TO 5
                #####################################
        return {"vote": player_msg, "election": general_msg}


@router.get("/{game_id}/proclamations")
async def get_proclamations(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)

        current_player = Player.user_player(user, game_id)

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status["phase"] == "minister play":
            if current_player["current_position"] != "minister":
                raise HTTPException(status_code=404, detail="This player is not the minister")
            cards = game.board.deck.split(',')[:3]
            data = {"data": cards}
        elif game.status["phase"] == "headmaster play":
            if current_player["current_position"] != "headmaster":
                raise HTTPException(status_code=404, detail="This player is not the headmaster")
            cards = game.board.deck.split(',')[:2]
            data = {"data": cards}
        else:
            raise HTTPException(status_code=400, detail="It is not a phase for geting a proclamation")
        return data


@router.post("/{game_id}/proclamations")
async def play(proc: ProcM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        current_player = Player.user_player(user, game_id)

        if game.status["phase"] == "minister play":
            if current_player["current_position"] != "minister":
                raise HTTPException(status_code=404, detail="This player is not the minister")
            cards = game.board.deck.split(',')[:3]
            if proc.card in cards:
                cards = game.board.deck.split(',')
                cards.remove(proc.card)
                game.board.deck = ','.join(cards)
            else:
                raise HTTPException(status_code=400, detail="The input card was not one of the options")
            msg = f'{proc.card} card discarded successfully'
            # PASS THE TURN #####################
            game.status["phase"] = "headmaster play"
            #####################################

        elif game.status["phase"] == "headmaster play":
            if current_player["current_position"] != "headmaster":
                raise HTTPException(status_code=404, detail="This player is not the headmaster")
            cards = game.board.deck.split(',')[:2]
            if proc.card in cards:
                cards = game.board.deck.split(',')[2:]
                game.board.deck = ','.join(cards)
                if proc.card == 'phoenix':
                    game.board.po_proc += 1
                else:
                    game.board.de_proc += 1
                # IMPORTANT! HERE GOES THE LOGIC FOR SPELL ACTIVATION
                # PASS THE TURN ###########
                spell_fields = game.board.spell_fields.split(",")
                spells = ["divination", "avadakedavra"]
                if game.board.de_proc != 0 and spell_fields[game.board.de_proc - 1] in spells:
                    game.status["phase"] = "spell play"
                else:
                    Player.reassign_minister(game)
                #####################################
                msg = f'{proc.card} card played successfully'
            else:
                raise HTTPException(status_code=400, detail="The input card was not one of the options")

        else:
            raise HTTPException(status_code=400, detail="It is not a phase for playing a proclamation")

        return {"message": msg}


@router.delete("/{game_id}/delete")
async def end_game(game_id: int, user=Depends(manager)):
    with db_session:
        current_game = Game.get(id=game_id)
        if current_game is None:
            raise HTTPException(status_code=404, detail="The game does not exist")
        if current_game.created_by != user["id"]:
            raise HTTPException(status_code=403, detail="The game does not belong to the current user")
        g_name = current_game.name
        players = current_game.players
        for p in players:
            p.delete()
        if current_game.board:
            current_game.board.delete()
        current_game.delete()
        return {"message": f"The game {game_id} ({g_name}) was deleted"}


@router.get("/{game_id}/me")
async def get_current_player(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="The game does not exist")

        return Player.user_player(user, game_id)


@router.get("/{game_id}/crucio")
async def play_crucio(player_id: PlayerM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        current_player = Player.user_player(user, game_id)
        victim_player = Player.select(
            lambda p: p.id == player_id.id and p.game.id == game_id).first()
        deck = game.board.spell_fields.split(",")
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        if not victim_player:
            raise HTTPException(status_code=400, detail="The victim player does not belong to this game")
        if game.status["phase"] != "spell play":
            raise HTTPException(status_code=400, detail="Its not time for playing spells!")
        if current_player["current_position"] != "minister":
            raise HTTPException(status_code=400, detail=f"This player is not the minister")
        if game.board.de_proc == 0 or deck[game.board.de_proc - 1] != "crucio":
            raise HTTPException(status_code=400, detail="The crucio spell is not available")
        victim_user = User.select(
            lambda u: u.id == victim_player.user.id).first()
        role = victim_player.role
        Player.reassign_minister(game)
        return {"role": role, "player_id": player_id.id , "player_alias": victim_user.useralias}

@router.get("/{game_id}/divination")
async def play_divination(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        current_player = Player.user_player(user, game_id)
        deck = game.board.spell_fields.split(",")
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        if game.status["phase"] != "spell play":
            raise HTTPException(status_code=400, detail="Its not time for playing spells!")
        if current_player["current_position"] != "minister":
            raise HTTPException(status_code=400, detail=f"This player is not the minister")
        if game.board.de_proc == 0 or deck[game.board.de_proc - 1] != "divination":
            raise HTTPException(status_code=400, detail="The divination spell is not available")
        return {"data": game.board.deck.split(",")[:3]}


# THIS ENDPOINT ENDS THE TURN FOR DIVINATION AND TEST PURPOSES, USE CAREFULLY!!!
@router.post("/{game_id}/endturn")
async def end_turn(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        Player.reassign_minister(game)
        return {"message": "Turn ended!"}

@router.post("/{game_id}/avadakedavra")
async def kill_player(player_id: PlayerM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        current_player = Player.user_player(user, game_id)
        victim_player = Player.select(
            lambda p: p.id == player_id.id and p.game.id == game_id).first()
        deck = game.board.spell_fields.split(",")
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status["phase"] != "spell play":
            raise HTTPException(status_code=400, detail="Its not time for playing spells!")
        if not game.board.de_proc or deck[game.board.de_proc - 1] != 'avadakedavra':
            raise HTTPException(status_code=400, detail="The avadakedavra spell is not available")
        if not victim_player:
            raise HTTPException(status_code=400, detail="The victim player does not belong to this game")
        if current_player["current_position"] != "minister":
                raise HTTPException(status_code=404, detail="This player is not the minister")
        victim_player.alive = False
        if victim_player.is_voldemort:
            game.status = {"info": "game ended", "winner": "Phoenix Order", "detail": "voldemort killed"}
        else:
            Player.reassign_minister(game)
        victim_user = User.select(
            lambda u: u.id == victim_player.user.id).first()
        return {"avadakedavra": "succed!", "dead_player_id": player_id.id, "dead_player_alias": victim_user.useralias}


@router.get("/{game_id}/messages")
async def all_messages(game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        Player.user_player(user, game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        chats = game.chats.order_by(lambda c: desc(c.date))
        return {'data': [{"content": m.content, "date": m.date, "send_by": m.player.to_dict()} for m in chats]}


@router.post("/{game_id}/messages")
async def write_message(msg_content: MessageM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        current_player = Player.user_player(user, game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        Message(date=datetime.datetime.now(), content=msg_content.content, game=game_id, player=current_player["id"])
        return {"detail": "the message was recorder successfully"}


@router.post("/{game_id}/imperius")
async def play_imperius(obj_player: PlayerM, game_id: int, user=Depends(manager)):
    with db_session:
        game = Game.get(id=game_id)
        current_player = Player.user_player(user, game_id)
        objective_player = game.players.select(lambda p: p.id == obj_player.id and p.game.id == game.id).first()
        board = game.board.spell_fields.split(",")
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        if not game.started:
            raise HTTPException(status_code=400, detail="Game is not started")
        if game.status["phase"] != "spell play":
            raise HTTPException(status_code=400, detail="Its not time for playing spells!")
        if current_player["current_position"] != "minister":
            raise HTTPException(status_code=400, detail=f"This player is not the minister")
        if game.board.de_proc == 0 or board[game.board.de_proc - 1] != "imperius":
            raise HTTPException(status_code=400, detail="The imperius spell is not available")
        if not objective_player:
            raise HTTPException(status_code=400, detail="The objective player does not belong to this game")
        if not objective_player.alive:
            raise HTTPException(status_code=400, detail="The objective player is dead")
        game.status["temporal_minister"] = objective_player.id
        game.status["return_minister"] = current_player["id"]
        Player.reassign_minister(game)
        return {"message": f"The player {objective_player.id} ({objective_player.user.username}) is going to be the "
                           f"next minister!"}
