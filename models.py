from datetime import datetime
from pony.orm import *


db = Database()


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    password = Required(str)
    username = Optional(str, unique=True)
    players = Set('Player')


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    choosable = Required(bool)
    current_position = Optional(str)
    role = Required(str)
    is_voldemort = Required(bool)
    alive = Required(bool)
    user = Required(User)
    games = Set('Game')
    chats = Set('Message')


class Board(db.Entity):
    id = PrimaryKey(int, auto=True)
    de_proc = Required(int)
    po_proc = Required(int)
    spell_fields = Optional(str)
    caos = Optional(int)
    deck = Required(LongStr)
    game = Required('Game')


class Game(db.Entity):
    id = PrimaryKey(int, auto=True)
    creation_date = Required(datetime)
    player_amount = Required(int)
    status = Required(Json)
    board = Optional(Board)
    players = Set(Player)
    chats = Set('Message')


class Message(db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Required(datetime)
    content = Required(LongStr)
    game = Required(Game)
    player = Required(Player)



db.generate_mapping()