from pony.orm import PrimaryKey, Required, Optional, Set
from .base import db


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    password = Required(str)
    username = Optional(str, unique=True)
    useralias = Required(str)
    email = Required(str, unique=True)
    verified = Required(bool, default=False)
    players = Set('Player')