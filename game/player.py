from __future__ import annotations

import pygame

from . import settings
from .dungeon import Dungeon


class Player:
    def __init__(self, position: tuple[int, int]) -> None:
        self.rect = pygame.Rect(0, 0, settings.TILE_SIZE - 10, settings.TILE_SIZE - 10)
        self.rect.center = position
        self.base_speed = settings.PLAYER_SPEED
        self.speed = self.base_speed
        self.max_health = settings.PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.score = 0
        self.lives = settings.PLAYER_LIVES
        self.facing = pygame.Vector2(1, 0)
        self.attack_cooldown = 0.0
        self.attack_timer = 0.0
        self.damage_flash_timer = 0.0
        self.invulnerability_timer = 0.0
        self.active_power_up: str | None = None
        self.power_up_timer = 0.0
        self.is_moving = False

    def update(self, delta_time: float, dungeon: Dungeon) -> None:
        self.attack_cooldown = max(0.0, self.attack_cooldown - delta_time)
        self.attack_timer = max(0.0, self.attack_timer - delta_time)
        self.damage_flash_timer = max(0.0, self.damage_flash_timer - delta_time)
        self.invulnerability_timer = max(0.0, self.invulnerability_timer - delta_time)

        if self.power_up_timer > 0:
            self.power_up_timer = max(0.0, self.power_up_timer - delta_time)
            if self.power_up_timer == 0:
                self._clear_power_up()

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
            self.facing = movement.normalize()
            movement = movement.normalize() * self.speed * delta_time

        self.is_moving = movement.length_squared() > 0

        self._move_axis(movement.x, 0, dungeon)
        self._move_axis(0, movement.y, dungeon)

    def _move_axis(self, dx: float, dy: float, dungeon: Dungeon) -> None:
        candidate = self.rect.move(round(dx), round(dy))
        if dungeon.is_walkable(candidate):
            self.rect = candidate

    def take_damage(self, amount: int) -> bool:
        if self.invulnerability_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.damage_flash_timer = 0.2
        self.invulnerability_timer = settings.PLAYER_INVULNERABILITY_TIME
        return True

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def attack(self) -> pygame.Rect | None:
        # PRD 3.1: this starts as a directional melee hitbox and can expand later.
        if self.attack_cooldown > 0:
            return None

        direction = self.facing if self.facing.length_squared() > 0 else pygame.Vector2(1, 0)
        offset = direction * settings.ATTACK_RANGE
        attack_rect = pygame.Rect(0, 0, settings.ATTACK_SIZE, settings.ATTACK_SIZE)
        attack_rect.center = (
            round(self.rect.centerx + offset.x),
            round(self.rect.centery + offset.y),
        )
        self.attack_cooldown = settings.ATTACK_COOLDOWN
        self.attack_timer = settings.ATTACK_ACTIVE_TIME
        return attack_rect

    def get_attack_rect(self) -> pygame.Rect | None:
        if self.attack_timer <= 0:
            return None
        direction = self.facing if self.facing.length_squared() > 0 else pygame.Vector2(1, 0)
        offset = direction * settings.ATTACK_RANGE
        attack_rect = pygame.Rect(0, 0, settings.ATTACK_SIZE, settings.ATTACK_SIZE)
        attack_rect.center = (
            round(self.rect.centerx + offset.x),
            round(self.rect.centery + offset.y),
        )
        return attack_rect

    def collect_pickup(self, pickup_type: str, value: int) -> None:
        # PRD 3.1 and 3.2: connect health packs, treasure, and dungeon loot here.
        if pickup_type == "score":
            self.score += value
        elif pickup_type == "health":
            self.heal(value)
        elif pickup_type == "power_up":
            self.apply_power_up("speed")

    def apply_power_up(self, power_up_type: str) -> None:
        # PRD 3.1: temporary speed, damage, and invulnerability hooks belong here.
        self.active_power_up = power_up_type
        self.power_up_timer = settings.POWER_UP_DURATION
        if power_up_type == "speed":
            self.speed = self.base_speed + settings.SPEED_POWER_UP_BONUS

    def _clear_power_up(self) -> None:
        self.active_power_up = None
        self.speed = self.base_speed

    def is_defeated(self) -> bool:
        return self.health <= 0

    def respawn(self, position: tuple[int, int]) -> None:
        self.rect.center = position
        self.health = self.max_health
        self.attack_cooldown = 0.0
        self.attack_timer = 0.0
        self.damage_flash_timer = 0.0
        self.invulnerability_timer = settings.PLAYER_INVULNERABILITY_TIME
        self._clear_power_up()

    def draw(self, surface: pygame.Surface, assets, animation_time: float) -> None:
        sprite = assets.get_entity_frame(
            "player",
            animation_time,
            moving=self.is_moving,
            attacking=self.attack_timer > 0,
            facing_x=self.facing.x,
            flash=self.damage_flash_timer > 0,
            size=self.rect.size,
        )
        surface.blit(sprite, self.rect)

        attack_rect = self.get_attack_rect()
        if attack_rect is not None:
            pygame.draw.rect(surface, settings.ACCENT_COLOR, attack_rect, width=2, border_radius=4)