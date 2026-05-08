# Star Hero — Architecture

This document explains **how the Star Hero code is put together and why**. It is meant for anyone touching the code — human or AI. It deliberately skips things any Pygame project does and focuses on the parts specific to this game.

> **Maintenance rule:** every pass that meaningfully changes a system must update the matching section here. Out-of-date architecture docs are worse than none.

---

## 1. The shape of the program

```
                                  +----------------+
                                  |   main.py      |
                                  |  GameManager   |   (coordinator)
                                  +-------+--------+
                                          |
   +----------+----------+----------+-----+------+----------+----------+
   |          |          |          |            |          |          |
   v          v          v          v            v          v          v
Collision  Score    SessionState  SpawnDirector  Audio    Style       CRT
Manager    Manager  Manager       (systems/      (systems (ui/        (ui/
(systems/  (systems (systems/      managers)     /audio)   style)      crt)
 managers) managers) managers)
                                          |
                            +-------------+-------------+
                            |                           |
                            v                           v
                   core/sprites.py            core/animations.py
                   (Player, Alien, Laser,     (Background, Explosion)
                    PowerUp, BombProjectile,
                    BombBlast)
```

Responsibility split:

- **`GameManager`** owns the screen, clock, controllers, sprite groups, hearts, the volume HUD timer, and the main loop. It dispatches input and orchestrates phase transitions but does not implement gameplay rules itself.
- **`CollisionManager`** runs every per-frame collision query (player vs alien, player vs alien laser, player laser vs alien, bomb blast vs alien, powerup vs player).
- **`ScoreManager`** owns the running score, the persisted leaderboard, and the initials-entry flow on game over.
- **`SessionStateManager`** owns run lifecycle: `game_active`, `player_alive`, pausing, and `reset_for_new_game`.
- **`SpawnDirector`** owns alien spawning, alien firing, drop rolls, and difficulty ramping. It owns its own `pygame.event.custom_type` timers for spawning, alien firing, and player death.
- **`Audio`** owns mixer state, music tracks, SFX cache, and master volume.
- **`Style`** owns HUD/menu rendering (intro, game-over, pause, hearts, score, volume bar, status icons).
- **`CRT`** is the last-pass overlay (scanlines + flicker).
- **`core/sprites.py`** holds gameplay entities: `Player`, `Alien`, `Laser`, `PowerUp`, `BombProjectile`, `BombBlast`.
- **`core/animations.py`** holds non-entity animated visuals: `Background`, `Explosion`.

---

## 2. The frame loop

`GameManager.run()`:

1. Compute `delta_time` from `time.time()` so animations are frame-rate independent (FPS is 120 but tunable).
2. Check the controller quit combo (top of frame, for held-state quits).
3. `_process_events` drains `pygame.event.get()` and dispatches by event type — including the `volume_display_timer` and the spawn/laser/death timers when a run is active.
4. `_world_speed_multiplier` reads the player's brake/boost state to compute a single scalar that is applied uniformly to scrolling background, alien movement, and alien lasers.
5. `_update_music` flips between intro music and BGM based on `session.game_active`.
6. `_update_world` advances every gameplay sprite group and runs collision checks (only when `game_active`).
7. `_render_frame` paints background → gameplay sprites *or* menu screens → volume HUD → CRT.
8. `pygame.display.flip()` then `clock.tick(FPS)`.

---

## 3. Run lifecycle

`SessionStateManager` is the source of truth for "is a run happening":

- **Intro** (`game_active=False`, `score=0`): `Style` renders the intro screen, intro music plays.
- **Active run** (`game_active=True`): gameplay updates and draws, BGM plays, `SpawnDirector` spawn/laser timers tick.
- **Death delay** (`player_alive=False`, `game_active` still True): the `player_death_timer` is armed; the player ship is hidden but the world keeps moving for `PlayerSettings.DEATH_DELAY` ms.
- **Death timer fires** (`_on_player_death_timer`): aliens / powerups cleared, background scroll reset, `game_active=False`, `ScoreManager.finalize_game_over_score` decides whether initials entry is offered.
- **Game over** (`game_active=False`, `score>0`): `Style` renders the game-over screen; if `entering_initials`, the initials cursor is driven by directional input.
- **Restart**: `session.reset_for_new_game()` clears state and starts a fresh run.

---

## 4. The player

`Player` lives in `core/sprites.py` and tracks ship position, weapon state, shield orb, bombs, and a "world speed multiplier" used to express brake/boost.

### Weapon tiers
The player's weapon evolves through pickups (laser → twin → hyper) and rate (default → rapid tier 1 → rapid tier 2). The active fire pattern is computed each shot from these two state variables so a single helper produces the correct laser color and arrangement.

### Status effects
- **Shield**: temporary damage immunity drawn as an orb around the ship. Duration `PlayerSettings.SHIELD_DURATION`.
- **Rainbow beam**: temporary screen-wide attack with cycling hue per segment.
- **Confusion**: blue alien attack reverses horizontal controls for `PlayerSettings.CONFUSION_TIMEOUT` ms; ship sprite tints magenta.

### Boost / brake meter
The player has a single boost meter that drains while a boost direction is held and recharges while idle. Brake is a separate held-input state that scales the world speed multiplier down, slowing every world-moving thing including aliens and the background.

### Bombs
The bomb is a two-stage input: first press launches a `BombProjectile`, second press while one is airborne detonates it into a `BombBlast`. `handle_bomb_input` in `GameManager` chooses which behavior to invoke based on whether a projectile is active.

### Damage layering
On a successful hit:
1. Active shield blocks everything.
2. Otherwise, an active weapon power state (rapid tier, hyper, rainbow) is **stripped** before any heart is removed — this is the "first hit knocks down the powerup" rule.
3. Otherwise, a heart is removed.

---

## 5. Aliens and difficulty ramp

`Alien` lives in `core/sprites.py`. There are four colors with distinct behavior:

| Color | Speed | Behavior | Drop |
| --- | --- | --- | --- |
| Red | 1 | Straight | Heart / shield |
| Green | 2 | Straight | Laser upgrade |
| Yellow | 3 | Zigzag | Rapid fire |
| Blue | 5 | Fast, may stop and confuse | Rainbow beam |

Spawn weights live in `AlienSettings.SPAWN_CHANCE`. `SpawnDirector` uses these weights every spawn timer tick.

### Difficulty ramp
`SpawnDirector.adjust_difficulty()` runs after every alien kill. As score crosses each `AlienSettings.DIFFICULTY_STEP` boundary:
- Spawn rate gets shorter, clamped at `MIN_SPAWN_RATE`.
- Alien laser rate gets shorter, clamped at `MIN_LASER_RATE`.
- Background scroll speed steps up by `BG_SCROLL_STEP`, clamped at `BG_SCROLL_MAX`.

### Confusion attack (blue alien)
When a blue alien rolls `CONFUSION_CHANCE`:
- It descends to `CONFUSION_STOP_Y` and stops.
- It draws a fan-shaped purple beam toward the player for `CONFUSION_DURATION` ms.
- If the beam is in line with the player when it lands, the player enters the confused state.
- Visual tuning lives in the `CONFUSION_BEAM_*` constants in `AlienSettings`.

---

## 6. Score and leaderboard

`ScoreManager` owns:

- **Running score**, incremented by `alien.value` per kill.
- **Persisted save data** (the leaderboard and the highest score) loaded once on boot and saved on `close_game`.
- **Initials entry**: a 3-character cursor with `_move_initials_cursor` and `_cycle_initials_char` driven by both keyboard arrows and controller D-pad / left stick.
- **Game-over qualification**: `finalize_game_over_score` decides whether the run qualifies for the leaderboard and arms `entering_initials` accordingly.

The legacy `high_score.txt` at the project root is no longer the source of truth; the leaderboard JSON now drives the high-score readout. The stale file is kept on disk only because nothing has cleaned it up yet — it should not be read or written from gameplay code.

---

## 7. Audio

`Audio` (`systems/audio.py`) owns the `pygame.mixer` lifecycle:

- Pre-loads SFX into a dict at boot for instant `play(name)` lookup.
- Drives intro vs BGM playback through `play_intro_music`, `stop_intro_music`, `ensure_bgm_playing`, `stop_bgm`.
- Has a debug mute toggle (`AudioSettings.DEBUG_MUTE`) bound to `M` for development.
- Master volume is held on `Audio.master_volume` and clamped to `[0, 1]` by `GameManager.adjust_master_volume`. The volume bar HUD is shown for `UISettings.VOLUME_DISPLAY_TIME` ms via the `volume_display_timer` event.

The loading screen at boot is painted directly in `GameManager._show_loading_screen` because `Style` and `Audio` aren't constructed yet — the splash exists *because* audio pre-loading takes a noticeable beat on slower hardware.

---

## 8. The CRT post-process

`CRT` (`ui/crt.py`) blits a TV-frame image at a per-frame random alpha (`ScreenSettings.CRT_ALPHA_RANGE`) for flicker, then draws horizontal scanlines spaced `ScreenSettings.CRT_SCANLINE_HEIGHT` pixels apart. It is the **last** thing drawn each frame.

---

## 9. Settings as the only knob panel

[settings.py](../settings.py) groups every tunable into a `*Settings` class, plus `AssetPaths`, `FontSettings`, `UISettings`, `ColorSettings`, `BombSettings`, `ExplosionSettings`, etc. Subsystems use `from settings import *` because the file historically grew that way; new code should still import only what it needs where practical.

When adding a new tunable, add it to the most appropriate `*Settings` class with a comment explaining its **units**.

---

## 10. Input model

Two devices, one event loop, with explicit context-aware routing:

- **Keyboard** events → `KEYDOWN` dispatched by `_handle_keydown`.
- **Controller** events → `JOYBUTTONDOWN` dispatched by `_handle_joybuttondown`; D-pad → `JOYHATMOTION` dispatched by `_handle_joyhatmotion`.

`_handle_keydown` is a good model for the dispatch shape: global keys first (fullscreen, escape, debug mute, volume), then a branch on `session.game_active`, and within game-over a sub-branch on `entering_initials`.

Globals that intentionally fall through every other handler:
- `F11` and Back (Select) toggle fullscreen.
- `Esc` exits.
- `Start + Back + L1 + R1` quit combo on any controller exits immediately (top-of-frame held-state check; `quit_combo_pressed` re-syncs the joystick cache when count drifts).
- Hotplugged controllers are detected via `JOYDEVICEADDED` / `JOYDEVICEREMOVED` and the cache is rebuilt.

---

## 11. Code conventions worth knowing

Most rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md). Two that shape how files **look**:

**Section banners.** Inside any file with multiple logical groupings, sections are separated by an all-caps banner:

```python
    # -------------------------
    # SECTION NAME
    # -------------------------
```

**Function order inside a class.** Functions are grouped by role; `update` and `run` go **last** and should only call other functions on the class.

---

## 12. Source tree

```
core/
  animations.py    Background, Explosion
  sprites.py       Player, Alien, Laser, PowerUp, BombProjectile, BombBlast
systems/
  audio.py         Audio
  managers.py      CollisionManager, ScoreManager, SessionStateManager, SpawnDirector
ui/
  crt.py           CRT
  style.py         Style (HUD + menu rendering)
tools/             Standalone dev/debug tools
assets/
  audio/           Music + SFX
  graphics/        Sprites and overlays
  font/            Pixeled.ttf
docs/              README index, ARCHITECTURE, TODO, TESTING, CHANGELOG
main.py            GameManager + entry point
settings.py        All tunables grouped into *Settings classes
```

The layout deliberately mirrors Dungeon Digger so a contributor moving between the two games doesn't have to re-orient.
