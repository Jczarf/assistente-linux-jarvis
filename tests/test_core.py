from jarvis.core import JarvisAssistant


def test_tool_signature_is_deterministic():
    first = JarvisAssistant._call_signature("open_app", {"app": "Firefox", "x": 1})
    second = JarvisAssistant._call_signature("open_app", {"x": 1, "app": "Firefox"})
    assert first == second
