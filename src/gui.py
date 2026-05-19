import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QFileDialog, QMessageBox, QLabel, QPushButton
)
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor, QPixmap
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from config import Config, RESOURCES_PATH
from utils import is_valid_game_path, get_game_version
from api.scanner import build_snapshot, save_snapshot, scan_mod_archives, list_archive_contents, load_snapshot
from api.deployer import install_mod, remove_mods

log = logging.getLogger(__name__)


class _LogHandler(logging.Handler, QObject):
    """Logging handler that emits each record as a Qt signal."""
    message_ready = pyqtSignal(str, int)  # (formatted message, levelno)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        self.message_ready.emit(self.format(record), record.levelno)


class LogPanel(QTextEdit):
    """Read-only widget that displays log records with level-based coloring."""

    _COLORS = {
        logging.DEBUG:    "#888888",
        logging.INFO:     "#e0e0e0",
        logging.WARNING:  "#f0c060",
        logging.ERROR:    "#f06060",
        logging.CRITICAL: "#ff4040",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #1a1a2e; font-family: monospace; font-size: 12px;")

    def append_record(self, message: str, levelno: int) -> None:
        color = self._COLORS.get(levelno, "#e0e0e0")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyberpunk 2077 Mod Organizer")
        self.resize(1024, 768)
        self._build_ui()
        self._setup_logging()
        self.config = Config.load()
        if not is_valid_game_path(self.config.game_path):
            self._prompt_game_path()
        if is_valid_game_path(self.config.game_path):
            version = get_game_version(self.config.game_path)
            log.info("Cyberpunk 2077 version: %s", version)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # Logo
        logo_path = Path(__file__).parent.parent / "resources" / "logo.png"
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("[ logo not found ]")
        layout.addWidget(logo_label)

        # Option buttons
        button_area = QWidget()
        button_layout = QVBoxLayout(button_area)
        button_layout.setSpacing(8)

        btn_snapshot = QPushButton("Create Clean Baseline Snapshot")
        btn_snapshot.setFixedSize(440, 50)
        btn_snapshot.clicked.connect(self._create_snapshot)
        button_layout.addWidget(btn_snapshot, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_install = QPushButton("Install a mod")
        btn_install.setFixedSize(440, 50)
        btn_install.clicked.connect(self._install_mod)
        button_layout.addWidget(btn_install, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_install_all = QPushButton("Install all mods")
        btn_install_all.setFixedSize(440, 50)
        btn_install_all.clicked.connect(self._install_all_mods)
        button_layout.addWidget(btn_install_all, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_remove = QPushButton("Remove all mods")
        btn_remove.setFixedSize(440, 50)
        btn_remove.clicked.connect(self._remove_all_mods)
        button_layout.addWidget(btn_remove, alignment=Qt.AlignmentFlag.AlignHCenter)

        for i in range(5, 6):
            btn = QPushButton(f"Option {i}")
            btn.setFixedSize(440, 50)
            button_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(button_area)

        layout.addStretch()

        # Bottom toolbar — sits just above the log panel
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(24, 0, 0, 0)
        toolbar_layout.setSpacing(0)
        self.btn_mod_folder = QPushButton("Mod folder")
        self.btn_mod_folder.setFixedSize(160, 36)
        self.btn_mod_folder.clicked.connect(self._select_mod_folder)
        toolbar_layout.addWidget(self.btn_mod_folder)
        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        # Log panel
        self.log_panel = LogPanel()
        self.log_panel.setFixedHeight(180)
        layout.addWidget(self.log_panel)

    def _setup_logging(self):
        self._log_handler = _LogHandler()
        self._log_handler.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
        self._log_handler.message_ready.connect(self.log_panel.append_record)
        logging.getLogger().addHandler(self._log_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    def _create_snapshot(self):
        if not is_valid_game_path(self.config.game_path):
            log.error("No valid game path set — cannot create snapshot")
            return
        snapshot = build_snapshot(self.config.game_path)
        save_snapshot(snapshot, RESOURCES_PATH)

    def _install_mod(self):
        if not self.config.mods_path.is_dir():
            log.warning("Mods folder not set — use the 'Mod folder' button first")
            return

        archives = scan_mod_archives(self.config.mods_path)
        if not archives:
            log.warning("No .zip / .rar / .7z files found in %s", self.config.mods_path)
            return

        start = str(self.config.mods_path)
        file, _ = QFileDialog.getOpenFileName(
            self, "Select a mod to install", start,
            "Archives (*.zip *.rar *.7z)"
        )
        if not file:
            return

        archive_path = Path(file)
        log.info("Installing %s...", archive_path.name)
        try:
            count = install_mod(archive_path, self.config.game_path)
            log.info("Done — %d files installed from %s", count, archive_path.name)
        except Exception as e:
            log.error("Installation failed: %s", e)

    def _remove_all_mods(self):
        version = get_game_version(self.config.game_path)
        snapshot = load_snapshot(RESOURCES_PATH, version)

        if snapshot is None:
            log.error("No baseline snapshot found — cannot remove mods safely")
            return

        box = QMessageBox(self)
        box.setWindowTitle("Remove all mods")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText("<b>This will delete every file not present in the clean baseline.</b>")
        box.setInformativeText(
            "This removes files added by mods, but will NOT restore game files that "
            "were overwritten or edited by a mod.\n\n"
            "To restore those, go to Steam → Library → right-click Cyberpunk 2077 → "
            "Properties → Installed Files → Verify integrity of game files.\n\n"
            "Do you want to continue?"
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        log.info("Removing mods — comparing against baseline v%s...", snapshot.game_version)
        baseline = set(snapshot.files)
        try:
            files_deleted, dirs_deleted = remove_mods(self.config.game_path, baseline)
            log.info("Done — %d file(s) and %d empty folder(s) removed", files_deleted, dirs_deleted)
        except Exception as e:
            log.error("Failed during removal: %s", e)

    def _install_all_mods(self):
        if not self.config.mods_path.is_dir():
            log.warning("Mods folder not set — use the 'Mod folder' button first")
            return

        archives = scan_mod_archives(self.config.mods_path)
        if not archives:
            log.warning("No .zip / .rar / .7z files found in %s", self.config.mods_path)
            return

        log.info("Installing %d mod(s) from %s...", len(archives), self.config.mods_path)
        total_files = 0
        failed = 0
        for archive in archives:
            log.info("Installing %s...", archive.name)
            try:
                count = install_mod(archive, self.config.game_path)
                log.info("  %d files installed", count)
                total_files += count
            except Exception as e:
                log.error("  Failed: %s", e)
                failed += 1

        if failed:
            log.warning("Done — %d files installed, %d mod(s) failed", total_files, failed)
        else:
            log.info("Done — %d files installed across %d mod(s)", total_files, len(archives))

    def _select_mod_folder(self):
        start = str(self.config.mods_path) if self.config.mods_path.is_dir() else str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Mods Folder", start)
        if not folder:
            return
        self.config.mods_path = Path(folder)
        self.config.save()
        log.info("Mods folder set: %s", folder)

    def _prompt_game_path(self):
        log.warning("Cyberpunk 2077 folder not found automatically")

        hint_path = "~/.local/share/Steam/steamapps/common"

        box = QMessageBox(self)
        box.setWindowTitle("Game Not Found")
        box.setIcon(QMessageBox.Icon.Question)
        box.setText("<b>Cyberpunk 2077 folder not found.</b>")
        box.setInformativeText(
            "Would you like to browse for it?\n\n"
            f"It is usually found in:\n{hint_path}"
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(QMessageBox.StandardButton.Yes)

        if box.exec() != QMessageBox.StandardButton.Yes:
            log.warning("Game path not set — some features will be unavailable")
            return

        steam_common = Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common"
        start_dir = str(steam_common) if steam_common.exists() else str(Path.home())

        folder = QFileDialog.getExistingDirectory(self, "Select Cyberpunk 2077 folder", start_dir)
        if not folder:
            log.warning("No folder selected")
            return

        path = Path(folder)
        if not is_valid_game_path(path):
            log.error("Cyberpunk2077.exe not found in that folder — please try again")
            self._prompt_game_path()
            return

        self.config.game_path = path
        self.config.save()
        log.info("Game path saved: %s", path)

    def closeEvent(self, event):
        logging.getLogger().removeHandler(self._log_handler)
        super().closeEvent(event)
