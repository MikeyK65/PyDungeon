from __future__ import annotations

import random

import pygame

from . import settings
from .dungeon import Dungeon
from .player import Player


class Enemy:
    def __init__(self, position: tuple[int, int]) -> None:
        self.rect = pygame.Rect(0, 0, settings.TILE_SIZE - 12, settings.TILE_SIZE - 12)
        self.rect.center = position
        self.speed = settings.ENEMY_SPEED
        self.max_health = settings.ENEMY_MAX_HEALTH
        self.health = self.max_health
        self.wander_direction = pygame.Vector2(random.choice((-1, 1)), random.choice((-1, 1)))
        self.wander_timer = random.uniform(0.5, 1.5)

    def update(self, delta_time: float, player: Player, dungeon: Dungeon) -> None:
        to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if to_player.length_squared() < (settings.TILE_SIZE * 6) ** 2:
            direction = to_player.normalize() if to_player.length_squared() > 0 else pygame.Vector2()
        else:
            self.wander_timer -= delta_time
            if self.wander_timer <= 0:
                self.wander_direction = pygame.Vector2(
                    random.choice((-1, 0, 1)), random.choice((-1, 0, 1))
                )
                if self.wander_direction.length_squared() > 0:
                    self.wander_direction = self.wander_direction.normalize()
                self.wander_timer = random.uniform(0.5, 1.5)
            direction = self.wander_direction

        movement = direction * self.speed * delta_time
        self._move_axis(movement.x, 0, dungeon)
        self._move_axis(0, movement.y, dungeon)

    def _move_axis(self, dx: float, dy: float, dungeon: Dungeon) -> None:
        candidate = self.rect.move(round(dx), round(dy))
        if dungeon.is_walkable(candidate):
            self.rect = candidate

    def attack(self, player: Player) -> None:
        # PRD 3.1: this will branch into enemy-specific attack patterns.
        if self.rect.colliderect(player.rect):
            player.take_damage(1)

    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

    def is_defeated(self) -> bool:
        return self.health <= 0

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.ENEMY_COLOR, self.rect, border_radius=6)