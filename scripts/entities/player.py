import arcade 

from config import *


class Player(arcade.Sprite):
    def __init__(self, path_or_texture=None, scale=1, center_x=0, center_y=0, id=-1):
        super().__init__(path_or_texture, scale, center_x, center_y)
        
        self.id = id
        
        self.texture = arcade.make_soft_square_texture(
            size=50,
            color=(0, 0, 255),
            outer_alpha=255
        )
        
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT

    def set_pos(self, x, y):
        self.center_x = x
        self.center_y = y
    
    def update(self, delta_time=1 / 60):
        """ Обнавление персонажа """
        