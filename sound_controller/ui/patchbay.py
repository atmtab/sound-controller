"""Коммутатор: штекеры приложений втыкаются в гнёзда блоков-устройств."""
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from sound_controller.audio.devices import OutputDevice
from sound_controller.audio.sessions import RunningApp
from sound_controller.ui.skin import BRASS, BRASS_DARK, BRASS_LIGHT, CREAM, LAMP_WARM

CABLE_COLORS = ["#b3332f", "#d19a2a", "#2f7f8f", "#5f8a3c", "#8a4f8f", "#c2622d"]
IDLE_CABLE = QColor("#8d7b5c")

MARGIN = 6
ROW_H = 44
ROW_GAP = 4
APP_W = 236
DEV_W = 240
SCROLL_W = 12
PLUG_LEN = 30
PLUG_H = 16
SLOT_H = 34
BOX_PAD = 14
MIN_BOX_H = 82
BOX_GAP = 10
JACK_R = 12


def split_name(name: str) -> tuple[str, str]:
    """'Наушники (Logitech H570e)' -> ('Наушники', '(Logitech H570e)')."""
    head, sep, tail = name.partition(" (")
    return (head, "(" + tail) if sep else (name, "")


@dataclass
class _Box:
    device: OutputDevice
    color: QColor
    rect: QRectF
    slots: list[QPointF]  # slots[0] свободное гнездо, дальше по порядку подключённые приложения
    users: list[str]


class PatchBay(QWidget):
    assigned = Signal(object, object)  # RunningApp, id устройства или None

    def __init__(self) -> None:
        super().__init__()
        self._apps: list[RunningApp] = []
        self._devices: list[OutputDevice] = []
        self._assign: dict[str, str] = {}
        self._offset = 0.0
        self._drag: str | None = None
        self._pos = QPointF()
        self.setMouseTracking(True)
        self.setMinimumHeight(220)

    # ---- данные ----

    def set_data(self, apps, devices, assignments: dict[str, str | None]) -> None:
        self._apps = list(apps)
        self._devices = list(devices)
        known = {d.id for d in devices}
        self._assign = {n: d for n, d in assignments.items() if d in known}
        if self._drag not in {a.name for a in self._apps}:
            self._drag = None
        self._clamp_offset()
        self.update()

    def set_assignment(self, name: str, device_id: str | None) -> None:
        if device_id:
            self._assign[name] = device_id
        else:
            self._assign.pop(name, None)
        self.update()

    # ---- геометрия ----

    def _content_height(self) -> float:
        return 2 * MARGIN + len(self._apps) * (ROW_H + ROW_GAP)

    def _clamp_offset(self) -> None:
        self._offset = max(0.0, min(self._offset, self._content_height() - self.height()))

    def _row_rect(self, i: int) -> QRectF:
        y = MARGIN + i * (ROW_H + ROW_GAP) - self._offset
        return QRectF(MARGIN, y, APP_W, ROW_H)

    def _app_jack(self, i: int) -> QPointF:
        rect = self._row_rect(i)
        return QPointF(rect.right() - 26, rect.center().y())

    def _visible_rows(self) -> range:
        first = max(0, int(self._offset // (ROW_H + ROW_GAP)))
        last = min(len(self._apps), int((self._offset + self.height()) // (ROW_H + ROW_GAP)) + 1)
        return range(first, last)

    def _boxes(self) -> list[_Box]:
        n = len(self._devices)
        if not n:
            return []
        order = [a.name for a in self._apps]
        users = {
            d.id: [name for name in order if self._assign.get(name) == d.id]
            for d in self._devices
        }
        natural = [max(MIN_BOX_H, 2 * BOX_PAD + (len(users[d.id]) + 1) * SLOT_H) for d in self._devices]
        avail = self.height() - 2 * MARGIN - BOX_GAP * (n - 1)
        scale = max(0.6, min(1.0, avail / sum(natural)))
        slot_h = SLOT_H * scale
        heights = [h * scale for h in natural]
        top = MARGIN + max(0.0, (avail - sum(heights)) / 2)
        left = self.width() - MARGIN - SCROLL_W - DEV_W

        boxes = []
        for i, device in enumerate(self._devices):
            rect = QRectF(left, top, DEV_W, heights[i])
            count = len(users[device.id]) + 1
            slots = [
                QPointF(rect.left() + 26, rect.top() + BOX_PAD * scale + slot_h * (k + 0.5))
                for k in range(count)
            ]
            color = QColor(CABLE_COLORS[i % len(CABLE_COLORS)])
            boxes.append(_Box(device, color, rect, slots, users[device.id]))
            top += heights[i] + BOX_GAP
        return boxes

    def _cable_ends(self, boxes):
        """name -> (точка у приложения, точка у устройства, цвет)."""
        by_id = {b.device.id: b for b in boxes}
        ends = {}
        for i in self._visible_rows():
            name = self._apps[i].name
            box = by_id.get(self._assign.get(name))
            if box is None:
                continue
            slot = box.slots[1 + box.users.index(name)]
            ends[name] = (i, self._app_jack(i), slot, box.color)
        return ends

    # ---- рисование ----

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(QPen(QColor(BRASS.red(), BRASS.green(), BRASS.blue(), 120), 1.4))
        p.setBrush(QColor(24, 11, 4, 190))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)
        p.setClipRect(self.rect().adjusted(2, 2, -2, -2))

        boxes = self._boxes()
        hover = self._box_at(boxes, self._pos) if self._drag else None
        ends = self._cable_ends(boxes)

        for i in self._visible_rows():
            self._paint_app(p, i, plugged=self._apps[i].name in ends)
        for box in boxes:
            self._paint_box(p, box, hovered=box is hover)

        for name, (_i, a, b, color) in ends.items():
            if name == self._drag:
                continue
            self._paint_cable(p, a + QPointF(2 + PLUG_LEN, 0), b + QPointF(-2 - PLUG_LEN, 0), color)
        for name, (_i, a, b, color) in ends.items():
            if name == self._drag:
                continue
            self._paint_plug(p, a + QPointF(2, 0), +1, color)
            self._paint_plug(p, b + QPointF(-2, 0), -1, color)

        if self._drag:
            self._paint_drag(p, ends, hover)
        self._paint_scrollbar(p)

    def _paint_drag(self, p: QPainter, ends, hover) -> None:
        index = next((i for i, a in enumerate(self._apps) if a.name == self._drag), None)
        if index is None or not (0 <= self._row_rect(index).bottom() and self._row_rect(index).top() <= self.height()):
            return
        color = hover.color if hover else IDLE_CABLE
        start = self._app_jack(index)
        self._paint_cable(p, start + QPointF(2 + PLUG_LEN, 0), self._pos + QPointF(-2 - PLUG_LEN, 0), color)
        self._paint_plug(p, start + QPointF(2, 0), +1, color)
        self._paint_plug(p, self._pos + QPointF(-2, 0), -1, color)

    def _paint_app(self, p: QPainter, i: int, plugged: bool) -> None:
        app = self._apps[i]
        rect = self._row_rect(i)
        p.setPen(QPen(QColor(BRASS.red(), BRASS.green(), BRASS.blue(), 90), 1))
        plate = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        plate.setColorAt(0.0, QColor("#4a2c14"))
        plate.setColorAt(1.0, QColor("#2c170a"))
        p.setBrush(plate)
        p.drawRoundedRect(rect, 10, 10)

        self._paint_led(p, QPointF(rect.left() + 18, rect.center().y()), app.playing)

        font = QFont("Georgia", 10)
        font.setBold(True)
        p.setFont(font)
        text = QRectF(rect.left() + 36, rect.top(), rect.width() - 36 - 68, rect.height())
        name = p.fontMetrics().elidedText(app.name, Qt.TextElideMode.ElideRight, int(text.width()))
        p.setPen(QColor(0, 0, 0, 200))
        p.drawText(text.translated(0, 1), Qt.AlignmentFlag.AlignVCenter, name)
        p.setPen(CREAM)
        p.drawText(text, Qt.AlignmentFlag.AlignVCenter, name)

        jack = self._app_jack(i)
        if not plugged:
            small = QFont("Georgia", 7)
            small.setBold(True)
            p.setFont(small)
            p.setPen(QColor(168, 134, 76))
            p.drawText(
                QRectF(jack.x() - 54, rect.top(), 36, rect.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                "АВТО",
            )
        self._paint_jack(p, jack)

    def _paint_box(self, p: QPainter, box: _Box, hovered: bool) -> None:
        rect = box.rect
        body = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        body.setColorAt(0.0, QColor("#5b3a1e"))
        body.setColorAt(0.08, QColor("#46290f"))
        body.setColorAt(1.0, QColor("#2a1608"))
        border = QColor(BRASS_LIGHT) if hovered else QColor("#1a0c04")
        p.setPen(QPen(border, 2.2 if hovered else 1.4))
        p.setBrush(body)
        p.drawRoundedRect(rect, 12, 12)

        stripe = QColor(box.color)
        stripe.setAlpha(210 if box.users else 90)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(stripe)
        p.drawRoundedRect(QRectF(rect.left() + 8, rect.top() + 7, rect.width() - 16, 3), 1.5, 1.5)

        title, subtitle = split_name(box.device.name)
        text_left = rect.left() + 58
        width = int(rect.right() - 14 - text_left)
        font = QFont("Georgia", 10)
        font.setBold(True)
        p.setFont(font)
        y = rect.top() + 16
        p.setPen(QColor(0, 0, 0, 190))
        p.drawText(QPointF(text_left, y + 14), p.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, width))
        p.setPen(CREAM)
        p.drawText(QPointF(text_left, y + 13), p.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, width))
        if subtitle:
            small = QFont("Georgia", 8)
            small.setItalic(True)
            p.setFont(small)
            p.setPen(QColor("#c9b07a"))
            p.drawText(QPointF(text_left, y + 30), p.fontMetrics().elidedText(subtitle, Qt.TextElideMode.ElideRight, width))
        if box.device.is_virtual_cable:
            badge = QFont("Georgia", 7)
            badge.setBold(True)
            p.setFont(badge)
            p.setPen(QColor("#ff9a55"))
            p.drawText(QPointF(text_left, y + 46), "ВИРТУАЛЬНЫЙ КАБЕЛЬ")

        for k, slot in enumerate(box.slots):
            self._paint_jack(p, slot, tint=box.color if k > 0 else None, glow=hovered and k == 0)

    def _paint_jack(self, p: QPainter, c: QPointF, tint: QColor | None = None, glow: bool = False) -> None:
        p.setPen(QPen(QColor("#2a1a05"), 1.2))
        ring = QLinearGradient(c + QPointF(0, -JACK_R), c + QPointF(0, JACK_R))
        ring.setColorAt(0.0, BRASS_LIGHT)
        ring.setColorAt(0.5, BRASS)
        ring.setColorAt(1.0, BRASS_DARK)
        p.setBrush(ring)
        p.drawEllipse(c, JACK_R, JACK_R)

        hole = QRadialGradient(c + QPointF(0, 1.5), JACK_R * 0.75)
        hole.setColorAt(0.0, QColor("#000000"))
        hole.setColorAt(1.0, QColor("#1c1208"))
        p.setPen(QPen(QColor(255, 220, 150, 60), 1))
        p.setBrush(hole)
        p.drawEllipse(c, JACK_R * 0.62, JACK_R * 0.62)

        if tint is not None or glow:
            color = QColor(tint) if tint is not None else QColor(LAMP_WARM)
            color.setAlpha(230)
            p.setPen(QPen(color, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, JACK_R + 2.5, JACK_R + 2.5)

    def _paint_led(self, p: QPainter, c: QPointF, on: bool) -> None:
        if on:
            glow = QRadialGradient(c, 14)
            glow.setColorAt(0.0, QColor(255, 200, 74, 160))
            glow.setColorAt(1.0, QColor(255, 200, 74, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawEllipse(c, 14, 14)
        lens = QRadialGradient(c + QPointF(-2, -2.5), 9)
        if on:
            lens.setColorAt(0.0, QColor("#fffbe0"))
            lens.setColorAt(0.5, QColor(LAMP_WARM))
            lens.setColorAt(1.0, QColor(LAMP_WARM).darker(200))
        else:
            lens.setColorAt(0.0, QColor("#4a3612"))
            lens.setColorAt(1.0, QColor("#1c1306"))
        p.setPen(QPen(QColor("#2a1a05"), 1.6))
        p.setBrush(lens)
        p.drawEllipse(c, 6, 6)

    def _paint_cable(self, p: QPainter, a: QPointF, b: QPointF, color: QColor) -> None:
        dx = max(abs(b.x() - a.x()) * 0.45, 40.0)
        sag = 28.0
        path = QPainterPath(a)
        path.cubicTo(QPointF(a.x() + dx, a.y() + sag), QPointF(b.x() - dx, b.y() + sag), b)

        def stroke(pen_color: QColor, width: float, dy: float = 0.0) -> None:
            pen = QPen(pen_color, width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.save()
            p.translate(0, dy)
            p.drawPath(path)
            p.restore()

        stroke(QColor(0, 0, 0, 70), 7.0, 6.0)
        stroke(QColor("#120904"), 8.0)
        stroke(color, 5.4)
        stroke(QColor(255, 255, 255, 120), 1.5, -1.3)

    def _plug_rects(self, tip: QPointF, sign: int):
        def span(start: float, end: float, h: float) -> QRectF:
            x0, x1 = sorted((tip.x() + sign * start, tip.x() + sign * end))
            return QRectF(x0, tip.y() - h / 2, x1 - x0, h)

        return span(0, 12, 8), span(12, 16, 9), span(16, PLUG_LEN, PLUG_H)

    def _paint_plug(self, p: QPainter, tip: QPointF, sign: int, color: QColor) -> None:
        metal, collar, sleeve = self._plug_rects(tip, sign)
        p.setPen(QPen(QColor("#2a1a05"), 1))
        nickel = QLinearGradient(metal.topLeft(), metal.bottomLeft())
        nickel.setColorAt(0.0, QColor("#fff0c0"))
        nickel.setColorAt(0.5, BRASS)
        nickel.setColorAt(1.0, BRASS_DARK)
        p.setBrush(nickel)
        p.drawRoundedRect(metal, 2, 2)
        p.setBrush(QColor("#1c1208"))
        p.drawRect(collar)
        grip = QLinearGradient(sleeve.topLeft(), sleeve.bottomLeft())
        grip.setColorAt(0.0, color.lighter(150))
        grip.setColorAt(0.5, color)
        grip.setColorAt(1.0, color.darker(190))
        p.setBrush(grip)
        p.drawRoundedRect(sleeve, 4, 4)

    def _paint_scrollbar(self, p: QPainter) -> None:
        content = self._content_height()
        if content <= self.height():
            return
        track = QRectF(self.width() - MARGIN - SCROLL_W + 3, MARGIN, 6, self.height() - 2 * MARGIN)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 130))
        p.drawRoundedRect(track, 3, 3)
        ratio = self.height() / content
        handle_h = max(28.0, track.height() * ratio)
        span = track.height() - handle_h
        y = track.top() + span * (self._offset / (content - self.height()))
        p.setBrush(QColor(BRASS))
        p.drawRoundedRect(QRectF(track.left(), y, track.width(), handle_h), 3, 3)

    # ---- мышь ----

    @staticmethod
    def _box_at(boxes, pos: QPointF) -> _Box | None:
        return next((b for b in boxes if b.rect.adjusted(-30, 0, 0, 0).contains(pos)), None)

    def _app_hit(self, pos: QPointF, boxes) -> int | None:
        ends = self._cable_ends(boxes)
        for i in self._visible_rows():
            jack = self._app_jack(i)
            if (pos - jack).manhattanLength() <= JACK_R + 6:
                return i
            name = self._apps[i].name
            if name in ends:
                _i, a, b, _color = ends[name]
                _m, _c, sleeve_a = self._plug_rects(a + QPointF(2, 0), +1)
                _m, _c, sleeve_b = self._plug_rects(b + QPointF(-2, 0), -1)
                full_a = QRectF(a.x(), a.y() - 9, PLUG_LEN + 2, 18)
                full_b = QRectF(b.x() - PLUG_LEN - 2, b.y() - 9, PLUG_LEN + 2, 18)
                if full_a.contains(pos) or full_b.contains(pos):
                    return i
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = self._app_hit(event.position(), self._boxes())
        if index is None:
            return
        self._drag = self._apps[index].name
        self._pos = event.position()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        self._pos = event.position()
        if self._drag:
            self.update()
            return
        hit = self._app_hit(self._pos, self._boxes())
        self.setCursor(Qt.CursorShape.OpenHandCursor if hit is not None else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._drag:
            return
        name, self._drag = self._drag, None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        box = self._box_at(self._boxes(), event.position())
        target = box.device.id if box else None
        app = next((a for a in self._apps if a.name == name), None)
        if app is not None and target != self._assign.get(name):
            self.assigned.emit(app, target)
        self.update()

    def wheelEvent(self, event) -> None:
        self._offset -= event.angleDelta().y() / 120 * (ROW_H + ROW_GAP) * 1.5
        self._clamp_offset()
        self.update()

    def resizeEvent(self, event) -> None:
        self._clamp_offset()
        super().resizeEvent(event)
