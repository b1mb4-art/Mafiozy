import arcade
import arcade.gui as gui

from net import Client


class ConnectLobby(arcade.View):
    """Экран ввода IP-адреса для подключения к существующему лобби."""

    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)
        self.manager = gui.UIManager()
        self.anchor = gui.UIAnchorLayout()
        self.box = gui.UIBoxLayout(vertical=True, space_between=12)

        self.setup_ui()
        self.anchor.add(self.box)
        self.manager.add(self.anchor)
    
    def setup_ui(self):
        title = gui.UILabel(text="ПОДКЛЮЧЕНИЕ", font_size=24, bold=True)
        self.box.add(title)

        self.ip_input = gui.UIInputText(
            width=260,
            height=40,
            text="127.0.0.1:12345",
            font_size=16,
        )
        self.status_label = gui.UILabel(
            text="Введите IP-адрес хоста",
            font_size=14,
            text_color=arcade.color.LIGHT_GRAY,
        )
        self.box.add(self.ip_input)
        self.box.add(self.status_label)

        btn_connect = gui.UIFlatButton(text="Войти в лобби", width=260)
        btn_connect.on_click = self.on_connect_click
        self.box.add(btn_connect)

        btn_back = gui.UIFlatButton(text="Назад", width=260)
        btn_back.on_click = self.on_back_click
        self.box.add(btn_back)
    
    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_SLATE_BLUE
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()
    
    def on_draw(self):
        self.clear()
        self.manager.draw()
    
    def on_connect_click(self, event):
        try:
            target_ip = self.ip_input.text.strip().split(":")
            target_ip[1] = int(target_ip[1])
            target_ip = tuple(target_ip)
        
            self.window.client = Client()
            connected = self.window.client.connect(target_ip)
                    
            if connected:
                print("Подключился")
                self.window.client.start()
                
                from .lobby_view import LobbyView
                self.window.show_view(LobbyView(is_host=False))
            else:
                self.status_label.text= "Не удалось подключиться"
        except Exception as e:
            self.status_label.text = f"Ошибка подключения: {e}"
    
    def on_back_click(self, event):
        from .main_menu import MainMenu
        self.window.show_view(MainMenu())