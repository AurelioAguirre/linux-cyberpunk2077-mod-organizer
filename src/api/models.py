from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


@dataclass
class Mod:
    name: str
    path: Path
    enabled: bool = True
    internal_files: list[str] = field(default_factory=list)


@dataclass
class Profile:
    name: str
    mods: list[Mod] = field(default_factory=list)


@dataclass
class ConflictReport:
    file_path: str
    mods: list[Mod]


@dataclass
class GameSnapshot:
    game_version: str
    timestamp: str
    files: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, game_version: str, files: list[str]) -> GameSnapshot:
        return cls(
            game_version=game_version,
            timestamp=datetime.now().isoformat(),
            files=files,
        )
