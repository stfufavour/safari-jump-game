# Safari Jump 🦁

A simple 2D endless-runner game built with Python and `pygame-ce`.

You play a safari explorer running across the savanna, jumping over
obstacles that come your way: **water puddles**, **rocks**, and **sleeping
lions**. The game gets faster the longer you survive, and your best score
is saved between sessions.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5%2B-green)

## Gameplay

- Press **SPACE** or **UP ARROW** to jump over obstacles.
- Press **P** to pause the game.
- Press **R** to restart after Game Over.
- Press **ESC** to quit.

Your score increases the longer you survive, and every obstacle you clear
brings you closer to a new high score, which is stored in `high_score.json`
so it persists the next time you play.

## Project structure

```
safari-jump-game/
├── safari_jump.py      # main game source code
├── requirements.txt     # dependencies
├── high_score.json      # auto-created after your first run
└── .gitignore
```

## How it's built

The game is organized around a small state machine (`GameState`: MENU,
PLAYING, PAUSED, GAME_OVER) and a handful of classes that each handle one
part of the game:

- `Background` – draws the parallax sky, hills, trees, and scrolling ground
- `Player` – handles movement, jumping physics, and running animation
- `Obstacle` (abstract base class) with three subclasses:
  `WaterObstacle`, `RockObstacle`, `LionObstacle`
- `ObstacleSpawner` – decides when and what to spawn
- `ParticleSystem` – dust particles kicked up while running and landing
- `HighScoreManager` – loads/saves the best score to a JSON file

All graphics are drawn directly with `pygame.draw` calls — there are no
external image or sound assets, so the whole game is a single Python file.

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/stfufavour/safari-jump-game.git
   cd safari-jump-game
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the game:
   ```bash
   python safari_jump.py
   ```

## Possible future improvements

- Sound effects and background music
- More obstacle types (birds, thorny bushes)
- A scrolling difficulty curve tied to a proper level system
- Mobile touch controls

## Author

Favour — Information Systems and Data Management, BIUST
