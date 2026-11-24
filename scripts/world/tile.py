import arcade

from config import *


class Tile(arcade.Sprite):
    def __init__(self, path_or_texture = "assets/textures/world/tile.png", scale = 1, center_x = 0, center_y = 0, angle = 0, **kwargs):
        super().__init__(path_or_texture, scale, center_x, center_y, angle, **kwargs)
        
        