from __future__ import annotations

from pathlib import Path

import pygame

from . import settings


class AssetLibrary:
    def __init__(self, root: Path) -> None:
        self.sprite_dir = root / "assets" / "sprites"
        self.cache: dict[str, object] = {}

    def get_tile(self, tile_type: str, frame: int = 0) -> pygame.Surface:
        cache_key = f"tile:{tile_type}:{frame}"
        if cache_key not in self.cache:
            image = self._load_image(cache_key, f"tiles/{tile_type}.png", (settings.TILE_SIZE, settings.TILE_SIZE))
            if image is None:
                image = self._build_tile_surface(tile_type, frame)
            self.cache[cache_key] = image
        return self.cache[cache_key]  # type: ignore[return-value]

    def get_entity_frame(
        self,
        entity_type: str,
        animation_time: float,
        *,
        moving: bool,
        attacking: bool,
        facing_x: float,
        flash: bool,
        size: tuple[int, int],
    ) -> pygame.Surface:
        frame_count = 3 if attacking else 2
        frame_index = 2 if attacking else int(animation_time * settings.ENTITY_ANIMATION_FPS) % frame_count
        if not moving and not attacking:
            frame_index = 0
        base_key = f"entity:{entity_type}:{size[0]}x{size[1]}:{frame_index}"
        if base_key not in self.cache:
            image = self._load_image(base_key, f"{entity_type}_{frame_index}.png", size)
            if image is None:
                image = self._build_entity_surface(entity_type, size, frame_index)
            self.cache[base_key] = image

        surface = self.cache[base_key].copy()  # type: ignore[union-attr]
        if facing_x < 0:
            surface = pygame.transform.flip(surface, True, False)
        if flash:
            flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, 70))
            surface.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return surface

    def get_pickup_frame(
        self, pickup_type: str, animation_time: float, size: tuple[int, int]
    ) -> pygame.Surface:
        frame_index = int(animation_time * settings.PICKUP_ANIMATION_FPS) % 2
        cache_key = f"pickup:{pickup_type}:{size[0]}x{size[1]}:{frame_index}"
        if cache_key not in self.cache:
            image = self._load_image(cache_key, f"{pickup_type}.png", size)
            if image is None:
                image = self._build_pickup_surface(pickup_type, size, frame_index)
            self.cache[cache_key] = image
        return self.cache[cache_key]  # type: ignore[return-value]

    def get_trap_frame(self, animation_time: float, size: tuple[int, int]) -> pygame.Surface:
        frame_index = int(animation_time * settings.PICKUP_ANIMATION_FPS) % 2
        cache_key = f"trap:{size[0]}x{size[1]}:{frame_index}"
        if cache_key not in self.cache:
            image = self._load_image(cache_key, "trap.png", size)
            if image is None:
                image = self._build_trap_surface(size, frame_index)
            self.cache[cache_key] = image
        return self.cache[cache_key]  # type: ignore[return-value]

    def get_projectile_frame(self, size: int) -> pygame.Surface:
        cache_key = f"projectile:{size}"
        if cache_key not in self.cache:
            image = self._load_image(cache_key, "projectile.png", (size, size))
            if image is None:
                image = self._build_projectile_surface(size)
            self.cache[cache_key] = image
        return self.cache[cache_key]  # type: ignore[return-value]

    def get_exit_frame(self, unlocked: bool, animation_time: float) -> pygame.Surface:
        frame_index = int(animation_time * settings.PICKUP_ANIMATION_FPS) % 2
        cache_key = f"exit:{'open' if unlocked else 'locked'}:{frame_index}"
        if cache_key not in self.cache:
            file_name = "exit_open.png" if unlocked else "exit_locked.png"
            image = self._load_image(cache_key, file_name, (settings.TILE_SIZE, settings.TILE_SIZE))
            if image is None:
                image = self._build_exit_surface(unlocked, frame_index)
            self.cache[cache_key] = image
        return self.cache[cache_key]  # type: ignore[return-value]

    def _load_image(
        self, cache_key: str, relative_path: str, size: tuple[int, int]
    ) -> pygame.Surface | None:
        image_path = self.sprite_dir / relative_path
        if not image_path.exists():
            return None
        try:
            image = pygame.image.load(str(image_path)).convert_alpha()
        except pygame.error:
            return None
        if image.get_size() != size:
            image = pygame.transform.smoothscale(image, size)
        self.cache[cache_key] = image
        return image

    def _build_tile_surface(self, tile_type: str, frame: int) -> pygame.Surface:
        surface = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA)
        if tile_type == "floor":
            surface.fill(settings.FLOOR_COLOR)
            accent = (settings.FLOOR_COLOR[0] + 12, settings.FLOOR_COLOR[1] + 12, settings.FLOOR_COLOR[2] + 12)
            pygame.draw.rect(surface, accent, (4, 4 + frame, 8, 8), border_radius=2)
            pygame.draw.rect(surface, settings.BACKGROUND_COLOR, (18, 18 - frame, 6, 6), border_radius=2)
        else:
            surface.fill(settings.WALL_COLOR)
            brick = (settings.WALL_COLOR[0] + 18, settings.WALL_COLOR[1] + 18, settings.WALL_COLOR[2] + 18)
            for y_pos in range(0, settings.TILE_SIZE, 8):
                offset = 4 if (y_pos // 8) % 2 else 0
                for x_pos in range(-offset, settings.TILE_SIZE, 12):
                    pygame.draw.rect(surface, brick, (x_pos, y_pos, 10, 6), border_radius=2)
        pygame.draw.rect(surface, settings.BACKGROUND_COLOR, surface.get_rect(), 1)
        return surface

    def _build_entity_surface(
        self, entity_type: str, size: tuple[int, int], frame_index: int
    ) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        rect = surface.get_rect()
        body_colors = {
            "player": (settings.PLAYER_COLOR, settings.ACCENT_COLOR),
            "grunt": (settings.ENEMY_COLOR, settings.ACCENT_COLOR),
            "brute": (settings.BRUTE_COLOR, settings.ACCENT_COLOR),
            "skitter": (settings.SKITTER_COLOR, settings.ACCENT_COLOR),
            "shaman": (settings.SHAMAN_COLOR, settings.ACCENT_COLOR),
        }
        body_color, accent = body_colors.get(entity_type, (settings.ACCENT_COLOR, settings.TEXT_COLOR))
        bounce = 1 if frame_index == 1 else 0
        pygame.draw.ellipse(surface, body_color, rect.inflate(-4, -6).move(0, bounce))
        pygame.draw.rect(surface, accent, (rect.width - 11, 7 + bounce, 4, 4), border_radius=1)
        pygame.draw.rect(surface, settings.BACKGROUND_COLOR, (5, rect.height - 8 + bounce, rect.width - 10, 3), border_radius=2)
        if frame_index == 2:
            pygame.draw.line(surface, accent, (rect.centerx, rect.centery), (rect.width - 2, 3), 3)
        return surface

    def _build_pickup_surface(
        self, pickup_type: str, size: tuple[int, int], frame_index: int
    ) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        colors = {
            "health": settings.HEALTH_PICKUP_COLOR,
            "score": settings.SCORE_PICKUP_COLOR,
            "power_up": settings.POWER_UP_COLOR,
            "key": settings.KEY_COLOR,
        }
        color = colors.get(pickup_type, settings.ACCENT_COLOR)
        pulse = 1 if frame_index == 1 else 0
        points = [
            (surface.get_width() // 2, 2 + pulse),
            (surface.get_width() - 3, surface.get_height() // 2),
            (surface.get_width() // 2, surface.get_height() - 3 - pulse),
            (3, surface.get_height() // 2),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, settings.BACKGROUND_COLOR, points, 2)
        if pickup_type == "key":
            pygame.draw.circle(surface, settings.BACKGROUND_COLOR, (surface.get_width() // 2, surface.get_height() // 2 - 1), 4, 2)
        return surface

    def _build_trap_surface(self, size: tuple[int, int], frame_index: int) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, settings.TRAP_COLOR, surface.get_rect(), border_radius=5)
        inset = 6 if frame_index == 0 else 4
        inner = surface.get_rect().inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(surface, settings.BACKGROUND_COLOR, inner, border_radius=4)
        return surface

    def _build_projectile_surface(self, size: int) -> pygame.Surface:
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        pygame.draw.circle(surface, settings.PROJECTILE_COLOR, (center, center), center)
        pygame.draw.circle(surface, settings.TEXT_COLOR, (center + 1, center - 1), max(1, center // 2))
        return surface

    def _build_exit_surface(self, unlocked: bool, frame_index: int) -> pygame.Surface:
        surface = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA)
        color = settings.EXIT_COLOR if unlocked else settings.EXIT_LOCKED_COLOR
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=6)
        inner = surface.get_rect().inflate(-10, -10)
        pygame.draw.rect(surface, settings.BACKGROUND_COLOR, inner, border_radius=4)
        if unlocked:
            pygame.draw.line(surface, settings.ACCENT_COLOR, (8, 18 + frame_index), (24, 10 + frame_index), 3)
        else:
            pygame.draw.circle(surface, settings.KEY_COLOR, (16, 11), 4, 2)
            pygame.draw.rect(surface, settings.KEY_COLOR, (12, 12, 8, 8), 2, border_radius=2)
        return surface