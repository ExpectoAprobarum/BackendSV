from .base import db
from .user import User
from .player import Player
from .board import Board
from .message import Message
from .game import Game

db.generate_mapping(create_tables=True)
