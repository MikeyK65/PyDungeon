from __future__ import annotations

import pygame

from . import settings
from .dungeon import Dungeon
from .enemy import Enemy
from .hud import HUD
from .player import Player


class GameEngine:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.dungeon = Dungeon(settings.MAP_WIDTH, settings.MAP_HEIGHT, settings.TILE_SIZE)
        self.player = Player(self.dungeon.random_floor_position())
        self.enemies = self._spawn_enemies()
        self.hud = HUD()

    def _spawn_enemies(self) -> list[Enemy]:
        enemies: list[Enemy] = []
        for _ in range(settings.ENEMY_COUNT):
            enemies.append(Enemy(self.dungeon.random_floor_position()))
        return enemies

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(settings.FPS) / 1000.0
            self._handle_events()
            self._update(delta_time)
            self._render()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    # PRD 4: desktop keyboard attack binding placeholder.
                    self.player.attack()

    def _update(self, delta_time: float) -> None:
        self.player.update(delta_time, self.dungeon)

        for enemy in self.enemies:
            enemy.update(delta_time, self.player, self.dungeon)
            enemy.attack(self.player)

        self.enemies = [enemy for enemy in self.enemies if not enemy.is_defeated()]

        # PRD 3.1: pickups and power-ups will be updated alongside enemy and loot systems.
        self._update_pickups(delta_time)
        self._update_power_ups(delta_time)

    def _update_pickups(self, delta_time: float) -> None:
        _ = delta_time

    def _update_power_ups(self, delta_time: float) -> None:
        _ = delta_time

    def _render(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)
        self.dungeon.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)
        self.hud.draw(self.screen, self.player)
        pygame.display.flip()