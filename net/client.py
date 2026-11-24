import arcade
import socket
import time
import threading
import json

# from config import *
from net.protocol import PacketKey, RequestType, MatchState
from utils.network_utils import receive_data, send_data
from config import *
from scripts import Level

class Client:
    def __init__(self):
        self.host = False
        self.server_addr = None
        self.thread = None
        self.kill = False
        self.last_tick = -1
        self.lock = threading.Lock()

        self.match_state = MatchState.LOBBY
        self.Level = Level()
        self.collide_sprites = self.Level.get_collide_sprites()

        self.player_id = None
        self.action = PLAYER_DIRECTION.copy()
        self.all_players = dict()
        
        # AF_INET — IPv4, SOCK_DGRAM — UDP
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.settimeout(0.5)
    
    def receive_loop(self):
        """ Цикл получения пакетов с сервера """
        while not self.kill:
            try:
                # Инфа от сервера
                data, addr = receive_data(self.server_socket)

                # Игнорируем пакет, если прислали не JSON-объект (словарь)
                if not isinstance(data, dict) or addr != self.server_addr:
                    continue

                req = data.get(PacketKey.REQUEST)  # Тип запроса от клиента
                
                if req == RequestType.MESSAGE:
                    print(data.get(PacketKey.MESSAGE))

                if req == RequestType.INFO:
                    tick = data.get(PacketKey.TICK, 0)
                    if tick > self.last_tick:
                        self.last_tick = tick
                        raw_players = data.get(PacketKey.PLAYERS, {})
                        with self.lock:
                            self.match_state = data.get(PacketKey.STATE, self.match_state)
                            # Переводим строковые ключи ID обратно в целые числа (int)
                            self.all_players = {
                                int(pid): info for pid, info in raw_players.items()
                            }
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            except socket.timeout:
                continue 
            except OSError:
                break
    
    def send_loop(self):
        """ Цикл отправки пакетов на сервер """
        send_duration = 1.0 / 30.0
        next_tick = time.perf_counter()
        current_tick = 0
        
        while not self.kill:
            # Отправляем данные на сервер
            
            packet = {
                PacketKey.REQUEST: RequestType.MOVE,
                PacketKey.ACTION: self.action 
            }
            
            send_data(self.server_socket, self.server_addr, packet)
            
            current_tick += 1
            next_tick += send_duration
            sleep_time = next_tick - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_tick = time.perf_counter()
    
    def start(self):
        """ Главный цикл клиента: """
        self.kill = False
        
        self.thread_recieve = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread_recieve.start()
        print("Запущены циклы получения пакетов с сервера")
        
        self.thread_send = threading.Thread(target=self.send_loop, daemon=True)
        self.thread_send.start()
    
    def close(self):
        self.kill = True
        self.disconnect()
        self.server_socket.close()
    
    def connect(self, addr) -> bool:
        
        packet = {
            PacketKey.REQUEST: RequestType.CONNECT,
            PacketKey.HOST: self.host
        }
        
        for attempt in range(1, 11):
            try:
                print(f"Попытка подключения {attempt}/10 к {addr}")

                send_data(self.server_socket, addr, packet)
                
                data, _ = receive_data(self.server_socket)
                
                if data.get(PacketKey.REQUEST) == RequestType.CONNECT:
                    try:
                        print(data.get(PacketKey.MESSAGE))
                    except:
                        ...
                    self.player_id = data.get(PacketKey.ID)
                    self.server_addr = addr
                    return True
                    
                
            except socket.timeout:
                # Если пакет потерялся или сервер еще не ответил — пробуем снова
                continue
            except ConnectionResetError:
                # В Windows возникает, если сервер вообще не запущен (порт закрыт)
                print("Сервер недоступен (порт закрыт).")
                time.sleep(0.5)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        
        return False

    def disconnect(self):
        if self.server_addr:
            try:
                send_data(self.server_socket, self.server_addr, {
                    PacketKey.REQUEST: RequestType.DISCONNECT
                })
            except OSError:
                pass
            print("Отключился от сервера")
    
    def start_game(self):
        """ Отправляет запрос начать игру """
        if self.host:
            packet = {
                PacketKey.REQUEST: RequestType.START_GAME
            }
            send_data(self.server_socket, self.server_addr, packet)
        else:
            print("Вы не хост лобби")
    
    def ready(self, is_ready: bool):
        """ Отправляет информацию готовности к матчу """
        packet = {
            PacketKey.REQUEST: RequestType.READY,
            PacketKey.READY: is_ready
        }
        send_data(self.server_socket, self.server_addr, packet)

    def get_players_info(self) -> tuple[dict[int, dict], str]:
        """Возвращает (словарь_игроков, текущее_состояние_матча)."""
        with self.lock:
            return self.all_players.copy(), self.match_state
    
    def set_player_action(self, action: dict):
        """ Действия игрока """
        self.action = action.copy()

if __name__ == '__main__':
    client = Client()
    
    time.sleep(1)
    
    if client.connect(("127.0.0.1", 12345)):
        print("Подключился")
        client.start()
    else:
        print("Не удалось подключиться")