class ScreenSettings:
    """Holds all the settings related to the game screen, such as dimensions, frame rate, background color, and other visual parameters."""
    WIDTH = 600
    HEIGHT = 800
    RESOLUTION = (WIDTH,HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120
    BG_COLOR = (30, 30, 30) # Not visibile since we are using a scrolling image
    CRT_ALPHA_RANGE = (75, 90)
    BG_SCROLL_SPEED = 50

class PlayerSettings:
    """Contains all the settings related to the player, including movement speed, rotation, scale, laser cooldowns, and other gameplay parameters."""
    SPEED = 2
    ROTATION = 0 # Is this ever even used?
    SCALE = 0.15
    DEFAULT_LASER_COOLDOWN = 600 # lower numbers = faster rate of fire
    RAPID_FIRE_DURATION = 10000 # 10000 milliseconds = 10 seconds
    BEAM_DURATION = 5000        # 5 seconds (shorter than rapid fire)
    DEATH_DELAY = 500
    FLASH_DURATION = 1000 # Total time to flash in milliseconds
    FLASH_INTERVAL = 50 # How fast it toggles (smaller = faster flicker)
    JOYSTICK_DEADZONE = 0.2

class AlienSettings:
    """
    Defines all the settings related to the alien enemies,
    including spawn rates, movement speeds, point values, colors,
    and probabilities for spawning and dropping powerups.
    """
    SPAWN_RATE = 600 # lower numbers = faster rate of enemy spawn
    MIN_SPAWN_RATE = 150  # Hard limit on how fast they spawn

    LASER_RATE = 400 # lower numbers = more lasers
    MIN_LASER_RATE = 100  # Hard limit on how fast they shoot

    DIFFICULTY_STEP = 10000 # Increase difficulty every 10000 points

    SPAWN_OFFSET = (-300, -100)
    ZIGZAG_THRESHOLD = 100
    SPEED = {'red': 1, 'green': 2, 'yellow': 3, 'blue': 5} # How fast each alien descends
    POINTS = {'red': 100, 'green': 200, 'yellow': 300, 'blue': 500}
    COLOR = ['red', 'green', 'yellow', 'blue']
    SPAWN_CHANCE = [50, 30, 15, 5] # probability of each color alien appearing
    DROP_CHANCE = {'red': 0.20, 'green': 0.20, 'yellow': 0.15, 'blue': 0.25,} # Probability of each alien dropping a powerup

class LaserSettings:
    """Contains all the settings related to lasers fired by both the player and aliens, including dimensions, speeds, and colors for different laser types."""
    DEFAULT_WIDTH = 4
    BEAM_WIDTH = ScreenSettings.WIDTH
    HEIGHT = 20
    PLAYER_LASER_SPEED = -8
    ALIEN_LASER_SPEED = 4
    COLORS = {
        'standard': ('green', 'white'), 
        'rapid': ('yellow', 'white'), 
        'alien': ('red', 'white'), 
        'beam': ('cyan', 'white')
    }

class PowerupSettings:
    """
    Defines all the settings related to powerups that the player can collect,
    including their size, movement speed, flashing animation speed,
    and the different types of powerups with their associated colors, effects, and shapes.
    """
    RADIUS = 12
    SPEED = 2 # how fast the powerup floats down?
    FLASH_SPEED = 200 # 200 milliseconds .2 seconds?

    DATA = {
    'red':    {'draw_color': (255, 80, 80),  'type': 'heal',       'shape': 'heart'},
    'green':  {'draw_color': (60, 255, 100), 'type': 'twin_laser', 'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60), 'type': 'rapid_fire', 'shape': 'circle', 'cooldown': 150},
    'blue':   {'draw_color': (80, 160, 255), 'type': 'beam',       'shape': 'circle', 'cooldown': 0},
    }

class ExplosionSettings:
    """
    ontains all the settings related to explosion animations,
    including the number of frames in the sprite sheet, animation speed,
    size of each frame, and scale for rendering.
    """
    FRAMES = 7 # there are seven unique images in the explosion sprite sheet
    ANIMATION_SPEED = 0.15 # smaller numbers = slower explosion animation. Always 0.x
    SIZE = 192 # size of each frame in the spritesheet, definse both width and height
    SCALE = 0.5

class FontSettings:
    """
    Defines the settings related to fonts used in the game,
    including the path to the font file, sizes for different text elements,
    and the color of the text.
    """
    FONT = 'font/Pixeled.ttf'
    SMALL = 10
    MEDIUM = 20
    LARGE = 30
    COLOR = 'white'

class UISettings:
    """
    Contains settings related to the user interface elements,
    such as the size and spacing of heart sprites for health display,
    and the duration for which volume changes are displayed on the screen.
    """
    HEART_SPRITE_SIZE = (24, 24)
    HEART_SPACING = 10
    HEART_TOP_MARGIN = 8
    VOLUME_DISPLAY_TIME = 1000

class AudioSettings:
    """
    Defines settings related to audio in the game,
    including the volume boost applied during the intro sequence
    and the default master volume level for all sounds.
    """
    INTRO_VOL_BOOST = 2.0
    DEFAULT_MASTER_VOLUME = 0.5 # default value is 1.0