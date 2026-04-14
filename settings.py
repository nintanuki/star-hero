
# Window & Display Settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FRAMERATE = 120

# Background
BG_SCROLL_SPEED = 50

# Player Settings
SCREEN_CENTER = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
PLAYER_SPEED = 2
PLAYER_ROTATION = 0
PLAYER_SCALE = 0.15
PLAYER_LASER_SPEED = -8
DEFAULT_LASER_COOLDOWN = 600 # lower numbers = faster rate of fire
POWERUP_DURATION = 10000 # 10000 milliseconds = 10 seconds

# Alien Settings
ALIEN_SPAWN_RATE = 600 # lower numbers = faster rate of enemy spawn
ALIEN_LASER_RATE = 400 # lower numbers = more lasers
ALIEN_LASER_SPEED = 4
ALIEN_DESCEND_SPEED_RED = 1
ALIEN_DESCEND_SPEED_GREEN = 2
ALIEN_DESCEND_SPEED_YELLOW = 3
ALIEN_DESCEND_SPEED_BLUE = 5

ALIEN_TYPES = ['red','red','red','red','red',
'green','green','green',
'yellow','yellow',
'blue']

# Visual Effects
CRT_ALPHA_RANGE = (75, 90)
EXPLOSION_SPEED = 0.15 # smaller numbers = slower explosion animation. Always 0.x
EXPLOSION_SCALE = 0.5

# Powerup Visuals
POWERUP_RADIUS = 12
POWERUP_SPEED = 2
POWERUP_FLASH_SPEED = 200

POWERUP_DATA = {
    'red':    {'draw_color': (255, 80, 80),   'type': 'heal', 'shape': 'heart'},
    'green':  {'draw_color': (60, 255, 100),  'type': 'twin_laser',  'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60),  'type': 'fast_fire',   'shape': 'circle', 'cooldown': 200},
    'blue':   {'draw_color': (80, 160, 255),  'type': 'extreme_fire','shape': 'circle', 'cooldown': 60},
}

DROP_CHANCES = {
    'red': 0.20,
    'green': 0.20,
    'yellow': 0.15,
    'blue': 0.10,
}