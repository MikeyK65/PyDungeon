from __future__ import annotations

from dataclasses import dataclass

import pygame

from . import settings


@dataclass
class Pickup:
    pickup_type: str
    rect: pygame.Rect
    value: int

    @classmethod
    def create(cls, pickup_type: str, position: tuple[int, int]) -> "Pickup":
        rect = pygame.Rect(0, 0, settings.TILE_SIZE - 14, settings.TILE_SIZE - 14)
        rect.center = position
        if pickup_type == "health":
            value = settings.HEALTH_PICKUP_HEAL
        elif pickup_type == "score":
            value = settings.SCORE_PICKUP_VALUE
        elif pickup_type == "key":
            value = settings.KEY_SCORE_VALUE
        else:
            value = 1
        return cls(pickup_type=pickup_type, rect=rect, value=value)

    def draw(self, surface: pygame.Surface, assets, animation_time: float) -> None:
        sprite = assets.get_pickup_frame(self.pickup_type, animation_time, self.rect.size)
        surface.blit(sprite, self.rect)