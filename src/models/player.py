import random
from .base import db
from pony.orm import PrimaryKey, Required, Set, Optional
from fastapi import HTTPException


def fire_headmaster(game):
    player_query = Player.select(lambda pr: pr.current_position == 'headmaster')
    if 'headmaster' in game.status.keys():
        del game.status["headmaster"]
    for p in player_query:
        p.current_position = ""


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

    @staticmethod
    def assign_roles(player_set):
        # quantity of phoenix order players by player quantity
        get_phoenix_players = [0, 1, 1, 2, 3, 3, 4, 4, 4, 5, 6]

        players_array = [p.id for p in player_set]
        random.shuffle(players_array)
        minister_index = random.randrange(len(players_array))
        voldemort_index = random.randrange(len(players_array))
        phoenix_counter = get_phoenix_players[len(players_array)]

        minister_id = 0
        for idx, _ in enumerate(players_array):
            if idx == minister_index:
                minister_id = players_array[minister_index]
                Player[minister_id].current_position = "minister"

            if idx == voldemort_index:
                Player[players_array[voldemort_index]].role = "death eater"
                Player[players_array[voldemort_index]].role = "death eater"
                Player[players_array[voldemort_index]].is_voldemort = True
            else:
                if phoenix_counter > 0:
                    Player[players_array[idx]].role = "phoenix order"
                    phoenix_counter -= 1
                else:
                    Player[players_array[idx]].role = "death eater"

        return minister_id

    @staticmethod
    def reassign_minister(game):
        player_set = game.players
        players_array = [p.id for p in player_set if p.alive]
        players_array.sort()
        minister_id = game.status["minister"]

        spell_fields = game.board.spell_fields.split(",")
        if game.status["phase"] == "spell play":
            spell_fields[game.board.de_proc - 1] = ""
            game.board.spell_fields = ','.join(spell_fields)

        if game.board.de_proc == 6:
            game.status = {"info": "game ended", "winner": "Death Eaters"}
        elif game.board.po_proc == 5:
            game.status = {"info": "game ended", "winner": "Phoenix Order"}
        else:
            for i, mId in enumerate(players_array):
                if mId == minister_id:
                    if (i + 1) == len(players_array):
                        game.status["minister"] = players_array[0]
                    else:
                        game.status["minister"] = players_array[i + 1]
                    game.status["phase"] = "propose"
                    game.status["round"] += 1

                    fired_minister = Player.get(id=minister_id)
                    fired_minister.current_position = ""

                    new_minister = Player.get(id=game.status["minister"])
                    new_minister.current_position = "minister"

                    fire_headmaster(game)
                    break
        if 'votes' in game.status.keys():
            del game.status["votes"]

    @staticmethod
    def user_player(user, game_id):
        player_query = Player.select(lambda p: user["id"] == p.user.id and p.game.id == game_id)
        current_player_array = [p.to_dict() for p in player_query]
        if not current_player_array:
            raise HTTPException(status_code=400, detail="The player does not belong to this game")
        return current_player_array[0]

    @staticmethod
    def reset_choosable():
        player_query = Player.select(lambda p: not p.choosable)
        for p in player_query:
            p.choosable = True
