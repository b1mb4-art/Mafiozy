import arcade


class GameView(arcade.View):
    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)