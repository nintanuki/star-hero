import pygame
import random
from settings import *

class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, speed, colors, width):
        super().__init__()
        self.colors = colors
        self.color_index = 0
        self.image = pygame.Surface((width, LASER_HEIGHT))
        self.image.fill(self.colors[self.color_index])
        self.rect = self.image.get_rect(center = pos)
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        
        # Color Flickering Logic
        self.color_index = 1 - self.color_index # Toggles between 0 and 1 every frame
        self.image.fill(self.colors[self.color_index])
        
        # Kill if off screen (using settings)
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self,pos,audio):
        super().__init__()
        self.image = pygame.image.load('graphics/player_ship.png').convert_alpha()
        self.image = pygame.transform.rotozoom(self.image,0,PLAYER_SCALE)
        self.rect = self.image.get_rect(center = (pos)) # make pos = 400,500?
        self.speed = PLAYER_SPEED
        self.ready = True
        
        self.laser_time = 0
        self.laser_cooldown = DEFAULT_LASER_COOLDOWN
        self.beam_active = False
        self.beam_start_time = 0

        self.twin_laser_active = False
        self.twin_laser_start_time = 0

        self.rapid_fire_active = False
        self.rapid_fire_start_time = 0

        self.lasers = pygame.sprite.Group()

        self.audio = audio

    def get_input(self):
        # Keyboard input
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_w] or keys[pygame.K_UP]):
            self.rect.y -= self.speed
            if (keys[pygame.K_f]):
                self.rect.y -= self.speed
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]):
            self.rect.y += self.speed
            if (keys[pygame.K_f]):
                self.rect.y += self.speed
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]):
            self.rect.x -= self.speed
            if (keys[pygame.K_f]):
                self.rect.x -= self.speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            self.rect.x += self.speed
            if (keys[pygame.K_f]):
                self.rect.x += self.speed

        if keys[pygame.K_SPACE] and self.ready:
            self.shoot_laser()
            self.ready = False
            self.laser_time = pygame.time.get_ticks()
            self.audio.channel_3.play(self.audio.laser_sound)

    def recharge(self):
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown:
                self.ready = True

    def constraint(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def shoot_laser(self):
        
        # 1. Determine the colors and size of the lasers
        if self.beam_active:
            colors = LASER_COLORS['beam']
            width = BEAM_LASER_WIDTH
            offset = 20              # Extra space for thick beams
        elif self.rapid_fire_active:
            colors = LASER_COLORS['rapid']
            width = DEFAULT_LASER_WIDTH
            offset = 12
        else:
            colors = LASER_COLORS['standard']
            width = DEFAULT_LASER_WIDTH
            offset = 12

        # 2. Spawn the lasers
        if self.twin_laser_active:
            self.lasers.add(Laser((self.rect.centerx - offset, self.rect.centery), PLAYER_LASER_SPEED, colors, width))
            self.lasers.add(Laser((self.rect.centerx + offset, self.rect.centery), PLAYER_LASER_SPEED, colors, width))
        else:
            self.lasers.add(Laser(self.rect.center, PLAYER_LASER_SPEED, colors, width))

    def activate_powerup(self, powerup):
        current_time = pygame.time.get_ticks()

        if powerup.powerup_type == 'twin_laser':
            self.twin_laser_active = True
            self.twin_laser_start_time = current_time

        elif powerup.powerup_type == 'rapid_fire':
            self.rapid_fire_active = True
            self.rapid_fire_start_time = current_time
            self.laser_cooldown = powerup.cooldown_bonus
            # Turn off beam if it was active so they don't fight
            self.beam_active = False 

        elif powerup.powerup_type == 'beam':
            self.beam_active = True
            self.beam_start_time = current_time
            self.laser_cooldown = powerup.cooldown_bonus
            # Turn off rapid fire if it was active
            self.rapid_fire_active = False

    def check_powerup_timeout(self):
        current_time = pygame.time.get_ticks()

        if self.twin_laser_active:
            if current_time - self.twin_laser_start_time >= POWERUP_DURATION:
                self.twin_laser_active = False

        if self.rapid_fire_active:
            if current_time - self.rapid_fire_start_time >= POWERUP_DURATION:
                self.rapid_fire_active = False
                self.laser_cooldown = DEFAULT_LASER_COOLDOWN

        if self.beam_active:
            if current_time - self.beam_start_time >= POWERUP_DURATION:
                self.beam_active = False
                self.laser_cooldown = DEFAULT_LASER_COOLDOWN

    def update(self):
        self.get_input()
        self.constraint()
        self.recharge()
        self.check_powerup_timeout()
        self.lasers.update()

class Alien(pygame.sprite.Sprite):
    def __init__(self,color,screen_width,screen_height):
        super().__init__()
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height
        x_pos  = random.randint(20,self.screen_width - 20)
        file_path = 'graphics/' + self.color + '.png'
        self.image = pygame.image.load(file_path).convert_alpha()
        self.rect = self.image.get_rect(center = (x_pos,random.randint(-300,-100)))

        # Yellow aliens zigzag
        self.yellow_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left
        self.yellow_zigzag_counter = 0 

        # Blue aliens zigzag
        self.blue_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left

        # Give green aliens twin lasers
        self.is_twin = True if color == 'green' else False

        self.value = ALIEN_VALUES.get(color, 0)

    def destroy(self):
        if self.rect.y >= self.screen_height + 50: # added 50 to give the score time to decrease
            self.kill()

    # numbers round down if decimals are used? .05 doesn't move and 1 is the same as 1.5, etc
    def update(self):
        if self.color == 'red': self.rect.y += ALIEN_DESCEND_SPEED_RED
        elif self.color == 'green': self.rect.y += ALIEN_DESCEND_SPEED_GREEN
        elif self.color == 'yellow':
            self.rect.y += ALIEN_DESCEND_SPEED_YELLOW
            self.yellow_zigzag_counter += 1
            if self.yellow_zigzag_counter >= 100: # change direction every 100 updates
                self.yellow_zigzag_counter = 0
                self.yellow_zigzag_direction *= -1
            self.rect.x += self.yellow_zigzag_direction * 2
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.yellow_zigzag_direction *= -1
        else: # color is blue
            self.rect.y += ALIEN_DESCEND_SPEED_BLUE
            self.rect.x += self.blue_zigzag_direction * 2
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.blue_zigzag_direction *= -1
        self.destroy()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, color):
        super().__init__()
        self.speed = POWERUP_SPEED
        self.shape = POWERUP_DATA[color].get('shape', 'circle')

        self.draw_color = POWERUP_DATA[color]['draw_color']
        self.powerup_type = POWERUP_DATA[color]['type']
        self.cooldown_bonus = POWERUP_DATA[color].get('cooldown', None)

        self.flash_color = (255, 255, 255)
        self.current_color = self.draw_color

        if self.shape == 'heart':
            self.image = pygame.image.load('graphics/heart.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (24, 24))
            self.rect = self.image.get_rect(center=pos)
        else:
            self.image = pygame.Surface((POWERUP_RADIUS * 2, POWERUP_RADIUS * 2), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=pos)

        self.flash_timer = 0
        self.flash_speed = POWERUP_FLASH_SPEED

    def animate(self):
        if self.shape == 'heart':
            return  # skip animation, keep sprite static

        current_time = pygame.time.get_ticks()

        if current_time - self.flash_timer >= self.flash_speed:
            self.flash_timer = current_time

            # toggle between the orb's color and white
            if self.current_color == self.draw_color:
                self.current_color = self.flash_color
            else:
                self.current_color = self.draw_color

        # redraw circle every frame
        self.image.fill((0, 0, 0, 0))

        if self.shape == 'diamond':
            points = [
                (POWERUP_RADIUS, 0),                    # top
                (POWERUP_RADIUS * 2, POWERUP_RADIUS),      # right
                (POWERUP_RADIUS, POWERUP_RADIUS * 2),      # bottom
                (0, POWERUP_RADIUS)                     # left
            ]
            pygame.draw.polygon(self.image, self.current_color, points)
        else:
            pygame.draw.circle(
                self.image,
                self.current_color,
                (POWERUP_RADIUS, POWERUP_RADIUS),
                POWERUP_RADIUS
            )

    def destroy(self):
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def update(self):
        self.rect.y += self.speed
        self.animate()
        self.destroy()