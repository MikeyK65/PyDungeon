from __future__ import annotations

import json
from pathlib import Path

from . import settings


DEFAULT_SAVE_DATA = {
    "high_score": 0,
    "highest_floor": 1,
    "music_volume": settings.DEFAULT_MUSIC_VOLUME,
    "sfx_volume": settings.DEFAULT_SFX_VOLUME,
}


class SaveDataStore:
    def __init__(self, root: Path) -> None:
        self.file_path = root / settings.SAVE_FILE_NAME

    def load(self) -> dict[str, int | float]:
        if not self.file_path.exists():
            return DEFAULT_SAVE_DATA.copy()
        try:
            with self.file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return DEFAULT_SAVE_DATA.copy()

        merged = DEFAULT_SAVE_DATA.copy()
        merged.update({
            "high_score": int(data.get("high_score", 0)),
            "highest_floor": int(data.get("highest_floor", 1)),
            "music_volume": float(data.get("music_volume", settings.DEFAULT_MUSIC_VOLUME)),
            "sfx_volume": float(data.get("sfx_volume", settings.DEFAULT_SFX_VOLUME)),
        })
        return merged

    def save(self, data: dict[str, int | float]) -> None:
        payload = DEFAULT_SAVE_DATA.copy()
        payload.update(data)
        with self.file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)