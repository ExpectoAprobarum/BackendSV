import random

# REFACTOR ALL THIS FILE INTO MODEL CLASS FUNCTIONS


def defineBoard(player_amount):
    fiveSixPlayers =['', '', 'divination', 'avadakedavra', 'avadakedavra', 'win']
    sevenEightPlayers = ['', 'crucio', 'imperio', 'avadakedavra', 'avadakedavra', 'win']
    nineTenPlayers = ['crucio', 'crucio', 'imperio', 'avadakedavra','avadakedavra', 'win']
    return {
        5: fiveSixPlayers,
        6: fiveSixPlayers,
        7: sevenEightPlayers,
        8: sevenEightPlayers,
        9: nineTenPlayers,
        10: nineTenPlayers
    }[player_amount]


def newDeck(cards_amount):
    deck = []
    pCounter = 0
    dCounter = 0
    for i in range(cards_amount):
        rand = random.randrange(2)
        newCard = ''
        if rand == 1:
            newCard = 'phoenix'
            if pCounter >= cards_amount//2:
                newCard = 'death'
        else:
            newCard = 'death'
            if dCounter >= cards_amount//2:
                newCard = 'phoenix'
        if newCard == 'phoenix':
            pCounter += 1
        else:
            dCounter += 1
        deck.append(newCard)
    return deck


#we must transfer to this function the playerSet of the game, and the Player db object
def assignRoles(playerSet, Player):
    #quantity of phoenix order players by player quantity
    getPhoenixPlayers = [0,1,1,2,3,3,4,4,4,5,6]
    playersArray = [p.id for p in playerSet]
    random.shuffle(playersArray) 
    ministerIndex = random.randrange(len(playersArray))
    voldemortIndex = random.randrange(len(playersArray))
    phoenixCounter = getPhoenixPlayers[len(playersArray)]
    ministerId = 0
    for idx, _ in enumerate(playersArray):
        if idx == ministerIndex:
            ministerId = playersArray[ministerIndex]
            Player[ministerId].current_position = "minister"
        if idx == voldemortIndex:
            Player[playersArray[voldemortIndex]].role = "death eater"
            Player[playersArray[voldemortIndex]].role = "death eater"
            Player[playersArray[voldemortIndex]].is_voldemort = True
        else:
            if phoenixCounter > 0:
                Player[playersArray[idx]].role = "phoenix order"
                phoenixCounter-= 1
            else:
                Player[playersArray[idx]].role = "death eater"
    return ministerId


def reasignMinister(Player, game):
    playerSet = game.players
    playersArray = [p.id for p in playerSet]
    ministerId = game.status["minister"]
    if game.board.de_proc == 6:
        game.status = {"info": "game ended","winner": "Death Eaters"}
    elif game.board.po_proc == 5:
        game.status = {"info": "game ended","winner": "Phoenix Order"}
    else:
        for i, mId in enumerate(playersArray):
            if mId == ministerId:
                if (i + 1) == len(playersArray):
                    game.status["minister"] = playersArray[0]
                else:
                    game.status["minister"] = playersArray[i + 1]
                game.status["phase"] = "propose"
                game.status["round"] += 1
                firedMinister = Player.get(id=ministerId)
                firedMinister.current_position = ""
                newMinister = Player.get(id=game.status["minister"])
                newMinister.current_position = "minister"
                break

