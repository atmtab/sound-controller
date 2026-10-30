"""Логотип и иконка приложения: ламповый приёмник со шкалой и латунной ручкой. Рисуется кодом."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

from sound_controller.ui.skin import BRASS, BRASS_DARK, BRASS_LIGHT, LAMP_WARM


def _polar(center: QPointF, radius: float, degrees: float) -> QPointF:
    """Угол отсчитывается от верха по часовой стрелке."""
    angle = math.radians(degrees)
    return QPointF(center.x() + math.sin(angle) * radius, center.y() - math.cos(angle) * radius)


def render_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = float(size)
    pen = lambda color, width: QPen(color, max(1.0, s * width))  # noqa: E731

    # Корпус из шпона с текстурой.
    body = QRectF(s * 0.03, s * 0.03, s * 0.94, s * 0.94)
    shape = QPainterPath()
    shape.addRoundedRect(body, s * 0.22, s * 0.22)
    wood = QLinearGradient(body.topLeft(), body.bottomLeft())
    wood.setColorAt(0.0, QColor("#8a5428"))
    wood.setColorAt(0.5, QColor("#5d3516"))
    wood.setColorAt(1.0, QColor("#33180a"))
    p.setPen(pen(QColor("#1c0e04"), 0.018))
    p.setBrush(wood)
    p.drawPath(shape)

    p.save()
    p.setClipPath(shape)
    rng = random.Random(11)
    y = body.top()
    p.setBrush(Qt.BrushStyle.NoBrush)
    while y < body.bottom():
        amp = rng.uniform(0.004, 0.012) * s
        phase = rng.uniform(0, math.tau)
        line = QPainterPath(QPointF(body.left(), y))
        x = body.left()
        while x < body.right():
            x += s * 0.06
            line.lineTo(x, y + amp * math.sin(x / s * 9 + phase))
        dark = rng.random() < 0.6
        p.setPen(pen(QColor(38, 17, 5, rng.randint(25, 55)) if dark else QColor(255, 205, 140, 22), 0.006))
        p.drawPath(line)
        y += rng.uniform(0.016, 0.04) * s
    p.restore()

    gloss = QLinearGradient(body.topLeft(), QPointF(body.left(), body.top() + body.height() * 0.45))
    gloss.setColorAt(0.0, QColor(255, 225, 170, 90))
    gloss.setColorAt(1.0, QColor(255, 225, 170, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gloss)
    p.drawPath(shape)

    trim = body.adjusted(s * 0.035, s * 0.035, -s * 0.035, -s * 0.035)
    brass = QLinearGradient(trim.topLeft(), trim.bottomLeft())
    brass.setColorAt(0.0, BRASS_LIGHT)
    brass.setColorAt(0.5, BRASS)
    brass.setColorAt(1.0, BRASS_DARK)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(brass, max(1.0, s * 0.016)))
    p.drawRoundedRect(trim, s * 0.19, s * 0.19)

    # Тканевая решётка сверху.
    grille = QRectF(s * 0.2, s * 0.13, s * 0.6, s * 0.1)
    cloth = QLinearGradient(grille.topLeft(), grille.bottomLeft())
    cloth.setColorAt(0.0, QColor("#c2a263"))
    cloth.setColorAt(1.0, QColor("#8f7340"))
    p.setPen(QPen(brass, max(1.0, s * 0.012)))
    p.setBrush(cloth)
    p.drawRoundedRect(grille, s * 0.035, s * 0.035)
    p.setPen(pen(QColor(60, 38, 12, 120), 0.006))
    for i in range(1, 6):
        x = grille.left() + grille.width() * i / 6
        p.drawLine(QPointF(x, grille.top() + s * 0.012), QPointF(x, grille.bottom() - s * 0.012))

    # Шкала: латунный обод, кремовая лицевая часть, деления.
    center = QPointF(s * 0.5, s * 0.57)
    outer = s * 0.3
    ring = QLinearGradient(QPointF(center.x(), center.y() - outer), QPointF(center.x(), center.y() + outer))
    ring.setColorAt(0.0, BRASS_LIGHT)
    ring.setColorAt(0.5, BRASS)
    ring.setColorAt(1.0, BRASS_DARK)
    p.setPen(pen(QColor("#2a1a05"), 0.014))
    p.setBrush(QColor(0, 0, 0, 90))
    p.drawEllipse(center + QPointF(0, s * 0.012), outer, outer)
    p.setBrush(ring)
    p.drawEllipse(center, outer, outer)

    face = QRadialGradient(center + QPointF(-outer * 0.25, -outer * 0.3), outer * 1.1)
    face.setColorAt(0.0, QColor("#fff6d8"))
    face.setColorAt(1.0, QColor("#cdb27a"))
    p.setPen(pen(QColor("#4a3410"), 0.008))
    p.setBrush(face)
    p.drawEllipse(center, outer * 0.84, outer * 0.84)

    for i in range(13):
        degrees = -120 + i * 20
        major = i % 3 == 0
        start = _polar(center, outer * (0.55 if major else 0.62), degrees)
        end = _polar(center, outer * 0.74, degrees)
        p.setPen(QPen(QColor("#3a2410"), max(1.0, s * (0.014 if major else 0.008)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(start, end)

    # Стрелка и втулка.
    tip = _polar(center, outer * 0.7, 28)
    p.setPen(QPen(QColor("#a3281f"), max(1.0, s * 0.022), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(center, tip)
    hub = QRadialGradient(center + QPointF(-s * 0.01, -s * 0.012), s * 0.06)
    hub.setColorAt(0.0, BRASS_LIGHT)
    hub.setColorAt(1.0, BRASS_DARK)
    p.setPen(pen(QColor("#2a1a05"), 0.008))
    p.setBrush(hub)
    p.drawEllipse(center, s * 0.04, s * 0.04)

    # Сигнальная лампочка.
    lamp = QPointF(s * 0.5, s * 0.915)
    glow = QRadialGradient(lamp, s * 0.1)
    glow.setColorAt(0.0, QColor(255, 200, 74, 190))
    glow.setColorAt(1.0, QColor(255, 200, 74, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(glow)
    p.drawEllipse(lamp, s * 0.1, s * 0.1)
    bulb = QRadialGradient(lamp + QPointF(-s * 0.006, -s * 0.008), s * 0.035)
    bulb.setColorAt(0.0, QColor("#fffbe0"))
    bulb.setColorAt(0.5, LAMP_WARM)
    bulb.setColorAt(1.0, LAMP_WARM.darker(200))
    p.setPen(pen(QColor("#2a1a05"), 0.01))
    p.setBrush(bulb)
    p.drawEllipse(lamp, s * 0.03, s * 0.03)

    # Дуги звуковых волн по бокам шкалы.
    for side in (-1, 1):
        for k, radius in enumerate((0.35, 0.40)):
            arc = QRectF(center.x() - s * radius, center.y() - s * radius, s * radius * 2, s * radius * 2)
            alpha = 200 - k * 70
            p.setPen(QPen(QColor(BRASS_LIGHT.red(), BRASS_LIGHT.green(), BRASS_LIGHT.blue(), alpha),
                          max(1.0, s * 0.014), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            # drawArc отсчитывает угол против часовой от «3 часов».
            start = -22 if side > 0 else 180 - 22
            p.drawArc(arc, start * 16, 44 * 16)
    p.end()
    return pixmap


def app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(render_icon(size))
    return icon
