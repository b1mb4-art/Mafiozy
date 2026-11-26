import arcade


class Weapon(arcade.Sprite):
    def __init__(self, weapon_id: int, path_or_texture=None, scale=1, center_x=0, center_y=0, angle=0):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        
        self.weapon_id = weapon_id
        self.is_auto = False  # режим стрельбы
        self.player_sprite = None