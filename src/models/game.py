from .base import db
import datetime
from pony.orm import PrimaryKey, Required, Optional, Set, Json


class Game(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    creation_date = Required(datetime.datetime)
    created_by = Required(int)
    player_amount = Required(int)
    started = Required(bool)
    status = Required(Json)
    board = Optional('Board')
    players = Set('Player')
    chats = Set('Message')
