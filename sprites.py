import pygame
import random
from settings import *

class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, speed, colors, width):
        super().__init__()
        self.colors = colors
        self.color_index = 0
        self.image = pygame.Surface((width, LaserSettings.HEIGHT))
        self.image.fill(self.colors[self.color_index])
        self.rect = self.image.get_rect(center = pos)
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        
        # Color Flickering Logic
        self.color_index = 1 - self.color_index # Toggles between 0 and 1 every frame
        self.image.fill(self.colors[self.color_index])
        
        # Kill if off screen (using settings)
        if self.rect.bottom < 0 or self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self,pos,audio):
        super().__init__()
        # Store original image to revert back after flashing
        self.original_image = pygame.image.load('graphics/player_ship.png').convert_alpha()
        self.original_image = pygame.transform.rotozoom(self.original_image, 0, PlayerSettings.SCALE)
        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center = (pos)) # make pos = 400,500?
        self.speed = PlayerSettings.SPEED

        # Damage Flash Logic
        self.is_flashing = False
        self.flash_timer = 0
        self.last_flash_time = 0
        self.is_red = False

        self.ready = True
        
        self.laser_time = 0
        self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN
        self.beam_active = False
        self.beam_start_time = 0

        self.twin_laser_active = False
        self.twin_laser_start_time = 0

        self.rapid_fire_active = False
        self.rapid_fire_start_time = 0

        self.lasers = pygame.sprite.Group()

        self.audio = audio

    def trigger_damage_effect(self):
        """Called when the player takes damage"""
        self.is_flashing = True
        self.flash_timer = pygame.time.get_ticks()

        # Reset all powerups upon taking damage
        self.twin_laser_active = False
        self.rapid_fire_active = False
        self.beam_active = False
        self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

    def animate_damage(self):
        """Toggles the ship color between original and red tint"""
        if self.is_flashing:
            current_time = pygame.time.get_ticks()
            
            # Check if total duration has passed
            if current_time - self.flash_timer >= PlayerSettings.FLASH_DURATION:
                self.is_flashing = False
                self.image = self.original_image.copy() # Reset to normal
                return

            # Toggle flash state based on interval
            if current_time - self.last_flash_time >= PlayerSettings.FLASH_INTERVAL:
                self.last_flash_time = current_time
                self.is_red = not self.is_red

                if self.is_red:
                    # Create a red version of the ship
                    red_surf = self.original_image.copy()
                    # BLIT_RGBA_MULT multiplies the image by the color (R, G, B, A)
                    # This keeps the transparency but turns the pixels red
                    red_surf.fill((255, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = red_surf
                else:
                    self.image = self.original_image.copy()

    def get_input(self):
        # 1. Determine current speed (check Keyboard 'F' or Controller 'X')
        keys = pygame.key.get_pressed()
        current_speed = self.speed
        
        # Check all connected joysticks for the X button (Button 2)
        controller_boost = False
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            if joy.get_button(2): # 2 is usually 'X' on Logitech/Xbox layouts
                controller_boost = True

        if keys[pygame.K_f] or controller_boost:
            current_speed *= 2 # Doubles the movement speed

        # 2. Movement (Keyboard + Controller)
        if (keys[pygame.K_w] or keys[pygame.K_UP]): self.rect.y -= current_speed
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]): self.rect.y += current_speed
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]): self.rect.x -= current_speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]): self.rect.x += current_speed

        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            if abs(joy.get_axis(0)) > PlayerSettings.JOYSTICK_DEADZONE:
                self.rect.x += joy.get_axis(0) * current_speed
            if abs(joy.get_axis(1)) > PlayerSettings.JOYSTICK_DEADZONE:
                self.rect.y += joy.get_axis(1) * current_speed

        # 3. MANUAL Shooting (Only for standard weapon)
        # Only check for manual input if NO auto-powerup is active
        if not (self.rapid_fire_active or self.beam_active):
            # Keyboard
            if keys[pygame.K_SPACE] and self.ready:
                self.trigger_shot()
            # Controller (A Button)
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                if joy.get_button(0) and self.ready:
                    self.trigger_shot()

    def recharge(self):
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown:
                self.ready = True

    def constraint(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.right >= ScreenSettings.WIDTH:
            self.rect.right = ScreenSettings.WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= ScreenSettings.HEIGHT:
            self.rect.bottom = ScreenSettings.HEIGHT

    def shoot_laser(self):
        
        # 1. Determine the colors and size of the lasers
        if self.beam_active:
            colors = LaserSettings.COLORS['beam']
            width = LaserSettings.BEAM_WIDTH
            offset = 20              # Extra space for thick beams
        elif self.rapid_fire_active:
            colors = LaserSettings.COLORS['rapid']
            width = LaserSettings.DEFAULT_WIDTH
            offset = 12
        else:
            colors = LaserSettings.COLORS['standard']
            width = LaserSettings.DEFAULT_WIDTH
            offset = 12

        # 2. Spawn the lasers
        if self.twin_laser_active:
            self.lasers.add(Laser((self.rect.centerx - offset, self.rect.centery), LaserSettings.PLAYER_LASER_SPEED, colors, width))
            self.lasers.add(Laser((self.rect.centerx + offset, self.rect.centery), LaserSettings.PLAYER_LASER_SPEED, colors, width))
        else:
            self.lasers.add(Laser(self.rect.center, LaserSettings.PLAYER_LASER_SPEED, colors, width))

    def activate_powerup(self, powerup):
        current_time = pygame.time.get_ticks()

        if powerup.powerup_type == 'twin_laser':
            self.twin_laser_active = True

        elif powerup.powerup_type == 'rapid_fire':
            # Only activate rapid fire if the beam isn't already active
            if not self.beam_active:
                self.rapid_fire_active = True
                self.rapid_fire_start_time = current_time
                self.laser_cooldown = powerup.cooldown_bonus

        elif powerup.powerup_type == 'beam':
            self.beam_active = True
            self.beam_start_time = current_time
            self.laser_cooldown = powerup.cooldown_bonus
            self.rapid_fire_active = False

    def check_powerup_timeout(self):
        current_time = pygame.time.get_ticks()

        if self.rapid_fire_active:
            if current_time - self.rapid_fire_start_time >= PlayerSettings.RAPID_FIRE_DURATION:
                self.rapid_fire_active = False
                self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

        if self.beam_active:
            if current_time - self.beam_start_time >= PlayerSettings.BEAM_DURATION:
                self.beam_active = False
                self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

    def trigger_shot(self):
        """Helper to handle the act of shooting"""
        self.shoot_laser()
        self.ready = False
        self.laser_time = pygame.time.get_ticks()
        self.audio.channel_3.play(self.audio.laser_sound)

    def update(self):
        self.get_input()

        if (self.rapid_fire_active or self.beam_active) and self.ready:
            self.trigger_shot()
        
        self.constraint()
        self.recharge()
        self.check_powerup_timeout()
        self.animate_damage()
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
        self.rect = self.image.get_rect(center = (x_pos,random.randint(*AlienSettings.SPAWN_OFFSET)))

        # Yellow aliens zigzag
        self.yellow_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left
        self.yellow_zigzag_counter = 0 

        # Blue aliens zigzag
        self.blue_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left

        # Give green aliens twin lasers
        self.is_twin = True if color == 'green' else False

        self.value = AlienSettings.POINTS.get(color, 0)

    def destroy(self):
        if self.rect.y >= self.screen_height + 50: # added 50 to give the score time to decrease
            self.kill()

    # numbers round down if decimals are used? .05 doesn't move and 1 is the same as 1.5, etc
    def update(self):
        if self.color == 'red': self.rect.y += AlienSettings.SPEED['red']
        elif self.color == 'green': self.rect.y += AlienSettings.SPEED['green']
        elif self.color == 'yellow':
            self.rect.y += AlienSettings.SPEED['yellow']
            self.yellow_zigzag_counter += 1
            if self.yellow_zigzag_counter >= AlienSettings.ZIGZAG_THRESHOLD:
                self.yellow_zigzag_counter = 0
                self.yellow_zigzag_direction *= -1
            self.rect.x += self.yellow_zigzag_direction * 2
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.yellow_zigzag_direction *= -1
        else: # color is blue
            self.rect.y += AlienSettings.SPEED['blue']
            self.rect.x += self.blue_zigzag_direction * 2
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.blue_zigzag_direction *= -1
        self.destroy()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, color):
        super().__init__()
        self.speed = PowerupSettings.SPEED
        self.shape = PowerupSettings.DATA[color].get('shape', 'circle')

        self.draw_color = PowerupSettings.DATA[color]['draw_color']
        self.powerup_type = PowerupSettings.DATA[color]['type']
        self.cooldown_bonus = PowerupSettings.DATA[color].get('cooldown', None)

        self.flash_color = (255, 255, 255)
        self.current_color = self.draw_color

        if self.shape == 'heart':
            self.image = pygame.image.load('graphics/heart.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, UISettings.HEART_SPRITE_SIZE)
            self.rect = self.image.get_rect(center=pos)
        else:
            self.image = pygame.Surface((PowerupSettings.RADIUS * 2, PowerupSettings.RADIUS * 2), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=pos)

        self.flash_timer = 0
        self.flash_speed = PowerupSettings.FLASH_SPEED

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
                (PowerupSettings.RADIUS, 0),                    # top
                (PowerupSettings.RADIUS * 2, PowerupSettings.RADIUS),      # right
                (PowerupSettings.RADIUS, PowerupSettings.RADIUS * 2),      # bottom
                (0, PowerupSettings.RADIUS)                     # left
            ]
            pygame.draw.polygon(self.image, self.current_color, points)
        else:
            pygame.draw.circle(
                self.image,
                self.current_color,
                (PowerupSettings.RADIUS, PowerupSettings.RADIUS),
                PowerupSettings.RADIUS
            )

    def destroy(self):
        if self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

    def update(self):
        self.rect.y += self.speed
        self.animate()
        self.destroy()