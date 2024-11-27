import json
from IGameInstance import *


def createPlayerTurnPacket(current_player):
    return {"type": PacketType.PLAYER_TURN.value,
            "player": current_player}
