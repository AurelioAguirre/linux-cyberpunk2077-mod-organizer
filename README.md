# Cyberpunk 2077 Mod Organizer for Linux

A simple, native Linux mod organizer for Cyberpunk 2077. Built with Python and PyQt6.

> **Alpha — v0.1.** Core installation features work. More features are in progress.

---

## What it does

- Automatically locates your Cyberpunk 2077 installation by searching Steam library folders
- Reads the installed game version directly from the game executable
- Lets you point the app at a folder of downloaded mods
- Installs mods one at a time or all at once from that folder
- Handles `.zip`, `.rar`, and `.7z` archives
- Correctly strips the `Cyberpunk 2077/` root folder that some mod authors include in their archives
- Logs everything it does in a panel at the bottom of the window

## How it works

Cyberpunk 2077 mods on Linux are installed by placing files into specific subdirectories of the game folder (e.g. `archive/pc/mod/`, `bin/x64/plugins/`, `r6/scripts/`). This app extracts mod archives directly into the correct location, handling the path differences between mod packages automatically.

On first launch, if the game folder is not found automatically, the app prompts you to locate it. The path is saved so you are not asked again.

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

The log panel at the bottom of the window shows what the app is doing in real time.

## Notes

- Mods are extracted directly into the game directory. Uninstalling a mod currently requires verifying game files through Steam, which will restore any files that were overwritten.
- The **Create Clean Baseline Snapshot** feature records the file tree of an unmodded install. This will be used in a future version to detect which mods are installed and to selectively remove them.
- `.rar` support is provided by `libarchive` — no separate `unrar` binary is required.
