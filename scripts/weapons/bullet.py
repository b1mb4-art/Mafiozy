import arcade

from config import *


class Bullet(arcade.Sprite):
    def __init__(self, bullet_id: int, center_x: float = 0, center_y: float = 0):
        super().__init__(center_x=center_x, center_y=center_y)
        self.bullet_id = bullet_id
        self.texture = arcade.make_soft_square_texture(
            size=10,
            color=arcade.color.YELLOW,
            outer_alpha=255
        )
        self.width, self.height = BULLET_SIZE