from __future__ import annotations

from array import array
import math
from pathlib import Path

import pygame

from . import settings


class AudioManager:
    def __init__(self, root: Path, *, music_volume: float, sfx_volume: float) -> None:
        self.audio_dir = root / "assets" / "audio"
        self.enabled = False
        self.music_channel: pygame.mixer.Channel | None = None
        self.sfx_channel: pygame.mixer.Channel | None = None
        self.music_sounds: dict[str, pygame.mixer.Sound] = {}
        self.sfx_sounds: dict[str, pygame.mixer.Sound] = {}
        self.current_music_track: str | None = None
        self.music_volume = self._clamp_volume(music_volume)
        self.sfx_volume = self._clamp_volume(sfx_volume)

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=settings.AUDIO_SAMPLE_RATE,
                    size=-16,
                    channels=1,
                    buffer=512,
                )
            self.music_channel = pygame.mixer.Channel(0)
            self.sfx_channel = pygame.mixer.Channel(1)
            self.enabled = True
        except pygame.error:
            self.enabled = False
            return

        self._build_default_sounds()
        self.set_music_volume(self.music_volume)
        self.set_sfx_volume(self.sfx_volume)

    def play_sfx(self, event_name: str) -> None:
        if not self.enabled or self.sfx_channel is None:
            return
        sound = self.sfx_sounds.get(event_name)
        if sound is None:
            return
        self.sfx_channel.play(sound)

    def play_music(self, track_name: str) -> None:
        if not self.enabled or self.music_channel is None:
            return
        if self.current_music_track == track_name and self.music_channel.get_busy():
            return
        sound = self.music_sounds.get(track_name)
        if sound is None:
            return
        self.current_music_track = track_name
        self.music_channel.play(sound, loops=-1)
        self.music_channel.set_volume(self.music_volume)

    def stop_music(self) -> None:
        if not self.enabled or self.music_channel is None:
            return
        self.music_channel.stop()
        self.current_music_track = None

    def set_music_volume(self, volume: float) -> float:
        self.music_volume = self._clamp_volume(volume)
        if self.music_channel is not None:
            self.music_channel.set_volume(self.music_volume)
        return self.music_volume

    def set_sfx_volume(self, volume: float) -> float:
        self.sfx_volume = self._clamp_volume(volume)
        for sound in self.sfx_sounds.values():
            sound.set_volume(self.sfx_volume)
        return self.sfx_volume

    def _build_default_sounds(self) -> None:
        if not self.enabled:
            return

        self.sfx_sounds = {
            "attack": self._load_or_generate_sound("attack.wav", 440, 0.08, wave_type="square"),
            "hit": self._load_or_generate_sound("hit.wav", 220, 0.1, wave_type="triangle"),
            "enemy_defeat": self._load_or_generate_sound("enemy_defeat.wav", 170, 0.18, wave_type="saw"),
            "pickup": self._load_or_generate_sound("pickup.wav", 660, 0.12, wave_type="sine"),
            "key": self._load_or_generate_sound("key.wav", 780, 0.16, wave_type="square"),
            "power_up": self._load_or_generate_sound("power_up.wav", 880, 0.22, wave_type="sine"),
            "trap": self._load_or_generate_sound("trap.wav", 145, 0.18, wave_type="saw"),
            "projectile": self._load_or_generate_sound("projectile.wav", 540, 0.1, wave_type="sine"),
            "floor_clear": self._load_or_generate_sound("floor_clear.wav", 520, 0.28, wave_type="triangle"),
            "menu": self._load_or_generate_sound("menu.wav", 320, 0.08, wave_type="sine"),
            "pause": self._load_or_generate_sound("pause.wav", 260, 0.1, wave_type="triangle"),
            "game_over": self._load_or_generate_sound("game_over.wav", 120, 0.5, wave_type="saw"),
        }
        self.music_sounds = {
            "title": self._load_or_generate_music("title.wav", [261.63, 329.63, 392.0, 329.63], 0.35),
            "game": self._load_or_generate_music("game.wav", [196.0, 220.0, 246.94, 220.0], 0.3),
            "paused": self._load_or_generate_music("paused.wav", [220.0, 220.0, 174.61], 0.2),
        }

    def _load_or_generate_sound(
        self, file_name: str, frequency: float, duration: float, *, wave_type: str
    ) -> pygame.mixer.Sound:
        file_path = self.audio_dir / file_name
        if file_path.exists():
            try:
                sound = pygame.mixer.Sound(str(file_path))
                sound.set_volume(self.sfx_volume)
                return sound
            except pygame.error:
                pass
        sound = self._generate_tone(frequency, duration, wave_type=wave_type, amplitude=0.5)
        sound.set_volume(self.sfx_volume)
        return sound

    def _load_or_generate_music(
        self, file_name: str, frequencies: list[float], note_duration: float
    ) -> pygame.mixer.Sound:
        file_path = self.audio_dir / file_name
        if file_path.exists():
            try:
                sound = pygame.mixer.Sound(str(file_path))
                sound.set_volume(self.music_volume)
                return sound
            except pygame.error:
                pass
        sound = self._generate_phrase(frequencies, note_duration)
        sound.set_volume(self.music_volume)
        return sound

    def _generate_phrase(self, frequencies: list[float], note_duration: float) -> pygame.mixer.Sound:
        samples = array("h")
        for index, frequency in enumerate(frequencies):
            tone = self._build_wave_samples(
                frequency,
                note_duration,
                wave_type="sine" if index % 2 == 0 else "triangle",
                amplitude=0.22,
            )
            samples.extend(tone)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _generate_tone(
        self, frequency: float, duration: float, *, wave_type: str, amplitude: float
    ) -> pygame.mixer.Sound:
        samples = self._build_wave_samples(frequency, duration, wave_type=wave_type, amplitude=amplitude)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _build_wave_samples(
        self, frequency: float, duration: float, *, wave_type: str, amplitude: float
    ) -> array:
        sample_count = max(1, int(settings.AUDIO_SAMPLE_RATE * duration))
        envelope_attack = max(1, int(sample_count * 0.08))
        envelope_release = max(1, int(sample_count * 0.12))
        samples = array("h")
        max_amplitude = int(32767 * amplitude)
        for sample_index in range(sample_count):
            time_pos = sample_index / settings.AUDIO_SAMPLE_RATE
            phase = 2 * math.pi * frequency * time_pos
            if wave_type == "square":
                raw = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wave_type == "triangle":
                raw = 2 * abs(2 * ((frequency * time_pos) % 1) - 1) - 1
            elif wave_type == "saw":
                raw = 2 * ((frequency * time_pos) % 1) - 1
            else:
                raw = math.sin(phase)

            envelope = 1.0
            if sample_index < envelope_attack:
                envelope = sample_index / envelope_attack
            elif sample_index > sample_count - envelope_release:
                envelope = max(0.0, (sample_count - sample_index) / envelope_release)

            samples.append(int(raw * max_amplitude * envelope))
        return samples

    def _clamp_volume(self, value: float) -> float:
        return max(0.0, min(1.0, value))