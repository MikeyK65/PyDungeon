from __future__ import annotations

from dataclasses import dataclass

import pygame

from . import settings
from .dungeon import Dungeon


@dataclass
class Projectile:
    position: pygame.Vector2
    velocity: pygame.Vector2
    damage: int
    owner: str
    color: tuple[int, int, int]
    radius: int
    active: bool = True

    @classmethod
    def create(
        cls,
        position: tuple[int, int],
        direction: pygame.Vector2,
        *,
        speed: float,
        damage: int,
        owner: str,
        color: tuple[int, int, int],
    ) -> "Projectile":
        normalized = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1, 0)
        return cls(
            position=pygame.Vector2(position),
            velocity=normalized * speed,
            damage=damage,
            owner=owner,
            color=color,
            radius=settings.PROJECTILE_SIZE // 2,
        )

    @property
    def rect(self) -> pygame.Rect:
        size = self.radius * 2
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (round(self.position.x), round(self.position.y))
        return rect

    def update(self, delta_time: float, dungeon: Dungeon) -> None:
        if not self.active:
            return
        self.position += self.velocity * delta_time
        if not dungeon.is_walkable(self.rect):
            self.active = False

    def draw(self, surface: pygame.Surface, assets) -> None:
        sprite = assets.get_projectile_frame(self.radius * 2)
        surface.blit(sprite, self.rect)