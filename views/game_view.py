import arcade

from net import Client
from net.protocol import PacketKey, MatchState 
from scripts import Player, Level

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
        
        self.direction = PLAYER_DIRECTION.copy()
    
    def on_draw(self):
        """ Цикл отрисовки """
        self.clear()
        
        self.level.get_collide_sprites().draw()        
        self.all_players.draw()
    
    def on_update(self, delta_time):
        """ Основной цикл игры """
        
        if self.current_level_name != self.client.current_level_name:
            self.current_level_name = self.client.current_level_name
            self.load_level()
        
        self.all_players.update()
        
        self.move_players()
        
        self.client.set_player_action(self.direction)
        
    def on_key_press(self, key, modifiers):
        """ Обработка нажатых клавишь """
        if key == arcade.key.ESCAPE:
            self.direction = PLAYER_DIRECTION.copy()
            self.client.set_player_action(self.direction)
            from .pause_view import PauseView

            pause_view = PauseView(game_view=self)
            self.window.show_view(pause_view)
            return
        
        if key == arcade.key.A:
            self.direction['left'] = True
        if key == arcade.key.D:
            self.direction['right'] = True
        if key == arcade.key.W:
            self.direction['up'] = True
        if key == arcade.key.S:
            self.direction['down'] = True
    
    def on_key_release(self, key, modifiers):
        """ Обработка отжатых клавиш """
        if key == arcade.key.A:
            self.direction['left'] = False
        if key == arcade.key.D:
            self.direction['right'] = False
        if key == arcade.key.W:
            self.direction['up'] = False
        if key == arcade.key.S:
            self.direction['down'] = False
    
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

    def load_level(self):
        self.level.set_level_name(self.current_level_name)
        self.level.setup_level()