from jarvis.gui import layout_mode_for_width


def test_layout_modes_cover_small_medium_and_wide_windows():
    assert layout_mode_for_width(680) == "compact"
    assert layout_mode_for_width(900) == "medium"
    assert layout_mode_for_width(1280) == "wide"


def test_layout_thresholds_are_stable():
    assert layout_mode_for_width(779) == "compact"
    assert layout_mode_for_width(780) == "medium"
    assert layout_mode_for_width(1119) == "medium"
    assert layout_mode_for_width(1120) == "wide"
