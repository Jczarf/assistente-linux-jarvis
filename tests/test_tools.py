from jarvis.tools import execute_tool


def test_system_info_returns_structured_result():
    result = execute_tool("system_info")
    assert result["ok"] is True
    assert result["tool"] == "system_info"
    assert "RAM:" in result["message"]
    assert "ram_percent" in result["data"]


def test_unknown_tool_is_rejected_without_exception():
    result = execute_tool("nao_existe")
    assert result["ok"] is False
    assert result["error"] == "unknown_tool"
    assert "Ferramenta desconhecida" in result["message"]


def test_shell_disabled_returns_real_failure():
    result = execute_tool("run_command", {"command": "echo ok"})
    assert result["ok"] is False
    assert result["error"] == "blocked"
