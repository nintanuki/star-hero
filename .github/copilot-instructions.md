# Copilot Instructions for Star Hero

These rules apply to **every** editor of this codebase, human or AI. They are not suggestions. Read this file before each session.

This game is a **standalone project**. It happens to live inside the Arcade Cabinet repo, but its code is agnostic to the launcher: running `python main.py` from this folder must always work on its own. Do not import launcher modules, do not assume the launcher exists, and do not edit files outside this folder from a Star Hero change.

---

## Required reading order (before any change)

1. [README.md](../README.md) — what the project is and how to run it.
2. [docs/TODO.md](../docs/TODO.md) — current phase and roadmap.
3. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — how the code actually works.
4. [docs/CHANGELOG.md](../docs/CHANGELOG.md) — most recent changes, so you know the current state.
5. The source files relevant to your task.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

---

## Required actions (after any change)

- Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md) following the format defined at the top of that file (ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after code, why, and editor name including the AI model used).
- If your change altered how a system works, update the matching section of [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md). Out-of-date architecture docs are worse than none.
- If your change completes or adds a roadmap item, update [docs/TODO.md](../docs/TODO.md) (mark `[x]`, do not delete).
- Run the manual smoke checks in [docs/TESTING.md](../docs/TESTING.md).

---

## Code style

- All Python code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- Keep code free of dead imports, unused variables, unused functions, and legacy code.

## Architecture rules

- `GameManager` ([main.py](../main.py)) must stay thin. Offload responsibilities to dedicated managers (`CollisionManager`, `ScoreManager`, `SessionStateManager`, `SpawnDirector` in `systems/managers.py`; `Audio` in `systems/audio.py`; `Style` in `ui/style.py`; `CRT` in `ui/crt.py`).
- Classes should communicate through `GameManager` where possible. Avoid systems reaching directly into each other.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- All constants live in [settings.py](../settings.py). **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.
- Prefer adding a new `*Settings` class in `settings.py` over expanding an existing one when the new field is not closely related to its neighbors.

## File and function layout

- Inside a class, group functions by role (boot, lifecycle, gameplay actions, audio, event handling, per-frame update / render).
- `update` and `run` go **last** and should only call other functions on the class.
- Separate logical sections inside a file with an all-caps banner comment, exactly this style:

  ```python
      # -------------------------
      # SECTION NAME
      # -------------------------
  ```

  Match the leading indentation of the surrounding class body. Keep the dashes the same length and the name in ALL CAPS.

## Comments and docstrings

- Every class and function must have a docstring with a one-line summary, plus `Args:` / `Returns:` blocks when applicable.
- Do not remove docstrings. Update them in place if behavior changes.
- Do not remove comments unless they are inaccurate; prefer updating them.
- Comments must explain **why**, not just what.
- Do not leave comments noting that a change was made, unless they explain a non-obvious bug fix or unconventional code.

## UI text

- Player-facing text in the HUD, intro, pause, and game-over screens should remain in the existing visual style (the `Pixeled` font is already used at fixed sizes via `FontSettings`). When adding a new label, use ALL CAPS to match the retro aesthetic.

---

## Mental testing checklist (run after major changes)

- The game launches (`python main.py`) without console errors.
- Intro screen plays intro music; pressing Enter / A / Start begins a run.
- Player can move, fire, brake, boost, and bomb with both keyboard and controller.
- Aliens spawn, animate, fire, and award score; difficulty ramps with score.
- All four alien colors and all powerup drops resolve without crashing.
- Death triggers the death-delay timer, then the game-over screen with initials entry if the score qualifies.
- Pause/unpause, fullscreen, master volume, and debug mute all work in their permitted contexts.
- `Esc` and the controller quit combo (`Start + Back + L1 + R1`) both exit cleanly and call `ScoreManager.save_scores()` first.
- No new magic numbers leaked outside `settings.py`.

For the actionable run-through, see [docs/TESTING.md](../docs/TESTING.md).
