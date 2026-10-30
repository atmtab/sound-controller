"""Рисует логотип. Использование: python tools/make_icon.py <app.ico> [logo.png]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from sound_controller.ui.icon import render_icon  # noqa: E402


def main() -> int:
    app = QGuiApplication([])  # noqa: F841  нужен для QPixmap
    ico = Path(sys.argv[1])
    ico.parent.mkdir(parents=True, exist_ok=True)
    if not render_icon(256).save(str(ico), "ICO"):
        print("Не удалось записать ico", file=sys.stderr)
        return 1
    if len(sys.argv) > 2:
        png = Path(sys.argv[2])
        png.parent.mkdir(parents=True, exist_ok=True)
        if not render_icon(512).save(str(png), "PNG"):
            print("Не удалось записать png", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
