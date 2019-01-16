import pygame
import tcod

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
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100 ,100)
COLOR_RED = (255, 0, 0)

# game colors
COLOR_DEFAULT_BG = COLOR_GREY

# SPRITES
S_WALL = pygame.image.load("data/wallVersion2.jpg")
S_WALLEXPLORED = pygame.image.load("data/wallVersion2Unseen2.png")

S_FLOOR = pygame.image.load("data/floor.jpg")
S_FLOOREXPLORED = pygame.image.load("data/floorUnseen2.png")

# FOV SETTINGS
FOV_ALGO = tcod.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# FONTS
FONT_DEBUG_MESSAGE = pygame.font.Font("data/joystix monospace.ttf", 20)
FONT_MESSAGE_TEXT = pygame.font.Font("data/joystix monospace.ttf", 12)

# MESSAGE DEFAULTS
NUM_MESSAGES = 4