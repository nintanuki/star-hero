### Issues That Need to be Fixed
* Player ship sprite can still move and shoot lasers briefly after death
* Windows flags exe made with Pyinstaller as a virus... [try this.](https://plainenglish.io/blog/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184)
* Using joystick module program crashes if controller not plugged in?
* Add resize window option that works, see: https://stackoverflow.com/questions/64543449/update-during-resize-in-pygame
* Player can hold button down for laser, disable this for both keyboard and controller, unless they have the beam

### Ideas for Future Changes and Additions
* Player should not be able to hold down the shoot button, but rapid fire should be automatic
* Change Beam powerup into "nuke?"
* Ship should flash green, gold or blue when picking up powerups
* Display indicator when powerup is active (maybe it blinks before going away?)
* Different rates of fire for different enemies (yellow shoots more, blue shoots the most, but blue's lasers are too slow)
* Enemy shoots a beam (in the style of the ship stealer from Galaga) that makes play purple and reverses controls.
* Add shield powerup?
* Display sprites of aliens on screen with how many points they are worth
* Allow player to enter initials if they get the high score
* Figure out how to use increasing score to increase rate of alien and laser spawn
* Show controls in game (create images with WASD, Spacebar and arrow keys, etc)
* Menu and options
* Quit game option
* Enemy animations
* Bosses?
* Multiple levels/stages?
* Speed boost that uses energy?
* Add thrusters animation

### Refactoring Changes to Make
* Add timer class, remove this responsibility from GameManager
* Include a [state manager class](https://www.youtube.com/watch?v=j9yMFG3D7fg) to manage game_active status. Figure out how to integrate this with the game manager class

### Asset Changes to Make
* Replace player and enemy sprites with original art
* Replace placeholder music with original music

### Misc Notes
* Use `channel_#.play(music, -1)` to loop instead?
* Try [pygame.mixer.music](https://www.pygame.org/docs/ref/music.html) instead of the sound class for music, gives more control like queue music.