from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import logging
import yaml

log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "resources" / "config.yml"
RESOURCES_PATH = Path(__file__).parent.parent / "resources"


@dataclass
class Config:
    game_path: Path
    mods_path: Path

    @classmethod
    def load(cls) -> Config:
        from utils import find_game_path, is_valid_game_path

        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        game_path = Path(data.get("GAME_PATH", ""))
        mods_path = Path(data.get("MODS_PATH", ""))

        if is_valid_game_path(game_path):
            log.info("Game path loaded: %s", game_path)
        else:
            game_path = find_game_path() or Path()
            if game_path:
                data["GAME_PATH"] = str(game_path)
                CONFIG_PATH.write_text(yaml.dump(data))
                log.info("Game path saved to config")

        if mods_path.is_dir():
            log.info("Mods folder loaded: %s", mods_path)

        return cls(game_path=game_path, mods_path=mods_path)

    def save(self) -> None:
        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        data["GAME_PATH"] = str(self.game_path)
        data["MODS_PATH"] = str(self.mods_path)
        CONFIG_PATH.write_text(yaml.dump(data))
