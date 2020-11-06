import random
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

    @staticmethod
    def define_board(player_amount):
        five_six_players = ['', '', 'divination', 'avadakedavra', 'avadakedavra', 'win']
        seven_eight_players = ['', 'crucio', 'imperio', 'avadakedavra', 'avadakedavra', 'win']
        nine_ten_players = ['crucio', 'crucio', 'imperio', 'avadakedavra', 'avadakedavra', 'win']

        return {
            5: five_six_players,
            6: five_six_players,
            7: seven_eight_players,
            8: seven_eight_players,
            9: nine_ten_players,
            10: nine_ten_players
        }[player_amount]

    @staticmethod
    def new_deck(cards_amount):
        deck = []
        p_counter = 0
        d_counter = 0

        for i in range(cards_amount):
            rand = random.randrange(2)

            if rand == 1:
                new_card = 'phoenix'
                if p_counter >= cards_amount // 2:
                    new_card = 'death'
            else:
                new_card = 'death'
                if d_counter >= cards_amount // 2:
                    new_card = 'phoenix'

            if new_card == 'phoenix':
                p_counter += 1
            else:
                d_counter += 1

            deck.append(new_card)

        return deck
