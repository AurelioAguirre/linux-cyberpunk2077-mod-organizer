# Cyberpunk 2077 Mod Organizer for Linux

A simple, native Linux mod organizer for Cyberpunk 2077. Built with Python and PyQt6.

> **Alpha — v0.2.**

---

## What it does

- Automatically locates your Cyberpunk 2077 installation by searching Steam library folders
- Reads the installed game version directly from the game executable
- Lets you point the app at a folder of downloaded mod archives
- Installs mods one at a time or all at once from that folder
- Handles `.zip`, `.rar`, and `.7z` archives
- Correctly strips the `Cyberpunk 2077/` root folder that some mod authors include in their archives
- Removes all installed mods by comparing the current game folder against a clean baseline snapshot
- Logs everything it does in a panel at the bottom of the window

## How it works

Cyberpunk 2077 mods on Linux are installed by placing files into specific subdirectories of the game folder (e.g. `archive/pc/mod/`, `bin/x64/plugins/`, `r6/scripts/`). This app extracts mod archives directly into the correct location, handling the path differences between mod packages automatically.

On first launch, if the game folder is not found automatically, the app prompts you to locate it. The path is saved so you are not asked again.

**Mod removal** works by comparing the current game folder against a saved baseline snapshot of a clean install. Any file not present in the baseline is considered a mod file and deleted. Empty directories left behind are cleaned up automatically.

## Requirements

- **Linux**
- **Python 3.12**
- **Cyberpunk 2077** installed via Steam (or located manually on first launch)
- **libarchive** — handles all archive formats; almost certainly already installed as a system library (it is a dependency of `pacman`, `apt`, and most other package managers)

## Installation

```bash
git clone https://github.com/AurelioAguirre/linux-cyberpunk2077-mod-organizer.git
cd linux-cyberpunk2077-mod-organizer
chmod +x install.sh run.sh
./install.sh
```

`install.sh` creates a Python 3.12 virtual environment in `myenv/` and installs all dependencies. If Python 3.12 is not found, it will tell you and exit — install it via your distribution's package manager and try again.

## Running

```bash
./run.sh
```

## Usage

1. On first launch the app searches for your Cyberpunk 2077 installation automatically. If it is not found, you will be prompted to locate it manually. It is usually in:
   ```
   ~/.local/share/Steam/steamapps/common/Cyberpunk 2077
   ```
2. Click **Mod folder** to select the folder where you keep your downloaded mod archives.
3. Click **Install a mod** to pick a single archive from your mods folder and install it.
4. Click **Install all mods** to install every archive in the mods folder at once.
5. Click **Remove all mods** to delete every mod file from the game directory, restoring it to a clean state.

The log panel at the bottom of the window shows what the app is doing in real time.

## Removing mods

**Remove all mods** deletes every file in the game directory that is not part of the clean baseline. It will prompt you for confirmation before doing anything.

This removes files *added* by mods, but does not restore game files that were *overwritten or edited* by a mod. To restore those, use Steam's built-in file verification:

> Steam → Library → right-click Cyberpunk 2077 → Properties → Installed Files → **Verify integrity of game files**

This will restore any modified base game files without removing the mod files you added — so run **Remove all mods** first, then verify through Steam if needed.

## Notes

- The **Create Clean Baseline Snapshot** button records the full file tree of your current unmodded install to `resources/baseline_<version>.json`. This file is required for **Remove all mods** to work. It is shipped with the app for the game version it was built against — if you update the game, re-run the snapshot before using removal.
- `.rar` support is provided by `libarchive` — no separate `unrar` binary is required.
