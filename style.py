import pygame
from settings import *

class Style():
    """"Handles UI rendering for menus, scores, volume, and game-over screens."""
    def __init__(self,screen,audio):
        self.screen = screen
        self.small_font = pygame.font.Font(FontSettings.FONT,FontSettings.SMALL)
        self.medium_font = pygame.font.Font(FontSettings.FONT,FontSettings.MEDIUM)
        self.large_font = pygame.font.Font(FontSettings.FONT,FontSettings.LARGE)

        self.audio = audio # Audio reference used to read and display the current volume

        # Load image of ship for intro and game over screens
        self.player_ship = pygame.image.load('graphics/player_ship.png').convert_alpha()
        self.player_ship = pygame.transform.rotozoom(self.player_ship,0,0.2)
        self.player_ship_rect = self.player_ship.get_rect(center = (ScreenSettings.CENTER))

    def display_title(self):
        """Displays the title on the intro screen"""
        title = self.large_font.render('STAR HERO', False, FontSettings.COLOR)
        title_rect = title.get_rect(center=(ScreenSettings.WIDTH / 2, 70))
        self.screen.blit(title, title_rect)

    def display_game_over(self):
        """Displays Game Over message"""
        game_over_message = self.large_font.render('GAME OVER', False, FontSettings.COLOR)
        game_over_message_rect = game_over_message.get_rect(center=(ScreenSettings.WIDTH / 2, 70))
        self.screen.blit(game_over_message, game_over_message_rect)

    def display_player_ship(self, y_pos=None):
        """Displays the player ship on intro and game over screens"""
        if y_pos is None:
            rect = self.player_ship.get_rect(center=ScreenSettings.CENTER)
        else:
            rect = self.player_ship.get_rect(center=(ScreenSettings.WIDTH / 2, y_pos))
        self.screen.blit(self.player_ship, rect)

    def display_intro_message(self):
        intro_message = self.medium_font.render('PRESS START TO PLAY', False, FontSettings.COLOR)
        intro_message_rect = intro_message.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT - 70))
        self.screen.blit(intro_message, intro_message_rect)

    def display_high_score(self, save_data):
        """Displays the high score on the intro and game over screens"""
        self.save_data = save_data

        high_score_message = self.medium_font.render(
            f'HIGH SCORE: {self.save_data["high_score"]}',
            False,
            FontSettings.COLOR
        )
        high_score_message_rect = high_score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 520))
        self.screen.blit(high_score_message, high_score_message_rect)

    def display_in_game_score(self, save_data, score):
        """Displays the high score and current score on the top left during gameplay"""
        self.save_data = save_data
        self.score = score

        high_score_surf = self.small_font.render(f'HIGH SCORE: {self.save_data["high_score"]}', False, FontSettings.COLOR)
        high_score_rect = high_score_surf.get_rect(topleft=(10, 5))
        self.screen.blit(high_score_surf, high_score_rect)

        score_surf = self.medium_font.render(f'SCORE: {self.score}', False, FontSettings.COLOR)
        score_rect = score_surf.get_rect(topleft=(10, 20))
        self.screen.blit(score_surf, score_rect)

    def display_game_over_score(self, score):
        """Displays the player score on the game over screen"""
        self.score = score

        score_message = self.medium_font.render(f'YOUR SCORE: {self.score}', False, FontSettings.COLOR)
        score_message_rect = score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 560))
        self.screen.blit(score_message, score_message_rect)

    def display_pause_text(self):
        """Displays the Pause message on pause"""
        pause_text = self.medium_font.render('PAUSED', False, (FontSettings.COLOR))
        pause_text_rect = pause_text.get_rect(center = (ScreenSettings.CENTER))
        self.screen.blit(pause_text,pause_text_rect)

    def display_volume(self):
        """Displays the volume, called when + and - keys are pressed"""

        # Volume Number
        volume_message = self.small_font.render(f'VOLUME: {round(self.audio.master_volume * 10)}',False,(FontSettings.COLOR))
        volume_message_rect = volume_message.get_rect(bottomleft = (10,ScreenSettings.HEIGHT - 20))
        self.screen.blit(volume_message,volume_message_rect)
        
        # Volume Bar
        pygame.draw.rect(self.screen,'green',(10,ScreenSettings.HEIGHT - 20,(self.audio.master_volume*1000)/UISettings.VOLUME_BAR_RATIO,10))

    def display_leaderboard(self, leaderboard, title="TOP 10", start_y=300):
        screen_center_x = ScreenSettings.WIDTH // 2

        title_surf = self.small_font.render(title, False, FontSettings.COLOR)
        title_rect = title_surf.get_rect(center=(screen_center_x, start_y))
        self.screen.blit(title_surf, title_rect)

        y = start_y + 30
        for i, entry in enumerate(leaderboard, start=1):
            text = f"{i:>2}. {entry['name']}  {entry['score']}"
            surf = self.small_font.render(text, False, FontSettings.COLOR)
            rect = surf.get_rect(center=(screen_center_x, y))
            self.screen.blit(surf, rect)
            y += 22

    def display_level(self, score):
        """Displays the current level in the bottom left corner"""
        # Level starts at 1 and increases every DIFFICULTY_STEP points (max 20)
        level = min(20, (score // AlienSettings.DIFFICULTY_STEP) + 1)
        level_surf = self.small_font.render(f'LEVEL: {level}', False, FontSettings.COLOR)
        level_rect = level_surf.get_rect(bottomleft=(10, ScreenSettings.HEIGHT - 10))
        self.screen.blit(level_surf, level_rect)

    def display_player_status(self, player):
        """Displays a status table with split colors and rainbow effects"""
        
        # --- 1. Determine Values and Colors ---
        # Status
        status_val = "CONFUSED" if player.confused else "OKAY"
        status_color = 'magenta' if player.confused else 'white' # Red for danger, White for OKAY
        
        # Weapon
        if player.laser_level == 3:
            weapon_val = "HYPER"
            weapon_color = 'cyan'
        elif player.laser_level == 2:
            weapon_val = "TWIN"
            weapon_color = 'green'
        else:
            weapon_val = "NORMAL"
            weapon_color = 'white'
        
        # Upgrade
        upgrade_val = "NONE"
        upgrade_color = 'white'
        if player.rainbow_beam_active:
            upgrade_val = "RAINBOW BEAM"
            # Create rainbow effect using HSV conversion
            hue = (pygame.time.get_ticks() // 4) % 360
            upgrade_color = pygame.Color(0)
            upgrade_color.hsva = (hue, 100, 100, 100)
        elif player.rapid_fire_active:
            upgrade_val = "RAPID FIRE"
            upgrade_color = 'yellow'

        # --- 2. Define Rows ---
        # Format: (Label, Value, Value Color)
        rows = [
            ("STATUS: ", status_val, status_color),
            ("LASER: ", weapon_val, weapon_color),
            ("POWER: ", upgrade_val, upgrade_color)
        ]

        # --- 3. Rendering ---
        start_y = 40 
        right_margin = 10

        for i, (label, value, val_color) in enumerate(rows):
            # Render the white label
            label_surf = self.small_font.render(label, False, 'white')
            # Render the colored value
            val_surf = self.small_font.render(value, False, val_color)
            
            # Calculate positions to align the entire line to the right
            total_width = label_surf.get_width() + val_surf.get_width()
            x_pos = ScreenSettings.WIDTH - right_margin - total_width
            y_pos = start_y + (i * 15) # 15 pixel vertical spacing
            
            self.screen.blit(label_surf, (x_pos, y_pos))
            self.screen.blit(val_surf, (x_pos + label_surf.get_width(), y_pos))

    def update(self, game_state, save_data, score,
           entering_initials=False,
           initials="AAA",
           initials_index=0):

        self.game_state = game_state
        self.save_data = save_data
        self.score = score

        screen_center_x = ScreenSettings.WIDTH // 2
        leaderboard = save_data.get('leaderboard', [])

        if game_state == 'intro':
            self.display_title()
            self.display_player_ship(170)
            self.display_leaderboard(leaderboard, title="TOP 10", start_y=260)
            self.display_intro_message()

        elif game_state == 'game_active':
            self.display_in_game_score(self.save_data, self.score)
            self.display_level(self.score)

        elif game_state == 'game_over':
            self.display_game_over()
            self.display_high_score(self.save_data)
            self.display_game_over_score(self.score)

            if entering_initials:
                prompt = self.small_font.render("NEW HIGH SCORE! ENTER YOUR INITIALS", False, 'yellow')
                prompt_rect = prompt.get_rect(center=(screen_center_x, 125))
                self.screen.blit(prompt, prompt_rect)

                initials_text = ""
                for i, ch in enumerate(initials):
                    if i == initials_index:
                        initials_text += f"[{ch}] "
                    else:
                        initials_text += f" {ch}  "

                initials_surf = self.large_font.render(initials_text.strip(), False, FontSettings.COLOR)
                initials_rect = initials_surf.get_rect(center=(screen_center_x, 165))
                self.screen.blit(initials_surf, initials_rect)

                leaderboard_title_y = 220
            else:
                restart_surf = self.medium_font.render("PRESS ENTER TO PLAY AGAIN", False, FontSettings.COLOR)
                restart_rect = restart_surf.get_rect(center=(screen_center_x, ScreenSettings.HEIGHT - 70))
                self.screen.blit(restart_surf, restart_rect)

                leaderboard_title_y = 130

            self.display_leaderboard(
            leaderboard,
            title="TOP 10",
            start_y=leaderboard_title_y
            )

        elif game_state == 'pause':
            self.display_pause_text()