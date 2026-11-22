import arcade

from views import MainMenu


class Game(arcade.Window):
    def __init__(self, width = 1280, height = 720, title = "Arcade Window", fullscreen = False):
        super().__init__(width, height, title, fullscreen, center_window=True)
        arcade.enable_timings()
        
        # Для сервера
        self.client = None
        self.host_manager = None
        
        self.setup()
        
    def setup(self):
        main_menu = MainMenu()
        self.show_view(main_menu)
    
    def on_close(self):
        # Гарантированно убиваем сервер, если игрок закрыл окно крестиком
        if self.client:
            self.client.close()
        if self.host_manager:
            self.host_manager.stop()
        super().on_close()


if __name__ == "__main__":
    game = Game()
    game.run()