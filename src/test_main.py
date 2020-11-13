from fastapi.testclient import TestClient
from .main import app
import pytest
from src.models import Game, Board, User, Player
from pony.orm import db_session

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
    response = client.post("/games/1/start", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'board_id': 1,
        'message': 'Game started successfully'
        }
    response = client.post("/games/100/start", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': "The game does not exist"}
    response = client.post("/games/1/start", headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "The game was already started"}
