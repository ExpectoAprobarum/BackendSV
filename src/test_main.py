from fastapi.testclient import TestClient
from .main import app
import pytest
from src.models import Game, Board, User, Player
from pony.orm import db_session, commit
import datetime
client = TestClient(app)

pytest.users = {
    1: {"username": "andres", "useralias": "andres", "email": "a@a.com", "password": "12345"},
    2: {"username": "andres2", "useralias": "andres2", "email": "a2@a.com", "password": "12345"},
    3: {"username": "andres3", "useralias": "andres3", "email": "a3@a.com", "password": "12345"},
    4: {"username": "andres4", "useralias": "andres4", "email": "a4@a.com", "password": "12345"},
    5: {"username": "andres5", "useralias": "andres5", "email": "a5@a.com", "password": "12345"}
    }


def test_create_user():
    for i,u in enumerate(pytest.users.values()):
        response = client.post(
            "/users/", headers={},
            json={"username": u['username'], "useralias": u["useralias"], "email": u['email'], "password": "12345"}
        )
        assert response.status_code == 200
        rjson = response.json()
        assert rjson == {"id": i+1, "message": "User created successfully"}
    response = client.post(
        "/users/", headers={},
        json=pytest.users[1]
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}
    response = client.post(
        "/users/", headers={},
        json={"username": "andres345", "useralias": "andres234", "email": "a@a.com", "password": "12345"}
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
        print(u["token"])

def test_create_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/", headers=headers,
        json={"name":"Partida 1", "player_amount": 5})
    assert response.status_code == 200
    assert response.json() == {'id': 1, 'message': 'Game created successfully'}


def test_join_game():
    for i,u in enumerate(list(pytest.users.values())[1:]):
        headers = {
        'Authorization': 'Bearer ' + u["token"],
        'Content-Type': 'text/plain'
        }
        response = client.post("/games/1/join", headers=headers, json={})
        assert response.status_code == 200
        assert response.json() == {"message": 'joined successfully'}
    response = client.post("/games/100/join", headers=headers, json={})
    assert response.status_code == 404
    assert response.json() == {"detail": 'Game not found'}
    response = client.post("/games/1/join", headers=headers, json={})
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
        creation_data = str(Game.get(id=1).creation_date).replace(" ","T")
    print(creation_data)
    assert response.status_code == 200
    print(response.json())
    assert response.json() == {
    "data": [
            {"id": 1,
            "name": "Partida 1",
            "creation_date": creation_data,
            "created_by": 1,
            "player_amount": 5,
            "started": False,
            "status": {},
            "board": None
        }]}

def test_exit_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/100/exit", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": 'Game not found'}
    response = client.post("/games/1/exit", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": 'game left successfully'}
    response = client.post("/games/1/join", headers=headers, json={})
    assert response.status_code == 200
    assert response.json() == {"message": 'joined successfully'}
    pytest.users[6] = pytest.users[2]

def test_start_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/1/start", headers=headers)
    assert response.status_code == 403
    assert response.json() == {
        'detail': "The game does not belong to the current user"
        }
    headers['Authorization'] = 'Bearer ' + pytest.users[1]["token"]
    response = client.get("/games/1/board", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.post("/games/1/choosehm", headers=headers,
    json={"id":"2"})
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.get("/games/1/deck", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "Game is not started"}
    response = client.post("/games/1/start", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'board_id': 1,
        'message': 'Game started successfully'
        }
    headers['Authorization'] = 'Bearer ' + pytest.users[2]["token"]
    response = client.post("/games/1/exit", headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": 'The Game is already started'}
    response = client.post("/games/100/start", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "The game does not exist"}
    response = client.post("/games/1/start", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "The game was already started"}


def test_get_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get("/games/1", headers=headers)
    with db_session:
        creation_data = str(Game.get(id=1).creation_date).replace(" ","T")
        minister = int(Game.get(id=1).status["minister"])
    assert response.status_code == 200
    assert response.json() == {
            "id": 1,
            "name": "Partida 1",
            "creation_date": creation_data,
            "created_by": 1,
            "player_amount": 5,
            "started": True,
            "status": {
                "minister": minister,
                "phase": "propose",
                "round": 1
            },
            "board": 1}
    response = client.get("/games/100", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': 'Game not found'}

def test_players_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[2]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get("/games/1/players", headers=headers)
    assert response.status_code == 200
    with db_session:

        assert response.json() == {
                "data": [
                    {
                        "id": 1,
                        "choosable": True,
                        "current_position": Player.get(id=1).current_position,
                        "role": Player.get(id=1).role,
                        "is_voldemort": Player.get(id=1).is_voldemort,
                        "alive": True,
                        "user": {
                            "id": 1,
                            "username": "andres",
                            "useralias": "andres"
                        },
                        "game": 1
                    },
                    {
                        "id": 3,
                        "choosable": True,
                        "current_position": Player.get(id=3).current_position,
                        "role": Player.get(id=3).role,
                        "is_voldemort": Player.get(id=3).is_voldemort,
                        "alive": True,
                        "user": {
                            "id": 3,
                            "username": "andres3",
                            "useralias": "andres3"
                        },
                        "game": 1
                    },
                    {
                        "id": 4,
                        "choosable": True,
                        "current_position": Player.get(id=4).current_position,
                        "role": Player.get(id=4).role,
                        "is_voldemort": Player.get(id=4).is_voldemort,
                        "alive": True,
                        "user": {
                            "id": 4,
                            "username": "andres4",
                            "useralias": "andres4"
                        },
                        "game": 1
                    },
                    {
                        "id": 5,
                        "choosable": True,
                        "current_position": Player.get(id=5).current_position,
                        "role": Player.get(id=5).role,
                        "is_voldemort": Player.get(id=5).is_voldemort,
                        "alive": True,
                        "user": {
                            "id": 5,
                            "username": "andres5",
                            "useralias": "andres5"
                        },
                        "game": 1
                    },
                    {
                        "id": 6,
                        "choosable": True,
                        "current_position": Player.get(id=6).current_position,
                        "role": Player.get(id=6).role,
                        "is_voldemort": Player.get(id=6).is_voldemort,
                        "alive": True,
                        "user": {
                            "id": 2,
                            "username": "andres2",
                            "useralias": "andres2"
                        },
                        "game": 1
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
        minister = int(Game.get(id=1).status["minister"])
    response = client.get("/games/1/status", headers=headers)
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
    response = client.get("/games/1/me", headers=headers)
    with db_session:
        current_position = Player.get(id=1).current_position
        role = Player.get(id=1).role
        voldemort = Player.get(id=1).is_voldemort
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "choosable": True,
        "current_position": current_position,
        "role": role,
        "is_voldemort": voldemort,
        "alive": True,
        "user": 1,
        "game": 1
    }
    response = client.get("/games/100/me", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "The game does not exist"}


def test_board_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get("/games/1/board", headers=headers)
    with db_session:
        current_position = Player.get(id=1).current_position
        minister = int(Game.get(id=1).status["minister"])
    assert response.status_code == 200
    assert response.json() == {
            "id": 1,
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
            "game": 1
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
        deck = Game.get(id=1).board.deck
    response = client.get("/games/1/deck", headers=headers)
    assert response.status_code == 200
    assert response.json() == deck
    response = client.get("/games/100/deck", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}

def test_choosehm_game():
    with db_session:
        game = Game.get(id=1)
        minister = game.status["minister"]
        game.status["phase"] = "x"
    headers = {
    'Authorization': 'Bearer ' + pytest.users[minister]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.post("/games/100/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 404
    assert response.json() == {'detail': "Game not found"}
    response = client.post("/games/1/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The headmaster only can be elected in the propose phase"}
    with db_session:
        game = Game.get(id=1)
        game.status["phase"] = "propose"
    acc = minister
    acc = (acc % 5) + 1
    if acc == 2:
        acc = 3
    headers['Authorization'] = 'Bearer ' + pytest.users[acc]["token"]
    response = client.post("/games/1/choosehm", headers=headers,
    json={'id':'2'})
    assert response.status_code == 400
    assert response.json() == {
        'detail': "Only the minister can propose a headmaster"}
    headers['Authorization'] = 'Bearer ' + pytest.users[minister]["token"]
    response = client.post(
    "/games/1/choosehm", headers=headers,
    json={"id": "300"}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The selected player does not exist"}
    response = client.post(
    "/games/1/choosehm", headers=headers,
    json={"id": str(minister)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The minister can not be the headmaster"}
    with db_session:
        other_guy = Player.get(id=acc)
        other_guy.choosable = False
    response = client.post(
    "/games/1/choosehm", headers=headers,
    json={"id": str(acc)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player has been headmaster in the previous round"}
    with db_session:
        user = User.get(id=Player.get(id=minister).user.id)
        new_game = Game(name="x", created_by=1, started=False,
                    creation_date=datetime.datetime.now(),
                    player_amount=5, status={})
        new_player = Player(choosable=True, current_position='', role='', is_voldemort=False, alive=True,
                        user=user)
        new_game.players.add(new_player)
        other_guy = Player.get(id=acc)
        other_guy.choosable = True
        other_guy.alive = False
        commit()
    response = client.post(
    "/games/1/choosehm", headers=headers,
    json={"id": str(new_player.id)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player does not belong to this game"}
    response = client.post(
    "/games/1/choosehm", headers=headers,
    json={"id": str(other_guy.id)}
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': "The player cannot be headmaster because is dead"}
    with db_session:
        other_guy = Player.get(id=acc)
        other_guy.alive = True
        username = other_guy.user.username
    response = client.post(
    "/games/1/choosehm", headers=headers,
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
        game = Game.get(id=1)
        game.status["phase"] = "x"
    response = client.post("/games/1/vote", headers=headers,
    json={"vote":"true"})
    assert response.status_code == 400
    assert response.json() == {'detail': "It is not the vote phase"}
    with db_session:
        game = Game.get(id=1)
        game.status["phase"] = "vote"
    response = client.post("/games/1/vote", headers=headers,
        json={"vote": "true"})
    assert response.status_code == 200
    assert response.json() == {
        "vote": "Player: 1 (andres) successfully voted",
        "election": "election in progress"}
    response = client.post("/games/1/vote", headers=headers,
        json={"vote": "true"})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "This player already voted"}
    votes = {0 : "false", 1: "true"}
    for i in list(pytest.users.keys())[1:-2]:
        headers['Authorization'] = 'Bearer ' + pytest.users[i]["token"]
        response = client.post(
            "/games/1/vote", headers=headers,
            json={"vote": f"{votes[i%2]}"}
        )
        assert response.status_code == 200
        j = i
        if i == 2:
            j = 6
        assert response.json() == {
        "vote": f"Player: {j} (andres{i}) successfully voted",
        "election": "election in progress"}
    with db_session:
        old_status = Game.get(id=1).status.copy()
        headers['Authorization'] = 'Bearer ' + pytest.users[5]["token"]
        Game.get(id=1).status = old_status
        response = client.post(
            "/games/1/vote", headers=headers,
            json={"vote": "false"}
        )
        assert response.status_code == 200
        assert response.json() == {
        "vote": f"Player: {5} (andres{5}) successfully voted",
        "election": "election failed"}
        game = Game.get(id=1)
        game.board.caos -= 1
        Player.get(id=game.status['minister']).current_position = ""
        game.status = old_status
        Player.get(id=old_status['minister']).current_position = "minister"
        Player.get(id=int(old_status['headmaster'])).current_position = "headmaster"
        response = client.post(
            "/games/1/vote", headers=headers,
            json={"vote": "true"}
        )
        assert response.status_code == 200
        assert response.json() == {
        "vote": f"Player: {5} (andres{5}) successfully voted",
        "election": "election succeed"}

def test_get_proclamations_game():
    with db_session:
        game = Game.get(id=1)
        minister = game.status['minister']
        headmaster = int(game.status['headmaster'])
        otherguy = [1,3,4,5,6]
        otherguy.remove(headmaster)
        otherguy.remove(minister)
        otherguy = otherguy[0]
        print(otherguy)
        headers = {
        'Authorization': 'Bearer ' + pytest.users[otherguy]["token"],
        'Content-Type': 'text/plain'
        }
        game.status["phase"] = "x"
        response = client.get("/games/1/proclamations", headers=headers)
        assert response.status_code == 400
        assert response.json() == {'detail': "It is not a phase for geting a proclamation"}
        game.status["phase"] = "minister play"
        response = client.get("/games/1/proclamations", headers=headers)
        print(response.json())
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the minister"}
        headers['Authorization'] = 'Bearer ' + pytest.users[minister]["token"]
        response = client.get("/games/1/proclamations", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"data": game.board.deck.split(',')[:3]}
        game.status["phase"] = "headmaster play"
        response = client.get("/games/1/proclamations", headers=headers)
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the headmaster"}
        headers['Authorization'] = 'Bearer ' + pytest.users[headmaster]["token"]
        response = client.get("/games/1/proclamations", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"data": game.board.deck.split(',')[:2]}


def test_post_game_proclamations():
    with db_session:
        game = Game.get(id=1)
        minister = game.status['minister']
        headmaster = int(game.status['headmaster'])
        otherguy = [1,3,4,5,6]
        otherguy.remove(headmaster)
        otherguy.remove(minister)
        otherguy = otherguy[0]
        print(otherguy)
        headers = {
        'Authorization': 'Bearer ' + pytest.users[otherguy]["token"],
        'Content-Type': 'text/plain'
        }
        response = client.post("/games/100/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "Game not found"}
        game.status["phase"] = "x"
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 400
        assert response.json() == {'detail': "It is not a phase for playing a proclamation"}
        game.status["phase"] = "minister play"
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the minister"}
        headers['Authorization'] = 'Bearer ' + pytest.users[minister]["token"]
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 400
        assert response.json() == {'detail': "The input card was not one of the options"}
        card = game.board.deck.split(',')[:3][0]
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":card})
        assert response.status_code == 200
        assert response.json() == {'message': f'{card} card discarded successfully'}
        headers['Authorization'] = 'Bearer ' + pytest.users[otherguy]["token"]
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":""})
        assert response.status_code == 404
        assert response.json() == {'detail': "This player is not the headmaster"}
        headers['Authorization'] = 'Bearer ' + pytest.users[headmaster]["token"]
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":"defaef"})
        assert response.status_code == 400
        assert response.json() == {'detail': "The input card was not one of the options"}
        card = game.board.deck.split(',')[:2][0]
        response = client.post("/games/1/proclamations", headers=headers,
        json={"card":card})
        assert response.status_code == 200
        assert response.json() == {'message': f'{card} card played successfully'}
