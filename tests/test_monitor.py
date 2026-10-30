from sound_controller.audio.monitor import match_device

DEVICES = [
    {"name": "Speakers", "hostapi": 0, "max_output_channels": 2, "max_input_channels": 0},
    {"name": "Наушники (Logitech H570e Stereo)", "hostapi": 1, "max_output_channels": 2, "max_input_channels": 0},
    {"name": "Наушники (Logitech H570e Stereo) extra", "hostapi": 1, "max_output_channels": 2, "max_input_channels": 0},
    {"name": "Mic", "hostapi": 1, "max_output_channels": 0, "max_input_channels": 1},
]


def test_exact_match_wins_over_prefix():
    assert match_device(DEVICES, 1, "Наушники (Logitech H570e Stereo)", output=True) == 1


def test_ignores_other_hostapi_and_direction():
    assert match_device(DEVICES, 1, "Speakers", output=True) is None
    assert match_device(DEVICES, 1, "Mic", output=True) is None


def test_prefix_fallback_for_truncated_name():
    devices = [{"name": "Speakers (Realtek High Definition Audio)", "hostapi": 1,
                "max_output_channels": 2, "max_input_channels": 0}]
    assert match_device(devices, 1, "Speakers (Realtek High", output=True) == 0
