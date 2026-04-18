# Star Hero <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/graphics/player_ship.png" height="32">

This is a vertically scrolling space themed shmup (or Shoot'em up) that I am creating using the Pygame module in Python. This is the first game I ever made and the first program I've written of this size and scope. I am continuously changing and adding to this game as I learn more.

To play Star Hero you must have [Python](https://www.python.org/) and [Pygame](https://www.pygame.org/) installed.

I started learning Pygame using [Clear Code's Tutorials](https://www.youtube.com/@ClearCode) and strongly recommend starting with [The ultimate introduction to Pygame](https://www.youtube.com/watch?v=AY9MnQ4x3zk) if you are interested in learning how to make games in Pygame.

## How to Play 
Your ship starts at the center of the screen. You can move in four directions and fire upwards. There is a short cooldown timer between each shot so aim carefully. You have three hearts and if you get hit by a laser or crash into an alien ship you will take damage and lose these hearts If you lose three hearts it's game over and your score is reset. As your score increases the game gets harder, try to get the high score!

### Enemy Drops
* Hearts: Dropped by the Red Alien. Heals the player 
* Laser Upgrades: Twin Laser and Hyper Laser dropped by Green Alien in the shape of a green diamond. Twin laser allows you to hit two enemies side by side at once, hyper goes through enemies and hits those behind.
* Rapid Fire: Temporary powerup dropped by Yellow Alien, lowers cooldown for laser.
* Rainbow Beam: Temporary powerup dropped by Blue Alien. Area effect attack that can hit all the enemies on the screen at once.

### Keyboard Controls
* **WASD** or **Arrow Keys** moves the player ship
* **Spacebar** fires the laser
* Hold **F** key to move twice as fast
* **ALT + ENTER** toggles full screen mode
* **ESC** pauses and unpauses the game
* **+** and **-** keys increase and decrease the volume

On a logitech controller you can move with the left analog stick, press "A" to shoot the laser, and "X" to move faster. Select makes the window full screen, and the L1 and R1 control the volume.

### Enemy Aliens
Each alien sprite behaves differently and is worth a different score value based on color:
* <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/graphics/red1.png" width="20" height="16"> Slow - **100 Points**
* <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/graphics/green1.png" width="20" height="16"> Moderate Speed - **200 Points**
* <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/graphics/yellow1.png" width="20" height="16"> Fast - Moves in a Zigzag Pattern - **300 Points**
* <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/graphics/blue1.png" width="20" height="10"> Very Fast and Rare - **500 Points**
