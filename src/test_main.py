from fastapi.testclient import TestClient
from .main import app
import pytest
from src.models import Game, Board, User, Player, Message
from pony.orm import db_session, commit
import datetime
client = TestClient(app)

pytest.users = {
    1: {"username": "andres", "useralias": "andres", "email": "a@gmail.com", "password": "12345"},
    2: {"username": "andres2", "useralias": "andres2", "email": "a2@gmail.com", "password": "12345"},
    3: {"username": "andres3", "useralias": "andres3", "email": "a3@gmail.com", "password": "12345"},
    4: {"username": "andres4", "useralias": "andres4", "email": "a4@gmail.com", "password": "12345"},
    5: {"username": "andres5", "useralias": "andres5", "email": "a5@gmail.com", "password": "12345"}
    }
pytest.info = {}

def test_create_user():
    for i,u in enumerate(pytest.users.values()):
        with db_session:
            response = client.post(
                "/users/", headers={},
                json={"username": u['username'],
                "useralias": u["useralias"], "email": u['email'],
                "password": "12345", "frontURL":"ded"}
            )
    with db_session:
        for i,u in enumerate(pytest.users.values()):
            user = User.get(email=u["email"])
            user.verified = True
            u["user_id"] = int(user.id)
    response = client.post(
    "/users/", headers={},
    json={"username": "andres", "useralias": "andres", "email": "a@a.com", "password": "12345","frontURL":"ded"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}
    response = client.post(
        "/users/", headers={},
        json={"username": "andres345", "useralias": "andres234", "email": "a@gmail.com", "password": "12345","frontURL":"ded"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_auth():
    for i,u in enumerate(pytest.users.values()):
        response = client.post("/auth/token", headers={},
            json={"username": u["username"], "password": "12345"}
        )
        assert response.status_code == 200
        rjson = response.json()
        assert rjson['token_type'] == 'bearer'
        u["token"] = rjson['access_token']


def test_create_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/", headers=headers,
        json={"name":"Partida 1", "player_amount": 5})
    with db_session:
        game = Game.get(created_by=pytest.users[1]["user_id"])
        assert response.status_code == 200
        assert response.json() == {'id': game.id, 'message': 'Game created successfully'}
        pytest.info["game"] = game.id

def test_join_game():
    for i,u in enumerate(list(pytest.users.values())[1:]):
        headers = {
        'Authorization': 'Bearer ' + u["token"],
        'Content-Type': 'text/plain'
        }
        response = client.post(f"/games/{pytest.info['game']}/join", headers=headers, json={})
        assert response.status_code == 200
        assert response.json() == {"message": 'joined successfully'}
    response = client.post("/games/100/join", headers=headers, json={})
    assert response.status_code == 404
    assert response.json() == {"detail": 'Game not found'}
    response = client.post(f"/games/{pytest.info['game']}/join", headers=headers, json={})
    assert response.status_code == 403
    assert response.json() == {"detail": 'The game is full'}


def test_get_games():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get(
        "/games/", headers=headers,
        json={}
    )
    with db_session:
        def parseGame(game):
            game_dict = game.to_dict()
            players = game.players.count()
            game_dict["joined_players"] = players
            return game_dict
        creation_date = str(Game.get(id=pytest.info['game']).creation_date).replace(" ","T")
        games = Game.select()[:]
        result = {'data': [parseGame(g) for g in games if not g.started]}
    for g in result["data"]:
        g["creation_date"] = str(g["creation_date"]).replace(" ","T")
    assert response.status_code == 200
    assert response.json() == result

def test_exit_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/100/exit", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": 'Game not found'}
    response = client.post(f"/games/{pytest.info['game']}/exit", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": 'game left successfully'}
    response = client.post(f"/games/{pytest.info['game']}/join", headers=headers, json={})
    assert response.status_code == 200
    assert response.json() == {"message": 'joined successfully'}
    pytest.users[6] = pytest.users[2]

def test_start_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post(f"/games/{pytest.info['game']}/start", headers=headers)
    assert response.status_code == 403
    assert response.json() == {
        'detail': "The game does not belong to the current user"
        }
    headers['Authorization'] = 'Bearer ' + pytest.users[1]["token"]
    response = client.get(f"/games/{pytest.info['game']}/board", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.post(f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id":"2"})
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.get(f"/games/{pytest.info['game']}/deck", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.post(f"/games/{pytest.info['game']}/start", headers=headers)
    assert response.status_code == 200
    with db_session:
        board_id = Game.get(id=pytest.info['game']).board.id
    assert response.json() == {
        'board_id': board_id,
        'message': 'Game started successfully'
        }
    headers['Authorization'] = 'Bearer ' + pytest.users[2]["token"]
    response = client.post(f"/games/{pytest.info['game']}/exit", headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": 'The Game is already started'}
    response = client.post("/games/100/start", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "The game does not exist"}
    response = client.post(f"/games/{pytest.info['game']}/start", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "The game was already started"}


def test_get_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get(f"/games/{pytest.info['game']}", headers=headers)
    with db_session:
        game = Game.get(id=pytest.info['game'])
        creation_date = str(game.creation_date).replace(" ","T")
        minister = int(game.status["minister"])
        created_by = int(game.created_by)
        board = game.board.id
    assert response.status_code == 200
    assert response.json() == {
            "id": pytest.info['game'],
            "name": "Partida 1",
            "creation_date": creation_date,
            "created_by": created_by,
            "player_amount": 5,
            "started": True,
            "status": {
                "minister": minister,
                "phase": "propose",
                "round": 1
            },
            "board": board}
    response = client.get("/games/100", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': 'Game not found'}

def test_players_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get(f"/games/{pytest.info['game']}/players", headers=headers)
    assert response.status_code == 200
    with db_session:
        player1 = Player.select(
            lambda p: p.user.username == pytest.users[1]["username"] and 
            p.game.id == pytest.info['game']).first()
        pytest.users[1]["player_id"] = player1.id 
        player2 = Player.select(
            lambda p: p.user.username == pytest.users[2]["username"] and 
            p.game.id == pytest.info['game']).first()
        pytest.users[2]["player_id"] = player2.id
        player3 = Player.select(
            lambda p: p.user.username == pytest.users[3]["username"] and 
            p.game.id == pytest.info['game']).first()
        pytest.users[3]["player_id"] = player3.id
        player4 = Player.select(
            lambda p: p.user.username == pytest.users[4]["username"] and 
            p.game.id == pytest.info['game']).first()
        pytest.users[4]["player_id"] = player4.id
        player5 = Player.select(
            lambda p: p.user.username == pytest.users[5]["username"] and 
            p.game.id == pytest.info['game']).first()
        pytest.users[5]["player_id"] = player5.id
        assert response.json() == {
                "data": [
                    {
                        "id": player1.id,
                        "choosable": True,
                        "current_position": player1.current_position,
                        "game": pytest.info['game'],
                        "role": player1.role,
                        "is_voldemort": player1.is_voldemort,
                        "alive": True,
                        "user": {
                            "id": pytest.users[1]["user_id"],
                            "useralias": "andres",
                            "username": "andres",
                            'verified': True
                        },
                    },
                    {
                        "id": player3.id,
                        "choosable": True,
                        "current_position": player3.current_position,
                        "game": pytest.info['game'],
                        "role": player3.role,
                        "is_voldemort": player3.is_voldemort,
                        "alive": True,
                        "user": {
                            "id": pytest.users[3]["user_id"],
                            "useralias": "andres3",
                            "username": "andres3",
                            'verified': True
                        },
                    },
                    {
                        "id": player4.id,
                        "choosable": True,
                        "current_position": player4.current_position,
                        "game": pytest.info['game'],
                        "role": player4.role,
                        "is_voldemort": player4.is_voldemort,
                        "alive": True,
                        "user": {
                            "id": pytest.users[4]["user_id"],
                            "useralias": "andres4",
                            "username": "andres4",
                            "verified": True
                        },
                    },
                    {
                        "id": player5.id,
                        "choosable": True,
                        "current_position": player5.current_position,
                        "game": pytest.info['game'],
                        "role": player5.role,
                        "is_voldemort": player5.is_voldemort,
                        "alive": True,
                        "user": {
                            "id": pytest.users[5]["user_id"],
                            "useralias": "andres5",
                            "username": "andres5",
                            "verified": True
                        },
                    },
                    {
                        "id": player2.id,
                        "choosable": True,
                        "current_position": player2.current_position,
                        "game": pytest.info['game'],
                        "role": player2.role,
                        "is_voldemort": player2.is_voldemort,
                        "alive": True,
                        "user": {
                            "id": pytest.users[2]["user_id"],
                            "useralias": "andres2",
                            "username": "andres2",
                            "verified": True
                        }
                    }
                ]
            }
    response = client.get("/games/100/players", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}

def test_status_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    with db_session:
        minister = int(Game.get(id=pytest.info['game']).status["minister"])
    response = client.get(f"/games/{pytest.info['game']}/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
    "minister": minister,
    "phase": "propose",
    "round": 1
    }
    response = client.get("/games/100/players", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}

def test_me_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get(f"/games/{pytest.info['game']}/me", headers=headers)
    with db_session:
        player = Player.get(id=pytest.users[1]["player_id"])
        current_position = player.current_position
        role = player.role
        voldemort = player.is_voldemort
    assert response.status_code == 200
    assert response.json() == {
        "id": pytest.users[1]["player_id"],
        "choosable": True,
        "current_position": current_position,
        "role": role,
        "is_voldemort": voldemort,
        "alive": True,
        "user": pytest.users[1]["user_id"],
        "game": pytest.info['game']
    }
    response = client.get("/games/100/me", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "The game does not exist"}


def test_board_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get(f"/games/{pytest.info['game']}/board", headers=headers)
    with db_session:
        current_position = Player.get(id=pytest.users[1]["player_id"]).current_position
        game = Game.get(id=pytest.info['game'])
        board = game.board.id
        minister = int(game.status["minister"])
    assert response.status_code == 200
    assert response.json() == {
            "id": board,
            "de_proc": 0,
            "po_proc": 0,
            "spell_fields": [
                "",
                "",
                "divination",
                "avadakedavra",
                "avadakedavra",
                "win"
            ],
            "caos": 0,
            "game": pytest.info['game']
    }
    response = client.get("/games/100/board", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': 'Game not found'}

def test_deck_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    with db_session:
        deck = Game.get(id=pytest.info['game']).board.deck
    response = client.get(f"/games/{pytest.info['game']}/deck", headers=headers)
    assert response.status_code == 200
    assert response.json() == deck
    response = client.get("/games/100/deck", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}

def test_choosehm_game():
    with db_session:
        game = Game.get(id=pytest.info['game'])
        minister = game.status["minister"]
        game.status["phase"] = "x"
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/100/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}
    response = client.post(f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The headmaster only can be elected in the propose phase"}
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.status["phase"] = "propose"
    for i in pytest.users.keys():
        if pytest.users[i]["player_id"] != minister:
            acc = i
            break 
    headers['Authorization'] = 'Bearer ' + pytest.users[acc]["token"]
    response = client.post(f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 400
    assert response.json() == {
        'detail': "Only the minister can propose a headmaster"}
    for i in pytest.users.keys():
        if pytest.users[i]["player_id"] == minister:
            user_minister = i
            break 
    headers['Authorization'] = 'Bearer ' + pytest.users[user_minister]["token"]
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": "300"}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The selected player does not exist"}
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": str(minister)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The minister can not be the headmaster"}
    with db_session:
        other_guy = Player.get(id=pytest.users[acc]["player_id"])
        other_guy.choosable = False
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": str(pytest.users[acc]["player_id"])}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player has been headmaster in the previous round"}
    with db_session:
        user = User.get(id=pytest.users[user_minister]["user_id"])
        new_game = Game(name="x", created_by=pytest.users[acc]["user_id"], started=False,
                    creation_date=datetime.datetime.now(),
                    player_amount=5, status={})
        new_player = Player(choosable=True, current_position='', role='', is_voldemort=False, alive=True,
                        user=user)
        new_game.players.add(new_player)
        other_guy = Player.get(id=pytest.users[acc]["player_id"])
        other_guy.choosable = True
        other_guy.alive = False
        commit()
    pytest.info['other_game'] = new_game.id
    pytest.info['other_player'] = new_player.id
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": str(new_player.id)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player does not belong to this game"}
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": str(other_guy.id)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player cannot be headmaster because is dead"}
    with db_session:
        other_guy = Player.get(id=pytest.users[acc]["player_id"])
        other_guy.alive = True
        username = other_guy.user.username
    response = client.post(
    f"/games/{pytest.info['game']}/choosehm", headers=headers,
    json={"id": str(other_guy.id)}
    )
    assert response.status_code == 200
    assert response.json() == {
    "message": f"The player number {other_guy.id}: {username} was proposed as headmaster"
    }


def test_vote_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/100/vote", headers=headers,
    json={"vote":"true"})
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.status["phase"] = "x"
    response = client.post(f"/games/{pytest.info['game']}/vote", headers=headers,
    json={"vote":"true"})
    assert response.status_code == 400
    assert response.json() == {'detail': "It is not the vote phase"}
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.status["phase"] = "vote"
    response = client.post(f"/games/{pytest.info['game']}/vote", headers=headers,
        json={"vote": "true"})
    assert response.status_code == 200
    assert response.json() == {
        "vote": f"Player: {pytest.users[1]['player_id']} (andres) successfully voted",
        "election": "election in progress"}
    response = client.post(f"/games/{pytest.info['game']}/vote", headers=headers,
        json={"vote": "true"})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "This player already voted"}
    votes = {0 : "false", 1: "true"}
    for i in list(pytest.users.keys())[1:-2]:
        headers['Authorization'] = 'Bearer ' + pytest.users[i]["token"]
        response = client.post(
            f"/games/{pytest.info['game']}/vote", headers=headers,
            json={"vote": f"{votes[i%2]}"}
        )
        assert response.status_code == 200
        assert response.json() == {
        "vote": f"Player: {pytest.users[i]['player_id']} ({pytest.users[i]['username']}) successfully voted",
        "election": "election in progress"}
    with db_session:
        old_status = Game.get(id=pytest.info['game']).status.copy()
        headers['Authorization'] = 'Bearer ' + pytest.users[5]["token"]
        Game.get(id=pytest.info['game']).status = old_status
        response = client.post(
            f"/games/{pytest.info['game']}/vote", headers=headers,
            json={"vote": "false"}
        )
        assert response.status_code == 200
        assert response.json() == {
        "vote": f"Player: {pytest.users[5]['player_id']} ({pytest.users[5]['username']}) successfully voted",
        "election": "election failed"}
        game = Game.get(id=pytest.info['game'])
        game.board.caos -= 1
        Player.get(id=game.status['minister']).current_position = ""
        game.status = old_status
        Player.get(id=old_status['minister']).current_position = "minister"
        Player.get(id=int(old_status['headmaster'])).current_position = "headmaster"
        response = client.post(
            f"/games/{pytest.info['game']}/vote", headers=headers,
            json={"vote": "true"}
        )
        assert response.status_code == 200
        assert response.json() == {
        "vote": f"Player: {pytest.users[5]['player_id']} ({pytest.users[5]['username']}) successfully voted",
        "election": "election succeed"}

def test_get_proclamations_game():
    with db_session:
        game = Game.get(id=pytest.info["game"])
        minister = game.status['minister']
        headmaster = int(game.status['headmaster'])
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] != minister and pytest.users[i]["player_id"] != headmaster:
                acc = i
                break
        headers = {
        'Authorization': 'Bearer ' + pytest.users[acc]["token"],
        'Content-Type': 'text/plain'
        }
        game.status["phase"] = "x"
        response = client.get(f"/games/{pytest.info['game']}/proclamations", headers=headers)
        assert response.status_code == 400
        assert response.json() == {'detail': "It is not a phase for geting a proclamation"}
        game.status["phase"] = "minister play"
        response = client.get(f"/games/{pytest.info['game']}/proclamations", headers=headers)
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the minister"}
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] == minister:
                user_minister = i
                break
        headers['Authorization'] = 'Bearer ' + pytest.users[user_minister]["token"]
        response = client.get(f"/games/{pytest.info['game']}/proclamations", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"data": game.board.deck.split(',')[:3]}
        game.status["phase"] = "headmaster play"
        response = client.get(f"/games/{pytest.info['game']}/proclamations", headers=headers)
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the headmaster"}
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] == headmaster:
                user_headmaster = i
                break
        headers['Authorization'] = 'Bearer ' + pytest.users[user_headmaster]["token"]
        response = client.get(f"/games/{pytest.info['game']}/proclamations", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"data": game.board.deck.split(',')[:2]}


def test_post_game_proclamations():
    with db_session:
        game = Game.get(id=pytest.info['game'])
        minister = game.status['minister']
        headmaster = int(game.status['headmaster'])
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] != minister and pytest.users[i]["player_id"] != headmaster:
                acc = i
                break
        headers = {
        'Authorization': 'Bearer ' + pytest.users[acc]["token"],
        'Content-Type': 'text/plain'
        }
        response = client.post("/games/100/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "Game not found"}
        game.status["phase"] = "x"
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 400
        assert response.json() == {'detail': "It is not a phase for playing a proclamation"}
        game.status["phase"] = "minister play"
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the minister"}
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] == minister:
                user_minister = i
                break
        headers['Authorization'] = 'Bearer ' + pytest.users[user_minister]["token"]
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 400
        assert response.json() == {'detail': "The input card was not one of the options"}
        card = game.board.deck.split(',')[:3][0]
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":card})
        assert response.status_code == 200
        assert response.json() == {'message': f'{card} card discarded successfully'}
        headers['Authorization'] = 'Bearer ' + pytest.users[acc]["token"]
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the headmaster"}
        for i in pytest.users.keys():
            if pytest.users[i]["player_id"] == headmaster:
                user_headmaster = i
                break
        headers['Authorization'] = 'Bearer ' + pytest.users[user_headmaster]["token"]
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":"defaef"})
        assert response.status_code == 400
        assert response.json() == {'detail': "The input card was not one of the options"}
        card = game.board.deck.split(',')[:2][0]
        response = client.post(f"/games/{pytest.info['game']}/proclamations", headers=headers,
        json={"card":card})
        assert response.status_code == 200
        assert response.json() == {'message': f'{card} card played successfully'}

def test_get_divination():
    with db_session:
        headers = {
        'Authorization': 'Bearer ' + pytest.users[1]["token"],
        'Content-Type': 'text/plain'
        }
        #response = client.get("/games/100/divination", headers=headers)
        game = Game.get(id=pytest.info['game'])
        game.status["minister"]

def test_user_get():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[1]["token"],
        'Content-Type': 'text/plain'
    }
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    with db_session:
        user = User.get(id=pytest.users[1]["user_id"])
    assert response.json() == {
        "id": user.id, "username": user.username,
        "useralias": user.useralias, "email": user.email}


def test_users_get():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[1]["token"],
        'Content-Type': 'text/plain'
    }
    with db_session:
        users = User.select()[:]
        result = {'data': [{"id": u.id, "email": u.email, "username": u.username} for u in users]}
        response = client.get("/users", headers=headers)
        assert response.status_code == 200
        assert response.json() == result

def test_user_put():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[1]["token"],
        'Content-Type': 'text/plain'
    }
    j = {
    "useralias": "andresito",
    "oldpassword": "12345",
    "newpassword": "123456"
    }
    response = client.put("/users/", headers=headers,
    json=j)
    assert response.status_code == 200
    assert response.json() == ['fields modified: -useralias -password']
    j.pop("useralias",None)
    response = client.put("/users/", headers=headers,
    json=j)
    assert response.status_code == 400
    assert response.json() == {'detail': "Old password dont match"}

def test_post_msg():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[2]["token"],
        'Content-Type': 'text/plain'
    }
    response = client.post(f"/games/{pytest.info['game']}/messages",headers=headers,
        json={"content":"Hola Guachin"})
    assert response.status_code == 200
    assert response.json() == {"detail": 
        "the message was recorder successfully"}
    response = client.post(f"/games/1000/messages",headers=headers,
        json={"content":"Hola Guachin"})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Game not found'}
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.started = False
        response = client.post(f"/games/{pytest.info['game']}/messages",headers=headers,
        json={"content":"Hola Guachin"})
        assert response.status_code == 400
        assert response.json() == {'detail': "Game is not started"}
        game.started = True


def test_get_msg():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[3]["token"],
        'Content-Type': 'text/plain'
    }
    with db_session:
        date = str(Message.select(lambda u: u.game.id == pytest.info['game']).first().date)
        date = date.replace(" ","T")
    response = client.get(f"/games/{pytest.info['game']}/messages",
        headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "content": "Hola Guachin",
                "date": date,
                "send_by": {
                    "id": pytest.users[2]["user_id"],
                    "username": "andres2",
                    "useralias": "andres2"
                }
            }
        ]
    }
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.started = False
        response = client.get(f"/games/{pytest.info['game']}/messages",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {'detail': "Game is not started"}
        game.started = True


def test_post_avadakedavra():
    with db_session:
        game = Game.get(id=pytest.info['game'])
        player = Player.select(
            lambda p: p.current_position == "" and p.game.id == game.id).first()
        for i in pytest.users.keys():
            if pytest.users[i]["user_id"] == player.user.id:
                user = i
                break
        headers = {
            'Authorization': 'Bearer ' + pytest.users[user]["token"],
            'Content-Type': 'text/plain'
        }
        response = client.post(f"/games/{pytest.info['game']}/avadakedavra",
        headers=headers,json={'id': pytest.users[2]["player_id"]})
        assert response.status_code == 400
        assert response.json() == {"detail": "Its not time for playing spells!"}
        game.status["phase"] = "spell play"
        response = client.post(f"/games/{pytest.info['game']}/avadakedavra",
        headers=headers,json={'id': pytest.users[2]["player_id"]})
        assert response.status_code == 400
        assert response.json() == {"detail": "The avadakedavra spell is not available"}


def test_get_divination():
    with db_session:
        game = Game.get(id=pytest.info['game'])
        player = Player.select(
            lambda p: p.current_position == "" and p.game.id == game.id).first()
        for i in pytest.users.keys():
            if pytest.users[i]["user_id"] == player.user.id:
                user = i
                break
        headers = {
            'Authorization': 'Bearer ' + pytest.users[user]["token"],
            'Content-Type': 'text/plain'
        }
        game.status["phase"] = "otro estado"
        response = client.get(f"/games/{pytest.info['game']}/divination",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Its not time for playing spells!"}
        game.status["phase"] = "spell play"
        response = client.get(f"/games/{pytest.info['game']}/divination",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "This player is not the minister"}
        game.started = False
        response = client.get(f"/games/{pytest.info['game']}/divination",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Game is not started"}
        game.started = True


def test_get_crucio():
    with db_session:
        game = Game.get(id=pytest.info['game'])
        player = Player.select(
            lambda p: p.current_position == "" and p.game.id == game.id).first()
        for i in pytest.users.keys():
            if pytest.users[i]["user_id"] == player.user.id:
                user = i
                break
        headers = {
            'Authorization': 'Bearer ' + pytest.users[user]["token"],
            'Content-Type': 'text/plain'
        }
        game.status["phase"] = "otro estado"
        response = client.get(f"/games/{pytest.info['game']}/crucio/4000",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "The victim player does not belong to this game"}
        response = client.get(
            f"/games/{pytest.info['game']}/crucio/{pytest.users[user]['player_id']}",
            headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Its not time for playing spells!"}
        game.status["phase"] = "spell play"
        game.started = False
        response = client.get(f"/games/{pytest.info['game']}/divination",
        headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "Game is not started"}
        game.started = True

def test_end_turn():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post(f"/games/{pytest.info['game']}/endturn",
        headers=headers,json={})
    assert response.status_code == 200
    assert response.json() == {"message": "Turn ended!"}
    response = client.post(f"/games/1000/endturn",
        headers=headers,json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
    with db_session:
        game = Game.get(id=pytest.info['game'])
        game.started = False
        response = client.post(f"/games/{pytest.info['game']}/endturn",
        headers=headers,json={})
        assert response.status_code == 400
        assert response.json() == {'detail': "Game is not started"}
        game.started = True

def test_delete_game():
    headers = {
        'Authorization': 'Bearer ' + pytest.users[2]["token"],
        'Content-Type': 'text/plain'
    }
    response = client.delete("/games/100/delete", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': 'The game does not exist'}
    response = client.delete(f"/games/{pytest.info['game']}/delete", headers=headers)
    assert response.status_code == 403
    assert response.json() == {'detail': 'The game does not belong to the current user'}
    headers['Authorization'] = 'Bearer ' + pytest.users[1]["token"]
    response = client.delete(f"/games/{pytest.info['game']}/delete", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": f"The game {pytest.info['game']} (Partida 1) was deleted"}
    with db_session:
        Player.get(id=pytest.info['other_player']).delete()
        Game.get(id=pytest.info['other_game']).delete()
        for u in list(pytest.users.values())[:-1]:
            User.get(id=u["user_id"]).delete()
