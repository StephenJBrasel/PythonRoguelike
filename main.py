# third party modules
import tcod
import pygame

# game files
import constants

# bell, big, cybermedium, drpepper, fender, gothic, kban, nancyj, standard

# Definitions
# 888888ba           .8888b oo          oo   dP   oo                            
# 88    `8b          88   "                  88                                 
# 88     88 .d8888b. 88aaa  dP 88d888b. dP d8888P dP .d8888b. 88d888b. .d8888b. 
# 88     88 88ooood8 88     88 88'  `88 88   88   88 88'  `88 88'  `88 Y8ooooo. 
# 88    .8P 88.  ... 88     88 88    88 88   88   88 88.  .88 88    88       88 
# 8888888P  `88888P' dP     dP dP    dP dP   dP   dP `88888P' dP    dP `88888P' 

# Structs
# .d88888b    dP                                dP            
# 88.    "'   88                                88            
# `Y88888b. d8888P 88d888b. dP    dP .d8888b. d8888P .d8888b. 
#       `8b   88   88'  `88 88    88 88'  `""   88   Y8ooooo. 
# d8'   .8P   88   88       88.  .88 88.  ...   88         88 
#  Y88888P    dP   dP       `88888P' `88888P'   dP   `88888P' 


class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False

class struc_Assets:
    def __init__(self):
        # SPRITESHEETS
        self.charSpriteSheet = obj_Spritesheet("data/reptiles.png")
        self.enemySpriteSheet = obj_Spritesheet("data/aquaticCreatures.png")

        # ANIMATIONS
        self.A_PLAYER = self.charSpriteSheet.get_animation('m', 5, 16, 16, 2, (32, 32))
        self.A_ENEMY = self.enemySpriteSheet.get_animation('k', 1, 16, 16, 2, (32, 32))
        
        # SPRITES
        self.S_WALL = pygame.image.load("data/wallVersion2.jpg")
        self.S_WALLEXPLORED = pygame.image.load("data/wallVersion2Unseen2.png")

        self.S_FLOOR = pygame.image.load("data/floor.jpg")
        self.S_FLOOREXPLORED = pygame.image.load("data/floorUnseen2.png")
        
        # FONTS
        self.FONT_DEBUG_MESSAGE = pygame.font.Font("data/joystix monospace.ttf", 20)
        self.FONT_MESSAGE_TEXT = pygame.font.Font("data/joystix monospace.ttf", 12)


# Objects
#  .88888.  dP       oo                     dP            
# d8'   `8b 88                              88            
# 88     88 88d888b. dP .d8888b. .d8888b. d8888P .d8888b. 
# 88     88 88'  `88 88 88ooood8 88'  `""   88   Y8ooooo. 
# Y8.   .8P 88.  .88 88 88.  ... 88.  ...   88         88 
#  `8888P'  88Y8888' 88 `88888P' `88888P'   dP   `88888P' 
#                    88                                   
#                    dP                                   


class obj_Actor:
    def __init__(self, x, y, name_object, animation, animation_speed = 0.5, creature = None, ai = None):
        self.x = x #Map Address
        self.y = y #Map Address
        self.animation = animation
        self.animation_speed = animation_speed / 1.0 # time for entire animation in seconds

        # animation flicker speed
        self.flicker_speed = self.animation_speed / len(self.animation)
        self.flicker_timer = 0.0
        self.sprite_image = 0

        self.creature = creature
        if creature:
            creature.owner = self
        
        self.ai = ai
        if ai:
            ai.owner = self
    
    def draw(self):
        is_visible = tcod.map_is_in_fov(FOV_MAP, self.x, self.y)
        if is_visible:
            if len(self.animation) == 1:
               SURFACE_MAIN.blit(self.animation[0], (self.x*constants.CELL_WIDTH, self.y* constants.CELL_HEIGHT))

            elif len(self.animation) > 1:

                if CLOCK.get_fps() > 0.0:
                    self.flicker_timer += 1/CLOCK.get_fps()

                if self.flicker_timer >= self.flicker_speed:
                    self.flicker_timer = 0.0

                    if self.sprite_image >= len(self.animation) - 1:
                        self.sprite_image = 0
                    else:
                        self.sprite_image += 1
                
                SURFACE_MAIN.blit(self.animation[self.sprite_image], (self.x*constants.CELL_WIDTH, self.y* constants.CELL_HEIGHT))


class obj_Game:
    def __init__(self):
        self.current_map = map_create()
        self.current_objects = []

        self.message_history = []

class obj_Spritesheet:
    """ Class used to grab images out of a sprite sheet. 
    "data/aquaticCreatures.png"
    """
    def __init__(self, file_name):
        # load in sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
        self.tiledict = {'a':1, 'b':2, 'c':3, 'd':4,
                         'e':5, 'f':6, 'g':7, 'h':8,
                         'i':9, 'j':10, 'k':11, 'l':12,
                         'm':13, 'n':14, 'o':15, 'p':16}
    
    def get_image(self, column, row, width = constants.CELL_WIDTH, height = constants.CELL_HEIGHT,
        T_scale = None):
        """ T_scale is a Tuple """
        image_list = []

        image = pygame.Surface([width, height]).convert()

        image.blit(self.sprite_sheet, (0, 0), (self.tiledict[column]*width, row*height, width, height))
        image.set_colorkey(constants.COLOR_BLACK)

        if T_scale:
            (new_w, new_h) = T_scale
            image = pygame.transform.scale(image, (new_w, new_h))
        
        image_list.append(image)

        return image_list    

    def get_animation(self, column, row, width = constants.CELL_WIDTH, height = constants.CELL_HEIGHT,
        num_sprites = 1, T_scale = None):
        """ T_scale is a Tuple """
        image_list = []

        for i in range(num_sprites):
            # Create blank image

            image = pygame.Surface([width, height]).convert()
            # Copy image from sheet onto blank
            image.blit(self.sprite_sheet, (0, 0), ((self.tiledict[column] + i)*width, row*height, width, height))
            
            # Set transparency key to blank
            image.set_colorkey(constants.COLOR_BLACK)

            if T_scale:
                (new_w, new_h) = T_scale
                image = pygame.transform.scale(image, (new_w, new_h))
            
            image_list.append(image)

        return image_list

# Components
#  a88888b.                                                                    dP            
# d8'   `88                                                                    88            
# 88        .d8888b. 88d8b.d8b. 88d888b. .d8888b. 88d888b. .d8888b. 88d888b. d8888P .d8888b. 
# 88        88'  `88 88'`88'`88 88'  `88 88'  `88 88'  `88 88ooood8 88'  `88   88   Y8ooooo. 
# Y8.   .88 88.  .88 88  88  88 88.  .88 88.  .88 88    88 88.  ... 88    88   88         88 
#  Y88888P' `88888P' dP  dP  dP 88Y888P' `88888P' dP    dP `88888P' dP    dP   dP   `88888P' 
#                               88                                                           
#                               dP                                                           


class com_Creature:
    """
    Creatures have health, can damage other objects by "attacking" them, can die
    """
    def __init__(self, name_instance, hp = 10, death_function = None):
        self.name_instance = name_instance
        self.maxhp = hp
        self.hp = hp
        self.death_function = death_function

    def move(self, dx, dy):

        tile_is_wall = (GAME.current_map[self.owner.x + dx][self.owner.y + dy].block_path == True)
        
        target = map_check_for_creatures(self.owner.x + dx, self.owner.y + dy, self.owner)
        
        if target:
            self.attack(target, 3)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy
    
    def attack(self, target, damage):
        game_message(self.name_instance + " attacks " + target.creature.name_instance + " for " + str(damage) + " damage!", constants.COLOR_WHITE)
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        game_message(self.name_instance + "'s health is " + str(self.hp) + "/" + str(self.maxhp), constants.COLOR_RED)
        
        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)


# TODO class com_Item:

# TODO class com_Container:

# AI
#  .d888888  dP 
# d8'    88  88 
# 88aaaaa88a 88 
# 88     88  88 
# 88     88  88 
# 88     88  dP 


class ai_Test:
    """  
    Once per turn, execute.
    """
    def take_turn(self):
        self.owner.creature.move(tcod.random_get_int(0, -1, 1), tcod.random_get_int(0, -1, 1))

def death_monster(monster):
    """ On death, most monsters stop moving. """
    game_message(monster.creature.name_instance + " is dead!", constants.COLOR_GREY)
    monster.creature = None
    monster.ai = None

# Map
# 8888ba.88ba                    
# 88  `8b  `8b                   
# 88   88   88 .d8888b. 88d888b. 
# 88   88   88 88'  `88 88'  `88 
# 88   88   88 88.  .88 88.  .88 
# dP   dP   dP `88888P8 88Y888P' 
#                       88       
#                       dP       


def map_create():
    new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]
    new_map[10][10].block_path = True
    new_map[10][15].block_path = True

    for x in range(constants.MAP_WIDTH):
        new_map[x][0].block_path = True
        new_map[x][constants.MAP_HEIGHT - 1].block_path = True
    for y in range(constants.MAP_HEIGHT):
        new_map[0][y].block_path = True
        new_map[constants.MAP_WIDTH - 1][y].block_path = True

    map_make_fov(new_map)

    return new_map

def map_check_for_creatures(x, y, exclude_object = None):
    target = None
    if exclude_object:
        # check object list to find creature at location that isn't excluded.
        for obj in GAME.current_objects:
            if (obj is not exclude_object and 
                obj.x == x and 
                obj.y == y and 
                obj.creature):

                target = obj
            
        if target:
            return target
    else:
        # check object list to find any creature at location.
        for obj in GAME.current_objects:
            if (obj.x == x and 
                obj.y == y and 
                obj.creature):

                target = obj
            
        if target:
            return target

def map_make_fov(incoming_map):
    global FOV_MAP

    FOV_MAP = tcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    for y in range(constants.MAP_HEIGHT):
        for x in range(constants.MAP_WIDTH):
            tcod.map_set_properties(FOV_MAP, x, y,
            not incoming_map[x][y].block_path, not incoming_map[x][y].block_path)

def map_calculate_fov():
    global FOV_CALCULATE

    if FOV_CALCULATE:
        FOV_CALCULATE = False
        tcod.map_compute_fov(FOV_MAP, PLAYER.x, PLAYER.y, constants.TORCH_RADIUS, constants.FOV_LIGHT_WALLS, 
            constants.FOV_ALGO)


# Drawing
# 888888ba                               oo                   
# 88    `8b                                                   
# 88     88 88d888b. .d8888b. dP  dP  dP dP 88d888b. .d8888b. 
# 88     88 88'  `88 88'  `88 88  88  88 88 88'  `88 88'  `88 
# 88    .8P 88       88.  .88 88.88b.88' 88 88    88 88.  .88 
# 8888888P  dP       `88888P8 8888P Y8P  dP dP    dP `8888P88 
#                                                         .88 
#                                                     d8888P  


def draw_game():

    global SURFACE_MAIN

    # clear the surface
    SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)

    # draw the map
    draw_map(GAME.current_map)

    # draw all objects
    for obj in GAME.current_objects:
        obj.draw()

    draw_messages()
    draw_debug()

    # update the display
    pygame.display.flip() 

def draw_map(map_to_draw):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):

            is_visible = tcod.map_is_in_fov(FOV_MAP, x, y)

            if is_visible:

                map_to_draw[x][y].explored = True

                if map_to_draw[x][y].block_path:
                    # draw wall
                    SURFACE_MAIN.blit(ASSETS.S_WALL, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw floor
                    SURFACE_MAIN.blit(ASSETS.S_FLOOR, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
            elif map_to_draw[x][y].explored:

                if map_to_draw[x][y].block_path:
                    # draw explored wall
                    SURFACE_MAIN.blit(ASSETS.S_WALLEXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw explored floor
                    SURFACE_MAIN.blit(ASSETS.S_FLOOREXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))

def draw_debug():
    draw_text(SURFACE_MAIN, "FPS: " + str(int(CLOCK.get_fps())), (0, 0), constants.COLOR_WHITE, constants.COLOR_BLACK)

def draw_messages():
    
    if len(GAME.message_history) <= constants.NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-constants.NUM_MESSAGES:]

    text_height = helper_text_height(ASSETS.FONT_MESSAGE_TEXT)

    start_y = constants.MAP_HEIGHT*constants.CELL_HEIGHT - (constants.NUM_MESSAGES * text_height) - 5

    i = 0
    for message, color in to_draw:
        draw_text(SURFACE_MAIN, message, (0, start_y + (i * text_height)), color, constants.COLOR_BLACK)
        i += 1

def draw_text(display_surface, text_to_display, T_coords, text_color, back_color = None):
    """ this function takes in some text and displays it on the referenced surface. """

    text_surf, text_rect = helper_text_objects(text_to_display, text_color, back_color)

    text_rect.topleft = T_coords

    display_surface.blit(text_surf, text_rect)

# Helper Functions
# dP     dP           dP                                     
# 88     88           88                                     
# 88aaaaa88a .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b. 
# 88     88  88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo. 
# 88     88  88.  ... 88 88.  .88 88.  ... 88             88 
# dP     dP  `88888P' dP 88Y888P' `88888P' dP       `88888P' 
#                        88                                  
#                        dP                                  

def helper_text_objects(incoming_text, incoming_color, incoming_bg):
    if incoming_bg:
        Text_surface = ASSETS.FONT_DEBUG_MESSAGE.render(incoming_text, False, incoming_color, incoming_bg)
    else:
        Text_surface = ASSETS.FONT_DEBUG_MESSAGE.render(incoming_text, False, incoming_color)

    return Text_surface, Text_surface.get_rect()

def helper_text_height(font):
    font_obj = font.render('a', False, (0, 0, 0))
    font_rect = font_obj.get_rect()

    return font_rect.height

# Game
#  .88888.                               
# d8'   `88                              
# 88        .d8888b. 88d8b.d8b. .d8888b. 
# 88   YP88 88'  `88 88'`88'`88 88ooood8 
# Y8.   .88 88.  .88 88  88  88 88.  ... 
#  `88888'8 `88888P8 dP  dP  dP `88888P' 


def game_main_loop():

    ''' In this function we loop the main game'''

    game_quit = False
    # player action definition
    player_action = "no-action"

    while not game_quit:
        # player action definition

        # handle player input
        player_action = game_handle_keys()

        map_calculate_fov()

        if player_action == "quit":
            game_quit = True
        # turn-based system
        elif player_action != "no-action":
            for obj in GAME.current_objects:
                if obj.ai:
                    obj.ai.take_turn()
        
        # draw the game
        draw_game()

        CLOCK.tick(constants.GAME_FPS)
    
    # TODO quit the game
    pygame.quit()
    exit()

def game_initialize():
    ''' This function initializes the main window and pygame'''

    global SURFACE_MAIN, GAME, CLOCK, FOV_CALCULATE, ASSETS, PLAYER, ENEMY

    # initialize pygame
    pygame.init()

    SURFACE_MAIN = pygame.display.set_mode((constants.MAP_WIDTH*constants.CELL_WIDTH, 
                                            constants.MAP_HEIGHT*constants.CELL_HEIGHT))

    GAME = obj_Game()

    CLOCK = pygame.time.Clock()

    FOV_CALCULATE = True

    ASSETS = struc_Assets()

    creature_com1 = com_Creature("greg")
    PLAYER = obj_Actor(1, 1, "python", ASSETS.A_PLAYER, animation_speed=1.0, creature = creature_com1)

    creature_com2 = com_Creature("jackie", death_function = death_monster)
    ai_com = ai_Test()
    ENEMY = obj_Actor(15, 10, "crab", ASSETS.A_ENEMY, animation_speed=1.0,
        creature=creature_com2, ai = ai_com)

    GAME.current_objects = [ENEMY, PLAYER]

def game_handle_keys():
    global FOV_CALCULATE
    # get player input
    events_list = pygame.event.get()

    for event in events_list:
        if event.type == pygame.QUIT:
            return "quit"
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                PLAYER.creature.move(0, -1)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_DOWN:
                PLAYER.creature.move(0, 1)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_LEFT:
                PLAYER.creature.move(-1, 0)
                FOV_CALCULATE = True
                return "player-moved"
            if event.key == pygame.K_RIGHT:
                PLAYER.creature.move(1, 0)
                FOV_CALCULATE = True
                return "player-moved"
    
    return "no-action"

def game_message(game_msg, msg_color):
    GAME.message_history.append((game_msg, msg_color))


# Execution
#  88888888b                                       dP   oo                   
#  88                                              88                        
# a88aaaa    dP.  .dP .d8888b. .d8888b. dP    dP d8888P dP .d8888b. 88d888b. 
#  88         `8bd8'  88ooood8 88'  `"" 88    88   88   88 88'  `88 88'  `88 
#  88         .d88b.  88.  ... 88.  ... 88.  .88   88   88 88.  .88 88    88 
#  88888888P dP'  `dP `88888P' `88888P' `88888P'   dP   dP `88888P' dP    dP 


if __name__ == '__main__':
    game_initialize()
    game_main_loop()


#  88888888b 888888ba  888888ba  
#  88        88    `8b 88    `8b 
# a88aaaa    88     88 88     88 
#  88        88     88 88     88 
#  88        88     88 88    .8P 
#  88888888P dP     dP 8888888P  
