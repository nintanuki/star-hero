# Star Hero — Manual Testing Checklist

Run this after a non-trivial change. The mental rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md); this file lists what to *do*. The strict refactoring rules that used to live here have been consolidated into copilot-instructions.

---

## Smoke test (every change)

```powershell
cd games/sponsor/original/star-hero
python main.py
```

Or via the cabinet launcher: repo root → `python main.py` → **Mr. Navarro's Games → Original Games → Star Hero**. Both entry paths must work.

1. **Boot.** "LOADING..." card flashes; main window opens at 600 × 800; no console errors.
2. **Intro screen.** Title art + leaderboard render; intro music plays.
3. **CRT overlay** is visible (scanlines + flicker).

---

## Starting a run

4. Pressing `Enter` (keyboard) or `A` / `Start` (controller) starts a run.
5. Intro music stops and BGM begins on transition.
6. Player ship spawns at the configured `INITIAL_POSITION`.

## Player controls

7. **Move.** WASD / arrows / D-pad / left stick all move the ship.
8. **Fire.** `Space` / `A` button fires lasers at the active rate.
9. **Forward boost.** Holding `F` / `Y` increases speed and drains the boost meter.
10. **Side boost.** `L1` / `R1` boosts left / right respectively.
11. **Brake.** Holding `G` / `X` slows the world speed (background, aliens, alien lasers).
12. **Bomb.** First `B` press launches a bomb; second press while airborne detonates it into a blast.

## Aliens

13. Red, green, yellow, and blue aliens all spawn over time.
14. Yellow aliens follow a zigzag path.
15. Blue aliens occasionally stop midway and fire a confusion beam; if hit, the player's horizontal controls reverse for the duration.
16. Alien lasers descend at the configured speed and damage the player on contact.
17. Score ramps difficulty: spawn rate, alien laser rate, and background scroll all step up.

## Powerups

18. Red alien drops include hearts (when not at max) and rare shield orbs.
19. Green alien drops cycle the laser tier (single → twin → hyper).
20. Yellow alien drops cycle rapid-fire tiers.
21. Blue alien drops the rainbow beam.
22. Bomb pickups increase the bomb counter by one.
23. None of the above crash on pickup.

## Damage layering

24. Active shield blocks alien laser damage and alien collision damage.
25. With no shield but an active powerup state, the **first hit strips the powerup** instead of removing a heart.
26. With no shield and no powerup state, a hit removes a heart and triggers the damage flash.
27. Reaching 0 hearts triggers the death-delay timer; player ship is hidden but the world keeps moving.

## Game over

28. After the death delay, aliens / powerups clear, BGM stops, and the game-over screen appears.
29. If the score qualifies, initials entry is offered. Arrows / D-pad / hat all navigate; Enter / A / Start submits.
30. After submitting (or skipping), pressing Enter / A / Start starts a new run.

## Pause + global controls

31. `Enter` (during a run) and `Start` (during a run) pause the run; pause music plays.
32. `Enter` / `Start` again resumes.
33. `F11` and Back (Select) toggle fullscreen at any time.
34. `+` / `-` and D-pad up / down adjust master volume; the volume bar HUD appears for `UISettings.VOLUME_DISPLAY_TIME` ms.
35. `M` toggles debug mute.
36. `Esc` quits cleanly. **Scores are saved** before exit.
37. Holding `Start + Back + L1 + R1` on a controller exits cleanly. **Scores are saved** before exit.

---

## Failure-mode tests

- Hotplug a controller mid-run. Inputs continue to work without restart.
- Disconnect a controller mid-run. The game does not crash; `quit_combo_pressed` continues to function.
- Delete the leaderboard JSON. Boot. The game should display an empty leaderboard, not crash.

---

## Settings-change tests

When [settings.py](../settings.py) is edited:

- Visually confirm the changed section reflects the new values (player speed, alien speeds, spawn rates, durations, colors, font sizes).
- Confirm no other section regressed.
- `grep` for the literal value to confirm no constants leaked back into `core/`, `systems/`, or `ui/` files.

---

## Sign-off

- [ ] Smoke test passed.
- [ ] Player controls passed.
- [ ] Alien spawning, firing, and difficulty ramp passed.
- [ ] All powerup drops confirmed without crash.
- [ ] Damage layering (shield → powerup strip → heart loss) confirmed.
- [ ] Game over and initials entry passed.
- [ ] Pause and global controls passed.
- [ ] [docs/CHANGELOG.md](CHANGELOG.md) updated.
- [ ] [docs/ARCHITECTURE.md](ARCHITECTURE.md) updated if structure changed.
- [ ] [docs/TODO.md](TODO.md) updated if a roadmap item was completed.