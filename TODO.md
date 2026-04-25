### Issues That Need to be Fixed
* Volume goes up and down when player enters initials!
* Confusion beam sound still plays when game is paused
* Player can hold button down for laser, disable this so they have to press the buttone very time
* Logic for leaderboard scores and initials uses a lot of code and functions. Put into it's own class?
* Player ship sprite can still move and shoot lasers briefly after death?
* Windows flags exe made with Pyinstaller as a virus... [try this.](https://plainenglish.io/blog/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184)
* Add resize window option that works, see: https://stackoverflow.com/questions/64543449/update-during-resize-in-pygame
* Volume bar only shows up for keyboard, not controller
* Volume bar overlaps with level display

### Ideas for Future Changes and Additions
* Change every reference to break with "time slow"
* Boost should only drain meter if player is MOVING IN THE DIRECTION that boost is giving them. If the hold L1 while moving right, the boost drains and they don't go any faster...
* Changed controller buttons but did not update or add features to keyboard for boost, volume, etc
* Cleanup player's get input method, it's a mess, there are two separate loops for joystick
* No sound effect for bombs or when you lose a powerup yet
* Bombs should only be dropped by red enemies. Because they are not tiered, red enemies need to have different chances for each of their powerups. Commonality should be bombs > hearts > shield
* Add indicator for when the shield is about to disappear
* Change boost/time slow to L1 and R1 (which is which?) and move volume to D-Pad
* Add sound effects for all new powerups and effects
* Add floating scores
* Score bonus + message for destroying multiple enemies at once?
* Add border to the left and right sides of the screen
* Add special message for each level?
* Make enemy sprites occasionaly do a spin or divebomb
* Add random scrolling backgrounds (planet zone, nebula, etc)
* Add "barrel roll" to repel lasers? AND/OR fast movement left and right?
* Add drop shadow to sprites?
* Player should not be able to hold down the shoot button
* Add "bombs" that can be shot with a different button and have AOE damage
* Ship should flash green, gold or blue when picking up powerups
* Display indicator when powerup is active (maybe it blinks before going away?)
* Different rates of fire for different enemies (yellow shoots more, blue shoots the most, but blue's lasers are too slow)
* Enemy shoots a beam (in the style of the ship stealer from Galaga) that makes player purple and reverses controls.
* Add shield powerup?
* Display sprites of aliens on screen with how many points they are worth
* Allow player to enter initials if they get the high score
* Figure out how to use increasing score to increase rate of alien and laser spawn
* Show controls in game (create images with WASD, Spacebar and arrow keys, etc)
* Menu and options
* Quit game option
* Bosses?
* Multiple levels/stages?
* Speed boost that uses energy?
* Add thrusters animation

### Refactoring Changes to Make
* Add timer class, remove this responsibility from GameManager
* Include a [state manager class](https://www.youtube.com/watch?v=j9yMFG3D7fg) to manage game_active status. Figure out how to integrate this with the game manager class

### Asset Changes to Make
* Replace player and enemy sprites with original art
* Replace all placeholder music with better original music

### Misc Notes
* Use `channel_#.play(music, -1)` to loop instead?
* Try [pygame.mixer.music](https://www.pygame.org/docs/ref/music.html) instead of the sound class for music, gives more control like queue music.
* The dark blue for HYPER in the status is too dark to read, change to CYAN or flashing colors like rainbow beam. Consider doing the same for auto, fast flashing. Change sound effect for hyper to something that sounds very powerful (x wing or tie fighter laser sounds?)