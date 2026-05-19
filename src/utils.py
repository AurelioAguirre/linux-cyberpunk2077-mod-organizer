from pathlib import Path
import logging
import re
import pefile

log = logging.getLogger(__name__)

GAME_EXE = "REDprelauncher.exe"
_STEAM_ROOT = Path.home() / ".local" / "share" / "Steam"
_STEAM_VDF = _STEAM_ROOT / "steamapps" / "libraryfolders.vdf"


def find_game_path() -> Path | None:
    """Search for the Cyberpunk 2077 install directory.

    Search order:
    1. Default Steam library
    2. Additional Steam libraries declared in libraryfolders.vdf
    3. Common external-drive mount points (/run/media, /mnt)
    """
    log.info("Game path not set — searching Steam libraries...")
    for library in _steam_libraries():
        candidate = library / "steamapps" / "common" / "Cyberpunk 2077"
        log.debug("Checking %s", candidate)
        if (candidate / GAME_EXE).exists():
            log.info("Found game at %s", candidate)
            return candidate

    log.info("Not found in Steam libraries — checking external drives...")
    for base in _external_mount_bases():
        for candidate in base.glob("*/steamapps/common/Cyberpunk 2077"):
            if (candidate / GAME_EXE).exists():
                log.info("Found game at %s", candidate)
                return candidate

    log.warning("Cyberpunk2077.exe not found — set GAME_PATH manually")
    return None


_VERSION_EXE = Path("bin") / "x64" / "Cyberpunk2077.exe"


def get_game_version(game_path: Path) -> str:
    """Read the product version string from bin/x64/Cyberpunk2077.exe."""
    exe = game_path / _VERSION_EXE
    if not exe.exists():
        log.warning("Version exe not found at %s", exe)
        return "unknown"
    try:
        pe = pefile.PE(str(exe), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
        )
        if hasattr(pe, "FileInfo"):
            for block in pe.FileInfo:
                for info in block:
                    if info.Key == b"StringFileInfo":
                        for table in info.StringTable:
                            version = table.entries.get(b"ProductVersion")
                            if version:
                                return version.decode("utf-8", errors="replace").strip()
        if hasattr(pe, "VS_FIXEDFILEINFO"):
            ffi = pe.VS_FIXEDFILEINFO[0]
            ms, ls = ffi.ProductVersionMS, ffi.ProductVersionLS
            return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception as e:
        log.error("Could not read game version: %s", e)
    return "unknown"


def is_valid_game_path(path: Path) -> bool:
    return bool(path.name) and (path / GAME_EXE).exists()


def _steam_libraries() -> list[Path]:
    libraries = [_STEAM_ROOT]
    if not _STEAM_VDF.exists():
        return libraries
    text = _STEAM_VDF.read_text(errors="replace")
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        libraries.append(Path(match.group(1)))
    return libraries


def _external_mount_bases() -> list[Path]:
    bases = []
    user = Path.home().name
    for p in [Path("/run/media") / user, Path("/run/media"), Path("/mnt")]:
        if p.is_dir():
            bases.append(p)
    return bases
