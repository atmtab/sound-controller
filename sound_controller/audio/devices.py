"""Список активных устройств вывода звука."""
from dataclasses import dataclass

import comtypes
from pycaw.constants import DEVICE_STATE, EDataFlow
from pycaw.pycaw import AudioUtilities

# Ключ свойства PKEY_Device_FriendlyName в словаре, который собирает pycaw.
_FRIENDLY_NAME_KEY = "{A45C254E-DF1C-4EFD-8020-67D146A850E0} 14"
VIRTUAL_CABLE_MARKER = "CABLE Input"


@dataclass(frozen=True)
class OutputDevice:
    id: str
    name: str

    @property
    def is_virtual_cable(self) -> bool:
        return VIRTUAL_CABLE_MARKER in self.name


def list_output_devices() -> list[OutputDevice]:
    devices = AudioUtilities.GetAllDevices(
        data_flow=EDataFlow.eRender.value,
        device_state=DEVICE_STATE.ACTIVE.value,
    )
    return [
        OutputDevice(id=d.id, name=d.FriendlyName or d.id)
        for d in devices
    ]


def find_virtual_cable(devices: list[OutputDevice] | None = None) -> OutputDevice | None:
    for device in devices if devices is not None else list_output_devices():
        if device.is_virtual_cable:
            return device
    return None


def _endpoint_volume(device_id: str):
    device = AudioUtilities.CreateDevice(AudioUtilities.GetDeviceEnumerator().GetDevice(device_id))
    return device.EndpointVolume


def get_volume(device_id: str) -> float | None:
    """Громкость устройства 0..1 или None, если устройство недоступно."""
    try:
        return float(_endpoint_volume(device_id).GetMasterVolumeLevelScalar())
    except (comtypes.COMError, OSError):
        return None


def set_volume(device_id: str, level: float) -> bool:
    try:
        _endpoint_volume(device_id).SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)
        return True
    except (comtypes.COMError, OSError):
        return False


if __name__ == "__main__":
    for device in list_output_devices():
        mark = "  [VB-Cable]" if device.is_virtual_cable else ""
        print(f"{device.name}\n    {device.id}{mark}  громкость={get_volume(device.id)}")
