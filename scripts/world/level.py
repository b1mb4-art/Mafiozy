import arcade
import csv

from .tile import Tile
from config import *

class Level:
    def __init__(self, level_name="test"):
        self.level_name = level_name
        self.setup_level()
    
    def setup_level(self):
        """ Прогружает карту """
        self.collide_sprites = arcade.SpriteList(use_spatial_hash=True)
        self.spawn_sprites = arcade.SpriteList(use_spatial_hash=True)
        
        self.text_map = self.load_level_from_file()
        self.load_level_sprites()

    def load_level_from_file(self) -> list[list]:
        """ Выгружает text map из файла """
        data = list()
        with open(file=f"level/text_maps/test.csv", mode='r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            for i in list(reader):
                data.append(i)
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

    def add_tile(self, center_x: float, center_y: float):
        """ Добавляет новую стенку в collide_sprites """
        tile = Tile(center_x=center_x, center_y=center_y)
        self.collide_sprites.append(tile)
    
    def add_spawn(self, x: float, y: float):
        """ Добавляет новую точку спавна в spawn_sprites """
        sprite = arcade.Sprite(center_x=x + TILE_SIZE / 2, center_y=y + TILE_SIZE / 2)
        sprite.width = PLAYER_WIDTH
        sprite.height = PLAYER_HEIGHT
        self.spawn_sprites.append(sprite)

    def set_level_name(self, level_name: str):
        self.level_name = level_name

    def get_collide_sprites(self) -> arcade.SpriteList:
        return self.collide_sprites

    def get_srawn_sprites(self) -> arcade.SpriteList:
        return self.collide_sprites
                
if __name__ == "__main__":
    level = Level()
    