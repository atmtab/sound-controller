"""Иконка в системном трее."""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from sound_controller.ui.icon import app_icon
from sound_controller.ui.panel import Panel


class Tray:
    def __init__(self, app: QApplication, panel: Panel) -> None:
        self._panel = panel
        self.icon = QSystemTrayIcon(app_icon(), app)
        self.icon.setToolTip("Sound Controller")

        menu = QMenu()
        show = QAction("Открыть панель", menu)
        show.triggered.connect(self.show_panel)
        quit_action = QAction("Выход", menu)
        quit_action.triggered.connect(app.quit)
        menu.addAction(show)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._menu = menu

        self.icon.setContextMenu(menu)
        self.icon.activated.connect(self._on_activated)
        self.icon.show()

    def show_panel(self) -> None:
        self._panel.refresh()
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_panel()
