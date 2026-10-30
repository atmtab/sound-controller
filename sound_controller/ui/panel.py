"""Окно-саундбар: список приложений и выбор устройства вывода для каждого."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from sound_controller.audio import devices as devices_mod
from sound_controller.audio import routing, sessions
from sound_controller.audio.monitor import Monitor, MonitorError
from sound_controller.config import Config
from sound_controller.ui.patchbay import PatchBay
from sound_controller.ui.skin import (
    HEADER_HEIGHT,
    LAMP_RED,
    Chassis,
    Lcd,
    Led,
    RockerSwitch,
    Selector,
    engraved_label,
)

REFRESH_MS = 2000
HINT = (
    "Тяните штекер приложения к блоку устройства. "
    "Бросьте штекер в пустое место, чтобы вернуть устройство по умолчанию."
)




class Panel(Chassis):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setWindowTitle("Sound Controller")
        self.setMinimumSize(800, 540)
        self.resize(860, 620)
        self._config = config
        self._signature: tuple = ()
        self._monitor = Monitor()
        self._devices: list = []

        self._bay = PatchBay()
        self._bay.assigned.connect(self._on_assigned)

        self._status = Lcd(HINT, wrap=True, height=44)
        self._all_check = RockerSwitch()
        self._all_check.toggled.connect(self._force_refresh)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, HEADER_HEIGHT, 36, 34)
        layout.setSpacing(10)
        layout.addWidget(self._bay, 1)
        layout.addLayout(self._build_footer())
        layout.addWidget(self._status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(REFRESH_MS)
        self.refresh()
        if self._config.monitor_enabled:
            self._apply_monitor()

    def _build_footer(self) -> QVBoxLayout:
        self._monitor_check = RockerSwitch()
        self._monitor_led = Led(color=LAMP_RED)
        self._monitor_combo = Selector()
        self._monitor_check.setChecked(self._config.monitor_enabled)
        self._monitor_led.set_on(self._config.monitor_enabled)
        self._monitor_check.toggled.connect(self._apply_monitor)
        self._monitor_combo.activated.connect(self._apply_monitor)

        monitor = QHBoxLayout()
        monitor.setSpacing(12)
        monitor.addWidget(self._monitor_check)
        monitor.addWidget(self._monitor_led)
        monitor.addWidget(engraved_label("МОНИТОР В НАУШНИКАХ"))
        monitor.addWidget(self._monitor_combo, 1)

        everything = QHBoxLayout()
        everything.setSpacing(12)
        everything.addWidget(self._all_check)
        everything.addWidget(engraved_label("ВСЕ ПРОЦЕССЫ (ПРИЛОЖЕНИЯ В ТРЕЕ)"))
        everything.addStretch(1)

        footer = QVBoxLayout()
        footer.setSpacing(8)
        footer.addLayout(monitor)
        footer.addLayout(everything)
        return footer

    def _fill_monitor_devices(self, devices) -> None:
        candidates = [d for d in devices if not d.is_virtual_cable]
        self._monitor_combo.blockSignals(True)
        self._monitor_combo.clear()
        for device in candidates:
            self._monitor_combo.addItem(device.name, device.name)
        index = self._monitor_combo.findData(self._config.monitor_device)
        self._monitor_combo.setCurrentIndex(max(index, 0))
        self._monitor_combo.blockSignals(False)

    def _apply_monitor(self, *_args) -> None:
        self._config.monitor_enabled = self._monitor_check.isChecked()
        self._config.monitor_device = self._monitor_combo.currentData()
        self._config.save()
        self._monitor_led.set_on(self._config.monitor_enabled)
        if not self._config.monitor_enabled or not self._config.monitor_device:
            self._monitor.stop()
            return
        try:
            self._monitor.start(self._config.monitor_device)
        except MonitorError as exc:
            self._monitor_check.blockSignals(True)
            self._monitor_check.setChecked(False)
            self._monitor_check.blockSignals(False)
            self._monitor_led.set_on(False)
            self._config.monitor_enabled = False
            self._config.save()
            self.show_message(str(exc))

    def _force_refresh(self, *_args) -> None:
        self._signature = ()
        self.refresh()

    def show_message(self, text: str) -> None:
        self._status.setText(text)

    def refresh(self) -> None:
        devices = devices_mod.list_output_devices()
        apps = sessions.list_running_apps(
            include_all=self._all_check.isChecked(),
            always=set(self._config.app_devices),
        )
        signature = (
            tuple((a.name, a.pids, a.playing) for a in apps),
            tuple(d.id for d in devices),
        )
        if signature == self._signature:
            return
        self._signature = signature
        self._devices = devices
        self._fill_monitor_devices(devices)

        if devices_mod.find_virtual_cable(devices) is None:
            self.show_message(
                "VB-Cable не найден. Установите его, чтобы выводить звук в видеозвонки."
            )
        for app in apps:
            self._reapply_saved(app, devices)
        self._bay.set_data(
            apps, devices, {a.name: routing.get_apps_device(a.pids) for a in apps}
        )
        if not apps:
            self.show_message("Нет запущенных приложений")

    def _on_assigned(self, app: sessions.RunningApp, device_id) -> None:
        try:
            routing.set_apps_device(app.pids, device_id)
        except routing.RoutingError as exc:
            self.show_message(str(exc))
            return
        self._config.remember(app.name, device_id)
        self._bay.set_assignment(app.name, device_id)
        self.show_message(
            "Если звук не переключился сразу, перезапустите воспроизведение в приложении."
        )

    def _reapply_saved(self, app: sessions.RunningApp, devices) -> None:
        saved = self._config.device_for(app.name)
        if not saved or saved not in {d.id for d in devices}:
            return
        try:
            stale = []
            for pid in app.pids:
                try:
                    if routing.get_app_device(pid) != saved:
                        stale.append(pid)
                except routing.RoutingError:
                    continue  # Windows не отдаёт настройки этого процесса, пропускаем
            if stale:
                routing.set_apps_device(stale, saved)
        except routing.RoutingError as exc:
            self.show_message(str(exc))
