import pygame
import sys, random, time
import json
import os
from settings import *
from animations import Background, Explosion, CRT
from sprites import Laser, Player, Alien, PowerUp, BombBlast
from style import Style
from audio import Audio

class CollisionManager:
    """Handles all collision logic in one place"""
    def __init__(self, game):
        """
        Initializes the CollisionManager with a reference to the main game object.

        Args:
            game (GameManager): The main game manager instance.
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
                    self.game.handle_alien_destroyed(alien)

    def _player_bombs(self):
        """Checks collisions for active bomb projectiles and starts bomb blasts on impact."""
        player = self.game.player.sprite
        for bomb in player.bomb_projectiles.sprites():
            aliens_hit = pygame.sprite.spritecollide(bomb, self.game.aliens, True)
            if not aliens_hit:
                continue

            for alien in aliens_hit:
                self.game.handle_alien_destroyed(alien)

            blast_center = bomb.rect.center
            bomb.kill()
            self.game.trigger_bomb_blast(blast_center)

    def _bomb_blasts(self):
        """Applies bomb blast damage to aliens in the expanding area."""
        for blast in self.game.bomb_blasts:
            nearby_aliens = pygame.sprite.spritecollide(blast, self.game.aliens, False)
            for alien in nearby_aliens:
                if id(alien) in blast.hit_aliens:
                    continue

                dx = alien.rect.centerx - blast.center[0]
                dy = alien.rect.centery - blast.center[1]
                # Compare squared distances to avoid a costly sqrt call.
                # Equivalent to: distance(alien, blast_center) <= blast.radius
                if (dx * dx) + (dy * dy) <= (blast.radius * blast.radius):
                    blast.hit_aliens.add(id(alien))
                    alien.kill()
                    self.game.handle_alien_destroyed(alien)

    def _alien_lasers(self):
        """Checks for collisions between alien lasers and the player"""
        player = self.game.player.sprite
        for laser in self.game.alien_lasers:
            if pygame.sprite.spritecollide(laser, self.game.player, False):
                laser.kill() # Lasers always stop on player contact.
                if not player.is_invulnerable():
                    self.game.session.player_damage()

    def _ship_collisions(self):
        """Checks for collisions between the player's ship and aliens"""
        # Damage player if their ship collides with an alien
        aliens_crash = pygame.sprite.spritecollide(self.game.player.sprite, self.game.aliens, True)
        for alien in aliens_crash:
            self.game.scores.score += alien.value
            if self.game.hearts > 1:
                self.game.explode(alien.rect.centerx, alien.rect.centery)
        if aliens_crash and not self.game.player.sprite.is_invulnerable():
            self.game.session.player_damage()

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
                    if self.game.player.sprite.laser_level < 4:
                        self.game.audio.channel_8.play(self.game.audio.powerup_twin)
                elif powerup.powerup_type in ['rapid_fire', 'rainbow_beam', 'shield', 'bomb']:
                    self.game.audio.channel_8.play(self.game.audio.powerup_weapon)
                
                self.game.player.sprite.activate_powerup(powerup)

    def update(self):
        """Checks all collisions"""
        self._player_lasers()
        self._player_bombs()
        self._bomb_blasts()
        self._alien_lasers()
        self._ship_collisions()
        self._powerups()

class ScoreManager:
    """
    Manages score, high score, leaderboard I/O, and initials entry state.

    Args:
        game (GameManager): The main game manager instance, used for accessing score and saving data.
    """
    def __init__(self, game):
        self.game = game
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
            score_file_path = os.path.join(os.path.dirname(__file__), 'high_score.txt')
            with open(score_file_path) as high_score_file:
                self.save_data = json.load(high_score_file)
        except (OSError, json.JSONDecodeError):
            print('No file created yet')

    def reset(self) -> None:
        """Resets score and initials entry state for a new game."""
        self.score = 0
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

    def _sort_and_trim_leaderboard(self) -> None:
        """Sorts the leaderboard and keeps only the top 10 scores, also updates high score."""
        # Sort descending by score and keep only the top 10 entries.
        self.save_data['leaderboard'] = sorted(
            self.save_data.get('leaderboard', []),
            key=lambda entry: entry['score'],
            reverse=True
        )[:10]

        if self.save_data['leaderboard']:
            self.save_data['high_score'] = self.save_data['leaderboard'][0]['score']
        else:
            self.save_data['high_score'] = 0

    def save_scores(self) -> None:
        """Saves the current leaderboard and high score to a file."""
        self._sort_and_trim_leaderboard()
        score_file_path = os.path.join(os.path.dirname(__file__), 'high_score.txt')
        with open(score_file_path, 'w') as high_score_file:
            json.dump(self.save_data, high_score_file)

    def qualifies_for_leaderboard(self, score: int) -> bool:
        """
        Checks if the given score qualifies for the leaderboard.

        Args:
            score (int): The player's final score to check.

        Returns:
            bool: True if the score earns a leaderboard spot, False otherwise.
        """
        leaderboard = self.save_data.get('leaderboard', [])
        if len(leaderboard) < 10:
            return score > 0
        return score > leaderboard[-1]['score']

    def start_initial_entry(self) -> None:
        """Initiates the process of entering initials for a new high score."""
        self.entering_initials = True
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = self.score

    def submit_initials(self) -> None:
        """Submits the entered initials and score to the leaderboard."""
        leaderboard = self.save_data.get('leaderboard', [])
        # If this name already exists on the board, update it only if the new score is higher.
        # Otherwise add a fresh entry so duplicate names don't bloat the leaderboard.
        existing_entry = next((item for item in leaderboard if item["name"] == self.initials), None)

        if existing_entry:
            if self.pending_score > existing_entry['score']:
                existing_entry['score'] = self.pending_score
        else:
            leaderboard.append({'name': self.initials, 'score': self.pending_score})

        self.save_data['leaderboard'] = leaderboard
        self._sort_and_trim_leaderboard()
        self.save_scores()

        self.entering_initials = False
        self.pending_score = None
        self.score_processed = True

    def finalize_game_over_score(self) -> None:
        """Checks if the score qualifies for the leaderboard and starts initials entry or saves directly."""
        if self.score_processed:
            return
        if self.qualifies_for_leaderboard(self.score):
            self.start_initial_entry()
        else:
            self._sort_and_trim_leaderboard()
            self.save_scores()
            self.score_processed = True

    def _move_initials_cursor(self, step: int) -> None:
        """
        Move initials cursor left/right and clamp to valid range.

        Args:
            step (int): Direction to move (-1 for left, 1 for right).
        """
        self.initials_index = max(0, min(2, self.initials_index + step))

    def _cycle_initials_char(self, step: int) -> None:
        """
        Rotate the selected initials character by one alphabet step.

        Args:
            step (int): Direction to cycle (1 for forward, -1 for backward).
        """
        chars = list(self.initials)
        current = chars[self.initials_index]
        # Use ord/chr arithmetic to step through ASCII letters, wrapping Z→A and A→Z.
        if step > 0:
            chars[self.initials_index] = 'A' if current == 'Z' else chr(ord(current) + 1)
        else:
            chars[self.initials_index] = 'Z' if current == 'A' else chr(ord(current) - 1)
        self.initials = ''.join(chars)

class SessionStateManager:
    """Manages game session state: active/paused/player-alive flags, run resets, pause, and player damage."""
    def __init__(self, game):
        self.game = game
        self.game_active = False
        self.paused = False
        self.player_alive = True
        self.play_intro_music = True

    def reset_for_new_game(self) -> None:
        """Resets all necessary game state to start a new game."""
        game = self.game
        game.scores.reset()
        game.hearts = PlayerSettings.MAX_HEALTH
        self.player_alive = True
        self.game_active = True

        # Reset player position
        game.player.sprite.rect.center = ScreenSettings.CENTER

        # Clear all sprite groups from previous run
        game.aliens.empty()
        game.alien_lasers.empty()
        game.powerups.empty()
        game.exploding_sprites.empty()
        game.bomb_blasts.empty()
        game.player.sprite.lasers.empty()
        game.player.sprite.bomb_projectiles.empty()

        # Reset player state
        player = game.player.sprite
        player.ready = True
        player.laser_time = 0
        player.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN
        player.laser_level = 1
        player.rapid_fire_level = 0
        player.rainbow_beam_active = False
        player.rainbow_beam_start_time = 0
        player.shield_active = False
        player.shield_start_time = 0
        player.bombs = BombSettings.START_COUNT

        player.boost_meter = 1.0
        player.boost_active = False
        player.brake_active = False
        player.boost_locked_until_full = False
        player.world_speed_multiplier = 1.0

        player.confused = False
        player.confusion_timer = 0

        player.is_flashing = False
        player.flash_timer = 0
        player.last_flash_time = 0
        player.is_red = False
        player.image = player.original_image.copy()

        # Reset background speed
        for bg in game.background.sprites():
            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

        # Stop any lingering audio/effects from previous game
        game.audio.channel_4.stop()  # low health alarms
        game.audio.channel_9.stop()  # tractor beam if active

        # Make sure death timer isn't still hanging around
        pygame.time.set_timer(game.spawner.player_death_timer, 0)

    def pause(self) -> None:
        """Pauses game when ESC or START is pressed."""
        game = self.game
        self.paused = not self.paused
        # Stop confusion-beam loop while paused to prevent lingering audio.
        game.audio.channel_9.stop()
        while self.paused:
            if game.quit_combo_pressed():
                game.close_game()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.close_game()

                if game._handle_joystick_hotplug(event):
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        self.unpause_game()
                    if event.key == pygame.K_m:
                        game.toggle_debug_mute()

                if event.type == pygame.JOYBUTTONDOWN:
                    if game.quit_combo_pressed():
                        game.close_game()
                    if event.button == 7:
                        self.unpause_game()
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()
                    # if event.button == 4:
                    #     game.adjust_master_volume(-0.1, show_overlay=True)
                    # if event.button == 5:
                    #     game.adjust_master_volume(0.1, show_overlay=True)

            game.screen.fill((0, 0, 0))
            game.style.update('pause', game.scores.save_data, game.scores.score)
            pygame.display.update()

    def unpause_game(self) -> None:
        """Handles unpausing logic."""
        game = self.game
        game.audio.channel_0.unpause()
        game.audio.channel_1.unpause()
        game.audio.channel_7.play(game.audio.unpause_sound)
        self.paused = False

    def player_damage(self) -> None:
        """
        Handles logic for when the player takes damage.
        If the player has any active upgrade or powerup, that is stripped instead of losing a heart.
        """
        game = self.game
        player = game.player.sprite
        if player and player.shield_active:
            return

        # If the player has any active upgrade, strip it instead of removing a heart.
        # This gives the player a second chance before actually taking damage.
        has_upgrade = player and (
            player.laser_level > 1 or
            player.rapid_fire_level > 0 or
            player.rainbow_beam_active
        )

        if has_upgrade:
            player.trigger_damage_effect()
            return

        game.hearts -= 1

        if player:
            player.trigger_damage_effect()

        if game.hearts == 2:
            game.audio.channel_4.play(game.audio.low_health_alarm1)
        elif game.hearts == 1:
            game.audio.channel_4.play(game.audio.low_health_alarm2)

        if game.hearts <= 0:
            game.explode(player.rect.centerx, player.rect.centery)
            game.audio.channel_1.pause()
            self.player_alive = False
            player.ready = False
            player.shoot_button_held = True
            pygame.time.set_timer(game.spawner.player_death_timer, PlayerSettings.DEATH_DELAY)

class SpawnDirector:
    """Manages spawn timers, alien/powerup spawning, alien shooting, and adaptive difficulty."""
    def __init__(self, game):
        self.game = game

        self.alien_spawn_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_spawn_timer, AlienSettings.SPAWN_RATE)

        self.alien_laser_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_laser_timer, AlienSettings.LASER_RATE)

        # Custom timer for player death delay before showing game over screen
        self.player_death_timer = pygame.event.custom_type()
        self.volume_display_timer = pygame.event.custom_type()

    def spawn_aliens(self, alien_color: str) -> None:
        """
        Spawns a new alien of the given color.

        Args:
            alien_color (str): The color of the alien, which determines its behavior and point value.
        """
        self.game.aliens.add(Alien(alien_color, *ScreenSettings.RESOLUTION))
        if alien_color == 'blue':
            self.game.audio.channel_5.play(self.game.audio.ufo_sound)

    def spawn_powerup(self, pos: tuple[int, int], color: str) -> None:
        """
        Spawns a new powerup at the given position.

        Args:
            pos (tuple[int, int]): The (x, y) position to spawn the powerup.
            color (str): The color of the powerup, which determines its type and effect.
        """
        self.game.powerups.add(PowerUp(pos, color))

    def alien_shoot(self) -> None:
        """Spawns a new alien laser from a random alien."""
        game = self.game
        if game.aliens.sprites():
            attacking_aliens = [alien for alien in game.aliens.sprites() if alien.color != 'blue']
            if attacking_aliens:
                random_alien = random.choice(attacking_aliens)

                if random_alien.color == 'green':
                    # Green aliens fire a double shot — two lasers spread either side of center.
                    offset = 10
                    game.alien_lasers.add(
                        Laser(
                            pos=(random_alien.rect.centerx - offset, random_alien.rect.centery),
                            speed=LaserSettings.ALIEN_LASER_SPEED,
                            colors=LaserSettings.COLORS['alien'],
                            width=LaserSettings.DEFAULT_WIDTH
                        )
                    )
                    game.alien_lasers.add(
                        Laser(
                            pos=(random_alien.rect.centerx + offset, random_alien.rect.centery),
                            speed=LaserSettings.ALIEN_LASER_SPEED,
                            colors=LaserSettings.COLORS['alien'],
                            width=LaserSettings.DEFAULT_WIDTH
                        )
                    )
                else:
                    game.alien_lasers.add(
                        Laser(
                            random_alien.rect.center,
                            LaserSettings.ALIEN_LASER_SPEED,
                            LaserSettings.COLORS['alien'],
                            LaserSettings.DEFAULT_WIDTH
                        )
                    )

    def adjust_difficulty(self) -> None:
        """Gradually decreases timers as score increases."""
        game = self.game
        # Each full DIFFICULTY_STEP points earned unlocks one more level of difficulty.
        steps = game.scores.score // AlienSettings.DIFFICULTY_STEP

        # Reduce alien spawn interval by 25 ms per step, capped at the minimum.
        new_spawn_rate = max(
            AlienSettings.MIN_SPAWN_RATE,
            AlienSettings.SPAWN_RATE - (steps * 25)
        )
        pygame.time.set_timer(self.alien_spawn_timer, new_spawn_rate)

        # Reduce alien laser interval by 15 ms per step, capped at the minimum.
        new_laser_rate = max(
            AlienSettings.MIN_LASER_RATE,
            AlienSettings.LASER_RATE - (steps * 15)
        )
        pygame.time.set_timer(self.alien_laser_timer, new_laser_rate)

        # Speed up background scroll to reinforce the sense of increasing pace.
        new_bg_speed = min(
            ScreenSettings.BG_SCROLL_MAX,
            ScreenSettings.DEFAULT_BG_SCROLL_SPEED + (steps * ScreenSettings.BG_SCROLL_STEP)
        )
        for bg in game.background.sprites():
            bg.scroll_speed = new_bg_speed

    def get_bomb_drop_chance(self, alien_value: int) -> float:
        """
        Returns a rare bomb-drop chance weighted by alien point value.

        Args:
            alien_value (int): The point value of the defeated alien.

        Returns:
            float: Drop chance between BOMB_DROP_BASE and BOMB_DROP_BASE + BOMB_DROP_BONUS.
        """
        all_values = AlienSettings.POINTS.values()
        min_value = min(all_values)
        max_value = max(all_values)
        if max_value == min_value:
            # All alien types are worth the same — use the flat base chance.
            return AlienSettings.BOMB_DROP_BASE
        # Linear interpolation: rarer (higher-value) aliens drop bombs more often.
        # value_ratio == 0.0 for the weakest alien, 1.0 for the strongest.
        value_ratio = (alien_value - min_value) / (max_value - min_value)
        return AlienSettings.BOMB_DROP_BASE + (AlienSettings.BOMB_DROP_BONUS * value_ratio)

    def try_spawn_alien_drop(self, alien: Alien) -> None:
        """
        Handles standard drops and rare bomb drops for a defeated alien.

        Args:
            alien (Alien): The alien that was destroyed.
        """
        game = self.game
        player = game.player.sprite
        spawned_standard_drop = False

        if alien.color == 'red':
            if not player.shield_active and random.random() < AlienSettings.RED_SHIELD_DROP_CHANCE:
                self.spawn_powerup(alien.rect.center, 'red_shield')
                spawned_standard_drop = True
            elif game.hearts < PlayerSettings.MAX_HEALTH and random.random() < AlienSettings.DROP_CHANCE['red']:
                self.spawn_powerup(alien.rect.center, 'red')
                spawned_standard_drop = True
        else:
            can_drop_color_powerup = True
            if alien.color == 'green':
                can_drop_color_powerup = player.laser_level < 4
            elif alien.color == 'yellow':
                can_drop_color_powerup = player.rapid_fire_level < 3

            if can_drop_color_powerup and random.random() < AlienSettings.DROP_CHANCE[alien.color]:
                self.spawn_powerup(alien.rect.center, alien.color)
                spawned_standard_drop = True

        if not spawned_standard_drop and random.random() < self.get_bomb_drop_chance(alien.value):
            self.spawn_powerup(alien.rect.center, 'bomb')

class GameManager:
    """Main game manager class"""
    def __init__(self):
        """Initializes the game, setting up display, audio, sprites, managers, and game state."""
        # Game setup
        pygame.init()

        # Controller setup
        pygame.joystick.init()
        # Keep joystick objects alive so button events remain reliable on all backends.
        self.joysticks = []
        self.refresh_joysticks()

        # Display setup
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption('Star Hero')
        self.clock = pygame.time.Clock()

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

        self.show_volume = False

        # Managers
        self.collisions = CollisionManager(self)
        self.scores = ScoreManager(self)
        self.session = SessionStateManager(self)
        self.spawner = SpawnDirector(self)

        # Player Health
        self.hearts = PlayerSettings.MAX_HEALTH
        self.heart_surf = pygame.image.load(AssetPaths.HEART).convert_alpha()
        self.heart_x_start_pos = ScreenSettings.WIDTH - (self.heart_surf.get_size()[0] * PlayerSettings.MAX_HEALTH + 30)

        # Background Setup
        self.background = pygame.sprite.Group()
        Background(self.background)

        # Player setup
        player_sprite = Player((ScreenSettings.CENTER), self.audio)
        self.player = pygame.sprite.GroupSingle(player_sprite)  # type: ignore[arg-type]
        self.player.sprite.bombs = BombSettings.START_COUNT

        # Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()

        # Powerup setup
        self.powerups = pygame.sprite.Group()

        # Explosion setup
        self.exploding_sprites = pygame.sprite.Group()
        self.bomb_blasts = pygame.sprite.Group()

    def close_game(self):
        """Close the game process cleanly."""
        self.scores.save_scores()
        pygame.quit()
        sys.exit()

    def refresh_joysticks(self) -> None:
        """Rebuild the active joystick list to support controller hot-plugging."""
        self.joysticks = []
        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            if not joystick.get_init():
                joystick.init()
            self.joysticks.append(joystick)

    def quit_combo_pressed(self):
        """
        Checks whether the quit combo (START + SELECT + L1 + R1) is held on any controller.

        Returns:
            bool: True if the combo is held, False otherwise.
        """
        if len(self.joysticks) != pygame.joystick.get_count():
            self.refresh_joysticks()

        required_buttons = (7, 6, 4, 5)
        for joystick in self.joysticks:
            try:
                if all(joystick.get_button(button) for button in required_buttons):
                    return True
            except pygame.error:
                # Device may have disconnected between frames.
                continue
        return False

    def _is_joystick_device_event(self, event_type: int) -> bool:
        """
        Checks whether the event type indicates a joystick connect or disconnect.

        Args:
            event_type (int): The pygame event type integer.

        Returns:
            bool: True if the event is a joystick add/remove event.
        """
        joystick_events = {
            getattr(pygame, 'JOYDEVICEADDED', None),
            getattr(pygame, 'JOYDEVICEREMOVED', None),
        }
        return event_type in joystick_events

    def _handle_joystick_hotplug(self, event: pygame.event.Event) -> bool:
        """
        Refreshes the joystick cache when a controller connect/disconnect event arrives.

        Args:
            event (pygame.event.Event): The event to inspect.

        Returns:
            bool: True if the event was a hotplug event and was handled.
        """
        if self._is_joystick_device_event(event.type):
            self.refresh_joysticks()
            return True
        return False

    def handle_alien_destroyed(self, alien: Alien) -> None:
        """
        Awards score, triggers explosion, and evaluates drops after an alien is destroyed.

        Args:
            alien (Alien): The alien that was destroyed.
        """
        self.scores.score += alien.value
        self.spawner.adjust_difficulty()
        self.explode(alien.rect.centerx, alien.rect.centery)
        self.spawner.try_spawn_alien_drop(alien)

    def trigger_bomb_blast(self, center: tuple[int, int]) -> None:
        """
        Spawns an expanding bomb blast orb at the given center position.

        Args:
            center (tuple[int, int]): The (x, y) origin of the blast.
        """
        self.bomb_blasts.add(BombBlast(center))

    def handle_bomb_input(self) -> None:
        """Launches a bomb on first press or detonates the active bomb on second press."""
        detonation_center = self.player.sprite.detonate_air_bomb()
        if detonation_center:
            self.trigger_bomb_blast(detonation_center)
            return

        self.player.sprite.launch_bomb()

    def explode(self, x_pos: int, y_pos: int) -> None:
        """
        Triggers an explosion animation at the given position and plays the sound effect.

        Args:
            x_pos (int): The x-coordinate of the explosion's center.
            y_pos (int): The y-coordinate of the explosion's center.
        """
        self.audio.channel_2.play(self.audio.explosion_sound)
        explosion = Explosion(x_pos, y_pos)
        self.exploding_sprites.add(explosion)
        explosion.explode()

    def display_hearts(self) -> None:
        """displays the heart icons on the top right"""
        for heart in range(self.hearts):
            # Step right by (icon width + spacing) for each successive heart.
            x = self.heart_x_start_pos + (heart * (self.heart_surf.get_size()[0] + UISettings.HEART_SPACING))
            self.screen.blit(self.heart_surf,(x,UISettings.HEART_TOP_MARGIN))

    def toggle_debug_mute(self) -> None:
        """Flips debug mute and immediately reapplies all audio volumes."""
        AudioSettings.DEBUG_MUTE = not AudioSettings.DEBUG_MUTE
        self.audio.update()

    def adjust_master_volume(self, delta: float, show_overlay: bool = False) -> None:
        """
        Adjusts master volume with clamping and optionally shows the HUD volume bar.

        Args:
            delta (float): Amount to add to the current volume (can be negative).
            show_overlay (bool): If True, displays the volume bar HUD.
        """
        self.audio.master_volume = max(0.0, min(1.0, self.audio.master_volume + delta))
        self.audio.update()

        if show_overlay:
            pygame.time.set_timer(self.spawner.volume_display_timer, UISettings.VOLUME_DISPLAY_TIME)
            self.show_volume = True

    def run(self) -> None:
        """Main game loop"""
        last_time = time.time() # Track time for delta_time calculations for smooth movement and animations regardless of frame rate
        while True:
            delta_time = time.time() - last_time
            last_time = time.time()

            if self.quit_combo_pressed():
                self.close_game()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close_game()

                if self._handle_joystick_hotplug(event):
                    continue

                # Controller input
                if event.type == pygame.JOYHATMOTION:
                    # event.value is (x, y). y=1 is Up, y=-1 is Down
                    if event.value[1] == 1: 
                        self.adjust_master_volume(0.1, show_overlay=True)
                    elif event.value[1] == -1:
                        self.adjust_master_volume(-0.1, show_overlay=True)

                if event.type == pygame.JOYBUTTONDOWN:
                    if self.quit_combo_pressed():
                        self.close_game()

                    if event.button == 7:  # Button 7 is usually 'Start'
                        if self.session.game_active:
                            # Pause the game
                            self.audio.channel_0.pause()
                            self.audio.channel_1.pause()
                            self.audio.channel_6.play(self.audio.pause_sound)
                            self.session.pause()
                        else:
                            if not self.scores.entering_initials:
                                self.session.reset_for_new_game()

                    # Select Button (Toggle Fullscreen)
                    if event.button == 6:
                        pygame.display.toggle_fullscreen()

                    # B Button (Launch bomb / detonate active bomb)
                    if event.button == 1 and self.session.game_active:
                        self.handle_bomb_input()

                # Keyboard input
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        self.audio.channel_0.pause()
                        self.audio.channel_1.pause()
                        self.audio.channel_6.play(self.audio.pause_sound)
                        self.session.pause()
                    if event.key == pygame.K_m:
                        self.toggle_debug_mute()
                    if event.key == pygame.K_b and self.session.game_active:
                        self.handle_bomb_input()
                    if event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                        self.adjust_master_volume(0.1, show_overlay=True)
                    elif event.key == pygame.K_KP_MINUS or event.key == pygame.K_MINUS:
                        self.adjust_master_volume(-0.1, show_overlay=True)
                if event.type == self.spawner.volume_display_timer:
                    self.show_volume = False
                    pygame.time.set_timer(self.spawner.volume_display_timer, 0)

                # Game timers (alien spawn, alien shoot, player death delay)
                if self.session.game_active:
                    if event.type == self.spawner.alien_spawn_timer:
                        alien_color = random.choices(AlienSettings.COLOR, weights=AlienSettings.SPAWN_CHANCE)[0]
                        self.spawner.spawn_aliens(alien_color)
                    if event.type == self.spawner.alien_laser_timer:
                        self.spawner.alien_shoot()
                    if event.type == self.spawner.player_death_timer:
                        self.audio.player_down.play()
                        self.aliens.empty()
                        self.powerups.empty()

                        for bg in self.background.sprites():
                            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

                        self.session.game_active = False
                        pygame.time.set_timer(self.spawner.player_death_timer, 0)
                        self.scores.finalize_game_over_score()
                else:
                    # --- KEYBOARD INPUTS FOR INITIALS ---
                    if event.type == pygame.KEYDOWN:
                        if self.scores.entering_initials:
                            if event.key == pygame.K_LEFT:
                                self.scores._move_initials_cursor(-1)
                            elif event.key == pygame.K_RIGHT:
                                self.scores._move_initials_cursor(1)
                            elif event.key == pygame.K_UP:
                                self.scores._cycle_initials_char(1)
                            elif event.key == pygame.K_DOWN:
                                self.scores._cycle_initials_char(-1)
                            elif event.key == pygame.K_RETURN:
                                self.scores.submit_initials()
                        else:
                            if event.key == pygame.K_RETURN:
                                self.session.reset_for_new_game()

                    # --- CONTROLLER INPUTS FOR INTIIALS ---
                    if self.scores.entering_initials:
                        # Handle D-Pad (Hat) movement
                        if event.type == pygame.JOYHATMOTION:
                            hat_x, hat_y = event.value
                            
                            # Left/Right to change character index
                            if hat_x == -1: # D-pad Left
                                self.scores._move_initials_cursor(-1)
                            elif hat_x == 1: # D-pad Right
                                self.scores._move_initials_cursor(1)
                            
                            # Up/Down to cycle through letters
                            if hat_y == 1: # D-pad Up
                                self.scores._cycle_initials_char(1)
                            elif hat_y == -1: # D-pad Down
                                self.scores._cycle_initials_char(-1)

                        # Handle Button Press (A button or Start)
                        if event.type == pygame.JOYBUTTONDOWN:
                            # Button 0 is usually 'A' (Xbox) or 'Cross' (PS), Button 7 is 'Start'
                            if event.button == 0 or event.button == 7:
                                self.scores.submit_initials()
                    else:
                        # If not entering initials, press Start (7) or A (0) to restart
                        if event.type == pygame.JOYBUTTONDOWN:
                            if event.button == 0 or event.button == 7:
                                self.session.reset_for_new_game()

            # Drawing
            self.screen.fill(ScreenSettings.BG_COLOR)

            world_speed_multiplier = 1.0
            if self.session.game_active and self.player.sprite:
                world_speed_multiplier = self.player.sprite.get_world_speed_multiplier()

            self.background.update(delta_time, world_speed_multiplier)
            self.background.draw(self.screen)
            if self.show_volume:
                self.style.display_volume()

            # Game logic and drawing only happens if game is active, otherwise show intro or game over screen
            if self.session.game_active:
                self.audio.channel_0.stop()
                self.session.play_intro_music = False
                if not self.audio.channel_1.get_busy():
                    self.audio.load_random_bgm()
                    self.audio.channel_1.play(self.audio.bg_music)
                self.player.sprite.world_speed_multiplier = world_speed_multiplier
                if self.session.player_alive:
                    self.player.update()
                self.alien_lasers.update(world_speed_multiplier)
                self.aliens.update(world_speed_multiplier)
                self.powerups.update()
                self.bomb_blasts.update()
                self.collisions.update()
                self.display_hearts()

                self.player.sprite.lasers.draw(self.screen)
                self.player.sprite.bomb_projectiles.draw(self.screen)
                if self.session.player_alive:
                    self.player.draw(self.screen)
                    self.player.sprite.draw_shield_orb(self.screen)
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

                        # Draw a downward-expanding trapezoid for the confusion beam.
                        # The beam starts narrow at the alien's belly and fans out as it grows.
                        top_width = 10
                        bottom_width = top_width + (alien.confusion_growth * 0.2)  # widens by 20% of growth length

                        top_left  = (alien.rect.centerx - top_width // 2, alien.rect.bottom)
                        top_right = (alien.rect.centerx + top_width // 2, alien.rect.bottom)
                        bottom_right = (alien.rect.centerx + bottom_width // 2, alien.rect.bottom + alien.confusion_growth)
                        bottom_left  = (alien.rect.centerx - bottom_width // 2, alien.rect.bottom + alien.confusion_growth)
                        shape_points = [top_left, top_right, bottom_right, bottom_left]

                        field_surf = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT), pygame.SRCALPHA)
                        pygame.draw.polygon(field_surf, (200, 0, 255, 80), shape_points)
                        self.screen.blit(field_surf, (0, 0))

                        # Pixel-perfect overlap test: check if any non-transparent pixel
                        # of the beam overlaps the player's sprite mask.
                        beam_mask = pygame.mask.from_surface(field_surf, threshold=1)
                        offset = (self.player.sprite.rect.x, self.player.sprite.rect.y)
                        
                        if beam_mask.overlap(self.player.sprite.mask, offset):
                            self.player.sprite.shield_active = False
                            if not self.player.sprite.confused:
                                self.player.sprite.confused = True
                                self.player.sprite.confusion_timer = pygame.time.get_ticks()

                # 3. Handle Audio outside the loop based on the collective state
                if any_alien_confusing:
                    # Tractor beam sound disabled (file deleted)
                    pass
                else:
                    # Only stop if the channel is actually busy and NO aliens are attacking
                    if self.audio.channel_9.get_busy():
                        self.audio.channel_9.stop()

                self.aliens.draw(self.screen)
                self.alien_lasers.draw(self.screen)
                self.powerups.draw(self.screen)
                self.bomb_blasts.draw(self.screen)

                self.style.update('game_active', self.scores.save_data, self.scores.score) # Display score and high score
                self.style.display_player_status(self.player.sprite) # Display player status info under hearts
            else:
                self.audio.channel_1.stop()
                self.audio.channel_9.stop()
                if self.session.play_intro_music:
                    if not self.audio.channel_0.get_busy():
                        self.audio.channel_0.play(self.audio.intro_music)

                # Show intro screen if score is 0, otherwise show game over screen
                if self.scores.score == 0:
                    self.style.update('intro', self.scores.save_data, self.scores.score)
                else:
                    self.style.update(
                        'game_over',
                        self.scores.save_data,
                        self.scores.score,
                        entering_initials=self.scores.entering_initials,
                        initials=self.scores.initials,
                        initials_index=self.scores.initials_index
                    )

            # Apply CRT filter and update display
            self.crt.draw()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()
