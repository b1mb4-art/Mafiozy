import arcade
import arcade.gui as gui

from utils import disconnect_lobby

class PauseView(arcade.View):
    def __init__(self, window = None, background_color = None, game_view = None):
        super().__init__(window, background_color)
        
        self.game_view = game_view
        
        self.manager = gui.UIManager()
        self.anchor = gui.UIAnchorLayout()
        self.box_layout = gui.UIBoxLayout(vertical=True, space_between=12)
        self.button_width = 220

        self.setup_widgets()
        self.anchor.add(self.box_layout)
        self.manager.add(self.anchor)
    
    def setup_widgets(self):
        
        # Текст паузы
        label = gui.UILabel(
            text="PAUSE",
            font_size=24,
            bold=True,
            text_color=arcade.color.WHITE,
        )
        
        label.with_padding(top=10, bottom=10, left=25, right=25)
        label.with_background(color=arcade.color.AMAZON)
        self.box_layout.add(label)
        
        # Кнопка продолжить игру
        continue_button = gui.UIFlatButton(text="Вернуться в игру", width=self.button_width)
        continue_button.on_click = self.on_click_resume
        self.box_layout.add(continue_button)
        
        # Кнопка настроек
        ...
        
        # Кнопка выхода их матча
        disconnect_button = gui.UIFlatButton(text="Покинуть лобби", width=self.button_width)
        disconnect_button.on_click = self.on_click_exit
        self.box_layout.add(disconnect_button)
        
    
    def on_show_view(self):
        """Вызывается автоматически при открытии этого View."""
        self.manager.enable()

    def on_hide_view(self):
        """Вызывается автоматически при уходе с этого View."""
        self.manager.disable()
    
    def on_update(self, delta_time: float):
        # В мультиплеере продолжаем обновлять позиции других игроков на фоне
        self.game_view.on_update(delta_time)
    
    def on_draw(self):
        self.game_view.on_draw()

        # Накладываем полупрозрачный черный прямоугольник
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.window.width, self.window.height,
            color=(0, 0, 0, 150)
        )

        self.manager.draw()
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.resume_game()
    
    def on_click_resume(self, event):
        """ Возвращает обратно в игру по кнопке """
        self.resume_game()

    def on_click_exit(self, event):
        """ Возвращает в основное меню """
        disconnect_lobby(self.window)

        from .main_menu import MainMenu
        self.window.show_view(MainMenu())
        
    def resume_game(self):
        """ Возвращает обратно в игру """
        self.window.show_view(self.game_view)
