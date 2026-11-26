import arcade

from net import Client
from utils import PacketKey, MatchState, ActionKey, WeaponType
from scripts import Player, Level, Pistol

from config import *

class GameView(arcade.View):
    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)
        self.background_color = (55, 55, 55)

        self.client: Client = self.window.client
        
        self.current_level_name = ""
        self.level = Level()
        
        self.all_players = arcade.SpriteList()
        self.load_players()
        self.action = PLAYER_DIRECTION.copy()

        self.weapon_id = 0
        self.weapon_sprites = arcade.SpriteList()
        self.all_weapons = {}
    
    def on_draw(self):
        """ Цикл отрисовки """
        self.clear()
        
        self.level.get_drawing_sprites().draw()        
        self.all_players.draw()
        self.weapon_sprites.draw()
    
    def on_update(self, delta_time):
        """ Основной цикл игры """
        
        if self.current_level_name != self.client.current_level_name:
            self.current_level_name = self.client.current_level_name
            self.load_level()
        
        self.all_players.update()
        
        self.move_players()
        self.update_weapons()
        
        self.client.set_player_action(self.action)
        
    def on_key_press(self, key, modifiers):
        """ Обработка нажатых клавишь """
        if key == arcade.key.ESCAPE:
            self.action = PLAYER_DIRECTION.copy()
            self.client.set_player_action(self.action)
            from .pause_view import PauseView

            pause_view = PauseView(game_view=self)
            self.window.show_view(pause_view)
            return
        
        if key == arcade.key.A:
            self.action[ActionKey.LEFT] = True
        if key == arcade.key.D:
            self.action[ActionKey.RIGHT] = True
        if key == arcade.key.W:
            self.action[ActionKey.UP] = True
        if key == arcade.key.S:
            self.action[ActionKey.DOWN] = True
        
        if key == arcade.key.V:
            self.action[ActionKey.SHOT] += 1
            self.action[ActionKey.SHOOT] = True
        if key == arcade.key.C:
            self.action[ActionKey.PICKUP_SEQ] += 1
    
    def on_key_release(self, key, modifiers):
        """ Обработка отжатых клавиш """
        if key == arcade.key.A:
            self.action[ActionKey.LEFT] = False
        if key == arcade.key.D:
            self.action[ActionKey.RIGHT] = False
        if key == arcade.key.W:
            self.action[ActionKey.UP] = False
        if key == arcade.key.S:
            self.action[ActionKey.DOWN] = False
        
        if key == arcade.key.V:
            self.action[ActionKey.SHOOT] = False
        
    def load_players(self):
        for pid, client_player in self.client.all_players.items():
            player = Player(id=pid)
            player.set_pos(client_player[PacketKey.X], client_player[PacketKey.Y])
            self.all_players.append(player)
    
    def move_players(self):
        players_data, _ = self.client.get_players_info()

        for player in list(self.all_players):
            if player.id not in players_data:
                player.remove_from_sprite_lists()
                continue

            player.set_pos(
                x=players_data[player.id][PacketKey.X],
                y=players_data[player.id][PacketKey.Y]
            )
        
    def update_weapons(self):
        weapon_data = self.client.get_weapons_info()
        
        for pid, weapon in weapon_data.items():
            if pid not in self.all_weapons:
                self.create_weapon(weapon.get(PacketKey.X), weapon.get(PacketKey.Y), pid, weapon.get(PacketKey.WEAPON_TYPE))
        
        for pid, weapon in self.all_weapons.items():
            if pid not in weapon_data:
                self.remove_weapon(self.all_weapons[pid])
            else:
                weapon.center_x, weapon.center_y = weapon_data[pid].get(PacketKey.X), weapon_data[pid].get(PacketKey.Y)

    def create_weapon(self, x: float, y: float, id: int, weapon_type: WeaponType=None):
        if not weapon_type:
            return
        
        if weapon_type == WeaponType.PISTOL:
            sprite = Pistol(id, center_x=x, center_y=y)
        
        self.all_weapons[id] = sprite
        self.weapon_sprites.append(sprite)
    
    def remove_weapon(self, sprite: Pistol):
        self.all_weapons.pop(sprite.weapon_id)
        sprite.remove_from_sprite_lists()

    def load_level(self):
        self.level.set_level_name(self.current_level_name)
        self.level.setup_level()