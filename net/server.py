import arcade
import socket
import time
import threading
import json

# from config import *
from net.protocol import PacketKey, RequestType
from net.network_utils import receive_data, send_data

class Server:
    def __init__(self, addr: tuple[str, int] = ('0.0.0.0', 12345), tickrate=30):
        self.host, self.port = addr
        self.kill = False
        
        # Тикрейт
        self.tickrate = tickrate
        self.tickrate_duration = 1 / self.tickrate
        self.current_tick = 0
        
        self.lock = threading.Lock()
        self.client_timeout = 5.0
        self.clients = dict()
        self.next_id = 0

        # AF_INET — IPv4, SOCK_DGRAM — UDP
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(0.5)
    
    def receive_loop(self):
        """ Цикл получения данных от клиентов и обработка их """

        while not self.kill:
            try:
                # Инфа от клиента
                data, addr = receive_data(self.server_socket)

                # Игнорируем пакет, если прислали не JSON-объект (словарь)
                if not isinstance(data, dict):
                    continue

                req = data.get(PacketKey.REQUEST)  # Тип запроса от клиента
                
                # Обработка запроса
                with self.lock:
                    if req == RequestType.CONNECT:
                        self.add_client(addr)
                    elif req == RequestType.DISCONNECT:
                        self.remove_client(addr)
                    elif req == RequestType.MESSAGE:
                        print(f"Клиент (ID: {self.clients[addr].get(PacketKey.ID)}) отправил сообщение: {data.get(PacketKey.MESSAGE)}")
                    
                    if addr not in self.clients:
                        continue
                    else:
                        self.clients[addr][PacketKey.LAST_SEEN] = time.time()
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            except socket.timeout:
                continue 
            except OSError:
                break
    
    def send_loop(self):
        # Засекаем высокоточное время для контроля стабильного тикрейта
        next_tick_time = time.perf_counter()
        
        try:
            while not self.kill:
                now_wall = time.time()
                
                with self.lock:
                    # Отчистка клиентов, которые аварийно отключились
                    for addr in list(self.clients.keys()):
                        last_seen = self.clients[addr][PacketKey.LAST_SEEN]
                        if now_wall - last_seen > self.client_timeout:
                            self.remove_client(addr)
                            
                    self.on_update(self.tickrate_duration) # Обновление состояния сервера
                    
                next_tick_time += self.tickrate_duration
                self.current_tick += 1
                sleep_time = next_tick_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Тик занял больше времени, чем положено — сбрасываем таймер на текущее время
                    next_tick_time = time.perf_counter()

        except KeyboardInterrupt:
            print("\n Остановка сервера...")
            self.stop()
        finally:
            self.kill = True
            self.server_socket.close()
    
    def start(self):
        """Главный цикл сервера """

        self.thread_receive = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread_receive.start()
        self.thread_send = threading.Thread(target=self.send_loop, daemon=True)
        self.thread_send.start()
        print(f"UDP сервер запущен на {self.host}:{self.port} ({self.tickrate} TPS)")

    def add_client(self, addr: tuple[str, int]):
        """ Добавляет нового клиента в список """
        
        if addr in self.clients:
            reply = {
                PacketKey.REQUEST: RequestType.CONNECT,
                PacketKey.ID: self.clients[addr][PacketKey.ID],
                PacketKey.MESSAGE: f"Добро пожаловать на сервер твой ID:{self.clients[addr][PacketKey.ID]}"
            }
            print(f"Клиент уже есть на сервере, его ID:{self.clients[addr][PacketKey.ID]}, IP:{addr}")
        else:
            # Добавление клиента на сервер
            self.clients[addr] = {
                PacketKey.ID: self.next_id,
                PacketKey.LAST_SEEN: time.time()
            }
            reply = {
                PacketKey.REQUEST: RequestType.CONNECT,
                PacketKey.ID: self.next_id,
                PacketKey.MESSAGE: f"Добро пожаловать на сервер твой ID:{self.next_id}"
            }
            print(f"Добавлен клиент с ID:{self.next_id}, IP:{addr}")
            self.next_id += 1

        send_data(
            self.server_socket,
            addr,
            reply
        )
    
    def remove_client(self, addr: tuple[str, int]):
        """ Убирает клиента из списка """
        removed = self.clients.pop(addr)
        if removed:
            print(f"Клиент ID:{removed[PacketKey.ID]} отключился (IP:{addr})")
    
    def stop(self):
        self.kill = True
        self.server_socket.close()
        
    def on_update(self, delta_time):
        ...


if __name__ == "__main__":
    server = Server()
    
    server.start()
    