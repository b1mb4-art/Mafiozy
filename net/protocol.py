from enum import StrEnum

class MatchState(StrEnum):
    """ Константы состояния матча """
    LOBBY = 'lobby'
    PLAYING = 'playing'
    GAME_OVER = 'game_over'

class RequestType(StrEnum):
    """ Константы для типа запроса """
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    ID = 'id'
    MOVE = 'move'
    INFO = 'info'
    MESSAGE = 'message'
    START_GAME = 'start_game'
    READY = 'ready'


class PacketKey(StrEnum):
    """ Константы для ключей """
    REQUEST = 'request'
    ID = 'id'
    ACTION = 'action'
    PLAYERS = 'players'
    TICK = 'tick'
    LAST_SEEN = 'last_seen'
    MESSAGE = 'message'
    HOST = "host"
    READY = 'ready'
    STATE = 'state'
    X = 'x'
    Y = 'y'