from pathlib import Path
import json
import logging
import libarchive
from .models import Mod, GameSnapshot

log = logging.getLogger(__name__)


def build_snapshot(game_path: Path) -> GameSnapshot:
    from utils import get_game_version

    log.info("Reading game version...")
    version = get_game_version(game_path)
    log.info("Game version: %s", version)

    log.info("Scanning game folder — this may take a moment...")
    files = sorted(
        str(p.relative_to(game_path)).replace("\\", "/")
        for p in game_path.rglob("*")
        if p.is_file()
    )
    log.info("Found %d files", len(files))
    return GameSnapshot.create(game_version=version, files=files)


def save_snapshot(snapshot: GameSnapshot, resources_path: Path) -> Path:
    version_slug = snapshot.game_version.replace(" ", "_")
    out_path = resources_path / f"baseline_{version_slug}.json"
    out_path.write_text(json.dumps({
        "game_version": snapshot.game_version,
        "timestamp": snapshot.timestamp,
        "file_count": len(snapshot.files),
        "files": snapshot.files,
    }, indent=2))
    log.info("Snapshot saved → %s  (%d files)", out_path.name, len(snapshot.files))
    return out_path


def load_snapshot(resources_path: Path, game_version: str) -> GameSnapshot | None:
    """Load baseline snapshot matching game_version, or any available baseline."""
    versioned = resources_path / f"baseline_{game_version}.json"
    candidates = [versioned] if versioned.exists() else sorted(resources_path.glob("baseline_*.json"))
    if not candidates:
        return None
    data = json.loads(candidates[0].read_text())
    return GameSnapshot(
        game_version=data["game_version"],
        timestamp=data["timestamp"],
        files=data["files"],
    )


def list_archive_contents(archive_path: Path) -> list[str]:
    contents = []
    with libarchive.file_reader(str(archive_path)) as archive:
        for entry in archive:
            if not entry.isdir:
                contents.append(entry.pathname)
    return sorted(contents)


def scan_mod_archives(mods_path: Path) -> list[Path]:
    return sorted(
        p for p in mods_path.iterdir()
        if p.suffix.lower() in {".zip", ".rar", ".7z"}
    )


def scan_mods(mods_path: Path) -> list[Mod]:
    mods = []
    for entry in sorted(mods_path.iterdir()):
        if entry.suffix == ".archive":
            mods.append(Mod(name=entry.stem, path=entry))
    return mods


def detect_conflicts(mods: list[Mod]) -> dict[str, list[Mod]]:
    seen: dict[str, list[Mod]] = {}
    for mod in mods:
        for internal in mod.internal_files:
            seen.setdefault(internal, []).append(mod)
    return {k: v for k, v in seen.items() if len(v) > 1}
