import arcade


class WeaponStand(arcade.Sprite):
    def __init__(self, scale = 1, center_x = 0, center_y = 0, angle = 0):
        super().__init__("assets/textures/world/weaponStand.png", scale, center_x, center_y, angle)
        
        self.weapon_id = None
        self.weapon_sprite = None
        