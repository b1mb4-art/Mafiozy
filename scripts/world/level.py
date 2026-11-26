import arcade
import csv

from .tile import Tile
from .weapon_stand import WeaponStand
from utils import SpriteType
from config import *

class Level:
    def __init__(self, level_name="test", is_server: bool=False):
        self.level_name = level_name
        self.is_server = is_server
        self.collide_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        self.drawing_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        self.other_sprites = {
            SpriteType.WEAPON_STAND: arcade.SpriteList(use_spatial_hash=True, lazy=True),
            SpriteType.SPAWN: arcade.SpriteList(use_spatial_hash=True, lazy=True)
        }
    
    def setup_level(self):
        """ Прогружает карту """
        self.collide_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        self.drawing_sprites = arcade.SpriteList(use_spatial_hash=True, lazy=True)
        self.other_sprites = {
            SpriteType.WEAPON_STAND: arcade.SpriteList(use_spatial_hash=True, lazy=True),
            SpriteType.SPAWN: arcade.SpriteList(use_spatial_hash=True, lazy=True)
        }
        
        self.text_map = self.load_level_from_file()
        self.load_level_sprites()

    def load_level_from_file(self) -> list[list]:
        """ Выгружает text map из файла """
        data = list()
        with open(file=f"scripts/world/text_maps/{self.level_name}.csv", mode='r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            for i in list(reader):
                data.append(i)
        data.reverse()
        return data
    
    def load_level_sprites(self):
        """ По text_map загружает спрайты """
        for i in range(len(self.text_map)):
            for j in range(len(self.text_map[i])):
                if self.text_map[i][j] == " ":
                    continue
                center_x, center_y = j * TILE_SIZE + TILE_SIZE / 2, i * TILE_SIZE + TILE_SIZE / 2
                if self.text_map[i][j] == "#":
                    self.add_tile(center_x, center_y)
                elif self.text_map[i][j] == "s":
                    self.add_spawn(center_x, center_y)
                elif self.text_map[i][j] == 'w':
                    self.add_weapon_stand(center_x, center_y)

    def add_tile(self, center_x: float, center_y: float):
        """ Добавляет новую стенку в collide_sprites """
        if self.is_server:
            tile = arcade.Sprite(
                path_or_texture=arcade.make_soft_square_texture(
                    size=TILE_SIZE,
                    color=(0, 0, 0, 0),
                    outer_alpha=0
                ),
                center_x=center_x,
                center_y=center_y
            )
        else:
            tile = Tile(center_x=center_x, center_y=center_y)

        self.collide_sprites.append(tile)
        self.drawing_sprites.append(tile)
    
    def add_spawn(self, x: float, y: float):
        """ Добавляет новую точку спавна в spawn_sprites """
        sprite = arcade.Sprite(center_x=x + TILE_SIZE / 2, center_y=y + TILE_SIZE / 2)
        sprite.width = PLAYER_WIDTH
        sprite.height = PLAYER_HEIGHT
        self.other_sprites[SpriteType.SPAWN].append(sprite)

    def add_weapon_stand(self, c_x: float, c_y: float):
        if self.is_server:
            sprite = arcade.Sprite(center_x=c_x, center_y=c_y)
        else:
            sprite = WeaponStand(center_x=c_x, center_y=c_y)
            self.drawing_sprites.append(sprite)

        self.other_sprites[SpriteType.WEAPON_STAND].append(sprite)

    def set_level_name(self, level_name: str):
        self.level_name = level_name

    def get_collide_sprites(self) -> arcade.SpriteList:
        if self.is_server:
            return self.collide_sprites
        return arcade.SpriteList(use_spatial_hash=True, lazy=True)

    def get_spawn_sprites(self) -> arcade.SpriteList:
        if self.is_server:
            return self.other_sprites[SpriteType.SPAWN]
        return arcade.SpriteList(use_spatial_hash=True, lazy=True)

    def get_weapon_stand_sprites(self) -> arcade.SpriteList:
        if self.is_server:
            return self.other_sprites[SpriteType.WEAPON_STAND]
        return arcade.SpriteList(use_spatial_hash=True, lazy=True)

    def get_drawing_sprites(self) -> arcade.SpriteList:
        if not self.is_server:
            return self.drawing_sprites
        return arcade.SpriteList(use_spatial_hash=True, lazy=True)
                
if __name__ == "__main__":
    level = Level()
    