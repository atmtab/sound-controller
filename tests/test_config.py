from sound_controller.config import Config


def test_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    config = Config.load(path)
    config.remember("Spotify.exe", "dev-1")
    config.monitor_enabled = True
    config.save()

    loaded = Config.load(path)
    assert loaded.device_for("spotify.EXE") == "dev-1"
    assert loaded.monitor_enabled is True


def test_forget_and_missing_file(tmp_path):
    config = Config.load(tmp_path / "missing.json")
    assert config.device_for("a.exe") is None
    config.remember("a.exe", "dev-1")
    config.remember("a.exe", None)
    assert config.device_for("a.exe") is None


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    assert Config.load(path).app_devices == {}
