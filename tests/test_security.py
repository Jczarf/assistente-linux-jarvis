from jarvis.security import validate_command


def test_shell_disabled_by_default_policy():
    decision = validate_command("ls -la", enabled=False, max_length=500)
    assert decision.allowed is False


def test_safe_command_allowed_when_enabled():
    decision = validate_command("ls -la", enabled=True, max_length=500)
    assert decision.allowed is True


def test_destructive_rm_is_blocked():
    decision = validate_command("rm -rf /", enabled=True, max_length=500)
    assert decision.allowed is False


def test_device_write_is_blocked():
    decision = validate_command("dd if=/dev/zero of=/dev/sda", enabled=True, max_length=500)
    assert decision.allowed is False


def test_multiline_is_blocked():
    decision = validate_command("echo ok\nrm -rf /", enabled=True, max_length=500)
    assert decision.allowed is False
