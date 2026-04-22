import pygame
import random
from settings import *

class Laser(pygame.sprite.Sprite):
    """Represents a laser shot by either the player or an alien. Handles movement, animation, and self-destruction when off-screen."""
    def __init__(self, pos, speed, colors, width, should_grow=False, is_piercing=False):
        """
        Initializes the laser with position, speed, colors for flickering, width, and growth behavior (for beams).

        Args:
            pos (tuple): The initial (x, y) position of the laser.
            speed (int): The vertical speed of the laser (negative for player lasers, positive for alien lasers).
            colors (tuple): A pair of colors to alternate between for flickering effect.
            width (int): The width of the laser beam.
            should_grow (bool): If True, the laser will start thin and grow to the target width (used for beams).
            is_piercing (bool): If True, the laser will pierce through enemies.
        """
        super().__init__()
        self.colors = colors
        self.color_index = 0
        self.hue = 0  # Start at red in the HSV spectrum

        self.is_piercing = is_piercing

        # Beam Growth Logic
        self.target_width = width
        self.current_width = 1 if should_grow else width# Start as a thin line

        self.image = pygame.Surface((self.current_width, LaserSettings.HEIGHT))
        
        if self.colors == "rainbow":
            # Start with white as a default color so it doesn't crash before update() runs
            self.image.fill((255, 255, 255)) 
        else:
            self.image.fill(self.colors[self.color_index])

        self.rect = self.image.get_rect(center = pos)
        self.speed = speed
        self.should_grow = should_grow

    def move(self):
        """Moves the laser vertically based on its speed. Called every frame in update()."""
        self.rect.y += self.speed

    def rebuild_surface(self):
        """
        Rebuilds the laser's surface when its width changes (used for beams).
        Called during update() when should_grow is True.
        """
        old_center = self.rect.center
        self.image = pygame.Surface((self.current_width, LaserSettings.HEIGHT))
        self.rect = self.image.get_rect(center = old_center)

    def animate_rainbow(self):
        """
        Handles the rainbow animation for beam lasers by updating the hue and filling the laser surface with segmented colors.
        Called every frame in update() when the laser is a beam.
        """
        self.hue = (self.hue + LaserSettings.RAINBOW_HUE_STEP) % 360
        
        # To create a flowing rainbow effect, we divide the beam into segments and assign
        # a slightly different hue to each segment based on its position and the current hue value.
        # This creates the illusion of colors moving along the beam as it grows.
        for segment_index in range(LaserSettings.RAINBOW_SEGMENTS):
            # Offset the hue for each segment based on its position
            # Adding 'i * 20' creates the color shift along the beam
            seg_hue = (self.hue + (segment_index * LaserSettings.RAINBOW_SEGMENT_SHIFT)) % 360
            
            color = pygame.Color(0)
            color.hsva = (seg_hue, 100, 100, 100)
            
            # Draw the segment onto the image
            segment_rect = pygame.Rect(
                0,
                segment_index * LaserSettings.SEGMENT_HEIGHT,
                self.current_width,
                LaserSettings.SEGMENT_HEIGHT
                )
            self.image.fill(color, segment_rect)

    def animate_flicker(self):
        """
        Handles the flickering animation by alternating between two colors.
        Called every frame in update() for non-beam lasers.
        """
        self.color_index = 1 - self.color_index # Toggles between 0 and 1 every frame
        self.image.fill(self.colors[self.color_index])

    def update_color(self):
        """Updates the laser's color based on whether it's a beam (rainbow animation)
        or a standard laser (flicker animation).
        Called every frame in update()."""
        
        # Color  Logic for Beam
        if self.colors == "rainbow":
            self.animate_rainbow()
        else:
            # Standard flickering for non-beam lasers
            self.animate_flicker()

    def update_size(self):
        """
        Handles the growth of beam lasers by increasing their width until they reach the target width.
        Called every frame in update() when should_grow is True.
        """

        # Rapidly grow width of beam until target is reached
        # Only grow if the flag is set and we haven't hit the target yet
        if self.should_grow and self.current_width < self.target_width:
            self.current_width = min(self.target_width, self.current_width + LaserSettings.RAINBOW_BEAM_GROWTH_SPEED)
            # Re-create the surface and re-center the rect
            self.rebuild_surface()

    def destroy_if_offscreen(self):
        """Destroys the laser if it goes off the top or bottom of the screen. Called every frame in update()."""
        if self.rect.bottom < 0 or self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

    def update(self):
        """
        Handles laser movement, growth (for beams),
        color flickering, and self-destruction when off-screen.
        Called every frame.
        """
        self.move()
        self.update_size()
        self.update_color()
        self.destroy_if_offscreen()

class Player(pygame.sprite.Sprite):
    """
    Represents the player's ship. Handles movement, shooting, powerup effects,
    damage flashing, and constraints within the screen.
    """
    def __init__(self,pos,audio):
        """
        Initializes the player with position,
        audio for sound effects,
        and sets up all necessary attributes
        for movement, shooting, powerups, and damage effects.

        Args:
            pos (tuple): The initial (x, y) position of the player ship.
            audio (AudioManager): An instance of the AudioManager class to handle sound effects.
        """
        super().__init__()
        # Store original image to revert back after flashing
        self.original_image = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.original_image = pygame.transform.rotozoom(self.original_image, 0, PlayerSettings.SCALE)
        self.image = self.original_image.copy()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center = (pos)) # make pos = 400,500?

        # Damage Flash Logic
        self.is_flashing = False
        self.flash_timer = 0
        self.last_flash_time = 0
        self.is_red = False

        self.ready = True
        
        self.laser_time = 0
        self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

        # Powerup States
        self.laser_level = 1 # Tier 1 start
        self.rapid_fire_level = 0 # 0 = none, 1 = cooldown boost, 2 = timed rapid fire
        self.rapid_fire_active = False
        self.rapid_fire_start_time = 0
        self.rainbow_beam_active = False
        self.rainbow_beam_start_time = 0

        self.lasers = pygame.sprite.Group()

        self.audio = audio

        # Confusion state for when hit by blue alien attack
        self.confused = False
        self.confusion_timer = 0

    def trigger_damage_effect(self):
        """Called when the player takes damage"""
        self.is_flashing = True
        self.flash_timer = pygame.time.get_ticks()

        # Reset all powerups upon taking damage
        self.laser_level = 1 # Reset to Tier 1
        self.rapid_fire_level = 0
        self.rapid_fire_active = False
        self.rainbow_beam_active = False
        self.update_laser_cooldown()

    def update_laser_cooldown(self):
        """Sets the active cooldown from the current powerup state."""
        if self.rainbow_beam_active:
            self.laser_cooldown = 0
        elif self.rapid_fire_level == 2:
            self.laser_cooldown = PowerupSettings.DATA['yellow']['cooldown']
        elif self.rapid_fire_level >= 1:
            self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN // 2
        else:
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
        """Handles player input for movement and shooting. Called every frame in update()"""
        # 1. Determine current speed (check Keyboard 'F' or Controller 'X')
        keys = pygame.key.get_pressed()
        current_speed = PlayerSettings.SPEED

        # Determine direction: if confused, multiply by -1 to invert
        direction_mod = -1 if self.confused else 1
        
        # Check all connected joysticks for the X button (Button 2)
        controller_boost = False
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            if joy.get_button(2): # 2 is usually 'X' on Logitech/Xbox layouts
                controller_boost = True

        if keys[pygame.K_f] or controller_boost:
            current_speed *= PlayerSettings.SPEED_BOOST

        # Player Movement Input
        # Keyboard input (WASD or Arrow Keys)
        if (keys[pygame.K_w] or keys[pygame.K_UP]): self.rect.y -= (current_speed * direction_mod)
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]): self.rect.y += (current_speed * direction_mod)
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]): self.rect.x -= (current_speed * direction_mod)
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]): self.rect.x += (current_speed * direction_mod)

        # Controller input (Left Joystick)
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            if abs(joy.get_axis(0)) > PlayerSettings.JOYSTICK_DEADZONE:
                self.rect.x += (joy.get_axis(0) * current_speed * direction_mod)
            if abs(joy.get_axis(1)) > PlayerSettings.JOYSTICK_DEADZONE:
                self.rect.y += (joy.get_axis(1) * current_speed * direction_mod)

        # 3. MANUAL Shooting (Only for standard weapon)
        # Only check for manual input if NO auto-powerup is active
        if not (self.rapid_fire_active or self.rainbow_beam_active):
            # Keyboard
            if keys[pygame.K_SPACE] and self.ready:
                self.trigger_shot()
            # Controller (A Button)
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                if joy.get_button(0) and self.ready:
                    self.trigger_shot()

    def recharge(self):
        """Recharges the player's laser based on cooldown. Called every frame in update()"""
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown:
                self.ready = True

    def constraint(self):
        """Constrains the player within the screen. Called every frame in update()"""
        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.right >= ScreenSettings.WIDTH:
            self.rect.right = ScreenSettings.WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= ScreenSettings.HEIGHT:
            self.rect.bottom = ScreenSettings.HEIGHT

    def shoot_laser(self):
        """Spawns lasers based on current powerup state. Handles twin lasers, rapid fire, and beam logic."""
        is_rainbow_beam = self.rainbow_beam_active
        is_hyper = (self.laser_level == 3) # Tier 3 check
        
        # 1. Determine the behavior and growth of the rainbow beam
        width = LaserSettings.RAINBOW_BEAM_WIDTH if is_rainbow_beam else LaserSettings.DEFAULT_WIDTH
        offset = 20 if is_rainbow_beam else 12

        # 2. Assign colors based on priority
        if self.rainbow_beam_active:
            colors = "rainbow"
        elif self.rapid_fire_active:
            colors = LaserSettings.COLORS['rapid']
        elif is_hyper:
            colors = LaserSettings.COLORS['hyper']
        else:
            colors = LaserSettings.COLORS['standard']

        # 3. Spawn the lasers
        if self.laser_level >= 2:
            # Left laser
            self.lasers.add(Laser((self.rect.centerx - offset, self.rect.centery), 
                                LaserSettings.PLAYER_LASER_SPEED, colors, width, 
                                should_grow=is_rainbow_beam, is_piercing=is_hyper))
            # Right laser
            self.lasers.add(Laser((self.rect.centerx + offset, self.rect.centery), 
                                LaserSettings.PLAYER_LASER_SPEED, colors, width, 
                                should_grow=is_rainbow_beam, is_piercing=is_hyper))
        else:
            # Level 1: Single laser
            self.lasers.add(Laser(self.rect.center, LaserSettings.PLAYER_LASER_SPEED, 
                                colors, width, should_grow=is_rainbow_beam, is_piercing=is_hyper))
            
        
        if self.laser_level == 3 or self.rainbow_beam_active:
            self.audio.channel_10.play(self.audio.hyper_sound)
        else:
            self.audio.channel_3.play(self.audio.laser_sound)

    def activate_powerup(self, powerup):
        """
        Activates the given powerup's effect on the player. Called when player collects a powerup.

        Args:
            powerup (PowerUp): The powerup object that was collected, which contains information about the type and any cooldown bonuses.
        """
        current_time = pygame.time.get_ticks()
        
        if powerup.powerup_type == 'laser_upgrade':
            if self.laser_level < 3:
                self.laser_level += 1
                
        elif powerup.powerup_type == 'rapid_fire':
            # Only activate rapid fire if the rainbow beam isn't already active
            if not self.rainbow_beam_active:
                if self.rapid_fire_level == 0:
                    self.rapid_fire_level = 1
                else:
                    self.rapid_fire_level = 2
                    self.rapid_fire_active = True
                    self.rapid_fire_start_time = current_time
                self.update_laser_cooldown()
            
        elif powerup.powerup_type == 'rainbow_beam':
            self.rainbow_beam_active = True
            self.rainbow_beam_start_time = current_time
            self.rapid_fire_active = False # Deactivate rapid fire if it was active, since beam takes priority
            if self.rapid_fire_level == 2:
                self.rapid_fire_level = 1
            self.update_laser_cooldown()

    def check_powerup_timeout(self):
        """Checks if any time-limited powerups have expired and deactivates them. Called every frame in update()"""
        current_time = pygame.time.get_ticks()

        if self.rapid_fire_active:
            if current_time - self.rapid_fire_start_time >= PlayerSettings.RAPID_FIRE_DURATION:
                self.rapid_fire_active = False
                self.rapid_fire_level = 1
                self.update_laser_cooldown()

        if self.rainbow_beam_active:
            if current_time - self.rainbow_beam_start_time >= PlayerSettings.RAINBOW_BEAM_DURATION:
                self.rainbow_beam_active = False
                self.update_laser_cooldown()

    def trigger_shot(self):
        """Helper to handle the act of shooting"""
        self.shoot_laser()
        self.ready = False
        self.laser_time = pygame.time.get_ticks()

    def handle_auto_shooting(self):
        """
        Handles automatic shooting for powerups that require it (like rapid fire and beam).
        Called every frame in update().
        """
        if (self.rapid_fire_active or self.rainbow_beam_active) and self.ready:
            self.trigger_shot()

    def update_lasers(self):
        """Updates all lasers fired by the player. Called every frame in update()"""
        self.lasers.update()
    
    def update(self):
        """Handles player input for movement and shooting,
        applies constraints, manages powerup effects and durations,
        animates damage flashing, and updates lasers.
        Called every frame."""
        self.get_input()
        self.handle_auto_shooting()
        self.constraint()
        self.recharge()
        self.check_powerup_timeout()
        self.animate_damage()
        self.update_lasers()

        if self.confused:
            if pygame.time.get_ticks() - self.confusion_timer >= PlayerSettings.CONFUSION_TIMEOUT:
                self.confused = False
                self.image = self.original_image # Reset to original colors
            else:
                # Create a purple-tinted version of the ship
                # This creates a copy and "multiplies" the colors with purple
                tinted_surf = self.original_image.copy()
                # (200, 0, 255) is a bright purple/magenta
                tinted_surf.fill((200, 0, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.image = tinted_surf

class Alien(pygame.sprite.Sprite):
    """Represents an alien enemy. Handles movement patterns, zigzag behavior for certain types, and self-destruction when off-screen."""
    def __init__(self,color,screen_width,screen_height):
        """Initializes the alien with a color
        (which determines its behavior and points),
        screen dimensions for spawning and movement constraints,
        and sets up its sprite and movement attributes.
        
        Args:
            color (str): The color/type of the alien, which affects its speed, points, and behavior.
            screen_width (int): The width of the game screen, used for spawning and movement constraints
            screen_height (int): The height of the game screen, used for spawning and movement constraints
        """
        super().__init__()
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 1. Load the frames
        self.frames = []
        path1 = f'{AssetPaths.GRAPHICS_DIR}{self.color}1.png'
        path2 = f'{AssetPaths.GRAPHICS_DIR}{self.color}2.png'

        # Load frame 1
        self.frames.append(pygame.image.load(path1).convert_alpha())

        # Load frame 2 (if not blue)
        if color in ['red', 'green', 'yellow']:
            try:
                self.frames.append(pygame.image.load(path2).convert_alpha())
            except pygame.error:
                # Fallback if the file is missing
                self.frames.append(self.frames[0])

        self.frame_index = 0
        self.image = self.frames[self.frame_index]

        # Position setup
        x_pos  = random.randint(20,self.screen_width - 20)
        self.rect = self.image.get_rect(center = (x_pos,random.randint(*AlienSettings.SPAWN_OFFSET)))

        # Movement logic
        # Yellow aliens zigzag
        self.yellow_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left
        self.yellow_zigzag_counter = 0 
        # Blue aliens zigzag
        self.blue_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left

        # Point value based on color
        self.value = AlienSettings.POINTS.get(color, 0)

        # Confusion attack attributes (for blue aliens)
        self.is_confusing = False
        self.confusion_start_time = 0
        self.has_projected = False 
        # Only blue aliens have a chance to cause confusion
        self.can_confuse = (color == 'blue' and random.random() < AlienSettings.CONFUSION_CHANCE)

        self.confusion_growth = 0  # Starts at 0, will increase to ScreenSettings.HEIGHT

    def calculate_movement(self):
        """
        Calculates the movement of the alien based on its color and behavior patterns.
        Called every frame in update()
        """
        # Check for confusion attack trigger (only for blue aliens with the ability)
        if self.can_confuse and not self.has_projected:
            if self.rect.centery >= AlienSettings.CONFUSION_STOP_Y:
                self.is_confusing = True
                self.has_projected = True
                self.confusion_start_time = pygame.time.get_ticks()

        if self.is_confusing:
            # Check if the projection time is over
            if pygame.time.get_ticks() - self.confusion_start_time >= AlienSettings.CONFUSION_DURATION:
                self.is_confusing = False
            return # Stop moving while confusing the player
        
        # numbers round down if decimals are used? .05 doesn't move and 1 is the same as 1.5, etc
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

    def animate(self):
        """Cycles through the frames"""
        if len(self.frames) > 1:
            self.frame_index += AlienSettings.ANIMATION_SPEED
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]

    def destroy(self):
        """Destroys the alien if it moves off the bottom of the screen. Called every frame in update()."""
        if self.rect.y >= self.screen_height + 50: # added 50 to give the score time to decrease
            self.kill()

    def update(self):
        """Handles movement, animation, and self-destruction when off-screen. Called every frame."""
        self.calculate_movement()
        self.animate()
        self.destroy()

class PowerUp(pygame.sprite.Sprite):
    """Represents a powerup that the player can collect. Handles movement, animation (flashing), and self-destruction when off-screen."""
    def __init__(self, pos, color):
        """Initializes the powerup with a position and color (which determines its type and appearance),
        and sets up attributes for movement, flashing animation, and self-destruction.
        
        Args:
            pos (tuple): The initial (x, y) position of the powerup when it spawns.
            color (str): The color/type of the powerup, which determines its effect on the player and its appearance.
        """
        super().__init__()
        self.shape = PowerupSettings.DATA[color].get('shape', 'circle')

        self.draw_color = PowerupSettings.DATA[color]['draw_color']
        self.powerup_type = PowerupSettings.DATA[color]['type']
        self.cooldown_bonus = PowerupSettings.DATA[color].get('cooldown', None)

        self.flash_color = (255, 255, 255)
        self.current_color = self.draw_color

        if self.shape == 'heart':
            self.image = pygame.image.load(AssetPaths.HEART).convert_alpha()
            self.image = pygame.transform.scale(self.image, UISettings.HEART_SPRITE_SIZE)
            self.rect = self.image.get_rect(center=pos)
        else:
            self.image = pygame.Surface((PowerupSettings.RADIUS * 2, PowerupSettings.RADIUS * 2), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=pos)

        self.flash_timer = 0
        self.flash_speed = PowerupSettings.FLASH_SPEED

    def move(self):
        """Moves the powerup downward based on its speed. Called every frame in update()."""
        self.rect.y += PowerupSettings.SPEED

    def animate(self):
        """
        Handles the flashing animation of the powerup by toggling its color between the base color and white at a set interval.
        Called every frame in update().
        """
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

        # For diamonds, we have to redraw the polygon every frame to update the color.
        # For circles, we can just fill the surface with the new color.
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
        """Destroys the powerup if it moves off the bottom of the screen. Called every frame in update()."""
        if self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

    def update(self):
        """
        Handles the downward movement of the powerup,
        its flashing animation, and checks for self-destruction when off-screen.
        Called every frame in the game loop.
        """
        self.move()
        self.animate()
        self.destroy()
