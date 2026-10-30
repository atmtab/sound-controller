"""Выбор устройства вывода для конкретного процесса.

Публичного API для этого в Windows нет. Используется тот же недокументированный
интерфейс IAudioPolicyConfigFactory, что и в «Параметры -> Звук -> Микшер
громкости». Номера методов и IID взяты из реализации EarTrumpet и могут
измениться в обновлении Windows, поэтому всё изолировано в этом модуле.
"""
import ctypes
from ctypes import HRESULT, POINTER, WINFUNCTYPE, byref, c_uint32, c_void_p, wintypes
from uuid import UUID

# Windows 11 / сборка 10.0.21390 и новее.
_IID_FACTORY = "{2a59116d-6c4f-45e0-a74f-707e3fef9258}"
# Windows 10 и ранние сборки Windows 11.
_IID_FACTORY_DOWNLEVEL = "{ab3d4648-e242-459f-b02f-541c70306324}"
_CLASS_NAME = "Windows.Media.Internal.AudioPolicyConfig"

# 6 методов IInspectable + 19 нереализованных методов фабрики.
_SET_INDEX = 25
_GET_INDEX = 26

E_RENDER = 0
ROLE_CONSOLE = 0
ROLE_MULTIMEDIA = 1
ROLE_COMMUNICATIONS = 2

_RENDER_INTERFACE = "{e6327cad-dcec-4949-ae8a-991e976a79d2}"
_DEVICE_PREFIX = "\\\\?\\SWD#MMDEVAPI#"

_combase = ctypes.windll.combase
_HSTRING = c_void_p


class RoutingError(RuntimeError):
    pass


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_string(cls, text: str) -> "_GUID":
        guid = cls()
        raw = UUID(text).bytes_le
        ctypes.memmove(byref(guid), raw, ctypes.sizeof(guid))
        return guid


def _hstring(text: str) -> _HSTRING:
    handle = _HSTRING()
    hr = _combase.WindowsCreateString(text, len(text), byref(handle))
    if hr:
        raise RoutingError(f"WindowsCreateString: 0x{hr & 0xFFFFFFFF:08X}")
    return handle


def _read_hstring(handle: _HSTRING) -> str:
    if not handle.value:
        return ""
    length = c_uint32()
    _combase.WindowsGetStringRawBuffer.restype = ctypes.c_wchar_p
    text = _combase.WindowsGetStringRawBuffer(handle, byref(length))
    return text[: length.value] if text else ""


def to_persisted_id(device_id: str) -> str:
    """'{0.0.0.00000000}.{guid}' -> полный путь устройства для политики."""
    return f"{_DEVICE_PREFIX}{device_id}#{_RENDER_INTERFACE}"


def from_persisted_id(persisted: str) -> str:
    if persisted.startswith(_DEVICE_PREFIX):
        persisted = persisted[len(_DEVICE_PREFIX):]
    return persisted.rsplit("#", 1)[0] if "#" in persisted else persisted


class _PolicyConfig:
    def __init__(self) -> None:
        self._factory = None
        for iid in (_IID_FACTORY, _IID_FACTORY_DOWNLEVEL):
            pointer = c_void_p()
            class_name = _hstring(_CLASS_NAME)
            try:
                hr = _combase.RoGetActivationFactory(
                    class_name, byref(_GUID.from_string(iid)), byref(pointer)
                )
            finally:
                _combase.WindowsDeleteString(class_name)
            if hr == 0 and pointer.value:
                self._factory = pointer
                self._downlevel = iid == _IID_FACTORY_DOWNLEVEL
                break
        if self._factory is None:
            raise RoutingError(
                "Не удалось получить AudioPolicyConfig: эта версия Windows не поддерживается."
            )
        self._vtable = ctypes.cast(
            ctypes.cast(self._factory, POINTER(c_void_p))[0], POINTER(c_void_p)
        )

    def _method(self, index: int, prototype):
        return prototype(self._vtable[index])

    def set_endpoint(self, pid: int, role: int, device_id: str | None) -> None:
        proto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD, ctypes.c_int, ctypes.c_int, _HSTRING)
        handle = _hstring(to_persisted_id(device_id)) if device_id else _HSTRING()
        try:
            self._method(_SET_INDEX, proto)(self._factory, pid, E_RENDER, role, handle)
        finally:
            if handle.value:
                _combase.WindowsDeleteString(handle)

    def get_endpoint(self, pid: int, role: int) -> str | None:
        proto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD, ctypes.c_int, ctypes.c_int, POINTER(_HSTRING))
        handle = _HSTRING()
        self._method(_GET_INDEX, proto)(self._factory, pid, E_RENDER, role, byref(handle))
        try:
            text = _read_hstring(handle)
        finally:
            if handle.value:
                _combase.WindowsDeleteString(handle)
        return from_persisted_id(text) if text else None


_policy: _PolicyConfig | None = None


def _config() -> _PolicyConfig:
    global _policy
    if _policy is None:
        _policy = _PolicyConfig()
    return _policy


def get_app_device(pid: int) -> str | None:
    """id устройства, назначенного приложению, или None, если используется системное."""
    try:
        return _config().get_endpoint(pid, ROLE_MULTIMEDIA)
    except OSError as exc:
        raise RoutingError(f"Не удалось прочитать устройство для pid {pid}: {exc}") from exc


def set_app_device(pid: int, device_id: str | None) -> None:
    """Назначает приложению устройство. None сбрасывает на системное по умолчанию."""
    try:
        config = _config()
        # Окно Windows выставляет обе роли, иначе часть приложений не переключается.
        for role in (ROLE_CONSOLE, ROLE_MULTIMEDIA):
            config.set_endpoint(pid, role, device_id)
    except OSError as exc:
        raise RoutingError(f"Не удалось назначить устройство для pid {pid}: {exc}") from exc


def get_apps_device(pids) -> str | None:
    """Устройство первого процесса, у которого его удалось прочитать."""
    for pid in pids:
        try:
            return get_app_device(pid)
        except RoutingError:
            continue
    return None


def set_apps_device(pids, device_id: str | None) -> None:
    """Назначает устройство всем процессам приложения. Ошибка, только если не вышло ни у одного."""
    errors = []
    done = 0
    for pid in pids:
        try:
            set_app_device(pid, device_id)
            done += 1
        except RoutingError as exc:
            errors.append(exc)
    if errors and not done:
        raise errors[0]


if __name__ == "__main__":
    import sys

    from sound_controller.audio.devices import list_output_devices
    from sound_controller.audio.sessions import list_running_apps

    names = {d.id: d.name for d in list_output_devices()}
    for app in list_running_apps():
        current = get_apps_device(app.pids)
        print(f"{app.name:<28} -> {names.get(current, current or 'по умолчанию')}")
    sys.exit(0)
