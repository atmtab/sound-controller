import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from sound_controller.audio.devices import OutputDevice
from sound_controller.audio.sessions import RunningApp
from sound_controller.ui.patchbay import PatchBay


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def make_bay(qapp):
    bay = PatchBay()
    bay.resize(700, 400)
    apps = [RunningApp("a.exe", (1,), True), RunningApp("b.exe", (2,), False)]
    devices = [OutputDevice("d1", "Наушники (X)"), OutputDevice("d2", "Колонка")]
    bay.set_data(apps, devices, {"a.exe": None, "b.exe": "d1"})
    return bay, apps


def drag(bay, start, end):
    QTest.mousePress(bay, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(bay, end)
    QTest.mouseRelease(bay, Qt.MouseButton.LeftButton, pos=end)


def test_drop_on_device_assigns(qapp):
    bay, apps = make_bay(qapp)
    got = []
    bay.assigned.connect(lambda app, dev: got.append((app.name, dev)))
    box = bay._boxes()[1]
    drag(bay, bay._app_jack(0).toPoint(), box.rect.center().toPoint())
    assert got == [("a.exe", "d2")]


def test_drop_in_empty_space_unplugs(qapp):
    bay, apps = make_bay(qapp)
    got = []
    bay.assigned.connect(lambda app, dev: got.append((app.name, dev)))
    drag(bay, bay._app_jack(1).toPoint(), QPoint(350, 380))
    assert got == [("b.exe", None)]


def test_drop_on_same_device_is_noop(qapp):
    bay, apps = make_bay(qapp)
    got = []
    bay.assigned.connect(lambda app, dev: got.append(dev))
    box = bay._boxes()[0]
    drag(bay, bay._app_jack(1).toPoint(), box.rect.center().toPoint())
    assert got == []


def test_fader_drag_emits_volume(qapp):
    bay, _apps = make_bay(qapp)
    bay.set_volumes({"d1": 0.5, "d2": 0.5})
    got = []
    bay.volume_changed.connect(lambda dev, level: got.append((dev, level)))
    track = bay._fader_track(bay._boxes()[0])
    top = QPoint(int(track.x()), int(track.top()))
    mid = QPoint(int(track.x()), int(track.top() + track.height() / 2))
    QTest.mousePress(bay, Qt.MouseButton.LeftButton, pos=top)
    QTest.mouseMove(bay, mid)
    QTest.mouseRelease(bay, Qt.MouseButton.LeftButton, pos=mid)
    assert got[0] == ("d1", 1.0)
    assert got[-1][0] == "d1" and 0.45 <= got[-1][1] <= 0.55
    assert bay._fader_drag is None


def test_set_volumes_keeps_dragged_fader(qapp):
    bay, _apps = make_bay(qapp)
    bay._volumes = {"d1": 0.3}
    bay._fader_drag = "d1"
    bay.set_volumes({"d1": 0.1, "d2": 0.9})
    assert bay._volumes == {"d1": 0.3, "d2": 0.9}
