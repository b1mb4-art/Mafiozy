import socket
import json

def receive_data(socket: socket.socket) -> tuple[dict, tuple[str, int]]:
    """ Функция получения пакетов """
    raw_data, addr = socket.recvfrom(4096)
    data = json.loads(raw_data.decode('utf-8'))
    
    return (data, addr)

def send_data(socket: socket.socket, addr: tuple[str, int], data: dict) -> None:
    """ Функция отправки пакетов """
    try:
        socket.sendto(
            json.dumps(data).encode("utf-8"),
            addr
        )
    except OSError:
        ...