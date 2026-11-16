import arcade

from views import MainMenu


class Game(arcade.Window):
    def __init__(self, width = 1280, height = 720, title = "Arcade Window", fullscreen = False):
        super().__init__(width, height, title, fullscreen, center_window=True)
        arcade.enable_timings()
        
        self.setup()
        
    def setup(self):
        main_menu = MainMenu()
        self.show_view(main_menu)


if __name__ == "__main__":
    game = Game()
    game.run()