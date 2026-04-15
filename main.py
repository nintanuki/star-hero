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
    def __init__(self, game):
        self.game = game

    def check_all(self):
        self._player_lasers()
        self._alien_lasers()
        self._ship_collisions()
        self._powerups()

    def _player_lasers(self):
        if not self.game.player.sprite.lasers: return
        for laser in self.game.player.sprite.lasers:
            aliens_hit = pygame.sprite.spritecollide(laser, self.game.aliens, True)
            if aliens_hit:
                laser.kill()
                for alien in aliens_hit:
                    self.game.score += alien.value
                    self.game.explode(alien.rect.centerx, alien.rect.centery)

                    # Check if a powerup should drop
                    if random.random() < AlienSettings.DROP_CHANCE[alien.color]:

                        # If it's a red alien (heart), only spawn if player is hurt
                        if alien.color == 'red':
                            if self.game.hearts < 3:
                                self.game.spawn_powerup(alien.rect.center, alien.color)
                        else:
                            self.game.spawn_powerup(alien.rect.center, alien.color)

    def _alien_lasers(self):
        for laser in self.game.alien_lasers:
            if pygame.sprite.spritecollide(laser, self.game.player, False):
                laser.kill()
                self.game.player_damage()

    def _ship_collisions(self):
        aliens_crash = pygame.sprite.spritecollide(self.game.player.sprite, self.game.aliens, True)
        for alien in aliens_crash:
            self.game.score += alien.value
            if self.game.hearts > 1:
                self.game.explode(alien.rect.centerx, alien.rect.centery)
        if aliens_crash:
            self.game.player_damage()

    def _powerups(self):
        powerups_collected = pygame.sprite.spritecollide(self.game.player.sprite, self.game.powerups, True)
        for powerup in powerups_collected:
            if powerup.powerup_type == 'heal' and self.game.hearts < 3:
                self.game.audio.channel_8.play(self.game.audio.powerup_heart)
                self.game.hearts += 1
            else:
                if powerup.powerup_type == 'twin_laser' and not self.game.player.sprite.twin_laser_active:
                    self.game.audio.channel_8.play(self.game.audio.powerup_twin)
                elif powerup.powerup_type in ['rapid_fire', 'beam']:
                    self.game.audio.channel_8.play(self.game.audio.powerup_weapon)
                self.game.player.sprite.activate_powerup(powerup)

class GameManager:
    """Main game manager class"""
    def __init__(self):

        # Game setup
        pygame.init()

        # Controller setup
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Star Hero')
        self.clock = pygame.time.Clock()
        self.game_active = False
        self.crt = CRT(self.screen)
        self.audio = Audio()
        self.style = Style(self.screen,self.audio)
        self.paused = False
        self.show_volume = False

        # Collisions
        self.collisions = CollisionManager(self)

        # Player Health
        self.hearts = 3
        self.heart_surf = pygame.image.load('graphics/heart.png').convert_alpha()
        self.heart_x_start_pos = ScreenSettings.WIDTH - (self.heart_surf.get_size()[0] * 3 + 30)

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
        self.initials = "AAA"
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

        try:
            with open('high_score.txt') as high_score_file:
                self.save_data = json.load(high_score_file)
        except:
            print('No file created yet')

        # Timers
        self.alien_spawn_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_spawn_timer,AlienSettings.SPAWN_RATE)

        self.alien_laser_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_laser_timer,AlienSettings.LASER_RATE)

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
        self.play_intro_music = True # Set to False after user begins, only place once

    def _sort_and_trim_leaderboard(self):
        self.save_data['leaderboard'] = sorted(
            self.save_data.get('leaderboard', []),
            key=lambda entry: entry['score'],
            reverse=True
        )[:10]

        if self.save_data['leaderboard']:
            self.save_data['high_score'] = self.save_data['leaderboard'][0]['score']
        else:
            self.save_data['high_score'] = 0

    def save_scores(self):
        self._sort_and_trim_leaderboard()
        with open('high_score.txt', 'w') as high_score_file:
            json.dump(self.save_data, high_score_file)

    def qualifies_for_leaderboard(self, score):
        leaderboard = self.save_data.get('leaderboard', [])
        if len(leaderboard) < 10:
            return score > 0
        return score > leaderboard[-1]['score']

    def start_initial_entry(self):
        self.entering_initials = True
        self.initials = "AAA"
        self.initials_index = 0
        self.pending_score = self.score

    def submit_initials(self):
        entry = {
            'name': self.initials,
            'score': self.pending_score
        }
        self.save_data['leaderboard'].append(entry)
        self._sort_and_trim_leaderboard()
        self.save_scores()

        self.entering_initials = False
        self.pending_score = None
        self.score_processed = True

    def finalize_game_over_score(self):
        if self.score_processed:
            return

        if self.qualifies_for_leaderboard(self.score):
            self.start_initial_entry()
        else:
            self._sort_and_trim_leaderboard()
            self.save_scores()
            self.score_processed = True

    def reset_for_new_game(self):
        self.score = 0
        self.player.sprite.rect.center = ScreenSettings.CENTER
        self.hearts = 3
        self.alien_lasers.empty()
        self.powerups.empty()
        self.aliens.empty()
        self.player_alive = True
        self.game_active = True

        self.entering_initials = False
        self.initials = "AAA"
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

    def spawn_aliens(self,alien_color):
        self.aliens.add(Alien(alien_color,*ScreenSettings.RESOLUTION))
        if alien_color == 'blue':
            self.audio.channel_5.play(self.audio.ufo_sound)

    def spawn_powerup(self, pos, color):
        self.powerups.add(PowerUp(pos, color))

    def alien_shoot(self):  
        if self.aliens.sprites():
            random_alien = random.choice(self.aliens.sprites())
            
            if random_alien.color == 'green':
                offset = 10
                self.alien_lasers.add(Laser((random_alien.rect.centerx - offset, random_alien.rect.centery), LaserSettings.ALIEN_LASER_SPEED, LASER_COLORS['alien'], LaserSettings.DEFAULT_WIDTH))
                self.alien_lasers.add(Laser((random_alien.rect.centerx + offset, random_alien.rect.centery), LaserSettings.ALIEN_LASER_SPEED, LASER_COLORS['alien'], LaserSettings.DEFAULT_WIDTH))
            else:
                laser_sprite = Laser(random_alien.rect.center, LaserSettings.ALIEN_LASER_SPEED, LASER_COLORS['alien'], LaserSettings.DEFAULT_WIDTH)
                self.alien_lasers.add(laser_sprite)

    def explode(self,x_pos,y_pos):
        self.audio.channel_2.play(self.audio.explosion_sound)
        self.explosion = Explosion(x_pos,y_pos)
        self.exploding_sprites.add(self.explosion)
        self.explosion.explode()

    def player_damage(self):
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
            x = self.heart_x_start_pos + (heart * (self.heart_surf.get_size()[0] + HEART_SPACING))
            self.screen.blit(self.heart_surf,(x,HEART_TOP_MARGIN))

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
        self.audio.channel_0.unpause()
        self.audio.channel_1.unpause()
        self.audio.channel_7.play(self.audio.unpause_sound)
        self.paused = False

    def run(self):
        last_time = time.time()
        while True:
            delta_time = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_scores()
                    pygame.quit()
                    sys.exit()

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
                        pygame.time.set_timer(self.volume_display_timer,VOLUME_DISPLAY_TIME)
                        self.show_volume = True
                    elif event.key == pygame.K_KP_MINUS or event.key == pygame.K_MINUS:
                        self.audio.master_volume -= 0.1
                        self.audio.master_volume = max(self.audio.master_volume, 0.0)
                        self.audio.update()
                        pygame.time.set_timer(self.volume_display_timer,VOLUME_DISPLAY_TIME)
                        self.show_volume = True
                if event.type == self.volume_display_timer:
                    self.show_volume = False
                    pygame.time.set_timer(self.volume_display_timer,0)

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

            self.screen.fill(ScreenSettings.BG_COLOR)
            self.background.update(delta_time)
            self.background.draw(self.screen)
            if self.show_volume:
                self.style.display_volume()

            if self.game_active:
                self.audio.channel_0.stop()
                self.play_intro_music = False
                if not self.audio.channel_1.get_busy():
                    self.audio.channel_1.play(self.audio.bg_music)
                self.player.update()
                self.alien_lasers.update()
                self.aliens.update()
                self.powerups.update()
                self.collisions.check_all()
                self.display_hearts()

                self.player.sprite.lasers.draw(self.screen)
                if self.player_alive:
                    self.player.draw(self.screen)
                self.exploding_sprites.draw(self.screen)

                self.exploding_sprites.update(EXPLOSION_SPEED)

                self.aliens.draw(self.screen)
                self.alien_lasers.draw(self.screen)
                self.powerups.draw(self.screen)

                self.style.update('game_active',self.save_data,self.score)
            else:
                self.audio.channel_1.stop()
                if self.play_intro_music:
                    if not self.audio.channel_0.get_busy():
                        self.audio.channel_0.play(self.audio.intro_music)

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

            self.crt.draw()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()