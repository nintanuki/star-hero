import pygame
import random
from settings import *

# see https://www.youtube.com/watch?v=VUFvY349ess for more details
class Background(pygame.sprite.Sprite):
    """Creates a scrolling space themed background"""
    def __init__(self,groups):
        """
        Initializes the background by loading a space-themed image,
        creating a surface that is twice the height of the original image for seamless scrolling,
        and setting the initial position of the background.
        """
        super().__init__(groups)
        bg_image = pygame.image.load('graphics/background.png').convert()
        full_height = bg_image.get_height()
        full_width = bg_image.get_width()
        self.image = pygame.Surface((full_width,full_height * 2))

        self.image.blit(bg_image,(0,0))
        self.image.blit(bg_image,(0,full_height))

        self.rect = self.image.get_rect(bottomleft = (0,ScreenSettings.HEIGHT))
        self.pos = pygame.math.Vector2(self.rect.bottomleft)

    def update(self,delta_time):
        """
        Updates the position of the background to create a scrolling effect
        by moving it downwards based on the defined scroll speed and the time elapsed
        since the last update, and resets its position when it has scrolled completely.
        """
        self.pos.y += ScreenSettings.BG_SCROLL_SPEED * delta_time
        if self.rect.top >= 0:
            self.pos.y = -self.image.get_height() / 2
        self.rect.y = round(self.pos.y)

class Explosion(pygame.sprite.Sprite):
    """Creates an explosion animation"""
    def __init__(self, pos_x, pos_y):
        """
        Initializes the explosion animation by loading a sprite sheet,
        extracting individual frames, and setting the initial position of the explosion.
        """
        super().__init__()
        self.is_animating = False
        
        # sprite sheet from https://www.pngwing.com/en/free-png-xiyem/
        sprite_sheet = pygame.image.load('graphics/explosion.png').convert_alpha()

        # Using list comprehension to build the explosion animation fromt he sprite sheet
        self.sprites = [self.get_image(sprite_sheet, frame, ExplosionSettings.SIZE, ExplosionSettings.SIZE, ExplosionSettings.SCALE) for frame in range(ExplosionSettings.FRAMES)]

        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]

        self.rect = self.image.get_rect(center = (pos_x, pos_y))

    # see sprite sheet tutorials by Coding With Russ:
    # https://www.youtube.com/watch?v=M6e3_8LHc7A
    # https://www.youtube.com/watch?v=M6e3_8LHc7A 
    @staticmethod # use static method because it does not use the self argument
    def get_image(sheet, frame, width ,height, scale):
        """Extracts a single frame from a sprite sheet and scales it to the desired size."""
        surf = pygame.Surface((width,height), pygame.SRCALPHA) # pygame.SRCALPHA gives the surface per-pixel-transparency
        surf.blit(sheet,(0,0),((frame*width),0,width,height))
        surf = pygame.transform.scale(surf, (width * scale, height * scale))
        return surf

    def explode(self):
        """Starts the explosion animation by resetting the current sprite index and setting the is_animating flag to True."""
        self.is_animating = True

    def update(self, speed):
        """
        Updates the explosion animation by advancing the current sprite index based on the animation speed,
        and kills the sprite when the animation is complete.
        """
        if self.is_animating == True:
            self.current_sprite += speed
            if int(self.current_sprite) >= len(self.sprites):
                self.kill()
            else:
                self.image = self.sprites[int(self.current_sprite)]

class CRT:
    """Creates a CRT monitor effect"""
    def __init__(self,screen):
        """
        Initializes the CRT effect by loading a TV overlay image,
        scaling it to fit the screen,
        and storing a reference to the screen for drawing.
        """
        super().__init__()
        self.screen = screen
        self.tv = pygame.image.load('graphics/tv.png').convert_alpha()
        self.tv = pygame.transform.scale(self.tv,(ScreenSettings.RESOLUTION))

    def create_crt_lines(self):
        """Draws horizontal lines across the screen to create a CRT effect"""
        line_height = 3
        line_amount = int(ScreenSettings.HEIGHT / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv,'black',(0,y_pos),(ScreenSettings.WIDTH,y_pos),1)

    def draw(self):
        """
        Draws the CRT effect on the screen by randomly adjusting the alpha transparency
        of the TV overlay and creating horizontal lines across the screen.
        """
        self.tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines()
        self.screen.blit(self.tv,(0,0))