from __future__ import annotations

from dataclasses import dataclass

import pygame

from . import settings


@dataclass
class Trap:
    rect: pygame.Rect

    @classmethod
    def create(cls, position: tuple[int, int]) -> "Trap":
        rect = pygame.Rect(0, 0, settings.TILE_SIZE - 10, settings.TILE_SIZE - 10)
        rect.center = position
        return cls(rect=rect)

    def draw(self, surface: pygame.Surface, assets, animation_time: float) -> None:
        sprite = assets.get_trap_frame(animation_time, self.rect.size)
        surface.blit(sprite, self.rect)