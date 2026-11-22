class RequestType:
    """ Константы для типа запроса """
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    ID = 'id'
    MOVE = 'move'
    INFO = 'info'
    MESSAGE = 'message'


class PacketKey:
    """ Константы для ключей """
    REQUEST = 'request'
    ID = 'id'
    ACTION = 'action'
    PLAYERS = 'players'
    TICK = 'tick'
    LAST_SEEN = 'last_seen'
    MESSAGE = 'message'