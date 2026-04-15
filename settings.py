# Window & Display Settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FRAMERATE = 120

# Font Settings
UT_FONT = 'font/Pixeled.ttf'
FONT_SIZE_SMALL = 10
FONT_SIZE_MEDIUM = 20
FONT_SIZE_LARGE = 30

# Background
BG_SCROLL_SPEED = 50

# Player Settings
SCREEN_CENTER = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
PLAYER_SPEED = 2
PLAYER_ROTATION = 0
PLAYER_SCALE = 0.15
DEFAULT_LASER_COOLDOWN = 600 # lower numbers = faster rate of fire
RAPID_FIRE_DURATION = 10000 # 10000 milliseconds = 10 seconds
BEAM_DURATION = 5000        # 5 seconds (shorter than rapid fire)
PLAYER_FLASH_DURATION = 500 # Total time to flash in milliseconds
PLAYER_FLASH_INTERVAL = 50 # How fast it toggles (smaller = faster flicker)
PLAYER_DEATH_DELAY = 500

JOYSTICK_DEADZONE = 0.2

# Alien Settings
ALIEN_SPAWN_OFFSET = (-300, -100)
ALIEN_SPAWN_RATE = 600 # lower numbers = faster rate of enemy spawn
ALIEN_LASER_RATE = 400 # lower numbers = more lasers
ALIEN_DESCEND_SPEED_RED = 1
ALIEN_DESCEND_SPEED_GREEN = 2
ALIEN_DESCEND_SPEED_YELLOW = 3
ZIGZAG_THRESHOLD = 100
ALIEN_DESCEND_SPEED_BLUE = 5

ALIEN_TYPES = ['red', 'green', 'yellow', 'blue']
ALIEN_WEIGHTS = [50, 30, 15, 5] # probability of each color alien appearing

# Laser Settings
DEFAULT_LASER_WIDTH = 4
BEAM_LASER_WIDTH = 12
LASER_HEIGHT = 20
PLAYER_LASER_SPEED = -8
ALIEN_LASER_SPEED = 4

# Visual Effects
EXPLOSION_FRAMES = 7 # there are seven unique images in the explosion sprite sheet
EXPLOSION_SPEED = 0.15 # smaller numbers = slower explosion animation. Always 0.x
EXPLOSION_SIZE = 192 # size of each frame in the spritesheet, definse both width and height
EXPLOSION_SCALE = 0.5

# UI Settings
BG_COLOR = (30, 30, 30) # Not visibile since we are using a scrolling image
HEART_SPRITE_SIZE = (24, 24)
HEART_SPACING = 10
HEART_TOP_MARGIN = 8
VOLUME_DISPLAY_TIME = 1000
CRT_ALPHA_RANGE = (75, 90) # can't pass this into animations, not used

# Powerup Visuals
POWERUP_RADIUS = 12
POWERUP_SPEED = 2 # how fast the powerup floats down?
POWERUP_FLASH_SPEED = 200 # 200 milliseconds .2 seconds?

# Audio Mix (Master offsets)
INTRO_VOL_BOOST = 2.0
DEFAULT_MASTER_VOLUME = 0.5 # default value is 1.0

# Dictionaries

LASER_COLORS = {
    'standard': ('green', 'white'),
    'rapid':    ('yellow', 'white'),
    'alien':    ('red', 'white'),
    'beam':     ('cyan', 'white')
}

POWERUP_DATA = {
    'red':    {'draw_color': (255, 80, 80),  'type': 'heal',       'shape': 'heart'},
    'green':  {'draw_color': (60, 255, 100), 'type': 'twin_laser', 'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60), 'type': 'rapid_fire', 'shape': 'circle', 'cooldown': 150},
    'blue':   {'draw_color': (80, 160, 255), 'type': 'beam',       'shape': 'circle', 'cooldown': 0},
}

DROP_CHANCES = {
    'red': 0.20,
    'green': 0.20,
    'yellow': 0.15,
    'blue': 0.25,
}

# Scoring
ALIEN_VALUES = {
    'red': 100,
    'green': 200,
    'yellow': 300,
    'blue': 500
}