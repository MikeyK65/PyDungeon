from __future__ import annotations

import pygame

from . import settings
from .dungeon import Dungeon


class Player:
    def __init__(self, position: tuple[int, int]) -> None:
        self.rect = pygame.Rect(0, 0, settings.TILE_SIZE - 10, settings.TILE_SIZE - 10)
        self.rect.center = position
        self.speed = settings.PLAYER_SPEED
        self.max_health = settings.PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.score = 0
        self.lives = 3

    def update(self, delta_time: float, dungeon: Dungeon) -> None:
        movement = pygame.Vector2()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movement.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movement.x += 1

        if movement.length_squared() > 0:
            movement = movement.normalize() * self.speed * delta_time

        self._move_axis(movement.x, 0, dungeon)
        self._move_axis(0, movement.y, dungeon)

    def _move_axis(self, dx: float, dy: float, dungeon: Dungeon) -> None:
        candidate = self.rect.move(round(dx), round(dy))
        if dungeon.is_walkable(candidate):
            self.rect = candidate

    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def attack(self) -> None:
        # PRD 3.1: replace with melee, ranged, and magic attack handling.
        pass

    def collect_pickup(self, pickup_type: str) -> None:
        # PRD 3.1 and 3.2: connect health packs, treasure, and dungeon loot here.
        if pickup_type == "score":
            self.score += 100

    def apply_power_up(self, power_up_type: str) -> None:
        # PRD 3.1: temporary speed, damage, and invulnerability hooks belong here.
        _ = power_up_type

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.PLAYER_COLOR, self.rect, border_radius=6)