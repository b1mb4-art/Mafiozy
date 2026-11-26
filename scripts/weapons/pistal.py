import arcade

from .weapon import Weapon
from config import *

class Pistol(Weapon):
    def __init__(self, weapon_id, path_or_texture=None, scale=1, center_x=0, center_y=0, angle=0):
        super().__init__(weapon_id, path_or_texture, scale, center_x, center_y, angle)
        
        self.texture = arcade.make_soft_square_texture(
            10,
            (100, 100, 100),
            outer_alpha=255
        )
        self.width, self.height = PISTOL_SIZE