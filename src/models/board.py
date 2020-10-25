from .base import db
from pony.orm import PrimaryKey, Required, Optional, LongStr

class Board(db.Entity):
    id = PrimaryKey(int, auto=True)
    de_proc = Required(int)
    po_proc = Required(int)
    spell_fields = Optional(str)
    caos = Optional(int)
    deck = Required(LongStr)
    game = Required('Game')