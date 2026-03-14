from __future__ import annotations

import random

import pygame

from . import settings
from .dungeon import Dungeon
from .player import Player
from .projectile import Projectile


class Enemy:
    def __init__(
        self,
        position: tuple[int, int],
        *,
        speed: int,
        max_health: int,
        damage: int,
        score_value: int,
        color: tuple[int, int, int],
        enemy_type: str,
        size: int | None = None,
    ) -> None:
        rect_size = size if size is not None else settings.TILE_SIZE - 12
        self.rect = pygame.Rect(0, 0, rect_size, rect_size)
        self.rect.center = position
        self.speed = speed
        self.max_health = max_health
        self.health = self.max_health
        self.damage = damage
        self.score_value = score_value
        self.color = color
        self.enemy_type = enemy_type
        self.wander_direction = pygame.Vector2(random.choice((-1, 1)), random.choice((-1, 1)))
        self.wander_timer = random.uniform(0.5, 1.5)
        self.attack_cooldown = random.uniform(0.1, settings.ENEMY_ATTACK_COOLDOWN)
        self.facing = pygame.Vector2(1, 0)
        self.is_moving = False

    def update(self, delta_time: float, player: Player, dungeon: Dungeon) -> None:
        self.attack_cooldown = max(0.0, self.attack_cooldown - delta_time)
        direction = self._get_direction(delta_time, player)

        movement = direction * self.speed * delta_time
        if direction.length_squared() > 0:
            self.facing = direction
        self.is_moving = movement.length_squared() > 0
        self._move_axis(movement.x, 0, dungeon)
        self._move_axis(0, movement.y, dungeon)

    def _get_direction(self, delta_time: float, player: Player) -> pygame.Vector2:
        to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if to_player.length_squared() < settings.ENEMY_DETECTION_RANGE**2:
            return to_player.normalize() if to_player.length_squared() > 0 else pygame.Vector2()

        self.wander_timer -= delta_time
        if self.wander_timer <= 0:
            self.wander_direction = pygame.Vector2(
                random.choice((-1, 0, 1)), random.choice((-1, 0, 1))
            )
            if self.wander_direction.length_squared() > 0:
                self.wander_direction = self.wander_direction.normalize()
            self.wander_timer = random.uniform(0.5, 1.5)
        return self.wander_direction

    def _move_axis(self, dx: float, dy: float, dungeon: Dungeon) -> None:
        candidate = self.rect.move(round(dx), round(dy))
        if dungeon.is_walkable(candidate):
            self.rect = candidate

    def attack(self, player: Player) -> Projectile | None:
        # PRD 3.1: this will branch into enemy-specific attack patterns.
        if self.attack_cooldown > 0:
            return None
        if self.rect.colliderect(player.rect) and player.take_damage(self.damage):
            self.attack_cooldown = settings.ENEMY_ATTACK_COOLDOWN
        return None

    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

    def is_defeated(self) -> bool:
        return self.health <= 0

    def draw(self, surface: pygame.Surface, assets, animation_time: float) -> None:
        sprite = assets.get_entity_frame(
            self.enemy_type,
            animation_time,
            moving=self.is_moving,
            attacking=self.attack_cooldown > settings.ENEMY_ATTACK_COOLDOWN * 0.7,
            facing_x=self.facing.x,
            flash=False,
            size=self.rect.size,
        )
        surface.blit(sprite, self.rect)


class GruntEnemy(Enemy):
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(
            position,
            speed=settings.ENEMY_SPEED,
            max_health=settings.ENEMY_MAX_HEALTH,
            damage=settings.ENEMY_TOUCH_DAMAGE,
            score_value=settings.GRUNT_SCORE_VALUE,
            color=settings.ENEMY_COLOR,
            enemy_type="grunt",
        )


class BruteEnemy(Enemy):
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(
            position,
            speed=settings.BRUTE_SPEED,
            max_health=settings.BRUTE_MAX_HEALTH,
            damage=settings.BRUTE_TOUCH_DAMAGE,
            score_value=settings.BRUTE_SCORE_VALUE,
            color=settings.BRUTE_COLOR,
            enemy_type="brute",
            size=settings.TILE_SIZE - 6,
        )


class SkitterEnemy(Enemy):
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(
            position,
            speed=settings.SKITTER_SPEED,
            max_health=settings.SKITTER_MAX_HEALTH,
            damage=settings.SKITTER_TOUCH_DAMAGE,
            score_value=settings.SKITTER_SCORE_VALUE,
            color=settings.SKITTER_COLOR,
            enemy_type="skitter",
            size=settings.TILE_SIZE - 16,
        )

    def _get_direction(self, delta_time: float, player: Player) -> pygame.Vector2:
        to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if to_player.length_squared() == 0:
            return pygame.Vector2()

        if to_player.length_squared() < settings.ENEMY_DETECTION_RANGE**2:
            direction = to_player.normalize()
            if to_player.length() < settings.TILE_SIZE * 2:
                direction = pygame.Vector2(-direction.y, direction.x)
            jitter = pygame.Vector2(random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35))
            candidate = direction + jitter
            return candidate.normalize() if candidate.length_squared() > 0 else pygame.Vector2()

        return super()._get_direction(delta_time, player)


class ShamanEnemy(Enemy):
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(
            position,
            speed=settings.SHAMAN_SPEED,
            max_health=settings.SHAMAN_MAX_HEALTH,
            damage=settings.SHAMAN_TOUCH_DAMAGE,
            score_value=settings.SHAMAN_SCORE_VALUE,
            color=settings.SHAMAN_COLOR,
            enemy_type="shaman",
            size=settings.TILE_SIZE - 12,
        )

    def _get_direction(self, delta_time: float, player: Player) -> pygame.Vector2:
        to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        distance = to_player.length()
        if distance == 0:
            return pygame.Vector2()
        direction = to_player.normalize()

        if distance < settings.SHAMAN_PREFERRED_RANGE:
            retreat = -direction
            jitter = pygame.Vector2(random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25))
            candidate = retreat + jitter
            return candidate.normalize() if candidate.length_squared() > 0 else pygame.Vector2()

        if distance <= settings.SHAMAN_ATTACK_RANGE:
            strafe = pygame.Vector2(-direction.y, direction.x)
            jitter = pygame.Vector2(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15))
            candidate = strafe + jitter
            return candidate.normalize() if candidate.length_squared() > 0 else pygame.Vector2()

        return super()._get_direction(delta_time, player)

    def attack(self, player: Player) -> Projectile | None:
        if self.rect.colliderect(player.rect):
            return super().attack(player)
        if self.attack_cooldown > 0:
            return None

        to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if to_player.length_squared() > settings.SHAMAN_ATTACK_RANGE**2:
            return None

        self.attack_cooldown = settings.ENEMY_ATTACK_COOLDOWN + 0.35
        return Projectile.create(
            self.rect.center,
            to_player,
            speed=settings.SHAMAN_PROJECTILE_SPEED,
            damage=settings.SHAMAN_PROJECTILE_DAMAGE,
            owner="enemy",
            color=settings.PROJECTILE_COLOR,
        )


def create_enemy(enemy_type: str, position: tuple[int, int]) -> Enemy:
    if enemy_type == "brute":
        return BruteEnemy(position)
    if enemy_type == "skitter":
        return SkitterEnemy(position)
    if enemy_type == "shaman":
        return ShamanEnemy(position)
    return GruntEnemy(position)