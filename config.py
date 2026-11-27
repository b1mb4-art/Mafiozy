from utils import ActionKey

""" Основные константы """

# Экран
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Уровень
TILE_SIZE = 32

# Игрок
PLAYER_WIDTH = TILE_SIZE
PLAYER_HEIGHT = PLAYER_WIDTH * 2
PLAYER_MAX_SPEED_X = 15
PLAYER_MAX_SPEED_Y = 10
PLAYER_ACCELERATION_X = 2
PLAYER_ACCELERATION_Y = 1.5
PLAYER_JUMP_SPEED = 25
PLAYER_DIRECTION = {
    ActionKey.LEFT: False,
    ActionKey.RIGHT: False,
    ActionKey.UP: False,
    ActionKey.DOWN: False,
    ActionKey.PICKUP_SEQ: 0,
    ActionKey.SHOOT: False,
    ActionKey.SHOT: 0
}

# Оружие
PISTOL_SIZE = (16, 8)
PISTOL_AMMO = 8

# Пуля
BULLET_SPEED = 35
BULLET_SIZE = (10, 4)
BULLET_LIFETIME = 2