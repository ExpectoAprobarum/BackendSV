from .base import db
from pony.orm import PrimaryKey, Required, Set, Optional

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    choosable = Required(bool)
    current_position = Optional(str)
    role = Required(str)
    is_voldemort = Required(bool)
    alive = Required(bool)
    user = Required('User')
    games = Set('Game')
    chats = Set('Message')