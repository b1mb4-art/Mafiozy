import arcade
import socket
import time
import threading
import json

from utils import receive_data, send_data, PacketKey, RequestType, MatchState
from config import *
from scripts import Level

class Server:
    def __init__(self, addr: tuple[str, int] = ('0.0.0.0', 12345), tickrate=30):
        self.host, self.port = addr
        self.kill = False
        
        # матч
        self.state = MatchState.LOBBY
        self.current_level_name = ""
        self.level = Level(is_server=True)
        self.collide_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        self.spawn_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        
        # Тикрейт
        self.tickrate = tickrate
        self.tickrate_duration = 1 / self.tickrate
        self.current_tick = 0
        
        # клиент
        self.host_id = -1
        self.client_timeout = 5.0
        self.clients = dict()
        self.next_id = 0

        # AF_INET — IPv4, SOCK_DGRAM — UDP
        self.lock = threading.Lock()
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
                    
                    if req == RequestType.MOVE:
                        action = data.get(PacketKey.ACTION)
                        if isinstance(action, dict):
                            self.clients[addr][PacketKey.ACTION] = action
                        
                
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
                            
                    self.on_update(self.tickrate_duration)
                            
                    # Сбор инфы
                    players_data = {}
                    
                    for client in self.clients.values():
                        pid = str(client[PacketKey.ID])
                        players_data[pid] = {
                            PacketKey.READY: client.get(PacketKey.READY),
                            PacketKey.HOST: client.get(PacketKey.HOST),
                            PacketKey.X: client.get(PacketKey.X),
                            PacketKey.Y: client.get(PacketKey.Y),
                            PacketKey.FACING: client.get(PacketKey.FACING)
                        }
                    
                    packet = {
                        PacketKey.REQUEST: RequestType.INFO,
                        PacketKey.TICK: self.current_tick,
                        PacketKey.STATE: self.state,
                        PacketKey.LEVEL_NAME: self.current_level_name,
                        PacketKey.PLAYERS: players_data,
                    }
                    
                    for addr in self.clients:
                        send_data(self.server_socket, addr, packet)
                
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
        if len(self.clients) >= 4 or self.state != MatchState.LOBBY:
            return
        
        if addr in self.clients:
            reply = {
                PacketKey.REQUEST: RequestType.CONNECT,
                PacketKey.ID: self.clients[addr][PacketKey.ID],
                PacketKey.MESSAGE: f"Добро пожаловать на сервер твой ID:{self.clients[addr][PacketKey.ID]}"
            }
            print(f"Клиент уже есть на сервере, его ID:{self.clients[addr][PacketKey.ID]}, IP:{addr}")
        else:
            # Добавление клиента на сервер
            x = 128 * self.next_id
            y = 128
            sprite = self.create_server_player_hitbox(x, y)
            engine = self.create_server_player_engine(sprite)
            self.clients[addr] = {
                PacketKey.ID: self.next_id,  # ID игрока
                PacketKey.HOST: is_host,  # Является ли хоостом лобби
                PacketKey.READY: False,
                PacketKey.X: x,
                PacketKey.Y: y,
                PacketKey.ACTION: PLAYER_DIRECTION.copy(),
                PacketKey.SPRITE: sprite,
                PacketKey.ENGINE: engine,
                PacketKey.FACING: 1, 
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
                
                self.load_level()

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
    
    def create_server_player_hitbox(self, x: float, y: float) -> arcade.Sprite:
        sprite = arcade.Sprite(center_x=x, center_y=y)
        sprite.texture = arcade.make_soft_square_texture(
            size=50,
            color=(0, 0, 0),
            outer_alpha=255
        )
        sprite.width = PLAYER_WIDTH
        sprite.height = PLAYER_HEIGHT
        
        return sprite

    def create_server_player_engine(self, player_sprite: arcade.Sprite) -> arcade.PhysicsEnginePlatformer:
        engine = arcade.PhysicsEnginePlatformer(
            player_sprite=player_sprite,
            walls=self.collide_sprites,
            gravity_constant=PLAYER_ACCELERATION_Y
        )
        return engine
        
    def on_update(self, delta_time):
        if self.state != MatchState.PLAYING:
            return
        
        for player in self.clients.values():
            player_sprite: arcade.Sprite = player.get(PacketKey.SPRITE)
            engine: arcade.PhysicsEnginePlatformer = player.get(PacketKey.ENGINE)
            
            self.move_player(player)

            old_x = player_sprite.center_x
            engine.update()
            if old_x == player_sprite.center_x:
                player_sprite.change_x = 0
            
            self.on_jump(player)
            
            # Новый координаты
            player[PacketKey.X] = player_sprite.center_x
            player[PacketKey.Y] = player_sprite.center_y
        
    def move_player(self, player: dict):
        action = player.get(PacketKey.ACTION)
        player_sprite: arcade.Sprite = player.get(PacketKey.SPRITE)
        acceleration = 0
        
        if action['left']:
            acceleration = -PLAYER_ACCELERATION_X
            player[PacketKey.FACING] = -1
        elif action['right']:
            acceleration = PLAYER_ACCELERATION_X
            player[PacketKey.FACING] = 1
        
        # Скорость с ускорением
        player_sprite.change_x += acceleration
        if acceleration:
            if player_sprite.change_x >= PLAYER_MAX_SPEED_X:
                player_sprite.change_x = PLAYER_MAX_SPEED_X
            if player_sprite.change_x <= -PLAYER_MAX_SPEED_X:
                player_sprite.change_x = -PLAYER_MAX_SPEED_X
        else:
            if player_sprite.change_x > 0:
                if (player_sprite.change_x - PLAYER_ACCELERATION_X) <= 0:
                    player_sprite.change_x = 0
                else:
                    player_sprite.change_x -= PLAYER_ACCELERATION_X
            elif player_sprite.change_x < 0:
                if (player_sprite.change_x + PLAYER_ACCELERATION_X) >= 0:
                    player_sprite.change_x = 0
                else:
                    player_sprite.change_x += PLAYER_ACCELERATION_X

    def on_jump(self, player: dict):
        action = player.get(PacketKey.ACTION)
        player_sprite: arcade.Sprite = player.get(PacketKey.SPRITE)
        engine: arcade.PhysicsEnginePlatformer = player.get(PacketKey.ENGINE)

        if action.get('up') and engine.can_jump():
            engine.jump(PLAYER_JUMP_SPEED)

        if not action.get('up') and player_sprite.change_y > 0:
            player_sprite.change_y *= 0.6
    
    def load_level(self):
        self.current_level_name = "test"
        self.level.set_level_name(self.current_level_name)
        self.level.setup_level()
        self.collide_sprites = self.level.get_collide_sprites()
        self.spawn_sprites = self.level.get_spawn_sprites()
        self.other_sprites = self.level.ger
        self.players_on_spawns()
    
    def players_on_spawns(self):
        c = 0
        for client in self.clients.values():
            sprite: arcade.Sprite = client.get(PacketKey.SPRITE)
            engine: arcade.PhysicsEnginePlatformer = client.get(PacketKey.ENGINE)
            spawn: arcade.Sprite = self.spawn_sprites[c]

            sprite.center_x = spawn.center_x
            sprite.center_y = spawn.center_y

            engine.walls = self.collide_sprites
            c += 1     


if __name__ == "__main__":
    server = Server()
    
    server.start()
    