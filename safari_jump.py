"""
Safari Jump
-----------
An endless-runner game built with pygame-ce.

You control a safari explorer who must jump over obstacles that appear
along the trail: water puddles, rocks, and sleeping lions.

Controls:
    SPACE / UP ARROW  - Jump
    P                 - Pause / Unpause
    R                 - Restart after Game Over
    ESC               - Quit

Run with:
    python safari_jump.py

Author: Favour
"""

import pygame
import random
import sys
import json
import os
from enum import Enum, auto
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
WIDTH, HEIGHT = 900, 400
GROUND_Y = 320
FPS = 60

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_score.json")

# Colors - safari theme
SKY_TOP = (255, 200, 110)
SKY_BOTTOM = (255, 231, 170)
SAND = (222, 184, 122)
SAND_DARK = (196, 154, 92)
SUN = (255, 236, 150)
TREE_TRUNK = (101, 67, 33)
TREE_LEAF = (60, 110, 55)
WATER_COLOR = (64, 150, 205)
WATER_LIGHT = (120, 195, 235)
ROCK_COLOR = (120, 112, 100)
ROCK_DARK = (90, 84, 75)
LION_BODY = (196, 154, 88)
LION_MANE = (120, 78, 40)
SKIN = (196, 148, 108)
SAFARI_KHAKI = (168, 150, 96)
SAFARI_KHAKI_DARK = (132, 116, 72)
HAT_COLOR = (150, 111, 51)
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
TEXT_DARK = (60, 40, 20)
DUST_COLOR = (210, 180, 140)


# ----------------------------------------------------------------------
# Game state machine
# ----------------------------------------------------------------------
class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


# ----------------------------------------------------------------------
# High score persistence
# ----------------------------------------------------------------------
class HighScoreManager:
    """Loads and saves the best score to a small JSON file next to the script."""

    def __init__(self, path=HIGH_SCORE_FILE):
        self.path = path
        self.best_score = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                    return int(data.get("best_score", 0))
            except (json.JSONDecodeError, ValueError, OSError):
                return 0
        return 0

    def update(self, score):
        if score > self.best_score:
            self.best_score = score
            self._save()
            return True
        return False

    def _save(self):
        try:
            with open(self.path, "w") as f:
                json.dump({"best_score": self.best_score}, f)
        except OSError:
            pass  # not critical if this fails


# ----------------------------------------------------------------------
# Particle system (dust kicked up while running / landing)
# ----------------------------------------------------------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: int
    max_life: int
    radius: int


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=6):
        for _ in range(count):
            self.particles.append(Particle(
                x=x + random.uniform(-4, 4),
                y=y,
                vx=random.uniform(-1.5, 1.5),
                vy=random.uniform(-2.5, -0.5),
                life=random.randint(15, 30),
                max_life=30,
                radius=random.randint(1, 3),
            ))

    def update(self):
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.12
            p.life -= 1
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            alpha_ratio = max(0.0, p.life / p.max_life)
            radius = max(1, int(p.radius * alpha_ratio))
            color = tuple(int(c * alpha_ratio + 255 * (1 - alpha_ratio) * 0.15) for c in DUST_COLOR)
            pygame.draw.circle(surface, color, (int(p.x), int(p.y)), radius)


# ----------------------------------------------------------------------
# Background layers (parallax)
# ----------------------------------------------------------------------
class Background:
    """Draws the sky, sun, hills, trees, and scrolling ground."""

    def __init__(self):
        self.scroll_x = 0.0

    def update(self, speed):
        self.scroll_x += speed

    def draw(self, surface):
        self._draw_sky(surface)
        self._draw_sun(surface)
        self._draw_hills(surface)
        self._draw_trees(surface)
        self._draw_ground(surface)

    def _draw_sky(self, surface):
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
            g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
            b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

    def _draw_sun(self, surface):
        pygame.draw.circle(surface, SUN, (720, 90), 55)

    def _draw_hills(self, surface):
        hill_offset = int(self.scroll_x * 0.2) % WIDTH
        for ox in (-hill_offset, WIDTH - hill_offset):
            pygame.draw.ellipse(surface, (200, 160, 110), (ox, 250, 260, 120))
            pygame.draw.ellipse(surface, (200, 160, 110), (ox + 200, 260, 300, 130))

    def _draw_trees(self, surface):
        tree_offset = int(self.scroll_x * 0.5) % 400
        trunk_height = 70
        trunk_top = GROUND_Y - trunk_height
        for ox in range(-tree_offset, WIDTH + 400, 400):
            trunk_x = ox + 60
            pygame.draw.rect(surface, TREE_TRUNK, (trunk_x, trunk_top, 8, trunk_height))
            pygame.draw.ellipse(surface, TREE_LEAF, (trunk_x - 45, trunk_top - 35, 100, 30))
            pygame.draw.ellipse(surface, TREE_LEAF, (trunk_x - 25, trunk_top - 50, 70, 25))

    def _draw_ground(self, surface):
        pygame.draw.rect(surface, SAND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        stripe_offset = int(self.scroll_x) % 40
        for x in range(-stripe_offset, WIDTH, 40):
            pygame.draw.line(surface, SAND_DARK, (x, GROUND_Y + 10), (x + 20, GROUND_Y + 10), 3)
            pygame.draw.line(surface, SAND_DARK, (x + 10, GROUND_Y + 30), (x + 30, GROUND_Y + 30), 3)
        pygame.draw.line(surface, SAND_DARK, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)


# ----------------------------------------------------------------------
# Player
# ----------------------------------------------------------------------
class PlayerAnimState(Enum):
    RUNNING = auto()
    JUMPING = auto()


class Player:
    def __init__(self, particles: ParticleSystem):
        self.x = 110
        self.width = 40
        self.height = 60
        self.y = float(GROUND_Y - self.height)
        self.vel_y = 0.0
        self.gravity = 1.5
        self.jump_power = -20.0
        self.on_ground = True
        self.anim_state = PlayerAnimState.RUNNING
        self.particles = particles
        self._step_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            self.anim_state = PlayerAnimState.JUMPING
            self.particles.emit(self.x + self.width / 2, GROUND_Y, count=8)

    def update(self, frame):
        self.y += self.vel_y
        self.vel_y += self.gravity
        ground_level = GROUND_Y - self.height
        if self.y >= ground_level:
            just_landed = not self.on_ground
            self.y = ground_level
            self.vel_y = 0
            self.on_ground = True
            self.anim_state = PlayerAnimState.RUNNING
            if just_landed:
                self.particles.emit(self.x + self.width / 2, GROUND_Y, count=10)

        if self.on_ground:
            self._step_timer += 1
            if self._step_timer % 10 == 0:
                self.particles.emit(self.x + 12, GROUND_Y, count=2)

    def draw(self, surface, frame):
        x, y = int(self.x), int(self.y)
        bob = 0
        leg_swing = 0
        if self.anim_state == PlayerAnimState.RUNNING:
            bob = int(2 * abs((frame % 20) - 10) / 10)
            leg_swing = 8 * (1 if (frame // 6) % 2 == 0 else -1)

        # legs
        pygame.draw.line(surface, SAFARI_KHAKI_DARK,
                          (x + 15, y + 45 - bob), (x + 15 - leg_swing, y + 60 - bob), 6)
        pygame.draw.line(surface, SAFARI_KHAKI_DARK,
                          (x + 25, y + 45 - bob), (x + 25 + leg_swing, y + 60 - bob), 6)

        # body (safari vest)
        pygame.draw.rect(surface, SAFARI_KHAKI, (x + 8, y + 20 - bob, 24, 26), border_radius=4)

        # arms
        arm_swing = -leg_swing
        pygame.draw.line(surface, SKIN, (x + 10, y + 26 - bob), (x + 10 + arm_swing, y + 42 - bob), 5)
        pygame.draw.line(surface, SKIN, (x + 30, y + 26 - bob), (x + 30 - arm_swing, y + 42 - bob), 5)

        # head
        pygame.draw.circle(surface, SKIN, (x + 20, y + 12 - bob), 11)

        # safari hat
        pygame.draw.ellipse(surface, HAT_COLOR, (x + 4, y - 2 - bob, 32, 10))
        pygame.draw.ellipse(surface, HAT_COLOR, (x + 11, y - 10 - bob, 18, 14))

        # face
        pygame.draw.circle(surface, BLACK, (x + 24, y + 11 - bob), 2)


# ----------------------------------------------------------------------
# Obstacles (base class + subclasses)
# ----------------------------------------------------------------------
class Obstacle(ABC):
    def __init__(self, x):
        self.x = float(x)
        self.width = 0
        self.height = 0
        self.y = 0.0

    def update(self, speed):
        self.x -= speed

    def off_screen(self):
        return self.x + self.width < 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) + 4, int(self.y) + 4, self.width - 8, self.height - 4)

    @abstractmethod
    def draw(self, surface, frame):
        raise NotImplementedError


class WaterObstacle(Obstacle):
    def __init__(self, x):
        super().__init__(x)
        self.width = random.randint(70, 110)
        self.height = 14
        self.y = float(GROUND_Y - self.height + 4)

    @property
    def rect(self):
        # flatter hitbox since it's a puddle, not a solid block
        return pygame.Rect(int(self.x) + 6, int(self.y), self.width - 12, self.height)

    def draw(self, surface, frame):
        x, y = int(self.x), int(self.y)
        pygame.draw.ellipse(surface, WATER_COLOR, (x, y, self.width, self.height))
        wobble = int(2 * ((frame // 5) % 3))
        pygame.draw.ellipse(surface, WATER_LIGHT, (x + 8, y + 3 + wobble, self.width - 16, 5))


class RockObstacle(Obstacle):
    def __init__(self, x):
        super().__init__(x)
        self.width = random.randint(34, 50)
        self.height = random.randint(30, 46)
        self.y = float(GROUND_Y - self.height)

    def draw(self, surface, frame):
        x, y = int(self.x), int(self.y)
        pygame.draw.ellipse(surface, ROCK_DARK, (x, y + self.height - 10, self.width, 14))
        pygame.draw.polygon(surface, ROCK_COLOR, [
            (x, y + self.height),
            (x + self.width * 0.15, y + self.height * 0.3),
            (x + self.width * 0.5, y),
            (x + self.width * 0.85, y + self.height * 0.25),
            (x + self.width, y + self.height),
        ])
        pygame.draw.line(surface, ROCK_DARK,
                          (x + self.width * 0.5, y + self.height * 0.35),
                          (x + self.width * 0.4, y + self.height * 0.8), 2)


class LionObstacle(Obstacle):
    def __init__(self, x):
        super().__init__(x)
        self.width = 60
        self.height = 30
        self.y = float(GROUND_Y - self.height)

    def draw(self, surface, frame):
        x, y = int(self.x), int(self.y)
        pygame.draw.ellipse(surface, LION_BODY, (x + 14, y + 8, 44, 20))
        pygame.draw.circle(surface, LION_MANE, (x + 14, y + 15), 13)
        pygame.draw.circle(surface, LION_BODY, (x + 14, y + 15), 8)
        pygame.draw.polygon(surface, LION_BODY, [(x + 54, y + 12), (x + 60, y + 4), (x + 58, y + 16)])
        pygame.draw.circle(surface, BLACK, (x + 10, y + 13), 1)
        zz_bounce = int(4 * abs((frame % 40) - 20) / 20)
        font = pygame.font.SysFont("arial", 20)
        z_font = font.render("z z z", True, TEXT_DARK)
        surface.blit(z_font, (x + 8, y - 16 - zz_bounce))


OBSTACLE_CLASSES = [WaterObstacle, RockObstacle, LionObstacle]


class ObstacleSpawner:
    """Handles obstacle timing and creation so Game doesn't need to know the details."""

    def __init__(self):
        self.timer = 0
        self.gap = 90

    def maybe_spawn(self, obstacles):
        self.timer += 1
        if self.timer >= self.gap:
            self.timer = 0
            self.gap = random.randint(70, 130)
            obstacle_cls = random.choice(OBSTACLE_CLASSES)
            obstacles.append(obstacle_cls(WIDTH + 20))


# ----------------------------------------------------------------------
# Main game
# ----------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Safari Jump")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)

        self.high_scores = HighScoreManager()
        self.state = GameState.MENU
        self._new_run()

    def _new_run(self):
        self.particles = ParticleSystem()
        self.background = Background()
        self.player = Player(self.particles)
        self.spawner = ObstacleSpawner()
        self.obstacles = []
        self.speed = 7.0
        self.score = 0
        self.frame = 0
        self.just_beat_high_score = False

    # -- input handling --------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if self.state == GameState.MENU:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                    self.state = GameState.PLAYING
            elif self.state == GameState.PLAYING:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self.player.jump()
                elif event.key == pygame.K_p:
                    self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_p:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                if event.key == pygame.K_r:
                    self._new_run()
                    self.state = GameState.PLAYING
        return True

    # -- update ------------------------------------------------------------
    def update(self):
        if self.state != GameState.PLAYING:
            return

        self.frame += 1
        self.background.update(self.speed)
        self.player.update(self.frame)
        self.particles.update()

        self.spawner.maybe_spawn(self.obstacles)
        for obs in self.obstacles:
            obs.update(self.speed)
        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        for obs in self.obstacles:
            if self.player.rect.colliderect(obs.rect):
                self.state = GameState.GAME_OVER
                self.just_beat_high_score = self.high_scores.update(self.score // 5)

        self.score += 1
        if self.score % 400 == 0:
            self.speed += 0.6

    # -- drawing -------------------------------------------------------------
    def draw(self):
        surface = self.screen
        self.background.draw(surface)

        for obs in self.obstacles:
            obs.draw(surface, self.frame)
        self.particles.draw(surface)
        self.player.draw(surface, self.frame)

        score_text = self.font_med.render(f"Score: {self.score // 5}", True, TEXT_DARK)
        surface.blit(score_text, (20, 16))
        best_text = self.font_small.render(f"Best: {self.high_scores.best_score}", True, TEXT_DARK)
        surface.blit(best_text, (20, 50))

        if self.state == GameState.MENU:
            self._draw_menu(surface)
        elif self.state == GameState.PAUSED:
            self._draw_overlay(surface, "PAUSED", "Press P to resume")
        elif self.state == GameState.GAME_OVER:
            subtitle = "New High Score! Press R to Restart" if self.just_beat_high_score else "Press R to Restart"
            self._draw_overlay(surface, "GAME OVER", subtitle)

    def _draw_overlay(self, surface, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        title_text = self.font_big.render(title, True, WHITE)
        subtitle_text = self.font_med.render(subtitle, True, WHITE)
        surface.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        surface.blit(subtitle_text, subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    def _draw_menu(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        surface.blit(overlay, (0, 0))
        title_text = self.font_big.render("SAFARI JUMP", True, WHITE)
        subtitle_text = self.font_med.render("Press SPACE to Start", True, WHITE)
        hint_text = self.font_small.render("Jump over water, rocks, and sleeping lions!", True, WHITE)
        surface.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
        surface.blit(subtitle_text, subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
        surface.blit(hint_text, hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    # -- main loop -------------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                running = self.handle_event(event)
                if not running:
                    break

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
