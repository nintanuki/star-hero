SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FRAMERATE = 120

POWERUP_DATA = {
    'green':  {'draw_color': (60, 255, 100),  'type': 'twin_laser',  'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60),  'type': 'fast_fire',   'shape': 'circle', 'cooldown': 200},
    'blue':   {'draw_color': (80, 160, 255),  'type': 'extreme_fire','shape': 'circle', 'cooldown': 60},
}

DROP_CHANCES = {
    'red': 0.00,
    'green': 0.20,
    'yellow': 0.15,
    'blue': 0.10,
}