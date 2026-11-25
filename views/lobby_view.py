import arcade
import arcade.gui as gui

from .game_view import GameView
from utils.protocol import PacketKey, MatchState, RequestType
from utils import disconnect_lobby


class LobbyView(arcade.View):
    def __init__(self, window = None, background_color = None, is_host: bool=False):
        super().__init__(window, background_color)
        
        self.is_host = is_host
        self.is_ready = False
        self.client = self.window.client
        
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
        
        if self.is_host:
            self.status_label = gui.UILabel(
                text="",
                font_size=14,
                text_color=arcade.color.YELLOW,
                align="center"
            )
            self.box.add(self.status_label)

            # Кнопка старта доступна только хосту
            btn_start = gui.UIFlatButton(text="Начать матч", width=240)
            btn_start.on_click = self.on_start_match
            self.box.add(btn_start)
        
        self.btn_ready = gui.UIFlatButton(text="Готов", width=240)
        self.btn_ready.on_click = self.on_toggle_ready
        self.box.add(self.btn_ready)
        
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
    
    def on_update(self, delta_time):
        # Cписок игроков в лобби и состояние матча
        players, match_state = self.client.get_players_info()
        
        # Инфа о игроках
        if players:
            lines = [f"Игроков в комнате: {len(players)}\n"]
            for pid in sorted(players.keys()):
                info = players[pid]
                you_mark = " (Вы)" if pid == self.client.player_id else ""
                host_mark = " [Хост]" if info.get(PacketKey.HOST) else ""
                ready_mark = "Готов" if info.get(PacketKey.READY) else "Не готов"

                lines.append(f"Игрок #{pid}{host_mark}{you_mark} — {ready_mark}")

            new_text = "\n".join(lines)
        else:
            new_text = "Ожидание игроков..."
        
        # Выводим в лобби
        if self.players_list_label.text != new_text:
            self.players_list_label.text = new_text
            
        # Запуск игры
        if match_state == MatchState.PLAYING:
            self.window.show_view(GameView())

    def on_start_match(self, event):
        if self.is_host:
            self.client.start_game()

    def on_toggle_ready(self, event):
        self.is_ready = not self.is_ready
        self.client.ready(self.is_ready)
        self.btn_ready.text = "Отменить готовность" if self.is_ready else "Готов"
        
    def on_leave_lobby(self, event):
        disconnect_lobby(self.window)
        
        from .main_menu import MainMenu
        self.window.show_view(MainMenu())