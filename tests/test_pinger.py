import os
import logging
import tempfile
import pytest
from unittest.mock import patch


def test_load_config_success():
    env = {
        "TELEGRAM_BOT_TOKEN": "abc123",
        "TELEGRAM_CHAT_ID": "999",
    }
    with patch.dict(os.environ, env, clear=True):
        with patch("pinger.load_dotenv"):
            from pinger import load_config
            config = load_config()
    assert config["token"] == "abc123"
    assert config["chat_id"] == "999"


def test_load_config_missing_token():
    with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "999"}, clear=True):
        with patch("pinger.load_dotenv"):
            from pinger import load_config
            with pytest.raises(SystemExit):
                load_config()


def test_load_config_missing_chat_id():
    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "abc123"}, clear=True):
        with patch("pinger.load_dotenv"):
            from pinger import load_config
            with pytest.raises(SystemExit):
                load_config()


def test_setup_logging_returns_logger():
    fd, tmp = tempfile.mkstemp(suffix=".log")
    os.close(fd)
    from pinger import setup_logging
    logger = setup_logging(log_path=tmp)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "pinger"


def test_check_connectivity_success():
    with patch("pinger.socket.create_connection", return_value=None):
        from pinger import check_connectivity
        assert check_connectivity(retries=3, wait=0) is True


def test_check_connectivity_fails_then_succeeds():
    call_count = {"n": 0}
    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise OSError("timeout")
        return None
    with patch("pinger.socket.create_connection", side_effect=side_effect):
        from pinger import check_connectivity
        assert check_connectivity(retries=3, wait=0) is True


def test_check_connectivity_all_fail():
    with patch("pinger.socket.create_connection", side_effect=OSError("timeout")):
        from pinger import check_connectivity
        assert check_connectivity(retries=3, wait=0) is False


def test_get_emoji_healthy():
    from pinger import get_emoji
    assert get_emoji(50, warn=70, crit=90) == "✅"


def test_get_emoji_warning():
    from pinger import get_emoji
    assert get_emoji(75, warn=70, crit=90) == "⚠️"


def test_get_emoji_critical():
    from pinger import get_emoji
    assert get_emoji(95, warn=70, crit=90) == "🔴"


def test_get_emoji_boundary_warn():
    from pinger import get_emoji
    assert get_emoji(70, warn=70, crit=90) == "✅"
    assert get_emoji(71, warn=70, crit=90) == "⚠️"


def test_get_emoji_boundary_crit():
    from pinger import get_emoji
    assert get_emoji(90, warn=70, crit=90) == "⚠️"
    assert get_emoji(91, warn=70, crit=90) == "🔴"
