"""Мониторинг: ретрансляция звука с CABLE Output в выбранные наушники."""
import sounddevice as sd

CABLE_OUTPUT_MARKER = "CABLE Output"


class MonitorError(RuntimeError):
    pass


def _wasapi_index() -> int:
    for index, api in enumerate(sd.query_hostapis()):
        if api["name"] == "Windows WASAPI":
            return index
    raise MonitorError("WASAPI недоступен")


def match_device(devices: list[dict], hostapi: int, name: str, *, output: bool) -> int | None:
    """Индекс устройства sounddevice по имени: точное совпадение, затем по началу."""
    key = "max_output_channels" if output else "max_input_channels"
    candidates = [
        (i, d["name"]) for i, d in enumerate(devices)
        if d["hostapi"] == hostapi and d[key] > 0
    ]
    for i, candidate in candidates:
        if candidate == name:
            return i
    for i, candidate in candidates:
        if candidate.startswith(name) or name.startswith(candidate):
            return i
    return None


class Monitor:
    def __init__(self) -> None:
        self._stream: sd.Stream | None = None

    @property
    def running(self) -> bool:
        return self._stream is not None

    def start(self, output_name: str) -> None:
        self.stop()
        devices = list(sd.query_devices())
        hostapi = _wasapi_index()
        source = next(
            (i for i, d in enumerate(devices)
             if d["hostapi"] == hostapi and d["max_input_channels"] > 0
             and CABLE_OUTPUT_MARKER in d["name"]),
            None,
        )
        if source is None:
            raise MonitorError("CABLE Output не найден: установите VB-Cable.")
        target = match_device(devices, hostapi, output_name, output=True)
        if target is None:
            raise MonitorError(f"Устройство мониторинга не найдено: {output_name}")

        rate = int(devices[source]["default_samplerate"])
        channels = min(2, devices[source]["max_input_channels"], devices[target]["max_output_channels"])

        def relay(indata, outdata, frames, time, status):
            outdata[:] = indata

        try:
            self._stream = sd.Stream(
                device=(source, target),
                samplerate=rate,
                channels=channels,
                dtype="float32",
                latency="low",
                callback=relay,
                extra_settings=sd.WasapiSettings(auto_convert=True),
            )
            self._stream.start()
        except sd.PortAudioError as exc:
            self._stream = None
            raise MonitorError(f"Не удалось запустить мониторинг: {exc}") from exc

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
