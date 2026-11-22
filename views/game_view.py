import arcade


class GameView(arcade.View):
    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)
        
        self.background_color = (55, 55, 55)
        
        self.client = self.window.client
    
    def on_draw(self):
        """ Цикл отрисовки """
        self.clear()
    
    def on_update(self, delta_time):
        """ Основной цикл игры """
    
    def on_key_press(self, key, modifiers):
        """ Обработка нажатых клавишь """
        if key == arcade.key.ESCAPE:
            from .pause_view import PauseView

            pause_view = PauseView(game_view=self)
            self.window.show_view(pause_view)
            return
    
    def on_key_release(self, key, modifiers):
        """ Обработка отжатых клавиш """
        