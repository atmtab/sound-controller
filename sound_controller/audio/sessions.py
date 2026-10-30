"""Запущенные приложения и их аудиосессии."""
import ctypes
import getpass
import os
from ctypes import wintypes
from dataclasses import dataclass

import psutil
from pycaw.pycaw import AudioUtilities


@dataclass(frozen=True)
class AppSession:
    pid: int
    name: str
    exe: str | None
    playing: bool


def _process_info(pid: int) -> tuple[str, str | None]:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        try:
            exe = proc.exe()
        except (psutil.AccessDenied, psutil.ZombieProcess):
            exe = None
        return name, exe
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return f"pid {pid}", None


def list_app_sessions() -> list[AppSession]:
    """Сессии, склеенные по pid. Системные звуки (pid 0) пропускаем."""
    by_pid: dict[int, AppSession] = {}
    for session in AudioUtilities.GetAllSessions():
        pid = session.ProcessId
        if not pid:
            continue
        playing = session.State == 1  # AudioSessionStateActive
        known = by_pid.get(pid)
        if known is not None:
            if playing and not known.playing:
                by_pid[pid] = AppSession(pid, known.name, known.exe, True)
            continue
        name, exe = _process_info(pid)
        by_pid[pid] = AppSession(pid, name, exe, playing)
    return sorted(by_pid.values(), key=lambda s: (not s.playing, s.name.lower()))


@dataclass(frozen=True)
class RunningApp:
    name: str
    pids: tuple[int, ...]
    playing: bool


_user32 = ctypes.windll.user32
_dwmapi = ctypes.windll.dwmapi
_DWMWA_CLOAKED = 14
_WINDOWS_DIR = os.environ.get("SystemRoot", r"C:\Windows").lower()


def _visible_window_pids() -> set[int]:
    """pid процессов с видимым окном (скрытые окна UWP не считаем)."""
    pids: set[int] = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _lparam):
        if not _user32.IsWindowVisible(hwnd) or not _user32.GetWindowTextLengthW(hwnd):
            return True
        cloaked = wintypes.DWORD()
        _dwmapi.DwmGetWindowAttribute(hwnd, _DWMWA_CLOAKED, ctypes.byref(cloaked), 4)
        if cloaked.value:
            return True
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pids.add(pid.value)
        return True

    _user32.EnumWindows(visit, 0)
    return pids


def _user_process_pids() -> dict[int, str]:
    """Все процессы текущего пользователя вне папки Windows (для приложений в трее)."""
    me = getpass.getuser().lower()
    found: dict[int, str] = {}
    for proc in psutil.process_iter(["pid", "name", "exe", "username"]):
        info = proc.info
        exe = (info.get("exe") or "").lower()
        user = (info.get("username") or "").split("\\")[-1].lower()
        if exe and not exe.startswith(_WINDOWS_DIR) and user == me:
            found[info["pid"]] = info["name"]
    return found


def list_running_apps(include_all: bool = False, always: set[str] = frozenset()) -> list[RunningApp]:
    """Приложения, сгруппированные по имени exe.

    В список попадают процессы с окном, процессы с аудиосессией и процессы,
    имена которых в `always` (например, сохранённые в настройках, даже если
    окно свёрнуто в трей). С include_all показываются все процессы пользователя.
    """
    always = {n.lower() for n in always}
    playing_pids = {s.pid for s in list_app_sessions() if s.playing}
    session_pids = {s.pid for s in list_app_sessions()}
    window_pids = _visible_window_pids()

    wanted_pids = window_pids | session_pids
    user_procs = _user_process_pids()
    by_name: dict[str, set[int]] = {}
    for pid, name in user_procs.items():
        if include_all or pid in wanted_pids or name.lower() in always:
            by_name.setdefault(name, set()).add(pid)

    # Процессы вне выборки (например, служебные с сессией) добавляем отдельно.
    known = {pid for pids in by_name.values() for pid in pids}
    for pid in session_pids - known:
        name, _exe = _process_info(pid)
        by_name.setdefault(name, set()).add(pid)

    # Если у приложения есть окно или сессия, берём все процессы с этим именем:
    # звук у Chromium-приложений идёт из дочернего процесса.
    result = []
    for name, pids in by_name.items():
        siblings = {p for p, n in user_procs.items() if n == name}
        all_pids = tuple(sorted(pids | siblings))
        result.append(RunningApp(name, all_pids, bool(playing_pids & set(all_pids))))
    return sorted(result, key=lambda a: (not a.playing, a.name.lower()))


if __name__ == "__main__":
    for app in list_running_apps():
        state = "играет" if app.playing else "тихо"
        print(f"{app.name:<28} {state:<7} pids={list(app.pids)}")
