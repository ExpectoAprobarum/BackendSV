from fastapi.testclient import TestClient
from .main import app
import pytest

client = TestClient(app)

pytest.users = {1: {"username": "andres", "email": "a@a.com", "password": "12345"}, 2: {"username": "andres2", "email": "a2@a.com", "password": "12345"}}


def test_create_user():
    response = client.post(
        "/users/", headers={},
        json=pytest.users[1]
    )
    assert response.status_code == 200
    rjson = response.json()
    assert rjson == {"id": 1, "message": "User created successfully"}
    response = client.post(
        "/users/", headers={},
        json=pytest.users[1]
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}
    response = client.post(
        "/users/", headers={},
        json={"username": "andres345", "email": "a@a.com", "password": "12345"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_auth():
    response = client.post("/auth/token", headers={},
        json={"username": "andres", "password": "12345"}
    )
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['token_type'] == 'bearer'
    pytest.users[1]["token"] = rjson['access_token']



def test_get_game():
    headers = {
    'Authorization': 'Bearer ' + pytest.users[1]["token"],
    'Content-Type': 'text/plain'
    }
    response = client.get("/games/", headers=headers)
    assert response.status_code == 200
    
"""
def test_create_games():
    response = client.post(
        "/games/", headers={"X-Token": "coneofsilence"},
        json={"name": "Juego 1", "player_amount": 5}
    )
    assert response.status_code == 200
    g = response.json()
    assert type(g["id"]) is int
    assert type(g["message"]) is str


def test_start_game():
    response = client.post(
        "/games/7/start",
        headers={"X-Token": "coneofsilence"}
    )
    assert response.status_code == 200
"""