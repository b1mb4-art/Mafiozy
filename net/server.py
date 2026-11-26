import arcade
import socket
import time
import threading
import json

from utils import receive_data, send_data, PacketKey, RequestType, MatchState, WeaponType, ActionKey
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
        self.weapon_stand_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        
        # Тикрейт
        self.tickrate = tickrate
        self.tickrate_duration = 1 / self.tickrate
        self.current_tick = 0
        
        # клиент
        self.host_id = -1
        self.client_timeout = 5.0
        self.clients = dict()
        self.next_id = 0
        
        self.next_weapon_id = 0
        self.weapons = {}
        self.bullets = {}

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

                    packet = self.prepare_packet()
                    
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
                PacketKey.WEAPON_ID: None,
                PacketKey.LAST_PICKUP_SEQ: 0,
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
            color=(0, 0, 0, 0),
            outer_alpha=255
        )
        sprite.width = PLAYER_WIDTH
        sprite.height = PLAYER_HEIGHT
        sprite.sync_hit_box_to_texture
        
        return sprite

    def create_server_player_engine(self, player_sprite: arcade.Sprite) -> arcade.PhysicsEnginePlatformer:
        engine = arcade.PhysicsEnginePlatformer(
            player_sprite=player_sprite,
            walls=self.collide_sprites,
            gravity_constant=PLAYER_ACCELERATION_Y
        )
        return engine
        
    def create_new_weapon(self, stand_sprite: arcade.Sprite=None, center_x=0, center_y=0, weapon_type: WeaponType=None):
        """ Создает оружие на стенде или по координатам """
        if weapon_type is None:
            return
        if stand_sprite:
            x, y = stand_sprite.center_x, stand_sprite.center_y
        else:
            x, y = center_x, center_y

        is_auto, width, height = self.setup_weapon(weapon_type)

        self.next_weapon_id += 1
        sprite = arcade.Sprite(center_x=x, center_y=y)
        sprite.texture = arcade.make_soft_square_texture(
            size=50,
            color=(0, 0, 255),
            outer_alpha=255
        )
        sprite.width = width
        sprite.height = height
        sprite.sync_hit_box_to_texture()
        
        engine = arcade.PhysicsEnginePlatformer(
            sprite,
            walls=self.collide_sprites,
            gravity_constant=PLAYER_ACCELERATION_Y
        )

        weapon = {
            PacketKey.ID: self.next_weapon_id,
            PacketKey.X: x,
            PacketKey.Y: y,
            PacketKey.IS_AUTO: is_auto,
            PacketKey.WEAPON_TYPE: weapon_type,
            PacketKey.OWNER_ID: None,
            PacketKey.SPRITE: sprite,
            PacketKey.ENGINE: engine,
            PacketKey.FACING: 1
        }
        
        self.weapons[self.next_weapon_id] = weapon
    
    def setup_weapon(self, weapon_type=None) -> tuple[bool, int, int]:
        if weapon_type is None:
            return

        if weapon_type == WeaponType.PISTOL:
            is_auto = False
            width, height = PISTOL_SIZE
        
        return (is_auto, width, height)
        
    def on_update(self, delta_time):
        if self.state != MatchState.PLAYING:
            return
        
        for player in self.clients.values():
            self.update_player(player)
            self.handle_pickup_weapon(player)
            self.handle_shoot(player)
        
        for weapon in self.weapons.values():
            self.update_weapon(weapon)

    def update_weapon(self, weapon: dict):
        """ Обновление положение оружия """
        weapon_sprite: arcade.Sprite = weapon.get(PacketKey.SPRITE)
        player_id = weapon.get(PacketKey.OWNER_ID)
        
        if player_id is not None:
            c = 0
            for player in self.clients.values():
                if player_id == player.get(PacketKey.ID):
                    weapon[PacketKey.FACING] = player.get(PacketKey.FACING)
                    weapon_sprite.center_x = player.get(PacketKey.SPRITE).center_x + 10 * weapon.get(PacketKey.FACING)
                    weapon_sprite.center_y = player.get(PacketKey.SPRITE).center_y
                    c += 1
                    break
            if c == 0:
                weapon[PacketKey.OWNER_ID] = None
        else:
            # Оружие лежит или летит по земле — работает физика и трение
                weapon_sprite.change_x *= 0.85
                if abs(weapon_sprite.change_x) < 0.2:
                    weapon_sprite.change_x = 0
                weapon.get(PacketKey.ENGINE).update()
        
        weapon[PacketKey.X] = weapon_sprite.center_x
        weapon[PacketKey.Y] = weapon_sprite.center_y
    
    def update_player(self, player: dict):
        """ Обновление положениея игрока и его действий """
        player_sprite: arcade.Sprite = player.get(PacketKey.SPRITE)
        engine: arcade.PhysicsEnginePlatformer = player.get(PacketKey.ENGINE)
        
        self.move_player(player)
        self.on_jump(player)

        old_x = player_sprite.center_x
        engine.update()
        if old_x == player_sprite.center_x:
            player_sprite.change_x = 0
        
        # Новый координаты
        player[PacketKey.X] = player_sprite.center_x
        player[PacketKey.Y] = player_sprite.center_y
        
    def move_player(self, player: dict):
        action = player.get(PacketKey.ACTION)
        player_sprite: arcade.Sprite = player.get(PacketKey.SPRITE)
        acceleration = 0
        
        if action[ActionKey.LEFT]:
            acceleration = -PLAYER_ACCELERATION_X
            player[PacketKey.FACING] = -1
        elif action[ActionKey.RIGHT]:
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

        if action.get(ActionKey.UP) and engine.can_jump():
            engine.jump(PLAYER_JUMP_SPEED)

        if not action.get(ActionKey.UP) and player_sprite.change_y > 0:
            player_sprite.change_y *= 0.6
    
    def load_level(self):
        self.current_level_name = "test"
        self.level.set_level_name(self.current_level_name)
        self.level.setup_level()
        self.collide_sprites = self.level.get_collide_sprites()
        self.spawn_sprites = self.level.get_spawn_sprites()
        self.weapon_stand_sprites = self.level.get_weapon_stand_sprites()
        self.players_on_spawns()
    
    def players_on_spawns(self):
        c = 0
        for client in self.clients.values():
            sprite: arcade.Sprite = client.get(PacketKey.SPRITE)
            engine: arcade.PhysicsEnginePlatformer = client.get(PacketKey.ENGINE)
            spawn: arcade.Sprite = self.spawn_sprites[c]
            
            self.create_new_weapon(center_x=spawn.center_x, center_y=spawn.center_y, weapon_type=WeaponType.PISTOL)

            sprite.center_x = spawn.center_x
            sprite.center_y = spawn.center_y

            engine.walls = self.collide_sprites
            c += 1     

    def handle_pickup_weapon(self, player: dict):
        """ Подбор оружия игроком """
        action: dict = player.get(PacketKey.ACTION, {})
        seq = action.get(ActionKey.PICKUP_SEQ, 0)
        
        if seq <= player.get(PacketKey.LAST_PICKUP_SEQ, 0):
            return

        player[PacketKey.LAST_PICKUP_SEQ] = seq
        
        current_weapon_id = player.get(PacketKey.WEAPON_ID)
        
        if current_weapon_id is not None and current_weapon_id in self.weapons:
            weapon = self.weapons[current_weapon_id]
            weapon[PacketKey.OWNER_ID] = None
            weapon[PacketKey.SPRITE].change_x = (10 + 5 * abs(player[PacketKey.SPRITE].change_x)) * player[PacketKey.FACING]
            weapon[PacketKey.SPRITE].change_y = 6
            player[PacketKey.WEAPON_ID] = None
            return

        for weapon_id, weapon in self.weapons.items():
            if weapon[PacketKey.OWNER_ID] is None:
                if arcade.check_for_collision(weapon.get(PacketKey.SPRITE), player.get(PacketKey.SPRITE)):
                    player[PacketKey.WEAPON_ID] = weapon_id
                    weapon[PacketKey.OWNER_ID] = player.get(PacketKey.ID)
                    break

    def handle_shoot(self, player: dict):
        """ Стрельба """
        ...
    
    def prepare_packet(self) -> dict:
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
        
        weapons_data = {}
        for weapon in self.weapons.values():
            wid = str(weapon[PacketKey.ID])
            weapons_data[wid] = {
                PacketKey.X: weapon.get(PacketKey.X),
                PacketKey.Y: weapon.get(PacketKey.Y),
                PacketKey.WEAPON_TYPE: weapon.get(PacketKey.WEAPON_TYPE)
            }
        
        bullet_data = dict()
        for bullet in self.bullets.values():
            bid = str(bullet[PacketKey.ID])
            bullet_data[bid] = {
                PacketKey.X: bullet.get(PacketKey.X),
                PacketKey.Y: bullet.get(PacketKey.Y),
            }

        packet = {
            PacketKey.REQUEST: RequestType.INFO,
            PacketKey.TICK: self.current_tick,
            PacketKey.STATE: self.state,
            PacketKey.LEVEL_NAME: self.current_level_name,
            PacketKey.PLAYERS: players_data,
            PacketKey.WEAPONS: weapons_data,
            PacketKey.BULLETS: bullet_data,
        }
        return packet

if __name__ == "__main__":
    server = Server()
    
    server.start()
    