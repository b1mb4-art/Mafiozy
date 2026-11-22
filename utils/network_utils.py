import socket
import json

def receive_data(sock: socket.socket) -> tuple[dict, tuple[str, int]]:
    """ Функция получения пакетов """
    raw_data, addr = sock.recvfrom(4096)
    data = json.loads(raw_data.decode('utf-8'))
    
    return (data, addr)

def send_data(sock: socket.socket, addr: tuple[str, int], data: dict) -> None:
    """ Функция отправки пакетов """
    try:
        sock.sendto(
            json.dumps(data).encode("utf-8"),
            addr
        )
    except OSError:
        ...