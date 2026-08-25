from jarvis.tools import execute_tool


def test_system_info_returns_text():
    result = execute_tool("system_info")
    assert isinstance(result, str)
    assert "RAM:" in result


def test_unknown_tool_is_rejected():
    result = execute_tool("nao_existe")
    assert "Ferramenta desconhecida" in result
