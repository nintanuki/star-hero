import pygame
from settings import *

class Style():
    """Class for displaying text"""
    def __init__(self,screen,audio):
        self.screen = screen
        self.small_font = pygame.font.Font(UT_FONT,FONT_SIZE_SMALL)
        self.medium_font = pygame.font.Font(UT_FONT,FONT_SIZE_MEDIUM)
        self.large_font = pygame.font.Font(UT_FONT,FONT_SIZE_LARGE)
        self.font_color = 'white'

        # Needed to display the volume
        self.audio = audio

        # Volume Bar
        self.volume_bar = pygame.Surface((40,40))
        self.volume_bar.fill((240,240,240))
        self.volume_bar_rect = self.volume_bar.get_rect(center = (400,400))
        self.maximum_volume = 1000
        self.volume_bar_length = 150
        self.volume_bar_ratio = self.maximum_volume / self.volume_bar_length

        # Load image of ship for intro and game over screens
        self.player_ship = pygame.image.load('graphics/player_ship.png').convert_alpha()
        self.player_ship = pygame.transform.rotozoom(self.player_ship,0,0.2)
        self.player_ship_rect = self.player_ship.get_rect(center = (ScreenSettings.CENTER))

    def display_title(self):
        """Displays the title on the intro screen"""
        title = self.large_font.render('STAR HERO', False, self.font_color)
        title_rect = title.get_rect(center=(ScreenSettings.WIDTH / 2, 70))
        self.screen.blit(title, title_rect)

    def display_game_over(self):
        """Displays Game Over message"""
        game_over_message = self.large_font.render('GAME OVER', False, self.font_color)
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
        intro_message = self.medium_font.render('PRESS START TO PLAY', False, self.font_color)
        intro_message_rect = intro_message.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT - 70))
        self.screen.blit(intro_message, intro_message_rect)

    def display_high_score(self, save_data):
        """Displays the high score on the intro and game over screens"""
        self.save_data = save_data

        high_score_message = self.medium_font.render(
            f'HIGH SCORE: {self.save_data["high_score"]}',
            False,
            self.font_color
        )
        high_score_message_rect = high_score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 520))
        self.screen.blit(high_score_message, high_score_message_rect)

    def display_in_game_score(self, save_data, score):
        """Displays the high score and current score on the top left during gameplay"""
        self.save_data = save_data
        self.score = score

        high_score_surf = self.small_font.render(f'HIGH SCORE: {self.save_data["high_score"]}', False, self.font_color)
        high_score_rect = high_score_surf.get_rect(topleft=(10, 5))
        self.screen.blit(high_score_surf, high_score_rect)

        score_surf = self.medium_font.render(f'SCORE: {self.score}', False, self.font_color)
        score_rect = score_surf.get_rect(topleft=(10, 20))
        self.screen.blit(score_surf, score_rect)

    def display_game_over_score(self, score):
        """Displays the player score on the game over screen"""
        self.score = score

        score_message = self.medium_font.render(f'YOUR SCORE: {self.score}', False, self.font_color)
        score_message_rect = score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 560))
        self.screen.blit(score_message, score_message_rect)

    def display_pause_text(self):
        """Displays the Pause message on pause"""
        pause_text = self.medium_font.render('PAUSED', False, (self.font_color))
        pause_text_rect = pause_text.get_rect(center = (ScreenSettings.CENTER))
        self.screen.blit(pause_text,pause_text_rect)

    def display_volume(self):
        """Displays the volume, called when + and - keys are pressed"""

        # Volume Number
        volume_message = self.small_font.render(f'VOLUME: {round(self.audio.master_volume * 10)}',False,(self.font_color))
        volume_message_rect = volume_message.get_rect(bottomleft = (10,ScreenSettings.HEIGHT - 20))
        self.screen.blit(volume_message,volume_message_rect)
        
        # Volume Bar
        pygame.draw.rect(self.screen,'green',(10,ScreenSettings.HEIGHT - 20,(self.audio.master_volume*1000)/self.volume_bar_ratio,10))

    def display_leaderboard(self, leaderboard, title="TOP 10", start_y=300):
        screen_center_x = ScreenSettings.WIDTH // 2

        title_surf = self.small_font.render(title, False, self.font_color)
        title_rect = title_surf.get_rect(center=(screen_center_x, start_y))
        self.screen.blit(title_surf, title_rect)

        y = start_y + 30
        for i, entry in enumerate(leaderboard, start=1):
            text = f"{i:>2}. {entry['name']}  {entry['score']}"
            surf = self.small_font.render(text, False, self.font_color)
            rect = surf.get_rect(center=(screen_center_x, y))
            self.screen.blit(surf, rect)
            y += 22

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

                initials_surf = self.large_font.render(initials_text.strip(), False, 'white')
                initials_rect = initials_surf.get_rect(center=(screen_center_x, 165))
                self.screen.blit(initials_surf, initials_rect)

                leaderboard_title_y = 220
                leaderboard_start_y = 255
            else:
                restart_surf = self.medium_font.render("PRESS ENTER TO PLAY AGAIN", False, 'white')
                restart_rect = restart_surf.get_rect(center=(screen_center_x, ScreenSettings.HEIGHT - 70))
                self.screen.blit(restart_surf, restart_rect)

                leaderboard_title_y = 130
                leaderboard_start_y = 160

            leaderboard_title = self.small_font.render("TOP 10", False, 'white')
            leaderboard_title_rect = leaderboard_title.get_rect(center=(screen_center_x, leaderboard_title_y))
            self.screen.blit(leaderboard_title, leaderboard_title_rect)

            y = leaderboard_start_y
            for i, entry in enumerate(leaderboard, start=1):
                text = f"{i:>2}. {entry['name']}  {entry['score']}"
                surf = self.small_font.render(text, False, 'white')
                rect = surf.get_rect(center=(screen_center_x, y))
                self.screen.blit(surf, rect)
                y += 22

        elif game_state == 'pause':
            self.display_pause_text()