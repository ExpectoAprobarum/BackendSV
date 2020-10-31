from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_get_games():
    response = client.get("/games/", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    assert type(response.json()["data"]) is list

def test_get_game():
    response = client.get("/games/1", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    g = response.json()
    assert type(g["id"]) is int
    assert type(g["name"]) is str
    assert type(g['player_amount']) is int
    assert type(g["started"]) is bool
    assert type(g["status"]) is dict

def test_create_games():
    response = client.post("/games/", headers={"X-Token": "coneofsilence"}, 
                            json={"name": "Juego 1", "player_amount": 5})
    assert response.status_code == 200
    g = response.json()
    assert type(g["id"]) is int
    assert type(g["message"]) is str


def test_start_game():
    response = client.post("/games/7/start", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200