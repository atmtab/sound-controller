"""Виджеты в стиле старого лампового радиоприёмника: дерево, латунь, бакелит, шкала."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QAbstractButton, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

HEADER_HEIGHT = 100
LAMP_WARM = QColor("#ffc84a")
LAMP_RED = QColor("#ff5a3a")
DIAL_INK = QColor("#3a2410")
CREAM = QColor("#f0e2bc")
BRASS_LIGHT = QColor("#ecca7a")
BRASS = QColor("#b88a35")
BRASS_DARK = QColor("#6e4d17")
SERIF = "Georgia"

ENGRAVED_LABEL_STYLE = (
    f"color: #e3c98a; font: bold 8pt '{SERIF}'; letter-spacing: 1px; background: transparent;"
)

METAL_BUTTON_STYLE = f"""
QPushButton {{
    border: 1px solid #3a2508; border-radius: 7px;
    min-width: 30px; max-width: 30px; min-height: 28px; max-height: 28px;
    color: #2a1706; font: bold 10pt '{SERIF}';
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f0d489, stop:0.45 #c9993f, stop:0.55 #b9892f, stop:1 #8a6424);
}}
QPushButton:hover {{ color: black; }}
QPushButton:pressed {{
    padding-top: 1px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #7a5720, stop:1 #b58a35);
}}
QPushButton:disabled {{ color: #7d6535; background: #7a6030; }}
"""


def brass_gradient(top: QPointF, bottom: QPointF) -> QLinearGradient:
    gradient = QLinearGradient(top, bottom)
    gradient.setColorAt(0.0, BRASS_LIGHT)
    gradient.setColorAt(0.5, BRASS)
    gradient.setColorAt(1.0, BRASS_DARK)
    return gradient


def engraved_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(ENGRAVED_LABEL_STYLE)
    return label


class Chassis(QWidget):
    """Деревянный корпус: шпон с текстурой, латунный кант, тканевая решётка и табличка."""

    TITLE = "SOUND CONTROLLER"

    def __init__(self) -> None:
        super().__init__()
        self._cache: QPixmap | None = None

    def paintEvent(self, _event) -> None:
        dpr = self.devicePixelRatioF()
        size = self.size() * dpr
        if self._cache is None or self._cache.size() != size:
            self._cache = QPixmap(size)
            self._cache.setDevicePixelRatio(dpr)
            self._cache.fill(QColor("#150c06"))
            painter = QPainter(self._cache)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._render(painter)
            painter.end()
        QPainter(self).drawPixmap(0, 0, self._cache)

    def _render(self, p: QPainter) -> None:
        body = QRectF(self.rect()).adjusted(8, 6, -8, -12)
        shape = QPainterPath()
        shape.addRoundedRect(body, 22, 22)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawRoundedRect(body.translated(0, 5), 22, 22)

        wood = QLinearGradient(body.topLeft(), body.bottomLeft())
        wood.setColorAt(0.0, QColor("#7d4c22"))
        wood.setColorAt(0.5, QColor("#5d3516"))
        wood.setColorAt(1.0, QColor("#36190a"))
        p.setPen(QPen(QColor("#1c0e04"), 1.8))
        p.setBrush(wood)
        p.drawPath(shape)

        self._paint_grain(p, body, shape)

        side = QLinearGradient(body.topLeft(), body.topRight())
        side.setColorAt(0.0, QColor(0, 0, 0, 90))
        side.setColorAt(0.12, QColor(0, 0, 0, 0))
        side.setColorAt(0.88, QColor(0, 0, 0, 0))
        side.setColorAt(1.0, QColor(0, 0, 0, 90))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(side)
        p.drawPath(shape)

        rim = QLinearGradient(body.topLeft(), body.bottomLeft())
        rim.setColorAt(0.0, QColor(255, 220, 160, 120))
        rim.setColorAt(0.2, QColor(255, 220, 160, 0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QBrush(rim), 1.4))
        p.drawRoundedRect(body.adjusted(1.5, 1.5, -1.5, -1.5), 21, 21)

        trim = body.adjusted(11, 11, -11, -11)
        p.setPen(QPen(QBrush(brass_gradient(trim.topLeft(), trim.bottomLeft())), 2.2))
        p.drawRoundedRect(trim, 14, 14)
        p.setPen(QPen(QColor(0, 0, 0, 110), 1))
        p.drawRoundedRect(trim.adjusted(2.5, 2.5, -2.5, -2.5), 12, 12)

        self._paint_grille(p, QRectF(body.left() + 30, body.top() + 22, body.width() - 60, 44))
        self._paint_title(p, body)

    def _paint_grain(self, p: QPainter, body: QRectF, shape: QPainterPath) -> None:
        rng = random.Random(7)
        p.save()
        p.setClipPath(shape)
        p.setBrush(Qt.BrushStyle.NoBrush)
        y = body.top()
        while y < body.bottom():
            amp = rng.uniform(1.5, 4.5)
            freq = rng.uniform(0.006, 0.02)
            phase = rng.uniform(0.0, math.tau)
            x = body.left()
            line = QPainterPath(QPointF(x, y + amp * math.sin(x * freq + phase)))
            while x < body.right():
                x += 18
                line.lineTo(x, y + amp * math.sin(x * freq + phase) + 1.6 * math.sin(x * 0.045 + phase * 2))
            if rng.random() < 0.6:
                color = QColor(38, 17, 5, rng.randint(20, 52))
            else:
                color = QColor(255, 205, 140, rng.randint(8, 24))
            p.setPen(QPen(color, rng.choice((1.0, 1.0, 1.7))))
            p.drawPath(line)
            y += rng.uniform(2.0, 5.5)
        p.restore()

    def _paint_grille(self, p: QPainter, area: QRectF) -> None:
        p.setPen(QPen(QBrush(brass_gradient(area.topLeft(), area.bottomLeft())), 3))
        cloth = QLinearGradient(area.topLeft(), area.bottomLeft())
        cloth.setColorAt(0.0, QColor("#b8995a"))
        cloth.setColorAt(1.0, QColor("#8f7340"))
        p.setBrush(cloth)
        p.drawRoundedRect(area, 10, 10)

        inner = area.adjusted(3, 3, -3, -3)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(inner, 8, 8)
        p.setClipPath(clip)
        # Переплетение ткани.
        x = inner.left()
        while x < inner.right():
            p.setPen(QPen(QColor(50, 32, 10, 70), 1))
            p.drawLine(QPointF(x, inner.top()), QPointF(x, inner.bottom()))
            x += 3
        y = inner.top()
        while y < inner.bottom():
            p.setPen(QPen(QColor(255, 230, 170, 40), 1))
            p.drawLine(QPointF(inner.left(), y), QPointF(inner.right(), y))
            y += 3
        shade = QLinearGradient(inner.topLeft(), inner.bottomLeft())
        shade.setColorAt(0.0, QColor(0, 0, 0, 130))
        shade.setColorAt(0.35, QColor(0, 0, 0, 0))
        shade.setColorAt(1.0, QColor(0, 0, 0, 70))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(shade)
        p.drawRect(inner)
        # Латунные перемычки решётки.
        for fraction in (0.25, 0.5, 0.75):
            cx = inner.left() + inner.width() * fraction
            p.setBrush(brass_gradient(QPointF(cx - 2, inner.top()), QPointF(cx + 2, inner.top())))
            p.drawRect(QRectF(cx - 2, inner.top(), 4, inner.height()))
        p.restore()

    def _paint_title(self, p: QPainter, body: QRectF) -> None:
        plate = QRectF(body.left() + 30, body.top() + 74, 238, 22)
        p.setPen(QPen(QColor("#3a2508"), 1.2))
        p.setBrush(brass_gradient(plate.topLeft(), plate.bottomLeft()))
        p.drawRoundedRect(plate, 5, 5)
        for dx in (6, plate.width() - 6):
            p.setBrush(QColor("#4a3410"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(plate.left() + dx, plate.center().y()), 1.8, 1.8)

        font = QFont(SERIF, 9)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)
        p.setFont(font)
        p.setPen(QColor(255, 235, 180, 160))
        p.drawText(plate.translated(0, 1), Qt.AlignmentFlag.AlignCenter, self.TITLE)
        p.setPen(QColor("#2a1706"))
        p.drawText(plate, Qt.AlignmentFlag.AlignCenter, self.TITLE)

        right = QRectF(body.right() - 170, body.top() + 74, 140, 22)
        font = QFont(SERIF, 8)
        font.setItalic(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(font)
        p.setPen(QColor(0, 0, 0, 170))
        p.drawText(right.translated(0, 1), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "Model SB-1 · Hi-Fi")
        p.setPen(QColor(228, 196, 124, 220))
        p.drawText(right, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "Model SB-1 · Hi-Fi")


class Led(QWidget):
    """Сигнальная лампочка в латунной оправе."""

    def __init__(self, color: QColor = LAMP_WARM, on: bool = False, size: int = 16) -> None:
        super().__init__()
        self._color = QColor(color)
        self._on = on
        self.setFixedSize(size, size)

    def set_on(self, on: bool) -> None:
        if on != self._on:
            self._on = on
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 - 2
        if self._on:
            glow = QRadialGradient(c, radius * 2.0)
            glow.setColorAt(0.0, QColor(self._color.red(), self._color.green(), self._color.blue(), 160))
            glow.setColorAt(1.0, QColor(self._color.red(), self._color.green(), self._color.blue(), 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawEllipse(c, radius * 2.0, radius * 2.0)

        p.setPen(QPen(QColor("#2a1a05"), 1.2))
        p.setBrush(brass_gradient(c + QPointF(0, -radius), c + QPointF(0, radius)))
        p.drawEllipse(c, radius + 1, radius + 1)

        bulb = QRadialGradient(c + QPointF(-radius * 0.25, -radius * 0.3), radius * 1.1)
        if self._on:
            bulb.setColorAt(0.0, QColor("#fffbe0"))
            bulb.setColorAt(0.45, self._color)
            bulb.setColorAt(1.0, self._color.darker(200))
        else:
            bulb.setColorAt(0.0, self._color.darker(380))
            bulb.setColorAt(1.0, self._color.darker(800))
        p.setPen(QPen(QColor("#1a1005"), 1))
        p.setBrush(bulb)
        p.drawEllipse(c, radius * 0.72, radius * 0.72)


class Lcd(QWidget):
    """Шкала приёмника: кремовое стекло в латунной оправе, текст тёмной сепией."""

    def __init__(self, text: str = "", wrap: bool = False, height: int = 32) -> None:
        super().__init__()
        self._text = text
        self._wrap = wrap
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if not wrap:
            self.setFixedHeight(height)

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        self._text = text
        self.setToolTip(text if self._wrap else "")
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        p.setPen(QPen(QBrush(brass_gradient(rect.topLeft(), rect.bottomLeft())), 3))
        paper = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        paper.setColorAt(0.0, QColor("#f7ebc4"))
        paper.setColorAt(1.0, QColor("#dcc387"))
        p.setBrush(paper)
        p.drawRoundedRect(rect, 7, 7)

        inner = rect.adjusted(2, 2, -2, -2)
        shade = QLinearGradient(inner.topLeft(), inner.topLeft() + QPointF(0, 11))
        shade.setColorAt(0.0, QColor(60, 30, 5, 110))
        shade.setColorAt(1.0, QColor(60, 30, 5, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(shade)
        p.drawRoundedRect(inner, 6, 6)

        font = QFont(SERIF, 10)
        font.setBold(True)
        p.setFont(font)
        text_rect = rect.adjusted(11, 2, -11, -2)
        if self._wrap:
            flags = Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            text = self._text
        else:
            flags = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            text = p.fontMetrics().elidedText(self._text, Qt.TextElideMode.ElideRight, int(text_rect.width()))
        p.setPen(QColor(255, 250, 225, 150))
        p.drawText(text_rect.translated(0, 1), flags, text)
        p.setPen(DIAL_INK if self.isEnabled() else QColor("#8a7650"))
        p.drawText(text_rect, flags, text)

        glare = QLinearGradient(inner.topLeft(), inner.bottomLeft())
        glare.setColorAt(0.0, QColor(255, 255, 255, 70))
        glare.setColorAt(0.5, QColor(255, 255, 255, 12))
        glare.setColorAt(0.52, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glare)
        p.drawRoundedRect(inner, 6, 6)


class MetalButton(QPushButton):
    """Латунная кнопка."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setStyleSheet(METAL_BUTTON_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)


class Selector(QWidget):
    """Переключатель «◀ шкала ▶». Повторяет нужные методы QComboBox."""

    activated = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._items: list[tuple[str, object]] = []
        self._index = -1
        self._lcd = Lcd()
        self._prev = MetalButton("◀")
        self._next = MetalButton("▶")
        self._prev.clicked.connect(lambda: self._step(-1))
        self._next.clicked.connect(lambda: self._step(1))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._prev)
        layout.addWidget(self._lcd, 1)
        layout.addWidget(self._next)

    def addItem(self, text: str, data: object = None) -> None:
        self._items.append((text, data))
        if self._index < 0:
            self.setCurrentIndex(0)

    def clear(self) -> None:
        self._items.clear()
        self._index = -1
        self._refresh()

    def count(self) -> int:
        return len(self._items)

    def findData(self, data: object) -> int:
        for i, (_text, value) in enumerate(self._items):
            if value == data:
                return i
        return -1

    def setCurrentIndex(self, index: int) -> None:
        self._index = index if 0 <= index < len(self._items) else -1
        self._refresh()

    def currentIndex(self) -> int:
        return self._index

    def currentData(self) -> object:
        return self._items[self._index][1] if self._index >= 0 else None

    def _step(self, delta: int) -> None:
        if len(self._items) < 2:
            return
        self._index = (self._index + delta) % len(self._items)
        self._refresh()
        self.activated.emit(self._index)

    def _refresh(self) -> None:
        text = self._items[self._index][0] if self._index >= 0 else "— нет устройств —"
        self._lcd.setText(text)
        self._lcd.setToolTip(text)
        multiple = len(self._items) > 1
        self._prev.setEnabled(multiple)
        self._next.setEnabled(multiple)


class RockerSwitch(QAbstractButton):
    """Бакелитовый тумблер: слоновая кость на тёмном ореховом ложе."""

    def __init__(self) -> None:
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(58, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(self.rect()).adjusted(1, 2, -1, -2)

        p.setPen(QPen(QColor(255, 220, 160, 50), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(track.adjusted(0, 1, 0, 1), 12, 12)
        well = QLinearGradient(track.topLeft(), track.bottomLeft())
        well.setColorAt(0.0, QColor("#1a0d04"))
        well.setColorAt(1.0, QColor("#3a2010"))
        p.setPen(QPen(QBrush(brass_gradient(track.topLeft(), track.bottomLeft())), 1.6))
        p.setBrush(well)
        p.drawRoundedRect(track, 12, 12)

        font = QFont(SERIF, 10)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(LAMP_WARM) if self.isChecked() else QColor(150, 118, 70))
        mark = QRectF(track.left() + 9, track.top(), track.width() - 18, track.height())
        if self.isChecked():
            p.drawText(mark, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "I")
        else:
            p.drawText(mark, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "O")

        knob_w = track.width() * 0.5
        x = track.right() - knob_w - 1 if self.isChecked() else track.left() + 1
        knob = QRectF(x, track.top() + 1, knob_w, track.height() - 2)
        ivory = QLinearGradient(knob.topLeft(), knob.bottomLeft())
        ivory.setColorAt(0.0, QColor("#fbf0d2"))
        ivory.setColorAt(0.5, QColor("#d9c79b"))
        ivory.setColorAt(1.0, QColor("#a8946a"))
        p.setPen(QPen(QColor("#2a1706"), 1.2))
        p.setBrush(ivory)
        p.drawRoundedRect(knob, 10, 10)
        p.setPen(QColor(90, 60, 20, 120))
        for dx in (-4, 0, 4):
            cx = knob.center().x() + dx
            p.drawLine(QPointF(cx, knob.top() + 7), QPointF(cx, knob.bottom() - 7))
