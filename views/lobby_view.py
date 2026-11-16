import arcade
import arcade.gui as gui


class LobbyView(arcade.View):
    def __init__(self, window = None, background_color = None, is_host: bool=False):
        super().__init__(window, background_color)
        
        self.is_host = is_host
        
        self.manager = gui.UIManager()
        self.anchor = gui.UIAnchorLayout()
        self.box = gui.UIBoxLayout(vertical=True, space_between=12)

        # блок со списком подключенных игроков
        self.players_list_label = gui.UILabel(
            text="Ожидание списка игроков...",
            font_size=16,
            multiline=True,
            width=350,
            align="center",
        )

        self.setup_ui()
        self.anchor.add(self.box)
        self.manager.add(self.anchor)
    
    def setup_ui(self):
        if self.is_host:
            role_text = "ЛОББИ (Вы — Хост)"
        else: 
            role_text = "ЛОББИ (Ожидание хоста)"

        title = gui.UILabel(text=role_text, font_size=24, bold=True)
        self.box.add(title)
        self.box.add(self.players_list_label)
        
        # Кнопка старта доступна только хосту
        if self.is_host:
            btn_start = gui.UIFlatButton(text="Начать матч", width=240)
            btn_start.on_click = self.on_start_match
            self.box.add(btn_start)
        
        btn_leave = gui.UIFlatButton(text="Выйти из лобби", width=240)
        btn_leave.on_click = self.on_leave_lobby
        self.box.add(btn_leave)
        
    def on_show_view(self):
        self.window.background_color = arcade.color.AMAZON
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()
    
    def on_draw(self):
        self.clear()
        self.manager.draw()
    
    def on_start_match(self, event):
        ...

    def on_leave_lobby(self, event):
        # Закрываем клиент и, если мы хост, останавливаем фоновый сервер
        if getattr(self.window, "client", None):
            self.window.client.close()
            self.window.client = None
        if self.is_host and getattr(self.window, "host_manager", None):
            self.window.host_manager.stop()
