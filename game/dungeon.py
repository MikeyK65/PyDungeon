from __future__ import annotations

from dataclasses import dataclass
import random

import pygame

from . import settings


@dataclass(frozen=True)
class Room:
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def intersects(self, other: "Room") -> bool:
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )


class Dungeon:
    def __init__(self, width: int, height: int, tile_size: int) -> None:
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.rooms: list[Room] = []
        self.tiles: list[list[int]] = []
        self.generate()

    def generate(self) -> None:
        """PRD 3.2: generate replayable dungeon layouts with guaranteed traversal paths."""
        self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        room_attempts = 24

        for _ in range(room_attempts):
            room_width = random.randint(4, 8)
            room_height = random.randint(4, 7)
            room_x = random.randint(1, self.width - room_width - 2)
            room_y = random.randint(1, self.height - room_height - 2)
            candidate = Room(room_x, room_y, room_width, room_height)

            if any(candidate.intersects(existing) for existing in self.rooms):
                continue

            self._carve_room(candidate)
            if self.rooms:
                previous_center = self.rooms[-1].center
                current_center = candidate.center
                self._carve_corridor(previous_center, current_center)
            self.rooms.append(candidate)

        if not self.rooms:
            fallback = Room(2, 2, self.width - 4, self.height - 4)
            self._carve_room(fallback)
            self.rooms.append(fallback)

    def _carve_room(self, room: Room) -> None:
        for y_index in range(room.y, room.y + room.height):
            for x_index in range(room.x, room.x + room.width):
                self.tiles[y_index][x_index] = 1

    def _carve_corridor(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        start_x, start_y = start
        end_x, end_y = end
        for x_index in range(min(start_x, end_x), max(start_x, end_x) + 1):
            self.tiles[start_y][x_index] = 1
        for y_index in range(min(start_y, end_y), max(start_y, end_y) + 1):
            self.tiles[y_index][end_x] = 1

    def is_walkable(self, rect: pygame.Rect) -> bool:
        points = [
            rect.topleft,
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]
        return all(self._is_floor_pixel(x_pos, y_pos) for x_pos, y_pos in points)

    def _is_floor_pixel(self, x_pos: int, y_pos: int) -> bool:
        tile_x = x_pos // self.tile_size
        tile_y = y_pos // self.tile_size
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return False
        return self.tiles[tile_y][tile_x] == 1

    def random_floor_position(self) -> tuple[int, int]:
        room = random.choice(self.rooms)
        tile_x = random.randint(room.x, room.x + room.width - 1)
        tile_y = random.randint(room.y, room.y + room.height - 1)
        center_x = tile_x * self.tile_size + self.tile_size // 2
        center_y = tile_y * self.tile_size + self.tile_size // 2
        return center_x, center_y

    def random_floor_position_away_from(
        self, position: tuple[int, int], minimum_distance: float
    ) -> tuple[int, int]:
        for _ in range(32):
            candidate = self.random_floor_position()
            if pygame.Vector2(candidate).distance_to(position) >= minimum_distance:
                return candidate
        return self.random_floor_position()

    def draw(self, surface: pygame.Surface, assets, animation_time: float) -> None:
        frame = int(animation_time * settings.PICKUP_ANIMATION_FPS) % 2
        floor_tile = assets.get_tile("floor", frame)
        wall_tile = assets.get_tile("wall", frame)
        for y_index, row in enumerate(self.tiles):
            for x_index, tile in enumerate(row):
                tile_rect = pygame.Rect(
                    x_index * self.tile_size,
                    y_index * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                surface.blit(floor_tile if tile == 1 else wall_tile, tile_rect)