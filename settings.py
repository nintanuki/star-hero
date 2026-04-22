class ScreenSettings:
    """Holds all the settings related to the game screen, such as dimensions, frame rate, background color, and other visual parameters."""
    WIDTH = 600
    HEIGHT = 800
    RESOLUTION = (WIDTH,HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120
    BG_COLOR = (30, 30, 30) # Not visibile since we are using a scrolling image
    CRT_ALPHA_RANGE = (75, 90)
    DEFAULT_BG_SCROLL_SPEED = 50
    BG_SCROLL_STEP = 25 # how many pixels the background moves each difficulty step (lower = smoother, higher = more noticeable)
    BG_SCROLL_MAX = 500 # maximum scroll speed for the background, to prevent it from becoming too fast at high scores

class PlayerSettings:
    """Contains all the settings related to the player, including movement speed, rotation, scale, laser cooldowns, and other gameplay parameters."""
    MAX_HEALTH = 3
    SPEED = 2
    SPEED_BOOST = 2
    BRAKE_WORLD_SPEED_MULT = 0.45
    BOOST_DRAIN_PER_SECOND = 0.35 # meter drained per second while boost is held
    BOOST_RECHARGE_PER_SECOND = 0.25 # meter recharged per second when not boosting
    SCALE = 0.15
    DEFAULT_LASER_COOLDOWN = 600 # lower numbers = faster rate of fire
    RAPID_FIRE_TIER_1_COOLDOWN = DEFAULT_LASER_COOLDOWN / 2
    RAPID_FIRE_TIER_2_COOLDOWN = 150
    SHIELD_DURATION = 7000 # how long the shield lasts in milliseconds
    RAINBOW_BEAM_DURATION = 5000        # 5 seconds (shorter than rapid fire)
    DEATH_DELAY = 500
    FLASH_DURATION = 1000 # Total time to flash in milliseconds
    FLASH_INTERVAL = 50 # How fast it toggles (smaller = faster flicker)
    JOYSTICK_DEADZONE = 0.2
    CONFUSION_TIMEOUT = 4000 # how long the confusion effect lasts after being hit by a blue alien attack (in milliseconds)

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

    DIFFICULTY_STEP = 5000 # Increase difficulty every x amount of points

    SPAWN_OFFSET = (-300, -100)
    COLOR = ['red', 'green', 'yellow', 'blue']
    SPAWN_CHANCE = [50, 30, 15, 5] # probability of each color alien appearing
    ANIMATION_SPEED = 0.015  # higher is faster, lower is slower

    # Movement speeds for each alien color (how fast each alien moves down the screen)
    SPEED = {
        'red':    1,
        'green':  2,
        'yellow': 3,
        'blue':   5
        }
    
    ZIGZAG_THRESHOLD = 100 # how wide the zigzag pattern is for yellow aliens (in pixels)

    # Point values for each alien color
    POINTS = {
        'red':    100,
        'green':  200,
        'yellow': 300,
        'blue':   500
        }

    # Probability of each alien dropping a powerup upon destruction, by color
    DROP_CHANCE = {
        'red':    0.25,
        'green':  0.20,
        'yellow': 0.15,
        'blue':   0.10,
        }
    RED_SHIELD_DROP_CHANCE = 0.05
    
    # Blue alien confusion attack settings
    CONFUSION_CHANCE = 0.1 # chance that a blue alien will trigger the confusion attack
    CONFUSION_STOP_Y = ScreenSettings.HEIGHT // 2 # Halfway down screen
    CONFUSION_DURATION = 3000 # How long the alien stays to project it's confusion attack (in milliseconds)

class LaserSettings:
    """Contains all the settings related to lasers fired by both the player and aliens, including dimensions, speeds, and colors for different laser types."""
    DEFAULT_WIDTH = 4
    HEIGHT = 20
    PLAYER_LASER_SPEED = -8
    ALIEN_LASER_SPEED = 4
    COLORS = {
        'single': ('green', 'white'),
        'twin': ('green', 'white'),
        'hyper': ('cyan', 'white'), # Hyper
        'rapid': ('yellow', 'white'), # Rapid (any tier)
        'hyper_rapid': ('cyan', 'yellow'), # Hyper + Rapid alternation
        'alien': ('red', 'white'),
        'rainbow': None 
    }

    # Rainbow Beam Settings
    RAINBOW_BEAM_WIDTH = ScreenSettings.WIDTH
    RAINBOW_BEAM_GROWTH_SPEED = 5 # Pixels added per frame
    RAINBOW_HUE_STEP = 4
    RAINBOW_SEGMENTS = 5
    # Divide the laser into 5 vertical segments for a "flow" effect
    SEGMENT_HEIGHT = HEIGHT // RAINBOW_SEGMENTS
    RAINBOW_SEGMENT_SHIFT = 20

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
    'red_shield': {'draw_color': (80, 255, 255), 'type': 'shield', 'shape': 'circle'},
    'green':  {'draw_color': (60, 255, 100), 'type': 'laser_upgrade', 'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60), 'type': 'rapid_fire', 'shape': 'diamond'},
    'blue':   {'draw_color': (80, 160, 255), 'type': 'rainbow_beam', 'shape': 'diamond'},
    }

class ExplosionSettings:
    """
    Contains all the settings related to explosion animations,
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
    DEFAULT_INITIALS = "AAA"

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

    # Volume Bar Settings
    MAX_VOLUME = 1000
    VOLUME_BAR__LENGTH = 150
    VOLUME_BAR_RATIO = MAX_VOLUME / VOLUME_BAR__LENGTH

class AudioSettings:
    """
    Defines settings related to audio in the game,
    including the volume boost applied during the intro sequence
    and the default master volume level for all sounds.
    """
    INTRO_VOL_BOOST = 2.0
    DEFAULT_MASTER_VOLUME = 0.5 # default value is 1.0
    DEBUG_MUTE = False # set True to silence all audio for debugging
    MUSIC_DIR = 'music/'
    AUDIO_DIR = 'audio/'
    BGM_PLAYLIST = [
        'star_fox_64_katina.mp3',
        # 'star_fox_64_meteo.mp3',
        # 'star_fox_64_sector_x.mp3',
        # 'star_fox_64_solar_and_sector_y.mp3',
        # 'star_fox_64_titania_and_macbeth.mp3',
        # 'star_fox_snes_corneria.mp3',
        # 'star_fox_snes_meteor.mp3',
        'Area 6 - Star Fox 64 Restored OST.mp3',
        'star_fox_snes_space_armada.mp3',
        # 'star_fox_snes_venom_asteroid_venom_orbital.mp3',
        'star_hero.mp3'
    ]

class AssetPaths:
    GRAPHICS_DIR = 'graphics/'
    BACKGROUND = 'graphics/background.png'
    EXPLOSION = 'graphics/explosion.png'
    PLAYER = 'graphics/player_ship.png'
    HEART = 'graphics/heart.png'
    TV = 'graphics/tv.png'
