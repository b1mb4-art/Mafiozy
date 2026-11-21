class RequestType:
    """ Константы для типа запроса """
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    ID = 'id'
    MOVE = 'move'
    INFO = 'info'


class PacketKey:
    """ Константы для ключей """
    REQUEST = 'request'
    ID = 'id'
    ACTION = 'action'
    PLAYERS = 'players'
    TICK = 'tick'
    LASTSEEN = 'last_seen'
    MESSAGE = 'message'