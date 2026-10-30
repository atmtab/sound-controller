"""Сохранение выбора «приложение -> устройство» и настроек мониторинга."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def default_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "SoundController" / "config.json"


@dataclass
class Config:
    path: Path = field(default_factory=default_path)
    # имя exe (нижний регистр) -> id устройства
    app_devices: dict[str, str] = field(default_factory=dict)
    monitor_enabled: bool = False
    monitor_device: str | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        config = cls(path=path or default_path())
        try:
            data = json.loads(config.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return config
        config.app_devices = {
            str(k).lower(): str(v) for k, v in data.get("app_devices", {}).items()
        }
        config.monitor_enabled = bool(data.get("monitor_enabled", False))
        config.monitor_device = data.get("monitor_device")
        return config

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "app_devices": self.app_devices,
            "monitor_enabled": self.monitor_enabled,
            "monitor_device": self.monitor_device,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def remember(self, exe_name: str, device_id: str | None) -> None:
        key = exe_name.lower()
        if device_id:
            self.app_devices[key] = device_id
        else:
            self.app_devices.pop(key, None)
        self.save()

    def device_for(self, exe_name: str) -> str | None:
        return self.app_devices.get(exe_name.lower())
