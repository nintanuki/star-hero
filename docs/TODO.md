# Star Hero — Roadmap & TODO

The build is **playable and content-complete** for a one-stage shoot 'em up. Active work is bug fixes, balance tuning, polish, and stretch-goal content. Items are grouped by phase so contributors know where to push next.

---

## Phase 1 — Bugs to fix

- [ ] Confusion beam sound still plays when the game is paused. *(Workaround: sound currently removed.)*
- [ ] Verify whether the player ship can still move and fire briefly after death. May already be fixed.
- [ ] Explosions sometimes don't trigger from touching an enemy with the shield active.
- [ ] Windows flags PyInstaller-built `.exe` as a virus. See [this writeup](https://plainenglish.io/blog/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184) for known mitigations.
- [ ] Add a working resize-window option. See [this thread](https://stackoverflow.com/questions/64543449/update-during-resize-in-pygame).

## Phase 2 — Balance

- [ ] Different rates of fire per alien color. Yellow should shoot the most; blue the most often, but blue's lasers are currently slow enough to be trivial.
- [ ] Re-evaluate spawn weights at high score brackets — the ramp may saturate too aggressively at `MIN_SPAWN_RATE`.

## Phase 3 — UI / UX

- [ ] When the player picks up the third yellow powerup (auto-fire tier), display "HOLD THE A BUTTON" on screen.
- [ ] Display an indicator when a powerup is active (and have it blink before expiry).
- [ ] Add floating score numbers when an alien is destroyed.
- [ ] Bonus score + on-screen message for destroying multiple enemies at once.
- [ ] Ship flashes green / gold / blue when picking up powerups.
- [ ] Show controls in-game (image cards for WASD, Space, arrow keys, controller buttons).
- [ ] Display alien sprites + their point values somewhere on screen (intro? pause?).
- [ ] Menu and options screen with a quit-game option.
- [ ] Drop shadows on sprites.
- [ ] Border art on the left and right edges of the screen.

## Phase 4 — Content

- [ ] Special intro message for each "level" (score-bracket).
- [ ] Random scrolling backgrounds (planet zone, nebula, etc.) with parallax.
- [ ] Aliens occasionally spin or divebomb.
- [ ] Add player thruster animation.
- [ ] "Barrel roll" maneuver to repel lasers and/or fast horizontal dash.
- [ ] Bosses.
- [ ] Multiple stages.

## Phase 5 — Asset replacement

- [ ] Replace player and enemy sprites with original art.
- [ ] Replace placeholder music with original tracks.

## Phase 6 — Naming / refactor

- [ ] Rename every reference to "brake" with "time slow" (the mechanic was renamed conceptually but the code still calls it brake).

---

## Code health

- [ ] `high_score.txt` at the project root is vestigial — the leaderboard JSON is now the source of truth. Decide whether to migrate any remaining content out of it and delete the file, or document why it stays.
- [ ] `from settings import *` is used in `main.py` and several other files. Acceptable historically; new modules should import only what they need.

---

## Open questions

- Does the project ever ship as a standalone PyInstaller `.exe`, or is the cabinet launcher the only deployment target? Affects whether Phase 1's antivirus item is a real priority.
- Is the bomb-detonate-on-second-press control intuitive enough, or should detonation move to a separate button?

---

## Documentation maintenance

Every pass that meaningfully changes a system must:

1. Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) to reflect the new shape.
2. Append entries to [docs/CHANGELOG.md](CHANGELOG.md) per the format in that file.
3. Move completed items here from `[ ]` to `[x]` (do not delete — leave as a record).
