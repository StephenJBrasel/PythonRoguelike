# third party modules
import tcod
import pygame
import math
import pickle
import gzip
import os
import datetime

# game files
import constants

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


class struc_Preferences:
    def __init__(self,
            vol_music = 0.1,
            vol_sound = 0.5):
        self.vol_music = vol_music
        self.vol_sound = vol_sound

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
    def __init__(self, x, y,
                 name_object,
                 animation_key,
                 animation_speed=0.5,
                 depth = 0,
                 state = None,
                 creature=None,
                 ai=None,
                 container=None,
                 item=None,
                 equipment=None,
                 stairs=None,
                 exitportal = None):
        self.x = x  # Map Address
        self.y = y  # Map Address
        self.name_object = name_object
        self.animation_key = animation_key
        self.animation = ASSETS.animation_dict[self.animation_key]
        # time for entire animation in seconds
        self.animation_speed = animation_speed / 1.0
        self.depth = depth
        self.state = state

        # animation flicker speed
        self.flicker_speed = self.animation_speed / len(self.animation)
        self.flicker_timer = 0.0
        self.sprite_image = 0

        self.creature = creature
        if self.creature:
            self.creature.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.container = container
        if self.container:
            self.container.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self

            self.item = com_Item()
            self.item.owner = self

        self.stairs = stairs
        if self.stairs:
            self.stairs.owner = self

        self.exitportal = exitportal
        if self.exitportal:
            self.exitportal.owner = self

    @property
    def display_name(self):
        # if self == PLAYER:
        #     return ("you")
        if self.creature:
            return (self.creature.name_instance + " the " + self.name_object)
        if self.item:
            if self.equipment and self.equipment.equipped:
                return (self.name_object + " (e)")
            else:
                return (self.name_object)

    def draw(self):
        is_visible = tcod.map_is_in_fov(FOV_MAP, self.x, self.y)
        if is_visible:
            if len(self.animation) == 1:
                SURFACE_MAP.blit(
                    self.animation[0], (self.x*constants.CELL_WIDTH, self.y * constants.CELL_HEIGHT))

            elif len(self.animation) > 1:

                if CLOCK.get_fps() > 0.0:
                    self.flicker_timer += 1/CLOCK.get_fps()

                if self.flicker_timer >= self.flicker_speed:
                    self.flicker_timer = 0.0

                    if self.sprite_image >= len(self.animation) - 1:
                        self.sprite_image = 0
                    else:
                        self.sprite_image += 1

                SURFACE_MAP.blit(self.animation[self.sprite_image], (
                    self.x*constants.CELL_WIDTH, self.y * constants.CELL_HEIGHT))

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y

        return math.sqrt((dx*dx) + (dy*dy))

    def move_towards(self, other):
        dx = other.x - self.x
        dy = other.y - self.y

        distance = math.sqrt((dx*dx) + (dy*dy))

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        self.creature.move(dx, dy)

    def move_away(self, other):
        dx = self.x - other.x
        dy = self.y - other.y

        distance = math.sqrt((dx*dx) + (dy*dy))

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        self.creature.move(dx, dy)

    def animation_destroy(self):
        self.animation = None

    def animation_init(self):
        self.animation = ASSETS.animation_dict[self.animation_key]


class obj_Game:
    def __init__(self):
        self.current_map, self.current_rooms = map_create()
        self.current_objects = []
        self.message_history = []
        self.maps_previous = []
        self.maps_next = []

    def transition_next(self):
        global FOV_CALCULATE

        FOV_CALCULATE = True

        for obj in self.current_objects:
            obj.animation_destroy()
            
        self.maps_previous.append(
            ((PLAYER.x, PLAYER.y),
            self.current_map,
            self.current_rooms,
            self.current_objects))

        if len(self.maps_next) == 0:

            self.current_objects = [PLAYER]

            PLAYER.animation_init()

            self.current_map, self.current_rooms = map_create()
            map_place_objects(self.current_rooms)
        else:
            ((PLAYER.x, PLAYER.y), self.current_map, self.current_rooms, 
                self.current_objects) = self.maps_next[-1]

            for obj in self.current_objects:
                obj.animation_init()
            
            map_make_fov(self.current_map)

            FOV_CALCULATE = True

            del self.maps_next[-1]
    
    def transition_previous(self):
        # make a case for if there are 0 previous levels.
        global FOV_CALCULATE
        if len(self.maps_previous) != 0:

            for obj in self.current_objects:
                obj.animation_destroy()

            self.maps_next.append(
                ((PLAYER.x, PLAYER.y), 
                self.current_map, 
                self.current_rooms, 
                self.current_objects))
            global FOV_CALCULATE

            ((PLAYER.x, PLAYER.y), self.current_map, self.current_rooms, 
                self.current_objects) = self.maps_previous[-1]

            for obj in self.current_objects:
                obj.animation_init()
            
            map_make_fov(self.current_map)

            FOV_CALCULATE = True

            del self.maps_previous[-1]
        else:
            game_message("There is no way to ascend. ")
        

class obj_Spritesheet:
    """ Class used to grab images out of a sprite sheet.
    "data/aquaticCreatures.png"
    """

    def __init__(self, file_name):
        # load in sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
        self.tiledict = {'a': 1, 'b': 2, 'c': 3, 'd': 4,
                         'e': 5, 'f': 6, 'g': 7, 'h': 8,
                         'i': 9, 'j': 10, 'k': 11, 'l': 12,
                         'm': 13, 'n': 14, 'o': 15, 'p': 16}

    def get_image(self, column, row, width=constants.CELL_WIDTH, height=constants.CELL_HEIGHT,
                  T_scale=None):
        """ T_scale is a Tuple """
        image_list = []

        image = pygame.Surface([width, height]).convert()

        image.blit(self.sprite_sheet, (0, 0),
                   (self.tiledict[column]*width, row*height, width, height))
        image.set_colorkey(constants.COLOR_BLACK)

        if T_scale:
            (new_w, new_h) = T_scale
            image = pygame.transform.scale(image, (new_w, new_h))

        image_list.append(image)

        return image_list

    def get_animation(self, column, row, width=constants.CELL_WIDTH, height=constants.CELL_HEIGHT,
                      num_sprites=1, T_scale=None):
        """ T_scale is a Tuple """
        image_list = []

        for i in range(num_sprites):
            # Create blank image

            image = pygame.Surface([width, height]).convert()
            # Copy image from sheet onto blank
            image.blit(self.sprite_sheet, (0, 0), ((
                self.tiledict[column] + i)*width, row*height, width, height))

            # Set transparency key to blank
            image.set_colorkey(constants.COLOR_BLACK)

            if T_scale:
                (new_w, new_h) = T_scale
                image = pygame.transform.scale(image, (new_w, new_h))

            image_list.append(image)

        return image_list


class obj_Room:
    """
    This is a rectangle that lives on the map
    """
    def __init__(self, T_coords, T_size):
        self.x1, self.y1 = T_coords
        self.w, self.h = T_size

        self.x2 = self.x1 + self.w
        self.y2 = self.y1 + self.h
    
    @property
    def center(self):
        center_x = int((self.x1 + self.x2)* 0.5)
        center_y = int((self.y1 + self.y2)* 0.5)
        return (center_x, center_y)
    
    def intersect(self, other):
        # return True if other object intersects with this one.
        obj_intersect = (self.x1 <= other.x2 and self.x2 >= other.x1 and
                         self.y1 <= other.y2 and self.y2 >= other.y1)
        return obj_intersect


class obj_Camera:
    def __init__(self, follow_speed = 0.1):
        self.x, self.y = (0, 0)
        self.width = constants.CAMERA_WIDTH
        self.height = constants.CAMERA_HEIGHT
        self.follow_speed = follow_speed

    @property
    def rect(self):
        pos_rect = pygame.Rect((0, 0), 
            (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))

        pos_rect.center = (self.x, self.y)

        return pos_rect

    @property
    def map_address(self):
        map_x = int(self.x/constants.CELL_WIDTH)
        map_y = int(self.y/constants.CELL_HEIGHT)

        return (map_x, map_y)

    def update(self, T_target):

        target_x = T_target.x * constants.CELL_WIDTH + int(constants.CELL_WIDTH/2)
        target_y = T_target.y * constants.CELL_HEIGHT + int(constants.CELL_HEIGHT/2)

        distance_x, distance_y = self.map_dist((target_x, target_y))

        self.x += int(distance_x * self.follow_speed)
        self.y += int(distance_y * self.follow_speed)

    def win_to_map(self, T_coords):

        tar_x, tar_y = T_coords
        # convert window coordinates to distance from camera
        cam_d_x, cam_d_y = self.cam_dist((tar_x, tar_y))

        # distance from camera -> map coordinate
        map_p_x = self.x + cam_d_x
        map_p_y = self.y + cam_d_y

        return (map_p_x, map_p_y)

    def map_dist(self, T_coords):
        new_x, new_y = T_coords
        
        dist_x = new_x - self.x
        dist_y = new_y - self.y

        return (dist_x, dist_y)

    def cam_dist(self, T_coords):
        win_x, win_y = T_coords
        dist_x = int(win_x - (self.width/2))
        dist_y = int(win_y - (self.height/2))

        return (dist_x, dist_y)


class obj_Assets:
    def __init__(self):
        self.load_assets()
        self.volume_adjust()

    def load_assets(self):

        """ ART """
        # SPRITESHEETS
        self.reptiles = obj_Spritesheet("data/graphics/Characters/Reptile.png")
        self.aquatic = obj_Spritesheet("data/graphics/Characters/Aquatic.png")
        self.rodent = obj_Spritesheet("data/graphics/Characters/Rodent.png")
        self.wall = obj_Spritesheet("data/graphics/Objects/Wall.png")
        self.floor = obj_Spritesheet("data/graphics/Objects/Floor.png")
        self.tile = obj_Spritesheet("data/graphics/Objects/Tile.png")
        self.shield = obj_Spritesheet("data/graphics/Items/Shield.png")
        self.medwep = obj_Spritesheet("data/graphics/Items/MedWep.png")
        self.scroll = obj_Spritesheet("data/graphics/Items/Scroll.png")
        self.flesh = obj_Spritesheet("data/graphics/Items/Flesh.png")
        self.misc = obj_Spritesheet("data/graphics/Items/Light.png")
        self.doors = obj_Spritesheet("data/graphics/Objects/Door.png")

        # ANIMATIONS
        self.A_PLAYER = self.reptiles.get_animation(
            'm', 5, 16, 16, 2, (32, 32))
        self.A_SNAKE_01 = self.reptiles.get_animation(
            'e', 5, 16, 16, 2, (32, 32))
        self.A_SNAKE_02 = self.reptiles.get_animation(
            'k', 5, 16, 16, 2, (32, 32))
        self.A_MOUSE = self.rodent.get_animation(
            'a', 2, 16, 16, 2, (32, 32))

        # SPRITES
        self.S_WALL = self.wall.get_image('d', 7, 16, 16, (32, 32))[0]
        self.S_WALLEXPLORED = self.wall.get_image('d', 13, 16, 16, (32, 32))[0]

        self.S_FLOOR = self.floor.get_image('b', 8, 16, 16, (32, 32))[0]
        self.S_FLOOREXPLORED = self.floor.get_image(
            'b', 14, 16, 16, (32, 32))[0]

        # ITEMS
        self.S_SWORD = self.medwep.get_image('a', 1, 16, 16, (32, 32))
        self.S_SHIELD = self.shield.get_image('a', 1, 16, 16, (32, 32))
        self.S_SCROLL_YELLOW = self.scroll.get_image('e', 1, 16, 16, (32, 32))
        self.S_SCROLL_RED = self.scroll.get_image('c', 2, 16, 16, (32, 32))
        self.S_SCROLL_BLANK = self.scroll.get_image('d', 6, 16, 16, (32, 32))
        self.S_FLESH_01 = self.flesh.get_image('b', 4, 16, 16, (32, 32))
        self.S_FLESH_02 = self.flesh.get_image('a', 1, 16, 16, (32, 32))

        # SPECIAL
        self.S_STAIRS_DOWN = self.tile.get_image('f', 4, 16, 16, (32, 32))
        self.S_STAIRS_UP = self.tile.get_image('e', 4, 16, 16, (32, 32))
        self.I_MAIN_MENU_BG = pygame.image.load("data/graphics/game/mainmenu.jpg")
        self.I_MAIN_MENU_BG = pygame.transform.scale(self.I_MAIN_MENU_BG, 
            (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))
        self.S_MAGIC_LAMP = self.misc.get_image('e', 1, 16, 16, (32, 32))
        self.S_PORTAL_CLOSED = self.doors.get_image('j', 6, 16, 16, (32, 32))
        self.A_PORTAL_OPEN = self.doors.get_animation(
            'k', 6, 16, 16, 2, (32, 32))

        self.animation_dict = {
            # ANIMATIONS
            "A_PLAYER":self.A_PLAYER,
            "A_SNAKE_01":self.A_SNAKE_01,
            "A_SNAKE_02":self.A_SNAKE_02,
            "A_MOUSE":self.A_MOUSE,

            # ITEMS
            "S_SWORD":self.S_SWORD,
            "S_SHIELD":self.S_SHIELD, 
            "S_SCROLL_YELLOW":self.S_SCROLL_YELLOW,
            "S_SCROLL_RED":self.S_SCROLL_RED,
            "S_SCROLL_BLANK":self.S_SCROLL_BLANK,
            "S_FLESH_01":self.S_FLESH_01,
            "S_FLESH_02":self.S_FLESH_02,

            # SPECIAL
            "S_STAIRS_DOWN":self.S_STAIRS_DOWN,
            "S_STAIRS_UP":self.S_STAIRS_UP,
            "S_MAGIC_LAMP":self.S_MAGIC_LAMP,
            "S_PORTAL_CLOSED":self.S_PORTAL_CLOSED,
            "A_PORTAL_OPEN":self.A_PORTAL_OPEN
        }

        """ AUDIO """

        # Audio 
        self.music_background = "data/Audio/Boundless_Protest.mp3"
        # Sound
        self.snd_list = []

        self.snd_hit1 = self.sound_add("data/Audio/Hit_Hurt1.wav")
        self.snd_hit2 = self.sound_add("data/Audio/Hit_Hurt2.wav")
        self.snd_hit3 = self.sound_add("data/Audio/Hit_Hurt3.wav")
        self.snd_hit4 = self.sound_add("data/Audio/Hit_Hurt4.wav")
        self.snd_hit_list = [
            self.snd_hit1,
            self.snd_hit2,
            self.snd_hit3,
            self.snd_hit4]

    def sound_add(self, file_address):
        new_sound = pygame.mixer.Sound(file_address)
        self.snd_list.append(new_sound)
        return new_sound

    def volume_adjust(self):
        for sound in self.snd_list:
            sound.set_volume(PREFERENCES.vol_sound)
        pygame.mixer.music.set_volume(PREFERENCES.vol_music)


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

    def __init__(self, name_instance, base_atk=2, base_def=0, hp=10,
                 death_function=None):

        self.name_instance = name_instance
        self.base_atk = base_atk
        self.base_def = base_def
        self.maxhp = hp
        self.hp = hp
        self.death_function = death_function

    def move(self, dx, dy):

        tile_is_wall = (
            GAME.current_map[self.owner.x + dx][self.owner.y + dy].block_path == True)

        target = map_check_for_creatures(
            self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy

    def attack(self, target):

        damage_dealt = self.power - target.creature.defense
        if damage_dealt < 0:
            damage_dealt = 0
        # TODO if no damage is being dealt, display an appropriate message.

        game_message((self.owner.display_name + " attacks " +
                      target.display_name + " for " +
                      str(damage_dealt) + " damage!"),
                     constants.COLOR_WHITE)
        target.creature.take_damage(damage_dealt)

        if damage_dealt > 0 and self.owner is PLAYER:
            hit_effect = tcod.random_get_int(RAND_INSTANCE, 0, len(ASSETS.snd_hit_list) - 1)
            pygame.mixer.Sound.play(ASSETS.snd_hit_list[hit_effect])

    def take_damage(self, damage):
        self.hp -= damage
        game_message(self.owner.display_name + "'s health is " +
                     str(self.hp) + "/" + str(self.maxhp), constants.COLOR_RED)

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def heal(self, value):
        self.hp += value
        if self.hp > self.maxhp:
            self.hp = self.maxhp
        game_message(self.owner.display_name + "'s health is " +
                     str(self.hp) + "/" + str(self.maxhp), constants.COLOR_GREY)

    @property
    def power(self):
        total_power = self.base_atk

        if self.owner.container:
            obj_bonuses = [obj.equipment.attack_bonus
                           for obj in self.owner.container.equipped_items]
            for bonus in obj_bonuses:
                if bonus:
                    total_power += bonus

        return total_power

    @property
    def defense(self):
        total_defense = self.base_def

        if self.owner.container:
            obj_bonuses = [obj.equipment.defense_bonus
                           for obj in self.owner.container.equipped_items]
            for bonus in obj_bonuses:
                if bonus:
                    total_defense += bonus

        return total_defense


class com_Container:
    def __init__(self, volume=10.0, inventory=[]):
        self.inventory = inventory
        self.max_volume = volume
        # self.volume = 0.0 # TODO self.volume = get_total_volume()
        # self.weight = weight

    # TODO def get_names_inventory():

    # TODO def get_total_volume():
    @property
    def volume(self):
        return 0.0

    @property
    def equipped_items(self):
        list_of_equipped_items = [obj for obj in self.inventory if
                                  obj.equipment and obj.equipment.equipped]
        return list_of_equipped_items

    # TODO def get_total_weight():


class com_Item:
    def __init__(self, 
            weight=0.0, 
            volume=0.0, 
            use_function=None,
            value=None
            ):
        self.weight = weight
        self.volume = volume
        self.value = value
        self.use_function = use_function

    # def pickup_item():
    def pick_up(self, actor):

        if actor.container:
            if actor.container.volume + self.volume > actor.container.max_volume:
                game_message("Not enough room to pick up", constants.COLOR_RED)
            else:
                game_message(("Picking up " + self.owner.name_object), constants.COLOR_WHITE)
                actor.container.inventory.append(self.owner)
                self.owner.animation_destroy()
                GAME.current_objects.remove(self.owner)
                self.container = actor.container

    # def drop_item():
    def drop(self, new_x, new_y):
        GAME.current_objects.append(self.owner)
        self.owner.animation_init()
        self.container.inventory.remove(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y
        game_message("Item dropped", constants.COLOR_GREY)

    def use(self):
        """ 
        Use the item by producing an effect and removing it.
        """
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return "no-action"

        if self.use_function:  # """ == cast_heal """
            result = self.use_function(self.container.owner, self.value)
            if result is not None:
                print("use_function failed.")
            else:
                self.container.inventory.remove(self.owner)
                return result


class com_Equipment:
    def __init__(self, attack_bonus=None, defense_bonus=None, slot=None):
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.slot = slot

        self.equipped = False

    def toggle_equip(self):
        if self.equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):
        # check for equipment in slot

        all_equipped_items = self.owner.item.container.equipped_items
        # item_found = False

        for item in all_equipped_items:
            if (item.equipment.slot and
                    item.equipment.slot == self.slot):
                game_message("Equipment slot is occupied.",
                             constants.COLOR_RED)
                return

        self.equipped = True

        game_message("Item equipped")

    def unequip(self):
        # toggle self.equipped
        self.equipped = False

        game_message("Item unequipped")


class com_Stairs:
    def __init__(self,
            downwards=True):
        self.downwards = downwards

    def use(self):
        if self.downwards:
            GAME.transition_next()
        else:
            GAME.transition_previous()


class com_ExitPortal:
    def __init__(self):
        self.CLOSEDANIMATION = "S_PORTAL_CLOSED"
        self.OPENANIMATION = "A_PORTAL_OPEN"

    def update(self):

        found_lamp = False
        is_portal_open = (self.owner.state == "OPEN")

        for obj in PLAYER.container.inventory:
            if (obj.name_object == "THE LAMP"):
                found_lamp = True
                break
        if found_lamp and not is_portal_open:
            self.owner.state = "OPEN"
            self.owner.animation_key = self.OPENANIMATION
            self.owner.animation_init()
        if not found_lamp and is_portal_open:
            self.owner.state = "CLOSED"
            self.owner.animation_key = self.CLOSEDANIMATION
            self.owner.animation_init()

        #         if self.owner.state is not "OPEN":
        #             self.owner.state = "OPEN"
        #             self.owner.animation_key = self.OPENANIMATION
        #             self.owner.animation_init()
        # if not found_lamp and self.owner.state is "OPEN":
        #     self.owner.state = "CLOSED"
        #     self.owner.animation_key = self.CLOSEDANIMATION
        #     self.owner.animation_init()

# AI
#  .d888888  dP
# d8'    88  88
# 88aaaaa88a 88
# 88     88  88
# 88     88  88
# 88     88  dP


class ai_Confuse:
    """
    Once per turn, execute.
    """

    def __init__(self, old_ai, num_turns):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:
            self.owner.creature.move(
                tcod.random_get_int(RAND_INSTANCE, -1, 1),
                tcod.random_get_int(RAND_INSTANCE, -1, 1))
            self.num_turns -= 1
        else:
            self.owner.ai = self.old_ai
            game_message((self.owner.display_name +
                          " has broken free!"), constants.COLOR_RED)


class ai_Chase:
    """  
    AI needs to continuously moves toward target (PLAYER).

    Gets list of coords from self to target, 
    each turn move 1 coord closer to target.
    """

    def take_turn(self):
        monster = self.owner

        if tcod.map_is_in_fov(FOV_MAP, monster.x, monster.y):

            # move towards the player if far away.
            if monster.distance_to(PLAYER) >= 2:
                self.owner.move_towards(PLAYER)

            # if close enough, attack player.
            elif PLAYER.creature.hp > 0:
                monster.creature.attack(PLAYER)


class ai_Flee:
    """  
    AI needs to continuously moves toward target (PLAYER).

    Gets list of coords from self to target, 
    each turn move 1 coord closer to target.
    """

    def take_turn(self):
        monster = self.owner

        if tcod.map_is_in_fov(FOV_MAP, monster.x, monster.y):
            self.owner.move_away(PLAYER)


# Death
# 888888ba                      dP   dP
# 88    `8b                     88   88
# 88     88 .d8888b. .d8888b. d8888P 88d888b.
# 88     88 88ooood8 88'  `88   88   88'  `88
# 88    .8P 88.  ... 88.  .88   88   88    88
# 8888888P  `88888P' `88888P8   dP   dP    dP


def death_snake(monster):
    """ On death, most monsters stop moving. """
    game_message(monster.creature.name_instance +
                 " is dead!", constants.COLOR_GREY)
    monster.animation = ASSETS.S_FLESH_01
    monster.animation_key = "S_FLESH_01"
    monster.depth = constants.DEPTH_CORPSE
    monster.creature = None
    monster.ai = None


def death_mouse(mouse):
    """ On death, most monsters stop moving. """
    game_message(mouse.creature.name_instance +
                 " is dead! Eat him for more health!", 
                 constants.COLOR_GREEN)
    mouse.animation = ASSETS.S_FLESH_02
    mouse.animation_key = "S_FLESH_02"
    mouse.depth = constants.DEPTH_CORPSE
    mouse.creature = None
    mouse.ai = None


def death_player(player):
    player.state = "STATUS_DEAD"

    # display game over
    SURFACE_MAIN.fill(constants.COLOR_BLACK)
    screen_center = (int(constants.CAMERA_WIDTH*0.5), int(constants.CAMERA_HEIGHT*0.5))
    draw_text(SURFACE_MAIN,
        "YOU DIED",
        screen_center,
        constants.FONT_TITLE_SCREEN,
        constants.COLOR_RED, 
        back_color=None,
        center=True)

    pygame.display.update()

    pygame.time.wait(2000)
    # create legacy file
    fileName = ("data/graveyard/" + PLAYER.creature.name_instance + "." + 
        datetime.date.today().strftime("%Y%B%d") + ".txt")

    legacy_file = open(fileName, "a+")
    for msg, color in GAME.message_history:
        legacy_file.write(msg + "\n")
    legacy_file.write("----------\n")
    # delete save file
    # if os.path.exists("data/savedata/savegame"):
    #     os.remove("data/savedata/savegame")
    # kick player to main menu

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
    new_map = [[struc_Tile(True) for y in range(0, constants.MAP_HEIGHT)]
               for x in range(0, constants.MAP_WIDTH)]
    # for x in range(constants.MAP_WIDTH):
        #     new_map[x][0].block_path = True
        #     new_map[x][constants.MAP_HEIGHT - 1].block_path = True
        # for y in range(constants.MAP_HEIGHT):
        #     new_map[0][y].block_path = True
        #     new_map[constants.MAP_WIDTH - 1][y].block_path = True
    # generate new room
    list_of_rooms = []

    for i in range(constants.MAP_MAX_NUM_ROOMS):
        w = tcod.random_get_int(RAND_INSTANCE, 
                                constants.ROOM_MIN_WIDTH, 
                                constants.ROOM_MAX_WIDTH)
        h = tcod.random_get_int(RAND_INSTANCE, 
                                constants.ROOM_MIN_HEIGHT, 
                                constants.ROOM_MAX_HEIGHT)
        x = tcod.random_get_int(RAND_INSTANCE, 
                                constants.MAP_BORDER_WIDTH, 
                                (constants.MAP_WIDTH - w - constants.MAP_BORDER_WIDTH - 1))
        y = tcod.random_get_int(RAND_INSTANCE, 
                                constants.MAP_BORDER_WIDTH, 
                                (constants.MAP_HEIGHT - h - constants.MAP_BORDER_WIDTH - 1))
        # create the room
        new_room = obj_Room((x,y), (w, h))

        # check for other intersecting rooms
        failed = False
        for room in list_of_rooms:
            if new_room.intersect(room):
                failed = True
                break
        # if not failed, place the room
        if not failed:
            map_create_room(new_map, new_room)
            list_of_rooms.append(new_room)
            current_center = new_room.center
            
            if len(list_of_rooms) > 1:
                previous_center = list_of_rooms[-2].center
                # dig the tunnels
                map_create_tunnels(current_center, previous_center, new_map)

    map_make_fov(new_map)

    
    print("There are " + str(len(list_of_rooms)) + " rooms.")

    return new_map, list_of_rooms


def map_place_objects(room_list):

    current_level = len(GAME.maps_previous) + 1

    is_top_level = (current_level == 1)
    is_final_level = (current_level == constants.MAP_NUM_LEVELS)

    for room in room_list:

        # TODO clarify when PLAYER is centered in a new room
        # TODO stop enemies from being generated in the room you immediately go into.
        is_first_room = (room == room_list[0])
        is_last_room = (room == room_list[-1])

        if is_first_room: 
            PLAYER.x, PLAYER.y = room.center
        if is_first_room and is_top_level:
            gen_portal(room.center)
        if is_first_room and not is_top_level:
            gen_stairs((PLAYER.x, PLAYER.y), downwards=False)

        if is_last_room:
            if is_final_level:
                gen_LAMP(room.center)
            else:
                gen_stairs(room.center)
        
        x = tcod.random_get_int(RAND_INSTANCE, room.x1 + 1, room.x2 - 1)
        y = tcod.random_get_int(RAND_INSTANCE, room.y1 + 1, room.y2 - 1)

        gen_enemy((x, y))
        x = tcod.random_get_int(RAND_INSTANCE, room.x1 + 1, room.x2 - 1)
        y = tcod.random_get_int(RAND_INSTANCE, room.y1 + 1, room.y2 - 1)

        gen_item((x, y))


def map_create_room(new_map, new_room):
    for x in range(new_room.x1 + 1, new_room.x2):
        for y in range(new_room.y1 + 1, new_room.y2):
            new_map[x][y].block_path = False


def map_create_tunnels(coords1, coords2, new_map):

    coin_flip = (tcod.random_get_int(RAND_INSTANCE, 0, 1) == 1)

    x1, y1 = coords1
    x2, y2 = coords2

    minX = min(x1, x2)
    minY = min(y1, y2)

    maxX = max(x1, x2)
    maxY = max(y1, y2)

    if coin_flip:
        if ((minX == x1 and minY == y1) or 
            (minX == x2 and minY == y2)): 
            # 0 (min, min) x (max, min) y
            for x in range(minX, maxX + 1):
                new_map[x][minY].block_path = False
            for y in range(minY, maxY + 1):
                new_map[maxX][y].block_path = False
        else:
            # 2 (min, min) x (min, min) y
            for x in range(minX, maxX + 1):
                new_map[x][minY].block_path = False
            for y in range(minY, maxY + 1):
                new_map[minX][y].block_path = False
    else:
        if ((minX == x1 and minY == y1) or 
            (minX == x2 and minY == y2)): 
            # 1 (min, min) y (min, max) x
            for x in range(minX, maxX + 1):
                new_map[x][maxY].block_path = False
            for y in range(minY, maxY + 1):
                new_map[minX][y].block_path = False
        else:
            # 3 (min, max) x (max, min) y
            for x in range(minX, maxX + 1):
                new_map[x][maxY].block_path = False
            for y in range(minY, maxY + 1):
                new_map[maxX][y].block_path = False


def map_check_for_creatures(x, y, exclude_object=None):
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


def map_objects_at_coords(coords_x, coords_y):
    object_options = [obj for obj in GAME.current_objects
                      if obj.x == coords_x and obj.y == coords_y]

    return object_options


def map_find_line(coords1, coords2):
    """ 
    Converts two x, y coords into a list of tiles.

    coords1 : (x1, y1)
    coords2 : (x2, y2)
    """

    x1, y1 = coords1
    x2, y2 = coords2

    tcod.line_init(x1, y1, x2, y2)

    calc_x, calc_y = tcod.line_step()

    coord_list = []

    if x1 == x2 and y1 == y2:
        return [(x1, y1)]

    while (calc_x is not None):
        coord_list.append((calc_x, calc_y))

        calc_x, calc_y = tcod.line_step()

    return coord_list


def map_find_radius(coords, radius):

    center_x, center_y = coords

    tile_list = []

    start_x = center_x - radius
    end_x = center_x + radius + 1

    start_y = center_y - radius
    end_y = center_y + radius + 1

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            tile_list.append((x, y))

    return tile_list


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
    # clear the surface
    SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)
    SURFACE_MAP.fill(constants.COLOR_BLACK)

    CAMERA.update(PLAYER)

    # display_rect = pygame.Rect(
    #     (0 * constants.CELL_WIDTH, 0 * constants.CELL_HEIGHT), 
    #     (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))

    # draw the map
    draw_map(GAME.current_map)

    # draw all objects
    for obj in sorted(GAME.current_objects, key = lambda obj: obj.depth, reverse = True):
        obj.draw()

    SURFACE_MAIN.blit(SURFACE_MAP, (0, 0), CAMERA.rect)

    draw_messages()
    draw_debug()


def draw_map(map_to_draw):

    # convert camera into address
    cam_x, cam_y = CAMERA.map_address
    display_map_w = int(constants.CAMERA_WIDTH / constants.CELL_WIDTH)
    display_map_h = int(constants.CAMERA_HEIGHT / constants.CELL_HEIGHT)

    render_w_min = cam_x - int(display_map_w / 2)
    render_h_min = cam_y - int(display_map_h / 2)

    render_w_max = cam_x + int(display_map_w / 2)
    render_h_max = cam_y + int(display_map_h / 2)

    if render_h_min < 0: render_h_min = 0
    if render_w_min < 0: render_w_min = 0

    if render_w_max > constants.MAP_WIDTH : render_w_max = constants.MAP_WIDTH
    if render_h_max > constants.MAP_HEIGHT: render_h_max = constants.MAP_HEIGHT

    for x in range(render_w_min, render_w_max):
        for y in range(render_h_min, render_h_max):

            is_visible = tcod.map_is_in_fov(FOV_MAP, x, y)
            if FOV_CALCULATE:
                is_visible = True

            if is_visible:

                map_to_draw[x][y].explored = True

                if map_to_draw[x][y].block_path:
                    # draw wall
                    SURFACE_MAP.blit(
                        ASSETS.S_WALL, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw floor
                    SURFACE_MAP.blit(
                        ASSETS.S_FLOOR, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
            elif map_to_draw[x][y].explored:

                if map_to_draw[x][y].block_path:
                    # draw explored wall
                    SURFACE_MAP.blit(
                        ASSETS.S_WALLEXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))
                else:
                    # draw explored floor
                    SURFACE_MAP.blit(
                        ASSETS.S_FLOOREXPLORED, (x * constants.CELL_WIDTH, y * constants.CELL_HEIGHT))


def draw_debug():
    draw_text(SURFACE_MAIN, "FPS: " + str(int(CLOCK.get_fps())), (0, 0),
              constants.FONT_DEBUG_MESSAGE, constants.COLOR_WHITE, constants.COLOR_BLACK)


def draw_messages():

    if len(GAME.message_history) <= constants.NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-constants.NUM_MESSAGES:]

    text_height = helper_text_height(constants.FONT_MESSAGE_TEXT)

    start_y = (constants.CAMERA_HEIGHT - 
        (constants.NUM_MESSAGES * text_height))

    for i, (message, color) in enumerate(to_draw):
        draw_text(SURFACE_MAIN,
                  message,
                  (0, start_y + (i * text_height)),
                  constants.FONT_MESSAGE_TEXT,
                  color,
                  constants.COLOR_BLACK)


def draw_text(display_surface,
              text_to_display,
              T_coords,
              text_font,
              text_color,
              back_color=None,
              center=False):
    """ this function takes in some text and displays it on the referenced surface. """

    text_surf, text_rect = helper_text_objects(
        text_to_display, text_font, text_color, back_color)

    if not center:
        text_rect.topleft = T_coords
    else:
        text_rect.center = T_coords

    display_surface.blit(text_surf, text_rect)


def draw_tile_rect(T_coords,
                   tile_color=constants.COLOR_WHITE,
                   tile_alpha=constants.COLOR_ALPHA,
                   mark=None):
    x, y = T_coords

    # # default colors
    # if tile_alpha: local_color = tile_color
    # else: local_color = constants.COLOR_WHITE

    # # default alpha
    # if tile_color: local_alpha = tile_alpha
    # else: local_alpha = constants.alpha

    new_x = x * constants.CELL_WIDTH
    new_y = y * constants.CELL_HEIGHT

    new_surface = pygame.Surface((constants.CELL_WIDTH, constants.CELL_HEIGHT))

    new_surface.fill(tile_color)

    new_surface.set_alpha(tile_alpha)

    if mark:
        # draw_text(new_surface, mark, constants.FONT_CURSOR_TEXT,
        #     (new_x, new_y), constants.COLOR_GREY, center = True)
        draw_text(
            display_surface=new_surface,
            text_to_display=mark,
            T_coords=(constants.CELL_WIDTH/2, constants.CELL_HEIGHT/2),
            text_font=constants.FONT_CURSOR_TEXT,
            text_color=constants.COLOR_BLACK,
            back_color=None,
            center=True)

    SURFACE_MAP.blit(new_surface, (new_x, new_y))

# Helper Functions
# dP     dP           dP
# 88     88           88
# 88aaaaa88a .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
# 88     88  88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
# 88     88  88.  ... 88 88.  .88 88.  ... 88             88
# dP     dP  `88888P' dP 88Y888P' `88888P' dP       `88888P'
#                        88
#                        dP


def helper_text_objects(incoming_text, incoming_font, incoming_color, incoming_bg):
    if incoming_bg:
        Text_surface = incoming_font.render(
            incoming_text, False, incoming_color, incoming_bg)
    else:
        Text_surface = incoming_font.render(
            incoming_text, False, incoming_color)

    return Text_surface, Text_surface.get_rect()


def helper_text_height(font):
    font_obj = font.render('a', False, (0, 0, 0))
    font_rect = font_obj.get_rect()

    return font_rect.height


def helper_text_width(font, text):
    font_obj = font.render(text, False, (0, 0, 0))
    font_rect = font_obj.get_rect()

    return font_rect.width


# Magic
# 8888ba.88ba                    oo
# 88  `8b  `8b
# 88   88   88 .d8888b. .d8888b. dP .d8888b.
# 88   88   88 88'  `88 88'  `88 88 88'  `""
# 88   88   88 88.  .88 88.  .88 88 88.  ...
# dP   dP   dP `88888P8 `8888P88 dP `88888P'
#                            .88
#                        d8888P


def cast_heal(caster, value):

    if caster.creature.hp >= caster.creature.maxhp:
        game_message(caster.display_name +
                     " is already at full health!")
        return "cancelled"
    else:
        game_message(caster.display_name +
                     " healed for " + str(value) + " health!")
        caster.creature.heal(value)
    return None


def cast_lightning(caster, T_damage_maxrange=(10, 5)):

    damage, m_range = T_damage_maxrange

    caster_location = (caster.x, caster.y)

    # TODO prompt the caster for a tile
    # if caster == PLAYER:
    menu_return = menu_tile_select(coords_origin=caster_location,
                                   max_range=m_range, 
                                   penetrate_walls=False)
    # else:
    #   # TODO create AI function for enemy targeting system.
    #   # menu_return =
    #   # menu_return = (PLAYER.x, PLAYER.y)

    if not isinstance(menu_return, tuple):
        return menu_return
    else:
        # TODO IT'S NOT THE PLAYER COORDS, IT'S THE CASTER COORDS.
        # convert that tile into a list of tiles between CASTER and TARGET_TILE
        list_of_tiles = map_find_line((caster.x, caster.y), menu_return)
        # cycle through list, damage everything found.
        for i, (x, y) in enumerate(list_of_tiles):
            target = map_check_for_creatures(x, y)
            if target:  # and x != caster.x and y != caster.y
                target.creature.take_damage(damage)


def cast_fireball(caster, T_damage_radius_range=(5, 1, 4)):

    damage, radius, max_range = T_damage_radius_range

    caster_location = (caster.x, caster.y)
    # TODO get target tile
    menu_return = menu_tile_select(
        coords_origin=caster_location,
        max_range=max_range,
        radius=radius,
        penetrate_walls=False,
        pierce_creatures=False)
    if not isinstance(menu_return, tuple):
        return menu_return
    else:
        # get sequence of tiles
        tiles_to_damage = map_find_radius(menu_return, radius)

        creature_hit = False

        # damage all creatures in (radius) tiles.
        for (x, y) in tiles_to_damage:
            creature_to_damage = map_check_for_creatures(x, y)
            if creature_to_damage:
                creature_to_damage.creature.take_damage(damage)
                if creature_to_damage is not PLAYER:
                    creature_hit = True
        if creature_hit:
            game_message("Screams of pain echo around you.",
                         constants.COLOR_RED)


def cast_confusion(caster, num_turns=5):

    # TODO select tile
    menu_return = menu_tile_select()

    if not isinstance(menu_return, tuple):
        return menu_return
    else:
        # TODO get target
        tile_x, tile_y = menu_return
        target = map_check_for_creatures(tile_x, tile_y)

        # TODO temporarily give target confusion ai.
        if target:
            oldai = target.ai
            target.ai = ai_Confuse(oldai, num_turns)
            target.ai.owner = target

            game_message((target.display_name + "'s eyes glaze over"),
                         constants.COLOR_GREEN)


# UI
# dP     dP dP 
# 88     88 88 
# 88     88 88 
# 88     88 88 
# Y8.   .8P 88 
# `Y88888P' dP 


class ui_Button():
    def __init__(self, 
            surface, 
            size, 
            center_coords = (0, 0), 
            font = constants.FONT_DEBUG_MESSAGE,
            button_text = "",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_GREEN,
            color_text_mouseover = constants.COLOR_GREY,
            color_text_default = constants.COLOR_BLACK):
        self.surface = surface
        self.size = size
        self.center_coords = center_coords
        self.font = font
        self.button_text = button_text

        self.c_box_mo = color_box_mouseover
        self.c_box_default = color_box_default
        self.c_text_mo = color_text_mouseover
        self.c_text_default = color_text_default
        self.current_c_box = self.c_box_default
        self.current_c_text = self.c_text_default

        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = self.center_coords

    def update(self, player_input):
        mouse_clicked = False
        local_events, local_mousepos = player_input
        mouse_x, mouse_y = local_mousepos

        mouse_over = (mouse_x >= self.rect.left and
                      mouse_x <= self.rect.right and
                      mouse_y >= self.rect.top and
                      mouse_y <= self.rect.bottom)

        for event in local_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: mouse_clicked = True

        if mouse_over and mouse_clicked:
            return True

        if mouse_over:
            self.current_c_box = self.c_box_mo
            self.current_c_text = self.c_text_mo
        else:
            self.current_c_box = self.c_box_default
            self.current_c_text = self.c_text_default

    def draw(self):
        pygame.draw.rect(self.surface, self.current_c_box, self.rect)
        draw_text(display_surface = self.surface,
              text_to_display = self.button_text,
              T_coords = self.center_coords,
              text_font = self.font,
              text_color = self.current_c_text,
              back_color=False,
              center=True)


class ui_Slider():
    def __init__(self, 
            surface, 
            size, 
            center_coords = (0, 0),
            c_bg = constants.COLOR_BLACK,
            c_fg = constants.COLOR_GREEN,
            c_bg_mo = constants.COLOR_GREY,
            c_fg_mo = constants.COLOR_RED,
            parameter_value = 0.5
            ):
        self.surface = surface
        self.size = size
        self.center_coords = center_coords

        self.c_bg = c_bg
        self.c_fg = c_fg
        self.c_bg_mo = c_bg_mo
        self.c_fg_mo = c_fg_mo
        self.current_c_bg = self.c_bg
        self.current_c_fg = self.c_fg
        self.current_val = parameter_value

        self.rect_bg = pygame.Rect((0, 0), size)
        self.rect_bg.center = self.center_coords

        self.rect_fg = pygame.Rect(
            (0, 0), 
            (self.rect_bg.width * self.current_val, self.rect_bg.h))
        self.rect_fg.topleft = self.rect_bg.topleft

        self.grip_tab = pygame.Rect(
            (0, 0),
            (20, self.rect_bg.h + 4))
        self.grip_tab.center = (self.rect_fg.right, self.rect_bg.centery)
    
    def update(self, player_input):
        mouse_down = pygame.mouse.get_pressed()[0]

        local_events, local_mousepos = player_input
        mouse_x, mouse_y = local_mousepos

        mouse_over = (mouse_x >= self.rect_bg.left and
                      mouse_x <= self.rect_bg.right and
                      mouse_y >= self.rect_bg.top and
                      mouse_y <= self.rect_bg.bottom)
        
        if mouse_over:
            self.current_c_bg = self.c_bg_mo
            self.current_c_fg = self.c_fg_mo
        else:
            self.current_c_bg = self.c_bg
            self.current_c_fg = self.c_fg

        if mouse_down and mouse_over:
            self.current_val = (float(mouse_x) - float(self.rect_bg.left))/self.rect_bg.width
            self.rect_fg.width = self.rect_bg.width * self.current_val
            self.grip_tab.center = (self.rect_fg.right, self.rect_bg.centery)

        return self.current_val

    
    def draw(self):
        # draw background rect
        pygame.draw.rect(self.surface, self.current_c_bg, self.rect_bg)
        # draw foregound rect
        pygame.draw.rect(self.surface, self.current_c_fg, self.rect_fg)
        # draw slider tab
        pygame.draw.rect(self.surface, constants.COLOR_BLACK, self.grip_tab)



# Menus
# 8888ba.88ba
# 88  `8b  `8b
# 88   88   88 .d8888b. 88d888b. dP    dP .d8888b.
# 88   88   88 88ooood8 88'  `88 88    88 Y8ooooo.
# 88   88   88 88.  ... 88    88 88.  .88       88
# dP   dP   dP `88888P' dP    dP `88888P' `88888P'

def menu_main():

    y_offset = 40

    game_initialize()
    global FOV_CALCULATE
    menu_running = True

    title_x = int(constants.CAMERA_WIDTH*0.5)
    title_y = int(constants.CAMERA_HEIGHT*0.5) - y_offset
    title_text = "Python - RL"

    # BUTTON
    button_size = (200, 35)
    continue_button_y = title_y + y_offset
    new_game_button_y = continue_button_y + y_offset
    options_button_y = new_game_button_y + y_offset
    quit_button_y = options_button_y + y_offset

    continue_game_button = ui_Button(
            surface=SURFACE_MAIN, 
            size = button_size, 
            center_coords = (title_x, continue_button_y), 
            button_text = "Continue",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_GREEN,
            color_text_mouseover = constants.COLOR_GREY,
            color_text_default = constants.COLOR_BLACK)
    new_game_button = ui_Button(
            surface=SURFACE_MAIN, 
            size = button_size, 
            center_coords = (title_x, new_game_button_y), 
            button_text = "New Game",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_GREEN,
            color_text_mouseover = constants.COLOR_GREY,
            color_text_default = constants.COLOR_BLACK)
    options_button = ui_Button(
            surface=SURFACE_MAIN, 
            size = button_size, 
            center_coords = (title_x, options_button_y), 
            button_text = "Options",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_GREEN,
            color_text_mouseover = constants.COLOR_GREY,
            color_text_default = constants.COLOR_BLACK)
    quit_button = ui_Button(
            surface=SURFACE_MAIN, 
            size = button_size, 
            center_coords = (title_x, quit_button_y), 
            button_text = "Quit Game",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_GREEN,
            color_text_mouseover = constants.COLOR_GREY,
            color_text_default = constants.COLOR_BLACK)

    pygame.mixer.music.load(ASSETS.music_background)
    pygame.mixer.music.play(-1)
    
    while menu_running:

        list_of_events = pygame.event.get()
        mouse_position = pygame.mouse.get_pos()

        game_input = (list_of_events, mouse_position)

        # handle menu events
        for event in list_of_events:
            if event.type == pygame.QUIT:
                menu_running = False
                break
        if not menu_running:
            break

        if continue_game_button.update(game_input):
            # pygame.mixer.music.stop()
            # FOV_CALCULATE = True
            pygame.mixer.music.fadeout(2000)
            game_ret = game_continue()
            if not game_ret:
                break
            game_initialize()
            pygame.mixer.music.play(-1)
        elif new_game_button.update(game_input):
            # pygame.mixer.music.stop()
            # FOV_CALCULATE = True
            pygame.mixer.music.fadeout(2000)
            game_new()
            game_ret = game_main_loop()
            if not game_ret:
                break
            game_initialize()
            pygame.mixer.music.play(-1)

        elif options_button.update(game_input):
            menu_ret = menu_options()
            if not menu_ret:
                break
        elif quit_button.update(game_input):
            break
        
        # draw menu
        SURFACE_MAIN.blit(ASSETS.I_MAIN_MENU_BG, (0, 0))

        draw_text(display_surface = SURFACE_MAIN,
                text_to_display = title_text,
                T_coords = (title_x, title_y),
                text_font = constants.FONT_TITLE_SCREEN,
                text_color = constants.COLOR_RED,
                back_color=constants.COLOR_BLACK,
                center=True)

        continue_game_button.draw()
        new_game_button.draw()
        options_button.draw()
        quit_button.draw()

        # update surfaces
        pygame.display.update()
    
    pygame.quit()


def menu_options():

    # Menu Vars
    menu_close = False
    settings_menu_width = 200
    settings_menu_height = 200
    settings_menu_bg_color = constants.COLOR_GREY

    window_center = (int(constants.CAMERA_WIDTH*0.5), int(constants.CAMERA_HEIGHT*0.5))

    settings_menu_surface = pygame.Surface(
        (settings_menu_width, settings_menu_height))

    settings_menu_rect = pygame.Rect(
        0, 0, settings_menu_width, settings_menu_height)

    settings_menu_rect.center = window_center

    settings_menu_surface.fill(settings_menu_bg_color)
    
    # SLIDER VARS
    slider_x = settings_menu_rect.centerx
    sound_effect_slider_y = settings_menu_rect.top + 35
    music_slider_y = sound_effect_slider_y + 50

    # SLIDER TEXT VARS
    y_offset_text = 20
    sound_effect_text_y = sound_effect_slider_y - y_offset_text
    music_text_y = music_slider_y - y_offset_text

    # BUTTON VARS
    button_save_y = music_slider_y + 50
    button_font = constants.FONT_DEBUG_MESSAGE

    sound_effect_slider = ui_Slider(
        surface = SURFACE_MAIN, 
        size = (125, 15), 
        center_coords = (slider_x, sound_effect_slider_y),
        c_bg = constants.COLOR_BLACK,
        c_fg = constants.COLOR_GREEN,
        c_bg_mo = constants.COLOR_BLACK,
        c_fg_mo = constants.COLOR_RED,
        parameter_value=PREFERENCES.vol_sound
        )

    music_slider = ui_Slider(
        surface = SURFACE_MAIN, 
        size = (125, 15), 
        center_coords = (slider_x, music_slider_y),
        c_bg = constants.COLOR_BLACK,
        c_fg = constants.COLOR_GREEN,
        c_bg_mo = constants.COLOR_BLACK,
        c_fg_mo = constants.COLOR_RED,
        parameter_value=PREFERENCES.vol_music
        )

    button_save = ui_Button(
            surface = SURFACE_MAIN, 
            size = (70, 20), 
            center_coords = (slider_x, button_save_y), 
            button_text = "Save",
            color_box_mouseover = constants.COLOR_RED,
            color_box_default = constants.COLOR_DGREY,
            color_text_mouseover = constants.COLOR_BLACK,
            color_text_default = constants.COLOR_BLACK)

    while not menu_close:

        list_of_events = pygame.event.get()
        mouse_position = pygame.mouse.get_pos()

        game_input = (list_of_events, mouse_position)

        # handle menu events
        for event in list_of_events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_ESCAPE or
                    event.key == pygame.K_TAB):
                    menu_close = True
            # elif event.type == pygame.MOUSEBUTTONDOWN:

        if menu_close:
            break

        current_sound_vol = PREFERENCES.vol_sound
        current_music_vol = PREFERENCES.vol_music

        sound_effect_slider.update(game_input)
        music_slider.update(game_input)

        if current_sound_vol is not sound_effect_slider.current_val:
            PREFERENCES.vol_sound = sound_effect_slider.current_val
            ASSETS.volume_adjust()
        elif current_music_vol is not music_slider.current_val:
            PREFERENCES.vol_music = music_slider.current_val
            ASSETS.volume_adjust()
        elif button_save.update(game_input):
            preferences_save()
            menu_close = True
            break

        SURFACE_MAIN.blit(settings_menu_surface, settings_menu_rect.topleft)

        draw_text(
            display_surface = SURFACE_MAIN, 
            text_to_display = "SOUND", 
            T_coords = (slider_x, sound_effect_text_y), 
            text_font = constants.FONT_DEBUG_MESSAGE, 
            text_color = constants.COLOR_BLACK, 
            back_color=constants.COLOR_GREY, 
            center=True)
        sound_effect_slider.draw()

        draw_text(
            display_surface = SURFACE_MAIN, 
            text_to_display = "MUSIC", 
            T_coords = (slider_x, music_text_y), 
            text_font = constants.FONT_DEBUG_MESSAGE, 
            text_color = constants.COLOR_BLACK, 
            back_color=constants.COLOR_GREY, 
            center=True)
        music_slider.draw()

        button_save.draw()

        pygame.display.update()

    # preferences_save()
    return menu_close


def menu_pause():
    """ This menu pauses the game and displays a simple message. """
    # return 0

    menu_close = False
    menu_text = "PAUSED"
    menu_font = constants.FONT_DEBUG_MESSAGE

    message_x = constants.CAMERA_WIDTH*0.5
    message_y = constants.CAMERA_HEIGHT*0.5
    text_width = helper_text_width(menu_font, menu_text)
    text_height = helper_text_height(menu_font)
    message_x -= text_width*0.5
    message_y -= text_height*0.5

    while not menu_close:
        events_list = pygame.event.get()
        for event in events_list:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    menu_close = True

        draw_text(SURFACE_MAIN, menu_text,
                  (message_x, message_y),
                  menu_font,
                  constants.COLOR_WHITE,
                  constants.COLOR_BLACK)

        CLOCK.tick(constants.GAME_FPS)

        pygame.display.flip()
    return 'no-action'


def menu_inventory():
    menu_close = False
    item_interact = "use"

    menu_width = 200
    menu_height = 200

    window_width = constants.CAMERA_WIDTH*0.5 - menu_width*0.5
    window_height = constants.CAMERA_HEIGHT*0.5 - menu_height*0.5

    menu_text_font = constants.FONT_MESSAGE_TEXT
    menu_text_height = helper_text_height(menu_text_font)
    menu_text_color = constants.COLOR_WHITE

    local_inventory_surface = pygame.Surface((menu_width, menu_height))

    while not menu_close:

        # Clear the menu.
        local_inventory_surface.fill(constants.COLOR_BLACK)

        # Register changes.

        print_list = [obj.display_name for obj in PLAYER.container.inventory]

        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        mouse_x_rel = mouse_x - window_width
        mouse_y_rel = mouse_y - window_height

        mouse_in_window = (mouse_x_rel > 0 and
                           mouse_y_rel > 0 and
                           mouse_x_rel < menu_width and
                           mouse_y_rel < menu_height)

        if menu_text_height is not 0:
            mouse_line_selection = int(mouse_y_rel / menu_text_height)

        for event in events_list:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    menu_close = True
                if event.key == pygame.K_d:
                    if item_interact == "drop":
                        item_interact = "use"
                    elif item_interact == "use":
                        item_interact = "drop"
                    else:
                        item_interact = "use"
            if event.type == pygame.MOUSEBUTTONDOWN:
                # buttons:
                    # 1 == lmb
                    # 2 = mmb
                    # 3 == rmb
                    # 4 == scroll up
                    # 5 == scroll down
                if event.button == 1:
                    if (mouse_in_window and
                            (mouse_line_selection <= len(print_list) - 1)):
                        if item_interact == "use":
                            ret = PLAYER.container.inventory[mouse_line_selection].item.use(
                            )
                            print(ret)
                            # menu_close = True
                        if item_interact == "drop":
                            if PLAYER.container.inventory[mouse_line_selection].equipment:
                                if PLAYER.container.inventory[mouse_line_selection].equipment.equipped:
                                    PLAYER.container.inventory[mouse_line_selection].equipment.unequip(
                                    )
                            PLAYER.container.inventory[mouse_line_selection].item.drop(
                                PLAYER.x, PLAYER.y)

        # Draw list.
        for line, (name) in enumerate(print_list):
            if line == mouse_line_selection and mouse_in_window:
                if item_interact == "drop":
                    draw_text(local_inventory_surface,
                              name,
                              (0, (line * menu_text_height)),
                              menu_text_font,
                              menu_text_color,
                              constants.COLOR_RED)
                elif item_interact == "use":
                    draw_text(local_inventory_surface,
                              name,
                              (0, (line * menu_text_height)),
                              menu_text_font,
                              menu_text_color,
                              constants.COLOR_GREY)
            else:
                draw_text(local_inventory_surface,
                          name,
                          (0, (line * menu_text_height)),
                          menu_text_font,
                          menu_text_color,
                          constants.COLOR_BLACK)

        # Render game
        draw_game()

        # Display Menu
        SURFACE_MAIN.blit(local_inventory_surface,
                          (window_width, window_height))

        CLOCK.tick(constants.GAME_FPS)
        pygame.display.flip()
    return 'no-action'


def menu_tile_select(coords_origin=None, max_range=None, radius=None,
                     penetrate_walls=True, pierce_creatures=True):
    """  
    This menu lets the player select a tile.

    This function pauses the game, produces an on-screen rectangle, 
    and when the player presses the left mouse button, will return 
    (message for now) the map address. 
    """
    menu_close = False

    while not menu_close:

        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # get button clicks
        events_list = pygame.event.get()

        # mouse map selection

        mapx_pixel, mapy_pixel = CAMERA.win_to_map((mouse_x, mouse_y))

        map_coord_x = int(mapx_pixel / constants.CELL_WIDTH)
        map_coord_y = int(mapy_pixel / constants.CELL_HEIGHT)

        valid_tiles = []

        if coords_origin:
            full_list_tiles = map_find_line(
                coords_origin, (map_coord_x, map_coord_y))

            for i, (x, y) in enumerate(full_list_tiles):

                valid_tiles.append((x, y))

                # stop at max_range
                if max_range and i >= max_range - 1:
                    break

                # stop at wall
                if (not penetrate_walls and
                        GAME.current_map[x][y].block_path):
                    break

                # stop at creature.
                if (not pierce_creatures and
                        map_check_for_creatures(x, y)):
                    break

        else:
            valid_tiles = [(map_coord_x, map_coord_y)]

        # return map_coords when presses left mb
        for event in events_list:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                    menu_close = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # game_message(str( (map_coord_x, map_coord_y) ) )
                    return valid_tiles[-1]

        # draw game first
        SURFACE_MAIN.fill(constants.COLOR_DEFAULT_BG)
        SURFACE_MAP.fill(constants.COLOR_BLACK)

        CAMERA.update(PLAYER)

        # display_rect = pygame.Rect(
        #     (0 * constants.CELL_WIDTH, 0 * constants.CELL_HEIGHT), 
        #     (constants.CAMERA_WIDTH, constants.CAMERA_HEIGHT))

        # draw the map
        draw_map(GAME.current_map)

        # draw all objects
        for obj in sorted(GAME.current_objects, key = lambda obj: obj.depth, reverse = True):
            obj.draw()

        # draw rectangle at mouse position on top of game
        for (tile_x, tile_y) in valid_tiles:
            if not(tile_x, tile_y) == valid_tiles[-1]:
                draw_tile_rect((tile_x, tile_y))
            else:
                draw_tile_rect((tile_x, tile_y), mark='X')
        if radius:
            area_effect = map_find_radius(valid_tiles[-1], radius)
            for tile_x, tile_y in area_effect:
                draw_tile_rect((tile_x, tile_y),
                               tile_color=constants.COLOR_RED)

        SURFACE_MAIN.blit(SURFACE_MAP, (0, 0), CAMERA.rect)

        draw_messages()
        draw_debug()

        # update the display
        pygame.display.flip()

        # tick the CLOCK
        CLOCK.tick(constants.GAME_FPS)
    return 'no-action'


# Generators
#  .88888.                                                 dP
# d8'   `88                                                88
# 88        .d8888b. 88d888b. .d8888b. 88d888b. .d8888b. d8888P .d8888b. 88d888b. .d8888b.
# 88   YP88 88ooood8 88'  `88 88ooood8 88'  `88 88'  `88   88   88'  `88 88'  `88 Y8ooooo.
# Y8.   .88 88.  ... 88    88 88.  ... 88       88.  .88   88   88.  .88 88             88
#  `88888'  `88888P' dP    dP `88888P' dP       `88888P8   dP   `88888P' dP       `88888P'

# PLAYER
def gen_player(coords):
    # create the player
    x, y = coords
    container_com = com_Container(volume=10.0, inventory=[])
    creature_com = com_Creature(
        "greg", 
        base_atk=4,
        death_function=death_player
        )
    player = obj_Actor(x, y, "python",
                       animation_key="A_PLAYER",
                       animation_speed=1.0,
                       depth = constants.DEPTH_PLAYER, 
                       creature=creature_com,
                       container=container_com)
    return player


# SPECIAL

def gen_stairs(coords, downwards = True):
    x, y = coords

    if downwards:
        stairs_com = com_Stairs(downwards) 
        stairs = obj_Actor(x, y, "stairs", 
            animation_key = "S_STAIRS_DOWN",
            depth=constants.DEPTH_BKGD,
            stairs = stairs_com)
    else:
        stairs_com = com_Stairs(downwards) 
        stairs = obj_Actor(x, y, "stairs", 
            animation_key = "S_STAIRS_UP",
            depth=constants.DEPTH_BKGD,
            stairs = stairs_com)

    GAME.current_objects.append(stairs)


def gen_portal(coords):
    x, y = coords

    portal_com = com_ExitPortal() 
    portal = obj_Actor(x, y, "exit portal",
        animation_key = "S_PORTAL_CLOSED",
        animation_speed=0.2,
        depth=constants.DEPTH_BKGD,
        state="CLOSED",
        exitportal= portal_com)

    GAME.current_objects.append(portal)


def gen_LAMP(coords):
    x, y = coords

    item_com = com_Item()

    return_object = obj_Actor(x, y, "THE LAMP",
                              animation_key="S_MAGIC_LAMP",
                              depth = constants.DEPTH_ITEM, 
                              item=item_com)

    GAME.current_objects.append(return_object)


# ITEMS
def gen_item(coords):
    random_num = tcod.random_get_int(RAND_INSTANCE, 1, 5)
    new_item = None

    if (random_num == 1):
        new_item = gen_scroll_lightning(coords)
    elif (random_num == 2):
        new_item = gen_scroll_fireball(coords)
    elif (random_num == 3):
        new_item = gen_scroll_confusion(coords)
    elif (random_num == 4):
        new_item = gen_weapon_sword(coords)
    elif (random_num == 5):
        new_item = gen_armor_shield(coords)
    else:
        new_item = gen_scroll_confusion(coords)

    GAME.current_objects.append(new_item)


def gen_scroll_lightning(coords):
    x, y = coords

    damage = tcod.random_get_int(RAND_INSTANCE, 5, 7)
    m_range = tcod.random_get_int(RAND_INSTANCE, 7, 8)

    item_com = com_Item(use_function=cast_lightning, value=(damage, m_range))

    return_object = obj_Actor(x, y, "lightning scroll",
                              animation_key="S_SCROLL_YELLOW",
                              depth = constants.DEPTH_ITEM, 
                              item=item_com)

    return return_object


def gen_scroll_fireball(coords):
    x, y = coords

    damage = tcod.random_get_int(RAND_INSTANCE, 2, 4)
    radius = tcod.random_get_int(RAND_INSTANCE, 1, 2)
    m_range = tcod.random_get_int(RAND_INSTANCE, 9, 12)

    item_com = com_Item(use_function=cast_fireball,
                        value=(damage, radius, m_range))

    return_object = obj_Actor(x, y, "fireball scroll",
                              animation_key="S_SCROLL_RED",
                              depth = constants.DEPTH_ITEM,
                              item=item_com)

    return return_object


def gen_scroll_confusion(coords):
    x, y = coords

    effect_length = tcod.random_get_int(RAND_INSTANCE, 5, 10)

    item_com = com_Item(use_function=cast_confusion,
                        value=effect_length)

    return_object = obj_Actor(x, y, "confusion scroll",
                              animation_key="S_SCROLL_BLANK",
                              depth = constants.DEPTH_ITEM,
                              item=item_com)

    return return_object


def gen_weapon_sword(coords):
    x, y = coords

    bonus = tcod.random_get_int(RAND_INSTANCE, 1, 2)

    equipment_com = com_Equipment(attack_bonus=bonus, slot="hand_right")

    return_object = obj_Actor(x, y,
                              "sword",
                              animation_key="S_SWORD",
                              depth = constants.DEPTH_ITEM,
                              equipment=equipment_com)
    return return_object


def gen_armor_shield(coords):
    x, y = coords

    bonus = tcod.random_get_int(RAND_INSTANCE, 1, 2)

    equipment_com = com_Equipment(defense_bonus=bonus, slot="hand_left")

    return_object = obj_Actor(x, y,
                              "shield",
                              animation_key="S_SHIELD",
                              depth = constants.DEPTH_ITEM,
                              equipment=equipment_com)
    return return_object


# ENEMIES
def gen_enemy(coords):
    random_num = tcod.random_get_int(RAND_INSTANCE, 1, 100)
    new_enemy = None

    if (random_num <= 15):
        new_enemy = gen_snake_cobra(coords)
    elif (random_num <= 50):
        new_enemy = gen_mouse(coords)
    else:
        new_enemy = gen_snake_anaconda(coords)

    GAME.current_objects.append(new_enemy)


def gen_snake_anaconda(coords):
    # create an enemy
    x, y = coords

    max_health = tcod.random_get_int(RAND_INSTANCE, 5, 10)
    base_attack = tcod.random_get_int(RAND_INSTANCE, 1, 3)
    base_defense = 0 #tcod.random_get_int(RAND_INSTANCE, 0, 1)

    generated_name = tcod.namegen_generate("Celtic female")

    # item_com1 = com_Item(value=4, use_function=cast_heal)
    creature_com = com_Creature(generated_name, 
                                base_atk=base_attack, 
                                base_def=base_defense, 
                                hp=max_health,
                                death_function=death_snake)
    ai_com = ai_Chase()
    snake = obj_Actor(x, y, "anaconda",
                      animation_key="A_SNAKE_01",
                      animation_speed=1.0,
                      depth = constants.DEPTH_CREATURE,
                      creature=creature_com,
                      ai=ai_com)

    return snake


def gen_snake_cobra(coords):
    # create an enemy
    x, y = coords

    max_health = tcod.random_get_int(RAND_INSTANCE, 15, 20)
    base_attack = tcod.random_get_int(RAND_INSTANCE, 3, 6)
    base_defense = 0 #tcod.random_get_int(RAND_INSTANCE, 0, 1)

    generated_name = tcod.namegen_generate("Celtic male")


    # item_com1 = com_Item(value=4, use_function=cast_heal)
    creature_com = com_Creature(generated_name, 
                                base_atk=base_attack, 
                                base_def=base_defense, 
                                hp=max_health,
                                death_function=death_snake)
    ai_com = ai_Chase()
    cobra = obj_Actor(x, y, "cobra",
                      animation_key="A_SNAKE_02",
                      animation_speed=1.0,
                      depth = constants.DEPTH_CREATURE,
                      creature=creature_com,
                      ai=ai_com)

    return cobra


def gen_mouse(coords):
    # create an enemy
    x, y = coords

    max_health = 1
    base_attack = 0
    base_defense = 0 #tcod.random_get_int(RAND_INSTANCE, 0, 1)

    generated_name = tcod.namegen_generate("Celtic male")


    # item_com1 = com_Item(value=4, use_function=cast_heal)
    creature_com = com_Creature(generated_name, 
                                base_atk=base_attack, 
                                base_def=base_defense, 
                                hp=max_health,
                                death_function=death_mouse)
    ai_com = ai_Flee()

    item_com = com_Item(use_function = cast_heal, 
        value=2)
    mouse = obj_Actor(x, y, "mouse",
                      animation_key="A_MOUSE",
                      animation_speed=1.0,
                      depth = constants.DEPTH_CREATURE,
                      creature=creature_com,
                      item=item_com,
                      ai=ai_com)

    return mouse



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
            return game_exit()
            # break
        # turn-based system
        for obj in GAME.current_objects:
            if obj.ai:
                if player_action != "no-action":
                    obj.ai.take_turn()
            if obj.exitportal:
                obj.exitportal.update()

        if PLAYER.state is "STATUS_DEAD":
            game_quit = True

        # draw the game
        draw_game()

        # update the display
        pygame.display.flip()

        CLOCK.tick(constants.GAME_FPS)

    return game_quit


def game_initialize():
    ''' This function initializes the main window and pygame'''

    global PREFERENCES, SURFACE_MAIN, SURFACE_MAP, CAMERA, RAND_INSTANCE, CLOCK
    global ASSETS, FOV_CALCULATE

    # initialize pygame
    pygame.init()

    pygame.key.set_repeat(200, 70)

    try:
        preferences_load()
    except:
        PREFERENCES = struc_Preferences()

    tcod.namegen_parse("data/namegen/jice_celtic.cfg")
    # tcod.namegen_parse("data/namegen/jice_fantasy.cfg")
    # tcod.namegen_parse("data/namegen/jice_mesopotamian.cfg")

    SURFACE_MAIN = pygame.display.set_mode((constants.CAMERA_WIDTH, 
                                           constants.CAMERA_HEIGHT))

    SURFACE_MAP = pygame.Surface((constants.MAP_WIDTH*constants.CELL_WIDTH,
                                 constants.MAP_HEIGHT*constants.CELL_HEIGHT))

    CAMERA = obj_Camera()

    RAND_INSTANCE = None  # tcod.random_new_from_seed(1000)

    CLOCK = pygame.time.Clock()

    ASSETS = obj_Assets()

    FOV_CALCULATE = True


def game_handle_keys():
    global FOV_CALCULATE
    # get player input
    keys_list = pygame.key.get_pressed()
    events_list = pygame.event.get()

    # Check for mod key
    MOD_KEY = (keys_list[pygame.K_RSHIFT] or 
               keys_list[pygame.K_LSHIFT])

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
            if event.key == pygame.K_g:
                objects_at_player = map_objects_at_coords(PLAYER.x, PLAYER.y)
                for obj in objects_at_player:
                    if obj.item:
                        obj.item.pick_up(PLAYER)
            if event.key == pygame.K_d:
                if len(PLAYER.container.inventory) > 0:
                    PLAYER.container.inventory[-1].item.drop(
                        PLAYER.x, PLAYER.y)
            if event.key == pygame.K_p:
                return menu_pause()
            if event.key == pygame.K_i:
                return menu_inventory()
            if event.key == pygame.K_l:
                # return menu_tile_select()
                return cast_lightning(PLAYER)
            if event.key == pygame.K_f:
                return cast_fireball(PLAYER)
            if event.key == pygame.K_c:
                return cast_confusion(PLAYER)
            if MOD_KEY and event.key == pygame.K_PERIOD:
                list_of_objs = map_objects_at_coords(PLAYER.x, PLAYER.y)
                for obj in list_of_objs:
                    if obj.stairs:
                        obj.stairs.use()
            # if event.key == pygame.K_SPACE:
            #     GAME.transition_next()
            #     # PLAYER.x, PLAYER.y = GAME.current_rooms[0].center
            # if event.key == pygame.K_o:
            #     GAME.transition_previous()

    return "no-action"


def game_message(game_msg, msg_color=constants.COLOR_GREY):
    GAME.message_history.append((game_msg, msg_color))
    print(game_msg)


def game_new():

    global GAME, PLAYER
    
    GAME = obj_Game()

    PLAYER = gen_player(GAME.current_rooms[0].center)
    GAME.current_objects.append(PLAYER)

    map_place_objects(GAME.current_rooms)

    # map_make_fov(GAME.current_map)


def game_exit():

    game_save()

    # quit the game
    pygame.quit()
    # exit()
    return False


def game_save():
    global GAME, PLAYER

    for obj in GAME.current_objects:
        obj.animation_destroy()
        if obj.container:
            for objec in obj.container.inventory:
                objec.animation_destroy()

    with gzip.open("data/savedata/savegame", "wb") as file:
        pickle.dump([GAME, PLAYER], file)


def game_load():
    global GAME, PLAYER

    with gzip.open('data/savedata/savegame', 'rb') as file:
        GAME, PLAYER = pickle.load(file)

    for obj in GAME.current_objects:
        obj.animation_init()
        if obj.container:
            for objec in obj.container.inventory:
                objec.animation_init()
    # for obj in PLAYER.container.inventory:
    #     obj.animation_init()
        

    map_make_fov(GAME.current_map)


def game_continue():
    try:
        game_load()
    except:
        game_new()

    return game_main_loop()


def preferences_save():
    global PREFERENCES
    with gzip.open("data/pref/preferences", "wb") as file:
        pickle.dump(PREFERENCES, file)


def preferences_load():
    global PREFERENCES
    with gzip.open('data/pref/preferences', 'rb') as file:
        PREFERENCES = pickle.load(file)


# Execution
#  88888888b                                       dP   oo
#  88                                              88
# a88aaaa    dP.  .dP .d8888b. .d8888b. dP    dP d8888P dP .d8888b. 88d888b.
#  88         `8bd8'  88ooood8 88'  `"" 88    88   88   88 88'  `88 88'  `88
#  88         .d88b.  88.  ... 88.  ... 88.  .88   88   88 88.  .88 88    88
#  88888888P dP'  `dP `88888P' `88888P' `88888P'   dP   dP `88888P' dP    dP


if __name__ == '__main__':
    menu_main()


#  88888888b 888888ba  888888ba
#  88        88    `8b 88    `8b
# a88aaaa    88     88 88     88
#  88        88     88 88     88
#  88        88     88 88    .8P
#  88888888P dP     dP 8888888P
