from pathlib import Path
import logging
import libarchive
from .models import Mod

log = logging.getLogger(__name__)

ARCHIVE_TARGET = Path("archive") / "pc" / "mod"
_CP2077_ROOT = "cyberpunk 2077"


def install_mod(archive_path: Path, game_path: Path) -> int:
    """Extract a mod archive into game_path.

    If the archive contains a top-level 'Cyberpunk 2077' folder, its contents
    are extracted as if that folder were the game root.
    Returns the number of files written.
    """
    from .scanner import list_archive_contents

    contents = list_archive_contents(archive_path)
    strip = _detect_cp2077_root(contents)
    if strip:
        log.info("Detected root folder '%s' — stripping it from paths", strip)

    count = 0
    with libarchive.file_reader(str(archive_path)) as archive:
        for entry in archive:
            if entry.isdir:
                continue

            rel_path = entry.pathname
            if strip:
                parts = Path(rel_path).parts
                if len(parts) > 1 and parts[0] == strip:
                    rel_path = str(Path(*parts[1:]))
                else:
                    continue

            dest = game_path / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            log.debug("  → %s", rel_path)
            with open(dest, "wb") as f:
                for block in entry.get_blocks():
                    f.write(block)
            count += 1

    return count


def _detect_cp2077_root(contents: list[str]) -> str | None:
    """Return the root folder name if all paths share a 'Cyberpunk 2077' root."""
    roots = {Path(p).parts[0] for p in contents if Path(p).parts}
    if len(roots) == 1:
        root = roots.pop()
        if root.lower() == _CP2077_ROOT:
            return root
    return None


def remove_mods(game_path: Path, baseline_files: set[str]) -> tuple[int, int]:
    """Delete every file in game_path that is not in baseline_files.

    Returns (files_deleted, dirs_deleted).
    """
    files_deleted = 0
    for file in game_path.rglob("*"):
        if not file.is_file():
            continue
        rel = str(file.relative_to(game_path)).replace("\\", "/")
        if rel not in baseline_files:
            log.debug("Removing %s", rel)
            file.unlink()
            files_deleted += 1

    # Remove directories that are now empty, deepest first
    dirs_deleted = 0
    for folder in sorted(game_path.rglob("*"), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
            dirs_deleted += 1

    return files_deleted, dirs_deleted


def undeploy(game_path: Path) -> None:
    """Remove all deployed mods from the game directory."""
    target_dir = game_path / ARCHIVE_TARGET
    if not target_dir.exists():
        return
    for entry in target_dir.iterdir():
        if entry.suffix == ".archive":
            entry.unlink()
