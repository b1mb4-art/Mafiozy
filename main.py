import arcade

from views import MainMenu
from utils import disconnect_lobby
from config import *


class Game(arcade.Window):
    def __init__(self, width = SCREEN_WIDTH, height = SCREEN_HEIGHT, title = "Mafiozy", fullscreen = False):
        super().__init__(width, height, title, fullscreen, center_window=True)
        arcade.enable_timings()
        
        # Для сервера
        self.host_manager = None
        # Для клиента
        self.client = None
        self.game_view = None
        
        self.setup()
        
    def setup(self):
        main_menu = MainMenu()
        self.show_view(main_menu)
    
    def on_close(self):
        # Гарантированно убиваем сервер, если игрок закрыл окно крестиком
        disconnect_lobby(self)
        super().on_close()


if __name__ == "__main__":
    game = Game()
    game.run()