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
                    if random.random() < DROP_CHANCES[alien.color]:
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
                self.game.hearts += 1
            else:
                self.game.player.sprite.activate_powerup(powerup)

class GameManager:
    """Main game manager class"""
    def __init__(self):

        # Game setup
        pygame.init()

        # Controller setup
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

        self.screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.SCALED)
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
        self.heart_x_start_pos = SCREEN_WIDTH - (self.heart_surf.get_size()[0] * 3 + 30)

        # Background Setup
        self.background = pygame.sprite.Group()
        Background(self.background)

        # Player setup
        player_sprite = Player((SCREEN_CENTER),self.audio)
        self.player = pygame.sprite.GroupSingle(player_sprite)
        self.player_alive = True

        # Score setup
        self.score = 0
        self.save_data = {
            'high_score' : 0
        }

        try:
            with open('high_score.txt') as high_score_file:
                self.save_data = json.load(high_score_file)
        except:
            print('No file created yet')

        # Timers
        self.alien_spawn_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_spawn_timer,ALIEN_SPAWN_RATE)

        self.alien_laser_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_laser_timer,ALIEN_LASER_RATE)

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

    def spawn_aliens(self,alien_color):
        self.aliens.add(Alien(alien_color,SCREEN_WIDTH,SCREEN_HEIGHT))
        if alien_color == 'blue':
            self.audio.channel_5.play(self.audio.ufo_sound)

    def spawn_powerup(self, pos, color):
        self.powerups.add(PowerUp(pos, color))

    def alien_shoot(self):  
        if self.aliens.sprites():
            random_alien = random.choice(self.aliens.sprites())
            
            if random_alien.color == 'green':
                offset = 10
                self.alien_lasers.add(Laser((random_alien.rect.centerx - offset, random_alien.rect.centery), ALIEN_LASER_SPEED, LASER_COLORS['alien'], DEFAULT_LASER_WIDTH))
                self.alien_lasers.add(Laser((random_alien.rect.centerx + offset, random_alien.rect.centery), ALIEN_LASER_SPEED, LASER_COLORS['alien'], DEFAULT_LASER_WIDTH))
            else:
                laser_sprite = Laser(random_alien.rect.center, ALIEN_LASER_SPEED, LASER_COLORS['alien'], DEFAULT_LASER_WIDTH)
                self.alien_lasers.add(laser_sprite)

    def explode(self,x_pos,y_pos):
        self.audio.channel_2.play(self.audio.explosion_sound)
        self.explosion = Explosion(x_pos,y_pos)
        self.exploding_sprites.add(self.explosion)
        self.explosion.explode()

    def player_damage(self):
        self.hearts -= 1
        
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
            pygame.time.set_timer(self.player_death_timer, PLAYER_DEATH_DELAY)

    def score_check(self):
        """checks the current score against the high score"""
        if self.score > self.save_data['high_score']:
            self.save_data['high_score'] = self.score

    def display_hearts(self):
        """displays the heart icons on the top right"""
        for heart in range(self.hearts):
            x = self.heart_x_start_pos + (heart * (self.heart_surf.get_size()[0] + HEART_SPACING))
            self.screen.blit(self.heart_surf,(x,HEART_TOP_MARGIN))

    def pause(self):
        """Pauses game when ESC is pressed"""
        self.paused = not self.paused
        while self.paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    with open('high_score.txt','w') as high_score_file:
                        json.dump(self.save_data,high_score_file)
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        self.audio.channel_0.unpause()
                        self.audio.channel_1.unpause()
                        self.audio.channel_7.play(self.audio.unpause_sound)
                        self.paused = False
            self.screen.fill((0, 0, 0))
            self.style.update('pause',self.save_data,self.score)
            pygame.display.update()

    def run(self):
        last_time = time.time()
        while True:
            delta_time = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    with open('high_score.txt','w') as high_score_file:
                        json.dump(self.save_data,high_score_file)
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
                            # Start/Restart the game
                            self.score = 0
                            self.player.sprite.rect.center = SCREEN_CENTER
                            self.hearts = 3
                            self.alien_lasers.empty()
                            self.powerups.empty()
                            self.player_alive = True
                            self.game_active = True

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
                        alien_color = random.choices(ALIEN_TYPES, weights=ALIEN_WEIGHTS)[0]
                        self.spawn_aliens(alien_color)
                    if event.type == self.alien_laser_timer:
                        self.alien_shoot()
                    if event.type == self.player_death_timer:
                        self.audio.player_down.play()
                        self.aliens.empty()
                        self.powerups.empty()
                        self.game_active = False
                        pygame.time.set_timer(self.player_death_timer,0)
                else:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.score = 0
                        self.player.sprite.rect.center = SCREEN_CENTER
                        self.hearts = 3
                        self.alien_lasers.empty()
                        self.powerups.empty()
                        self.player_alive = True
                        self.game_active = True

            self.screen.fill((30,30,30))
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

                self.score_check()
                self.style.update('game_active',self.save_data,self.score)
            else:
                self.audio.channel_1.stop()
                if self.play_intro_music:
                    if not self.audio.channel_0.get_busy():
                        self.audio.channel_0.play(self.audio.intro_music)

                if self.score == 0:
                    self.style.update('intro',self.save_data,self.score)
                else:
                    self.style.update('game_over',self.save_data,self.score)

            self.crt.draw()
            pygame.display.flip()
            self.clock.tick(FRAMERATE)

if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()