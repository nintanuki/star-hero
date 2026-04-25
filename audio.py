import pygame
import random
import os
from settings import *

class Audio:
    """Manages all game audio including music, background tracks, and sound effects.

    Loads every sound asset on construction and exposes named channel references
    so callers can play, pause, and stop individual audio streams without
    worrying about channel allocation details.
    """
    def _effective_volume(self) -> float:
        """Returns the master volume scaled to 0 when debug mute is enabled.

        Returns:
            float: Effective volume level between 0.0 and 1.0.
        """
        return 0 if self.muted else self.master_volume

    def _half_effective_volume(self) -> float:
        """Returns half the effective volume; used for SFX mixed quieter than music.

        Returns:
            float: Half of the current effective volume level.
        """
        return self._effective_volume() / 2

    def __init__(self) -> None:
        """
        Initializes the pygame mixer, pre-loads all music tracks and sound effects,
        sets initial volume levels, and assigns each audio asset to a dedicated mixer channel.

        Note: A loading screen should be displayed before constructing this object
        as pre-loading all tracks can cause a brief freeze on slower hardware.
        """
        super().__init__()
        # Increase the number of available channels from 8 to 16
        pygame.mixer.set_num_channels(16)

        self.master_volume = AudioSettings.DEFAULT_MASTER_VOLUME
        self.muted = AudioSettings.DEBUG_MUTE

        """Music"""
        self.intro_music = pygame.mixer.Sound(
            os.path.join(AudioSettings.MUSIC_DIR, 'star_hero_intro.ogg')
        )
        self.intro_music.set_volume(self._half_effective_volume())
        self.channel_0 = pygame.mixer.Channel(0)


        self.channel_1 = pygame.mixer.Channel(1)

        # --- PRELOAD ALL BGM TRACKS ---
        self.bgm_tracks = []
        for filename in AudioSettings.BGM_PLAYLIST:
            sound = pygame.mixer.Sound(os.path.join(AudioSettings.MUSIC_DIR, filename))
            sound.set_volume(self._half_effective_volume())
            self.bgm_tracks.append(sound)

        self.bg_music = None
        self.last_bgm = None

        # Not tied to a channel?
        # self.player_down = pygame.mixer.Sound('audio/game_over.ogg')
        self.player_down = pygame.mixer.Sound(
            os.path.join(AudioSettings.MUSIC_DIR, 'game_over.ogg')
        )
        self.player_down.set_volume(self._effective_volume())

        """
        Sound Effects
        Divide by 2 on initialize and update as they are too loud compared to the music
        """
        self.laser_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'laser.wav'))
        self.laser_sound.set_volume(self._half_effective_volume())
        self.channel_3 = pygame.mixer.Channel(3)

        self.hyper_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'hyper.wav'))
        self.hyper_sound.set_volume(self._half_effective_volume())
        self.channel_10 = pygame.mixer.Channel(10)
        
        self.explosion_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'explosion.wav'))
        self.explosion_sound.set_volume(self._half_effective_volume())
        self.channel_2 = pygame.mixer.Channel(2)

        # Low Health Alarms share channel
        self.low_health_alarm1 = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_alarm_loop2.wav'))
        self.low_health_alarm1.set_volume(self._half_effective_volume())
        self.low_health_alarm2 = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_alarm_loop1.wav'))
        self.low_health_alarm2.set_volume(self._half_effective_volume())
        self.channel_4 = pygame.mixer.Channel(4)

        self.ufo_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_sound_bling.wav'))
        self.ufo_sound.set_volume(self._half_effective_volume())
        self.channel_5 = pygame.mixer.Channel(5)

        self.pause_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_sounds_pause2_in.wav'))
        self.pause_sound.set_volume(self._half_effective_volume())
        self.channel_6 = pygame.mixer.Channel(6)

        self.unpause_sound = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_sounds_pause2_out.wav'))
        self.unpause_sound.set_volume(self._half_effective_volume())
        self.channel_7 = pygame.mixer.Channel(7)

        # Powerup SFX (for now all three are sharing channel 8)
        self.powerup_twin = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_sounds_powerup1.wav'))
        self.powerup_weapon = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_sounds_powerup2.wav'))
        self.powerup_heart = pygame.mixer.Sound(os.path.join(AudioSettings.AUDIO_DIR, 'sfx_coin_cluster4.wav'))
        self.channel_8 = pygame.mixer.Channel(8)

        self.powerup_twin.set_volume(self._half_effective_volume())
        self.powerup_weapon.set_volume(self._half_effective_volume())
        self.powerup_heart.set_volume(self._half_effective_volume())

        # Tractor beam sound disabled (file deleted)
        self.tractor_beam = None
        self.channel_9 = pygame.mixer.Channel(9)

    def load_random_bgm(self) -> None:
        """Selects a random background music track from the pre-loaded playlist.

        Avoids repeating the most recently played track when more than one
        track is available. The selected track is stored in self.bg_music
        and must be explicitly played on a channel by the caller.
        """
        if not self.bgm_tracks:
            return

        choices = self.bgm_tracks

        if self.last_bgm and len(self.bgm_tracks) > 1:
            choices = [track for track in self.bgm_tracks if track is not self.last_bgm]

        self.bg_music = random.choice(choices)
        self.last_bgm = self.bg_music

    def update(self) -> None:
        """Reapplies volume levels to every loaded sound and music asset.

        Should be called whenever master_volume or DEBUG_MUTE changes so that
        all currently-loaded sounds reflect the new settings immediately.
        """
        self.muted = AudioSettings.DEBUG_MUTE
        effective_volume = self._effective_volume()
        half_effective_volume = effective_volume / 2

        # self.intro_music.set_volume(self.master_volume * 2)
        self.intro_music.set_volume(half_effective_volume)
        # self.bg_music.set_volume(self.master_volume)
        
        # To prevent crashing since self.bg_music is initialized as None and only set to a Sound object after the intro music finishes
        for track in self.bgm_tracks:
            track.set_volume(half_effective_volume)
        
        self.player_down.set_volume(half_effective_volume)
        self.laser_sound.set_volume(half_effective_volume)
        self.hyper_sound.set_volume(half_effective_volume)
        self.explosion_sound.set_volume(half_effective_volume)
        self.low_health_alarm1.set_volume(half_effective_volume)
        self.low_health_alarm2.set_volume(half_effective_volume)
        self.ufo_sound.set_volume(half_effective_volume)
        # self.tractor_beam.set_volume(half_effective_volume)  # Disabled
        self.pause_sound.set_volume(half_effective_volume)
        self.unpause_sound.set_volume(half_effective_volume)
        self.powerup_twin.set_volume(half_effective_volume)
        self.powerup_weapon.set_volume(half_effective_volume)
        self.powerup_heart.set_volume(half_effective_volume)