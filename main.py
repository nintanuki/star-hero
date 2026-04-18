import pygame
import sys, random, time
import json
from settings import *
from animations import Background, Explosion, CRT
from sprites import Laser, Player, Alien, PowerUp
from style import Style
from audio import Audio
import debug

class CollisionManager:
    """Handles all collision logic in one place"""
    def __init__(self, game):
        """Initializes the CollisionManager with a reference to the main game object
        to access necessary attributes and methods for handling collisions.
        
        Args:
            game (GameManager): The main game manager instance that contains game state and methods.
        """
        self.game = game

    def _player_lasers(self):
        """Checks for collisions between player lasers and aliens"""
        if not self.game.player.sprite.lasers: return
        for laser in self.game.player.sprite.lasers:
            aliens_hit = pygame.sprite.spritecollide(laser, self.game.aliens, True)
            if aliens_hit:
                # Laser only dies if it is NOT piercing
                if not laser.is_piercing:
                    laser.kill()

                for alien in aliens_hit:
                    self.game.score += alien.value # Add points for each alien hit
                    self.game.adjust_difficulty() # Adjust difficulty based on new score
                    self.game.explode(alien.rect.centerx, alien.rect.centery) # Trigger explosion animation at alien's position

                    # Check if a powerup should drop
                    if random.random() < AlienSettings.DROP_CHANCE[alien.color]:

                        # If it's a red alien (heart), only spawn if player is hurt
                        if alien.color == 'red':
                            if self.game.hearts < PlayerSettings.MAX_HEALTH: # Only drop if player isn't at full health
                                self.game.spawn_powerup(alien.rect.center, alien.color)
                        elif alien.color == 'green':
                            # Stop dropping if player is already at Hyper (Level 3)
                            if self.game.player.sprite.laser_level < 3:
                                self.game.spawn_powerup(alien.rect.center, alien.color)
                        else:
                            self.game.spawn_powerup(alien.rect.center, alien.color)

    def _alien_lasers(self):
        """Checks for collisions between alien lasers and the player"""
        # Prevent damage if the player is currently flashing or has the beam powerup (invincible)
        if self.game.player.sprite.is_flashing or self.game.player.sprite.beam_active: return

        # Cause damage when alien laser hits player
        for laser in self.game.alien_lasers:
            if pygame.sprite.spritecollide(laser, self.game.player, False):
                laser.kill() # Remove the laser on hit
                self.game.player_damage()

    def _ship_collisions(self):
        """Checks for collisions between the player's ship and aliens"""
        # Prevent damage if the player is currently flashing or has the beam powerup (invincible)
        if self.game.player.sprite.is_flashing or self.game.player.sprite.beam_active: return

        # Damage player if their ship collides with an alien
        aliens_crash = pygame.sprite.spritecollide(self.game.player.sprite, self.game.aliens, True)
        for alien in aliens_crash:
            self.game.score += alien.value
            if self.game.hearts > 1:
                self.game.explode(alien.rect.centerx, alien.rect.centery)
        if aliens_crash:
            self.game.player_damage()

    def _powerups(self):
        """Checks for collisions between player and powerups, applying effects and playing sounds as necessary"""
        powerups_collected = pygame.sprite.spritecollide(self.game.player.sprite, self.game.powerups, True)
        for powerup in powerups_collected:
            if powerup.powerup_type == 'heal' and self.game.hearts < PlayerSettings.MAX_HEALTH: # Only heal if player isn't at full health
                self.game.audio.channel_8.play(self.game.audio.powerup_heart)
                self.game.hearts += 1
            else:
                # Only play sound if it's a new powerup activation, not if player already has it active
                if powerup.powerup_type == 'laser_upgrade':
                    if self.game.player.sprite.laser_level < 3:
                        self.game.audio.channel_8.play(self.game.audio.powerup_twin)
                elif powerup.powerup_type in ['rapid_fire', 'rainbow_beam']:
                    self.game.audio.channel_8.play(self.game.audio.powerup_weapon)
                
                self.game.player.sprite.activate_powerup(powerup)

    def update(self):
        """Checks all collisions"""
        self._player_lasers()
        self._alien_lasers()
        self._ship_collisions()
        self._powerups()

class GameManager:
    """Main game manager class"""
    def __init__(self):
        """Initializes the game, setting up display, audio, sprites, timers, and game state variables."""
        # Game setup
        pygame.init()

        # Controller setup
        pygame.joystick.init()
        # Start button doesn't work without this
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

        # Display setup
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Star Hero')
        self.clock = pygame.time.Clock()
        self.game_active = False

        # Show a temporary loading screen while audio files are being loaded in to prevent lag during gameplay
        # This part can't be handled in the style class since we need to load audio before we can use that
        self.screen.fill((0, 0, 0))
        loading_font = pygame.font.Font(FontSettings.FONT, FontSettings.MEDIUM)
        loading_text = loading_font.render("LOADING...", False, FontSettings.COLOR)
        loading_rect = loading_text.get_rect(center=(ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2))
        self.screen.blit(loading_text, loading_rect)
        pygame.display.flip()

        self.crt = CRT(self.screen)
        self.audio = Audio()
        self.style = Style(self.screen, self.audio)
        
        self.paused = False
        self.show_volume = False

        # Collisions
        self.collisions = CollisionManager(self)

        # Player Health
        self.hearts = PlayerSettings.MAX_HEALTH
        self.heart_surf = pygame.image.load('graphics/heart.png').convert_alpha()
        self.heart_x_start_pos = ScreenSettings.WIDTH - (self.heart_surf.get_size()[0] * PlayerSettings.MAX_HEALTH + 30)

        # Background Setup
        self.background = pygame.sprite.Group()
        Background(self.background)

        # Player setup
        player_sprite = Player((ScreenSettings.CENTER),self.audio)
        self.player = pygame.sprite.GroupSingle(player_sprite)
        self.player_alive = True

        # Score setup
        self.score = 0
        self.save_data = {
            'high_score': 0,
            'leaderboard': []
        }

        # Leaderboard / initials entry state
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

        # Load saved high score and leaderboard data if available
        try:
            with open('high_score.txt') as high_score_file:
                self.save_data = json.load(high_score_file)
        except:
            print('No file created yet')

        # Timers
        self.alien_spawn_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_spawn_timer,AlienSettings.SPAWN_RATE)
        # Custom timer for alien shooting
        self.alien_laser_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_laser_timer,AlienSettings.LASER_RATE)
        # Custom timer for player death delay before showing game over screen and allowing restart
        self.player_death_timer = pygame.event.custom_type()
        self.volume_display_timer = pygame.event.custom_type()

        # Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()

        # Powerup setup
        self.powerups = pygame.sprite.Group()

        # Explosion setup
        self.exploding_sprites = pygame.sprite.Group()

        # Audio setup
        self.play_intro_music = True # Set to False after user begins, only plays once

    def _sort_and_trim_leaderboard(self):
        """Sorts the leaderboard and keeps only the top 10 scores, also updates high score"""

        # Sort the leaderboard by score in descending order and keep only the top 10 entries
        self.save_data['leaderboard'] = sorted(
            self.save_data.get('leaderboard', []),
            key=lambda entry: entry['score'],
            reverse=True
        )[:10]

        # Update high score based on the top entry in the leaderboard
        if self.save_data['leaderboard']:
            self.save_data['high_score'] = self.save_data['leaderboard'][0]['score']
        else:
            self.save_data['high_score'] = 0

    def save_scores(self):
        """Saves the current leaderboard and high score to a file"""
        self._sort_and_trim_leaderboard()
        with open('high_score.txt', 'w') as high_score_file:
            json.dump(self.save_data, high_score_file)

    def qualifies_for_leaderboard(self, score):
        """
        Checks if the given score qualifies for the leaderboard or is a personal best

        Args:
            score (int): The player's final score to check against the leaderboard
        """
        leaderboard = self.save_data.get('leaderboard', [])
        
        # If leaderboard isn't full, any score > 0 qualifies
        if len(leaderboard) < 10:
            return score > 0
            
        # If leaderboard is full, check if it beats the 10th place
        return score > leaderboard[-1]['score']

    def start_initial_entry(self):
        """Initiates the process of entering initials for a new high score"""
        self.entering_initials = True
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = self.score

    def submit_initials(self):
        """Submits the entered initials and score to the leaderboard, updating existing names"""
        leaderboard = self.save_data.get('leaderboard', [])
        
        # Check if this name already exists in the leaderboard
        existing_entry = next((item for item in leaderboard if item["name"] == self.initials), None)

        if existing_entry:
            # Only update if the new score is actually higher
            if self.pending_score > existing_entry['score']:
                existing_entry['score'] = self.pending_score
        else:
            # If it's a new player, create a new entry
            entry = {
                'name': self.initials,
                'score': self.pending_score
            }
            leaderboard.append(entry)

        # Re-assign (in case it was missing) and save
        self.save_data['leaderboard'] = leaderboard
        self._sort_and_trim_leaderboard()
        self.save_scores()

        self.entering_initials = False
        self.pending_score = None
        self.score_processed = True

    def finalize_game_over_score(self):
        """
        Finalizes the score at game over,
        checking if it qualifies for the leaderboard
        and either starting initials entry
        or just saving the score
        """
        if self.score_processed:
            return

        if self.qualifies_for_leaderboard(self.score):
            self.start_initial_entry()
        else:
            self._sort_and_trim_leaderboard()
            self.save_scores()
            self.score_processed = True

    def reset_for_new_game(self):
        """Resets all necessary game state to start a new game"""
        self.score = 0
        self.hearts = PlayerSettings.MAX_HEALTH
        self.player_alive = True
        self.game_active = True

        # Reset player position
        self.player.sprite.rect.center = ScreenSettings.CENTER
        
        # Clear all sprite groups from previous run
        self.aliens.empty()
        self.alien_lasers.empty()
        self.powerups.empty()
        self.exploding_sprites.empty()
        self.player.sprite.lasers.empty()

        # Reset player state
        self.player.sprite.ready = True
        self.player.sprite.laser_time = 0
        self.player.sprite.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

        self.player.sprite.beam_active = False
        self.player.sprite.beam_start_time = 0
        self.player.sprite.twin_laser_active = False
        self.player.sprite.twin_laser_start_time = 0
        self.player.sprite.rapid_fire_active = False
        self.player.sprite.rapid_fire_start_time = 0

        self.player.sprite.confused = False
        self.player.sprite.confusion_timer = 0

        self.player.sprite.is_flashing = False
        self.player.sprite.flash_timer = 0
        self.player.sprite.last_flash_time = 0
        self.player.sprite.is_red = False
        self.player.sprite.image = self.player.sprite.original_image.copy()

        # Reset menu / score-entry state
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

        # Reset background speed
        for bg in self.background.sprites():
            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

        # Stop any lingering audio/effects from previous game
        self.audio.channel_4.stop()  # low health alarms
        self.audio.channel_9.stop()  # tractor beam if active

        # Make sure death timer isn't still hanging around
        pygame.time.set_timer(self.player_death_timer, 0)

    def spawn_aliens(self,alien_color):
        """
        Spawns a new alien of the given color

        Args:
            alien_color (str): The color of the alien to spawn, which determines its behavior and point value
        """
        self.aliens.add(Alien(alien_color,*ScreenSettings.RESOLUTION))
        if alien_color == 'blue':
            self.audio.channel_5.play(self.audio.ufo_sound)

    def spawn_powerup(self, pos, color):
        """
        Spawns a new powerup of the given color at the given position

        Args:
            pos (tuple): The position where the powerup should be spawned
            color (str): The color of the powerup to spawn, which determines its type and effect
        """
        self.powerups.add(PowerUp(pos, color))

    def alien_shoot(self):
        """Spawns a new alien laser from a random alien"""
        if self.aliens.sprites():
            # Only select from aliens that aren't blue since they don't shoot lasers, and also prevents them from shooting while they're doing their confusion attack
            attacking_aliens = [alien for alien in self.aliens.sprites() if alien.color != 'blue']

            if attacking_aliens:
                random_alien = random.choice(attacking_aliens)
                
                # Give green aliens twin lasers
                if random_alien.color == 'green':
                    offset = 10
                    self.alien_lasers.add(
                        Laser(
                            pos=(random_alien.rect.centerx - offset, random_alien.rect.centery),
                            speed=LaserSettings.ALIEN_LASER_SPEED,
                            colors=LaserSettings.COLORS['alien'],
                            width=LaserSettings.DEFAULT_WIDTH
                        )
                    )
                    self.alien_lasers.add(
                        Laser(
                            pos=(random_alien.rect.centerx + offset, random_alien.rect.centery),
                            speed=LaserSettings.ALIEN_LASER_SPEED,
                            colors=LaserSettings.COLORS['alien'],
                            width=LaserSettings.DEFAULT_WIDTH
                        )
                    )
                else:
                    laser_sprite = Laser(
                        random_alien.rect.center,
                        LaserSettings.ALIEN_LASER_SPEED,
                        LaserSettings.COLORS['alien'],
                        LaserSettings.DEFAULT_WIDTH
                        )
                    self.alien_lasers.add(laser_sprite)

    def adjust_difficulty(self):
        """Gradually decreases timers as score increases"""
        # Calculate how many 'difficulty steps' the player has achieved
        steps = self.score // AlienSettings.DIFFICULTY_STEP
        
        # 1. Increase Spawn Rate (Decrease the timer interval)
        new_spawn_rate = max(
            AlienSettings.MIN_SPAWN_RATE, 
            AlienSettings.SPAWN_RATE - (steps * 25) # Decrease by 25ms per step
        )
        pygame.time.set_timer(self.alien_spawn_timer, new_spawn_rate)

        # 2. Increase Shooting Frequency
        new_laser_rate = max(
            AlienSettings.MIN_LASER_RATE, 
            AlienSettings.LASER_RATE - (steps * 15)
        )
        pygame.time.set_timer(self.alien_laser_timer, new_laser_rate)

        # 3. Increase background scroll speed
        new_bg_speed = min(
            ScreenSettings.BG_SCROLL_MAX,  # cap so it doesn't get ridiculous
            ScreenSettings.DEFAULT_BG_SCROLL_SPEED + (steps * ScreenSettings.BG_SCROLL_STEP)
        )
        for bg in self.background.sprites():
            bg.scroll_speed = new_bg_speed

    def explode(self,x_pos,y_pos):
        """
        Triggers an explosion animation at the given position and plays the sound effect

        Args:
            x_pos (int): The x-coordinate of the explosion's center
            y_pos (int): The y-coordinate of the explosion's center
        """
        self.audio.channel_2.play(self.audio.explosion_sound)
        self.explosion = Explosion(x_pos,y_pos)
        self.exploding_sprites.add(self.explosion)
        self.explosion.explode()

    def player_damage(self):
        """
        Handles logic for when the player takes damage,
        including reducing hearts, triggering flash effect, playing alarms, and handling death
        """
        self.hearts -= 1
        
        # Trigger the visual flash effect
        if self.player.sprite:
            self.player.sprite.trigger_damage_effect()

        # Handle alarms
        if self.hearts == 2:
            self.audio.channel_4.play(self.audio.low_health_alarm1)
        elif self.hearts == 1:
            self.audio.channel_4.play(self.audio.low_health_alarm2)
        
        # Handle death
        if self.hearts <= 0:
            self.explode(self.player.sprite.rect.centerx, self.player.sprite.rect.centery)
            self.audio.channel_1.pause()
            self.player_alive = False
            pygame.time.set_timer(self.player_death_timer, PlayerSettings.DEATH_DELAY)

    def display_hearts(self):
        """displays the heart icons on the top right"""
        for heart in range(self.hearts):
            x = self.heart_x_start_pos + (heart * (self.heart_surf.get_size()[0] + UISettings.HEART_SPACING))
            self.screen.blit(self.heart_surf,(x,UISettings.HEART_TOP_MARGIN))

    def pause(self):
        """Pauses game when ESC or START is pressed"""
        self.paused = not self.paused
        while self.paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_scores()
                    pygame.quit()
                    sys.exit()
                
                # Check for Keyboard ESC
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        self.unpause_game()

                # Check for Controller Start Button (Button 7)
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 7:
                        self.unpause_game()

                    # Select to Toggle Fullscreen
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()

                    # L1/R1 for Volume
                    if event.button == 4: # L1
                        self.audio.master_volume -= 0.1
                        if self.audio.master_volume < 0: self.audio.master_volume = 0
                        self.audio.update()
                    if event.button == 5: # R1
                        self.audio.master_volume += 0.1
                        if self.audio.master_volume > 1: self.audio.master_volume = 1
                        self.audio.update()

            self.screen.fill((0, 0, 0))
            self.style.update('pause', self.save_data, self.score)
            pygame.display.update()

    def unpause_game(self):
        """Helper to handle unpausing logic"""
        self.audio.channel_0.unpause() # Unpause intro music if it was playing
        self.audio.channel_1.unpause() # Unpause bg music if it was playing
        self.audio.channel_7.play(self.audio.unpause_sound) # Play unpause sound effect
        self.paused = False

    def run(self):
        """Main game loop"""
        last_time = time.time() # Track time for delta_time calculations for smooth movement and animations regardless of frame rate
        while True:
            delta_time = time.time() - last_time
            last_time = time.time()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_scores()
                    pygame.quit()
                    sys.exit()

                # Controller input
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 7:  # Button 7 is usually 'Start'
                        if self.game_active:
                            # Pause the game
                            self.audio.channel_0.pause()
                            self.audio.channel_1.pause()
                            self.audio.channel_6.play(self.audio.pause_sound)
                            self.pause()
                        else:
                            if not self.entering_initials:
                                self.reset_for_new_game()

                    # Select Button (Toggle Fullscreen)
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()

                    # L1 Button (Decrease Volume)
                    if event.button == 4:
                        self.audio.master_volume -= 0.1
                        if self.audio.master_volume < 0: self.audio.master_volume = 0
                        self.audio.update()
                        self.style.volume_display_timer = pygame.time.get_ticks()

                    # R1 Button (Increase Volume)
                    if event.button == 5:
                        self.audio.master_volume += 0.1
                        if self.audio.master_volume > 1: self.audio.master_volume = 1
                        self.audio.update()
                        self.style.volume_display_timer = pygame.time.get_ticks()

                # Keyboard input
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        self.audio.channel_0.pause()
                        self.audio.channel_1.pause()
                        self.audio.channel_6.play(self.audio.pause_sound)
                        self.pause()
                    if event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                        self.audio.master_volume += 0.1
                        self.audio.master_volume = min(self.audio.master_volume, 1.0)
                        self.audio.update()
                        pygame.time.set_timer(self.volume_display_timer,UISettings.VOLUME_DISPLAY_TIME)
                        self.show_volume = True
                    elif event.key == pygame.K_KP_MINUS or event.key == pygame.K_MINUS:
                        self.audio.master_volume -= 0.1
                        self.audio.master_volume = max(self.audio.master_volume, 0.0)
                        self.audio.update()
                        pygame.time.set_timer(self.volume_display_timer,UISettings.VOLUME_DISPLAY_TIME)
                        self.show_volume = True
                if event.type == self.volume_display_timer:
                    self.show_volume = False
                    pygame.time.set_timer(self.volume_display_timer,0)

                # Game timers (alien spawn, alien shoot, player death delay)
                if self.game_active:
                    if event.type == self.alien_spawn_timer:
                        alien_color = random.choices(AlienSettings.COLOR, weights=AlienSettings.SPAWN_CHANCE)[0]
                        self.spawn_aliens(alien_color)
                    if event.type == self.alien_laser_timer:
                        self.alien_shoot()
                    if event.type == self.player_death_timer:
                        self.audio.player_down.play()
                        self.aliens.empty()
                        self.powerups.empty()

                        for bg in self.background.sprites():
                            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

                        self.game_active = False
                        pygame.time.set_timer(self.player_death_timer,0)
                        self.finalize_game_over_score()
                else:
                    # --- KEYBOARD INPUTS FOR INITIALS ---
                    if event.type == pygame.KEYDOWN:
                        if self.entering_initials:
                            if event.key == pygame.K_LEFT:
                                self.initials_index = max(0, self.initials_index - 1)
                            elif event.key == pygame.K_RIGHT:
                                self.initials_index = min(2, self.initials_index + 1)
                            elif event.key == pygame.K_UP:
                                chars = list(self.initials)
                                current = chars[self.initials_index]
                                chars[self.initials_index] = 'A' if current == 'Z' else chr(ord(current) + 1)
                                self.initials = ''.join(chars)
                            elif event.key == pygame.K_DOWN:
                                chars = list(self.initials)
                                current = chars[self.initials_index]
                                chars[self.initials_index] = 'Z' if current == 'A' else chr(ord(current) - 1)
                                self.initials = ''.join(chars)
                            elif event.key == pygame.K_RETURN:
                                self.submit_initials()
                        else:
                            if event.key == pygame.K_RETURN:
                                self.reset_for_new_game()

                    # --- CONTROLLER INPUTS FOR INTIIALS ---
                    if self.entering_initials:
                        # Handle D-Pad (Hat) movement
                        if event.type == pygame.JOYHATMOTION:
                            hat_x, hat_y = event.value
                            
                            # Left/Right to change character index
                            if hat_x == -1: # D-pad Left
                                self.initials_index = max(0, self.initials_index - 1)
                            elif hat_x == 1: # D-pad Right
                                self.initials_index = min(2, self.initials_index + 1)
                            
                            # Up/Down to cycle through letters
                            if hat_y == 1: # D-pad Up
                                chars = list(self.initials)
                                current = chars[self.initials_index]
                                chars[self.initials_index] = 'A' if current == 'Z' else chr(ord(current) + 1)
                                self.initials = ''.join(chars)
                            elif hat_y == -1: # D-pad Down
                                chars = list(self.initials)
                                current = chars[self.initials_index]
                                chars[self.initials_index] = 'Z' if current == 'A' else chr(ord(current) - 1)
                                self.initials = ''.join(chars)

                        # Handle Button Press (A button or Start)
                        if event.type == pygame.JOYBUTTONDOWN:
                            # Button 0 is usually 'A' (Xbox) or 'Cross' (PS), Button 7 is 'Start'
                            if event.button == 0 or event.button == 7:
                                self.submit_initials()
                    else:
                        # If not entering initials, press Start (7) or A (0) to restart
                        if event.type == pygame.JOYBUTTONDOWN:
                            if event.button == 0 or event.button == 7:
                                self.reset_for_new_game()

            # Drawing
            self.screen.fill(ScreenSettings.BG_COLOR)
            self.background.update(delta_time)
            self.background.draw(self.screen)
            if self.show_volume:
                self.style.display_volume()

            # Game logic and drawing only happens if game is active, otherwise show intro or game over screen
            if self.game_active:
                self.audio.channel_0.stop()
                self.play_intro_music = False
                if not self.audio.channel_1.get_busy():
                    self.audio.load_random_bgm()
                    self.audio.channel_1.play(self.audio.bg_music)
                self.player.update()
                self.alien_lasers.update()
                self.aliens.update()
                self.powerups.update()
                self.collisions.update()
                self.display_hearts()

                self.player.sprite.lasers.draw(self.screen)
                if self.player_alive:
                    self.player.draw(self.screen)
                self.exploding_sprites.draw(self.screen)

                self.exploding_sprites.update(ExplosionSettings.ANIMATION_SPEED)

                # Draw blue alien confusion attack
                # 1. Track if ANY alien is currently confusing
                any_alien_confusing = False

                # 2. Draw blue alien confusion attack
                for alien in self.aliens:
                    if getattr(alien, 'is_confusing', False):
                        any_alien_confusing = True # Mark that at least one is attacking
                        
                        if alien.confusion_growth < ScreenSettings.HEIGHT:
                            alien.confusion_growth += 15 

                        top_width = 10
                        bottom_width = top_width + (alien.confusion_growth * 0.2) 

                        top_left  = (alien.rect.centerx - top_width // 2, alien.rect.bottom)
                        top_right = (alien.rect.centerx + top_width // 2, alien.rect.bottom)
                        bottom_right = (alien.rect.centerx + bottom_width // 2, alien.rect.bottom + alien.confusion_growth)
                        bottom_left  = (alien.rect.centerx - bottom_width // 2, alien.rect.bottom + alien.confusion_growth)
                        shape_points = [top_left, top_right, bottom_right, bottom_left]

                        field_surf = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT), pygame.SRCALPHA)
                        pygame.draw.polygon(field_surf, (200, 0, 255, 80), shape_points)
                        self.screen.blit(field_surf, (0, 0))

                        beam_mask = pygame.mask.from_surface(field_surf, threshold=1)
                        offset = (self.player.sprite.rect.x, self.player.sprite.rect.y)
                        
                        if beam_mask.overlap(self.player.sprite.mask, offset):
                            if not self.player.sprite.confused:
                                self.player.sprite.confused = True
                                self.player.sprite.confusion_timer = pygame.time.get_ticks()

                # 3. Handle Audio outside the loop based on the collective state
                if any_alien_confusing:
                    if not self.audio.channel_9.get_busy():
                        self.audio.channel_9.play(self.audio.tractor_beam, loops=-1)
                else:
                    # Only stop if the channel is actually busy and NO aliens are attacking
                    if self.audio.channel_9.get_busy():
                        self.audio.channel_9.stop()

                self.aliens.draw(self.screen)
                self.alien_lasers.draw(self.screen)
                self.powerups.draw(self.screen)

                self.style.update('game_active',self.save_data,self.score) # Display score and high score
                self.style.display_player_status(self.player.sprite) # Display player status info under hearts
            else:
                self.audio.channel_1.stop()
                if self.play_intro_music:
                    if not self.audio.channel_0.get_busy():
                        self.audio.channel_0.play(self.audio.intro_music)

                # Show intro screen if score is 0, otherwise show game over screen
                if self.score == 0:
                    self.style.update('intro',self.save_data,self.score)
                else:
                    self.style.update(
                        'game_over',
                        self.save_data,
                        self.score,
                        entering_initials=self.entering_initials,
                        initials=self.initials,
                        initials_index=self.initials_index
                    )

            # Apply CRT filter and update display
            self.crt.draw()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()