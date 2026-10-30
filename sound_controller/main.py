import sys

from PySide6.QtWidgets import QApplication

from sound_controller.config import Config
from sound_controller.ui.icon import app_icon
from sound_controller.ui.panel import Panel
from sound_controller.ui.tray import Tray


def main() -> int:
    app = QApplication(sys.argv)
    # Закрытие окна не должно завершать программу: она живёт в трее.
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(app_icon())

    panel = Panel(Config.load())
    tray = Tray(app, panel)
    tray.show_panel()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
