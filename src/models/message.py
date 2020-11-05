import datetime
from pony.orm import PrimaryKey, Required, Set, Json, LongStr
from .base import db


class Message(db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Required(datetime.datetime)
    content = Required(LongStr)
    game = Required('Game')
    player = Required('Player')
