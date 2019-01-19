import pygame
# import tcod

pygame.init()

# game sizes
GAME_WIDTH = 800
GAME_HEIGHT = 600
CELL_WIDTH = 32
CELL_HEIGHT = 32

# FPS LIMIT
GAME_FPS = 60

# MAP VARS
MAP_WIDTH = 20
MAP_HEIGHT = 20

# color definitions
COLOR_ALPHA = 150
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100 ,100)
COLOR_RED = (255, 0, 0)

# game colors
COLOR_DEFAULT_BG = COLOR_GREY

# FONTS
FONT_DEBUG_MESSAGE = pygame.font.Font("data/joystix monospace.ttf", 20)
FONT_MESSAGE_TEXT = pygame.font.Font("data/joystix monospace.ttf", 12)

# FOV SETTINGS
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# MESSAGE DEFAULTS
NUM_MESSAGES = 4