from .base import db
from pony.orm import PrimaryKey, Required, Set, Optional

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    choosable = Optional(bool)
    current_position = Optional(str)
    role = Optional(str)
    is_voldemort = Optional(bool)
    alive = Required(bool)
    user = Required('User')
    game = Optional('Game')
    chats = Set('Message')