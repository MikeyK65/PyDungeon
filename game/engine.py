from __future__ import annotations

import random
from pathlib import Path

import pygame

from .assets import AssetLibrary
from .audio import AudioManager
from . import settings
from .dungeon import Dungeon
from .enemy import Enemy, create_enemy
from .hazard import Trap
from .hud import HUD
from .pickup import Pickup
from .player import Player
from .projectile import Projectile
from .save_data import SaveDataStore


class GameEngine:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "title"
        self.floor_number = 1
        self.pickups: list[Pickup] = []
        self.traps: list[Trap] = []
        self.enemy_projectiles: list[Projectile] = []
        self.exit_rect: pygame.Rect | None = None
        self.has_exit_key = False
        self.message = ""
        self.message_timer = 0.0
        self.current_attack_hits: set[int] = set()
        self.root_path = Path(__file__).resolve().parent.parent
        self.assets = AssetLibrary(self.root_path)
        self.save_store = SaveDataStore(self.root_path)
        self.save_data = self.save_store.load()
        self.audio = AudioManager(
            self.root_path,
            music_volume=float(self.save_data["music_volume"]),
            sfx_volume=float(self.save_data["sfx_volume"]),
        )
        self.animation_time = 0.0

        self.dungeon = Dungeon(settings.MAP_WIDTH, settings.MAP_HEIGHT, settings.TILE_SIZE)
        self.player = Player(self.dungeon.random_floor_position())
        self.enemies: list[Enemy] = []
        self.hud = HUD()
        self._build_floor(reset_player=False)
        self.audio.play_music("title")

    def _spawn_enemies(self) -> list[Enemy]:
        enemies: list[Enemy] = []
        enemy_count = settings.ENEMY_COUNT + self.floor_number - 1
        minimum_distance = settings.TILE_SIZE * 4
        for _ in range(enemy_count):
            roll = random.random()
            enemy_type = "grunt"
            if self.floor_number >= 4 and roll < 0.18:
                enemy_type = "shaman"
            elif self.floor_number >= 2 and roll < 0.36:
                enemy_type = "brute"
            elif self.floor_number >= 3 and roll < 0.62:
                enemy_type = "skitter"
            enemies.append(
                create_enemy(
                    enemy_type,
                    self.dungeon.random_floor_position_away_from(
                        self.player.rect.center, minimum_distance
                    ),
                )
            )
        return enemies

    def _build_floor(self, reset_player: bool) -> None:
        self.dungeon.generate()
        spawn_position = self.dungeon.random_floor_position()
        if reset_player:
            self.player.respawn(spawn_position)
        else:
            self.player.rect.center = spawn_position
        self.pickups = []
        self.traps = self._spawn_traps()
        self.enemy_projectiles = []
        self.has_exit_key = False
        self.exit_rect = self._create_exit()
        self.pickups.append(self._create_key_pickup())
        self.enemies = self._spawn_enemies()
        self._set_message(f"Floor {self.floor_number}", 2.0)

    def _spawn_traps(self) -> list[Trap]:
        traps: list[Trap] = []
        trap_count = settings.TRAP_COUNT_BASE + max(0, self.floor_number - 1)
        minimum_distance = settings.TILE_SIZE * 3
        for _ in range(trap_count):
            position = self.dungeon.random_floor_position_away_from(
                self.player.rect.center, minimum_distance
            )
            traps.append(Trap.create(position))
        return traps

    def _create_key_pickup(self) -> Pickup:
        position = self.dungeon.random_floor_position_away_from(
            self.player.rect.center, settings.TILE_SIZE * 7
        )
        return Pickup.create("key", position)

    def _create_exit(self) -> pygame.Rect:
        exit_position = self.dungeon.random_floor_position_away_from(
            self.player.rect.center, settings.TILE_SIZE * 6
        )
        exit_rect = pygame.Rect(0, 0, settings.TILE_SIZE, settings.TILE_SIZE)
        exit_rect.center = exit_position
        return exit_rect

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(settings.FPS) / 1000.0
            self.animation_time += delta_time
            self._handle_events()
            self._update(delta_time)
            self._render()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == "title":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.audio.play_sfx("menu")
                        self._start_new_run()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif self._handle_volume_shortcuts(event.key):
                        self.audio.play_sfx("menu")
                    continue

                if self.state == "paused":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "playing"
                        self.audio.play_sfx("menu")
                        self.audio.play_music("game")
                        self._set_message("Resumed", 0.8)
                    elif event.key == pygame.K_r:
                        self.audio.play_sfx("menu")
                        self._start_new_run()
                    elif self._handle_volume_shortcuts(event.key):
                        self.audio.play_sfx("menu")
                    continue

                if self.state == "game_over":
                    if event.key == pygame.K_r:
                        self.audio.play_sfx("menu")
                        self._start_new_run()
                    elif event.key == pygame.K_RETURN:
                        self.audio.play_sfx("menu")
                        self.state = "title"
                        self.audio.play_music("title")
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif self._handle_volume_shortcuts(event.key):
                        self.audio.play_sfx("menu")
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.state = "paused"
                    self.audio.play_sfx("pause")
                    self.audio.play_music("paused")
                    self._set_message("Paused", 9999)
                    continue
                if event.key == pygame.K_q:
                    self.running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    # PRD 4: desktop keyboard attack binding placeholder.
                    if self.player.attack() is not None:
                        self.audio.play_sfx("attack")
                        self.current_attack_hits.clear()
                elif self._handle_volume_shortcuts(event.key):
                    self.audio.play_sfx("menu")

    def _update(self, delta_time: float) -> None:
        self.message_timer = max(0.0, self.message_timer - delta_time)
        if self.message_timer == 0:
            self.message = ""

        if self.state != "playing":
            return

        self.player.update(delta_time, self.dungeon)
        self._resolve_player_attacks()

        for enemy in self.enemies:
            enemy.update(delta_time, self.player, self.dungeon)
            projectile = enemy.attack(self.player)
            if projectile is not None:
                self.audio.play_sfx("projectile")
                self.enemy_projectiles.append(projectile)

        defeated_enemies = [enemy for enemy in self.enemies if enemy.is_defeated()]
        if defeated_enemies:
            for enemy in defeated_enemies:
                self.player.score += enemy.score_value
                self._spawn_enemy_drop(enemy.rect.center)
                self.audio.play_sfx("enemy_defeat")
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_defeated()]

        # PRD 3.1: pickups and power-ups will be updated alongside enemy and loot systems.
        self._update_pickups(delta_time)
        self._update_power_ups(delta_time)
        self._update_enemy_projectiles(delta_time)
        self._update_traps(delta_time)
        self._update_exit()
        self._update_player_state()

    def _update_pickups(self, delta_time: float) -> None:
        _ = delta_time
        remaining_pickups: list[Pickup] = []
        for pickup in self.pickups:
            if pickup.rect.colliderect(self.player.rect):
                if pickup.pickup_type == "key":
                    self.has_exit_key = True
                    self.player.score += pickup.value
                    self.audio.play_sfx("key")
                    self._set_message("Exit key found", 1.4)
                else:
                    self.player.collect_pickup(pickup.pickup_type, pickup.value)
                    if pickup.pickup_type == "power_up":
                        self.audio.play_sfx("power_up")
                    else:
                        self.audio.play_sfx("pickup")
                if pickup.pickup_type == "health":
                    self._set_message("Health recovered", 1.2)
                elif pickup.pickup_type == "score":
                    self._set_message("Treasure collected", 1.2)
                elif pickup.pickup_type == "key":
                    pass
                else:
                    self._set_message("Speed boost active", 1.2)
                continue
            remaining_pickups.append(pickup)
        self.pickups = remaining_pickups

    def _update_power_ups(self, delta_time: float) -> None:
        _ = delta_time

    def _update_enemy_projectiles(self, delta_time: float) -> None:
        active_projectiles: list[Projectile] = []
        for projectile in self.enemy_projectiles:
            projectile.update(delta_time, self.dungeon)
            if not projectile.active:
                continue
            if projectile.rect.colliderect(self.player.rect):
                if self.player.take_damage(projectile.damage):
                    self.audio.play_sfx("hit")
                    self._set_message("Hit by a projectile", 0.8)
                projectile.active = False
                continue
            active_projectiles.append(projectile)
        self.enemy_projectiles = active_projectiles

    def _update_traps(self, delta_time: float) -> None:
        _ = delta_time
        for trap in self.traps:
            if trap.rect.colliderect(self.player.rect):
                if self.player.take_damage(settings.TRAP_DAMAGE):
                    self.audio.play_sfx("trap")
                    self._set_message("Trap triggered", 0.8)

    def _update_exit(self) -> None:
        if self.exit_rect is None or not self.player.rect.colliderect(self.exit_rect):
            return
        if not self.has_exit_key:
            self._set_message("Find the exit key", 0.8)
            return
        if self.enemies:
            self._set_message("Defeat remaining enemies", 0.8)
            return
        self.floor_number += 1
        self.audio.play_sfx("floor_clear")
        self._persist_progress()
        self._build_floor(reset_player=True)

    def _update_player_state(self) -> None:
        if not self.player.is_defeated():
            return

        self.player.lives -= 1
        if self.player.lives <= 0:
            self.state = "game_over"
            self.audio.play_sfx("game_over")
            self.audio.play_music("title")
            self._persist_progress()
            self._set_message("Game over - press R to restart", 9999)
            return

        self._set_message("You fell - try again", 1.8)
        self._build_floor(reset_player=True)

    def _resolve_player_attacks(self) -> None:
        attack_rect = self.player.get_attack_rect()
        if attack_rect is None:
            self.current_attack_hits.clear()
            return
        for enemy in self.enemies:
            if enemy.is_defeated():
                continue
            enemy_id = id(enemy)
            if enemy_id in self.current_attack_hits:
                continue
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(settings.ATTACK_DAMAGE)
                self.audio.play_sfx("hit")
                self.current_attack_hits.add(enemy_id)

    def _spawn_enemy_drop(self, position: tuple[int, int]) -> None:
        drop_roll = random.random()
        if drop_roll <= settings.DROP_CHANCE_POWER_UP:
            pickup_type = "power_up"
        elif drop_roll <= settings.DROP_CHANCE_POWER_UP + settings.DROP_CHANCE_HEALTH:
            pickup_type = "health"
        elif drop_roll <= settings.DROP_CHANCE_POWER_UP + settings.DROP_CHANCE_HEALTH + settings.DROP_CHANCE_SCORE:
            pickup_type = "score"
        else:
            return
        self.pickups.append(Pickup.create(pickup_type, position))

    def _spawn_exit(self) -> None:
        self.exit_rect = self._create_exit()

    def _start_new_run(self) -> None:
        self.floor_number = 1
        self.state = "playing"
        self.player.score = 0
        self.player.lives = settings.PLAYER_LIVES
        self.player.health = self.player.max_health
        self.has_exit_key = False
        self.enemy_projectiles = []
        self.current_attack_hits.clear()
        self.audio.play_music("game")
        self._build_floor(reset_player=True)

    def _persist_progress(self) -> None:
        self.save_data["high_score"] = max(self.save_data["high_score"], self.player.score)
        self.save_data["highest_floor"] = max(self.save_data["highest_floor"], self.floor_number)
        self.save_data["music_volume"] = self.audio.music_volume
        self.save_data["sfx_volume"] = self.audio.sfx_volume
        self.save_store.save(self.save_data)

    def _handle_volume_shortcuts(self, key: int) -> bool:
        if key == pygame.K_MINUS:
            self._adjust_music_volume(-settings.VOLUME_STEP)
            return True
        if key == pygame.K_EQUALS:
            self._adjust_music_volume(settings.VOLUME_STEP)
            return True
        if key == pygame.K_LEFTBRACKET:
            self._adjust_sfx_volume(-settings.VOLUME_STEP)
            return True
        if key == pygame.K_RIGHTBRACKET:
            self._adjust_sfx_volume(settings.VOLUME_STEP)
            return True
        return False

    def _adjust_music_volume(self, delta: float) -> None:
        volume = self.audio.set_music_volume(self.audio.music_volume + delta)
        self._set_message(f"Music volume: {round(volume * 100):d}%", 1.1)
        self._persist_progress()

    def _adjust_sfx_volume(self, delta: float) -> None:
        volume = self.audio.set_sfx_volume(self.audio.sfx_volume + delta)
        self._set_message(f"SFX volume: {round(volume * 100):d}%", 1.1)
        self._persist_progress()

    def _set_message(self, message: str, duration: float) -> None:
        self.message = message
        self.message_timer = duration

    def _render(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)
        self.dungeon.draw(self.screen, self.assets, self.animation_time)

        if self.exit_rect is not None:
            exit_sprite = self.assets.get_exit_frame(self.has_exit_key and not self.enemies, self.animation_time)
            self.screen.blit(exit_sprite, self.exit_rect)

        for pickup in self.pickups:
            pickup.draw(self.screen, self.assets, self.animation_time)

        for trap in self.traps:
            trap.draw(self.screen, self.assets, self.animation_time)

        for projectile in self.enemy_projectiles:
            projectile.draw(self.screen, self.assets)

        for enemy in self.enemies:
            enemy.draw(self.screen, self.assets, self.animation_time)

        self.player.draw(self.screen, self.assets, self.animation_time)
        if self.state in {"playing", "paused", "game_over"}:
            self.hud.draw(
                self.screen,
                self.player,
                self.floor_number,
                len(self.enemies),
                self.has_exit_key,
                self.message,
            )

        if self.state == "title":
            self._render_title_screen()
        elif self.state == "paused":
            self._render_pause_overlay()
        elif self.state == "game_over":
            self._render_game_over_overlay()

        pygame.display.flip()

    def _render_title_screen(self) -> None:
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*settings.GAME_OVER_OVERLAY, 210))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 84)
        subtitle_font = pygame.font.Font(None, 36)
        body_font = pygame.font.Font(None, 30)

        title_text = title_font.render(settings.TITLE, True, settings.TEXT_COLOR)
        subtitle_text = subtitle_font.render("Retro dungeon crawling prototype", True, settings.ACCENT_COLOR)
        prompt_text = body_font.render("Press Enter to start | Esc to quit", True, settings.TEXT_COLOR)
        stats_text = body_font.render(
            f"Best score: {self.save_data['high_score']} | Highest floor: {self.save_data['highest_floor']}",
            True,
            settings.TEXT_COLOR,
        )
        controls_text = body_font.render(
            "Move: WASD/Arrows | Attack: Space/Enter | Pause: Esc | Quit run: Q",
            True,
            settings.TEXT_COLOR,
        )
        volume_text = body_font.render(
            f"Music +/-: {round(self.audio.music_volume * 100):d}% | SFX [ ]: {round(self.audio.sfx_volume * 100):d}%",
            True,
            settings.TEXT_COLOR,
        )

        self.screen.blit(title_text, title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 210)))
        self.screen.blit(subtitle_text, subtitle_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 275)))
        self.screen.blit(stats_text, stats_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 360)))
        self.screen.blit(controls_text, controls_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 405)))
        self.screen.blit(volume_text, volume_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 450)))
        self.screen.blit(prompt_text, prompt_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 500)))

    def _render_pause_overlay(self) -> None:
        self._render_center_panel(
            "Paused",
            [
                "Esc to resume",
                "R to restart run",
                f"Best score: {self.save_data['high_score']}",
                f"Music +/-: {round(self.audio.music_volume * 100):d}% | SFX [ ]: {round(self.audio.sfx_volume * 100):d}%",
            ],
        )

    def _render_game_over_overlay(self) -> None:
        self._render_center_panel(
            "Game Over",
            [
                f"Final score: {self.player.score}",
                f"Floor reached: {self.floor_number}",
                f"Best score: {self.save_data['high_score']} | Highest floor: {self.save_data['highest_floor']}",
                "R to restart | Enter for title | Esc to quit",
            ],
        )

    def _render_center_panel(self, title: str, lines: list[str]) -> None:
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*settings.GAME_OVER_OVERLAY, 190))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(0, 0, 680, 260)
        panel_rect.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.screen, settings.MENU_PANEL_COLOR, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, settings.ACCENT_COLOR, panel_rect, 2, border_radius=12)

        title_font = pygame.font.Font(None, 72)
        body_font = pygame.font.Font(None, 32)
        title_text = title_font.render(title, True, settings.TEXT_COLOR)
        self.screen.blit(title_text, title_text.get_rect(center=(panel_rect.centerx, panel_rect.y + 55)))

        for index, line in enumerate(lines):
            line_text = body_font.render(line, True, settings.TEXT_COLOR)
            self.screen.blit(
                line_text,
                line_text.get_rect(center=(panel_rect.centerx, panel_rect.y + 120 + index * 36)),
            )