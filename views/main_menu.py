import arcade
import arcade.gui as gui

from net import Client, Server


class MainMenu(arcade.View):
    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)
        
        # Менеджер интерфейса
        self.manager = gui.UIManager()
        self.manager.enable()
        
        self.anchor_layout = gui.UIAnchorLayout()
        self.box_layout = gui.UIBoxLayout(vertical=True, space_between=12)
        self.button_width = 220
        
        self.setup_widgets()
        
        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)
    
    def on_draw(self):
        self.clear()
        self.manager.draw()
    
    def on_show_view(self) -> None:
        self.window.background_color = arcade.color.AMAZON
        self.manager.enable()

    def on_hide_view(self) -> None:
        self.manager.disable()
    
    def setup_widgets(self):
        # Текст меню
        menu_label = gui.UILabel(
            text="MENU",
            font_size=28,
            bold=True,
            text_color=arcade.color.WHITE,
        )
        self.box_layout.add(menu_label)
        
        # кнопка создания лобби
        create_lobby_button = gui.UIFlatButton(text="Создать лобби", width=self.button_width)
        create_lobby_button.on_click = self.create_lobby_menu
        self.box_layout.add(create_lobby_button)
        
        # кнопка коннекта к лобби
        connect_lobby_button = gui.UIFlatButton(text="Присоединится к лобби", width=self.button_width)
        connect_lobby_button.on_click = self.connect_lobby_menu
        self.box_layout.add(connect_lobby_button)
        
        # Кастомизация персонажа
        character_button = settings_button = gui.UIFlatButton(text="Персонаж", width=self.button_width)
        character_button.on_click = self.character_menu
        self.box_layout.add(character_button)
        
        # Настройки
        settings_button = gui.UIFlatButton(text="Настройки", width=self.button_width)
        settings_button.on_click = self.settings_menu
        self.box_layout.add(settings_button)
    
        # Кнопка Выйти
        exit_button = gui.UIFlatButton(text="Выйти", width=self.button_width)
        exit_button.on_click = self.exit_game
        self.box_layout.add(exit_button)
    
    def exit_game(self, event):
        arcade.exit()
    
    def settings_menu(self, event):
        print('Настройки')
    
    def character_menu(self, event):
        print('Персонаж')
    
    def create_lobby_menu(self, event):
        self.window.host_manager = Server()
        self.window.host_manager.start()
        self.window.client = Client()
        
        connected = self.window.client.connect(("127.0.0.1", 12345))
        
        if connected:
            print("Подключился")
            self.window.client.start()
            
            from .lobby_view import LobbyView
            self.window.show_view(LobbyView(is_host=True))
        else:
            print("Не удалось подключиться")
        
    
    def connect_lobby_menu(self, event):
        from .connect_view import ConnectLobby
        self.window.show_view(ConnectLobby())