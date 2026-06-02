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
    tmp = tempfile.mktemp(suffix=".log")
    from pinger import setup_logging
    logger = setup_logging(log_path=tmp)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "pinger"
