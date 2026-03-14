from __future__ import annotations

import pygame

from . import settings
from .player import Player


class HUD:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

    def draw(self, surface: pygame.Surface, player: Player) -> None:
        hud_rect = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.HUD_HEIGHT)
        pygame.draw.rect(surface, settings.HUD_COLOR, hud_rect)
        pygame.draw.line(surface, settings.ACCENT_COLOR, (0, hud_rect.bottom), (hud_rect.right, hud_rect.bottom), 2)

        health_text = self.font.render(
            f"Health: {player.health}/{player.max_health}", True, settings.TEXT_COLOR
        )
        score_text = self.font.render(f"Score: {player.score}", True, settings.TEXT_COLOR)
        lives_text = self.small_font.render(f"Lives: {player.lives}", True, settings.ACCENT_COLOR)

        surface.blit(health_text, (20, 14))
        surface.blit(score_text, (280, 14))
        surface.blit(lives_text, (20, 38))