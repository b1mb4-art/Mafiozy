import arcade
import socket
import time
import threading
import json

# from config import *
from net.protocol import PacketKey, RequestType, MatchState
from utils import receive_data, send_data

class Server:
    def __init__(self, addr: tuple[str, int] = ('0.0.0.0', 12345), tickrate=30):
        self.host, self.port = addr
        self.kill = False
        
        self.host_id = -1
        self.state = MatchState.LOBBY
        
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
                        self.add_client(addr, data.get(PacketKey.HOST))
                    
                    # Обновление последнего контакта
                    if addr not in self.clients:
                        continue
                    else:
                        self.clients[addr][PacketKey.LAST_SEEN] = time.time()

                    if req == RequestType.DISCONNECT:
                        self.remove_client(addr)

                    if req == RequestType.MESSAGE:
                        ...
                    
                    if req == RequestType.READY:
                        self.player_ready(addr, data.get(PacketKey.READY))
                    
                    if req == RequestType.START_GAME:
                        self.start_match(addr)
                
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
                            
                    # Сбор инфы
                    players_data = {}
                    
                    for client in self.clients.values():
                        pid = str(client[PacketKey.ID])
                        players_data[pid] = {
                            PacketKey.READY: client.get(PacketKey.READY),
                            PacketKey.HOST: client.get(PacketKey.HOST)
                        }
                    
                    packet = {
                        PacketKey.REQUEST: RequestType.INFO,
                        PacketKey.TICK: self.current_tick,
                        PacketKey.STATE: self.state,
                        PacketKey.PLAYERS: players_data
                    }
                    
                    for addr in self.clients:
                        send_data(self.server_socket, addr, packet)
                        
                        
                    # Обновление игрового цикла
                    self.on_update(self.tickrate_duration) # Обновление состояния сервера
                
                # Работа с тикрейтом
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
            self.close()
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

    def add_client(self, addr: tuple[str, int], is_host: bool=False):
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
                PacketKey.ID: self.next_id,  # ID игрока
                PacketKey.HOST: is_host,  # Является ли хоостом лобби
                PacketKey.READY: False,
                PacketKey.LAST_SEEN: time.time()  # Последний раз видели
            }
            # Ответ клиенту
            reply = {
                PacketKey.REQUEST: RequestType.CONNECT,
                PacketKey.ID: self.next_id,
                PacketKey.MESSAGE: f"Добро пожаловать на сервер твой ID:{self.next_id}"
            }
            
            # (На всякий) Записываем ID хоста отдельно
            if is_host:
                self.host_id = self.next_id

            print(f"Добавлен клиент с ID:{self.next_id}, IP:{addr}")
            self.next_id += 1

        send_data(
            self.server_socket,
            addr,
            reply
        )
    
    def remove_client(self, addr: tuple[str, int]):
        """ Убирает клиента из списка """
        removed = self.clients.pop(addr, None)
        if removed:
            print(f"Клиент ID:{removed[PacketKey.ID]} отключился (IP:{addr})")
    
    def close(self):
        self.kill = True
        self.server_socket.close()
        print("Сервер закрыт")
      
    def player_ready(self, addr: tuple[str, int],  ready: bool):
        if self.state == MatchState.LOBBY:
            self.clients[addr][PacketKey.READY] = bool(ready)
            print(f"Клиент ID:{self.clients[addr].get(PacketKey.ID)} изменил готовность на {ready}")
    
    def start_match(self, addr: tuple[str, int]):
        if self.clients[addr].get(PacketKey.HOST):
            num_clients = len(list(self.clients.keys()))
            num_ready = 0
            
            # Количество готовых игроков
            for client in self.clients.values():
                if client.get(PacketKey.READY):
                    num_ready += 1
            
            if num_ready == num_clients:
                self.state = MatchState.PLAYING
                print("Матч запущен")
            else:
                send_data(
                    self.server_socket,
                    addr,
                    {
                        PacketKey.REQUEST: RequestType.MESSAGE,
                        PacketKey.MESSAGE: f"Не все игроки готовы ({num_ready}/{num_clients})"
                    }
                )
                print(f"Не все игроки готовы ({num_ready}/{num_clients})")
        
    def on_update(self, delta_time):
        ...


if __name__ == "__main__":
    server = Server()
    
    server.start()
    