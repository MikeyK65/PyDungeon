from __future__ import annotations

import pygame

from . import settings
from .player import Player


class HUD:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

    def draw(
        self,
        surface: pygame.Surface,
        player: Player,
        floor_number: int,
        enemies_remaining: int,
        has_key: bool,
        message: str | None = None,
    ) -> None:
        hud_rect = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.HUD_HEIGHT)
        pygame.draw.rect(surface, settings.HUD_COLOR, hud_rect)
        pygame.draw.line(surface, settings.ACCENT_COLOR, (0, hud_rect.bottom), (hud_rect.right, hud_rect.bottom), 2)

        health_text = self.font.render(
            f"Health: {player.health}/{player.max_health}", True, settings.TEXT_COLOR
        )
        score_text = self.font.render(f"Score: {player.score}", True, settings.TEXT_COLOR)
        lives_text = self.small_font.render(f"Lives: {player.lives}", True, settings.ACCENT_COLOR)
        floor_text = self.small_font.render(f"Floor: {floor_number}", True, settings.TEXT_COLOR)
        enemy_text = self.small_font.render(f"Enemies: {enemies_remaining}", True, settings.TEXT_COLOR)
        key_text = self.small_font.render(
            f"Key: {'Yes' if has_key else 'No'}",
            True,
            settings.KEY_COLOR if has_key else settings.TEXT_COLOR,
        )

        surface.blit(health_text, (20, 14))
        surface.blit(score_text, (280, 14))
        surface.blit(lives_text, (20, 38))
        surface.blit(floor_text, (280, 40))
        surface.blit(enemy_text, (390, 40))
        surface.blit(key_text, (500, 14))

        if player.active_power_up is not None:
            buff_text = self.small_font.render(
                f"Buff: {player.active_power_up} {player.power_up_timer:0.1f}s",
                True,
                settings.POWER_UP_COLOR,
            )
            surface.blit(buff_text, (580, 40))

        if message:
            message_text = self.font.render(message, True, settings.ACCENT_COLOR)
            surface.blit(message_text, (760, 18))