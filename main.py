import arcade

from views import MainMenu


class Game(arcade.Window):
    def __init__(self, width = 1280, height = 720, title = "Arcade Window", fullscreen = False):
        super().__init__(width, height, title, fullscreen, center_window=True)
        
    def setup(self):
        main_menu = MainMenu()


if __name__ == "__main__":
    game = Game()
    game.run()