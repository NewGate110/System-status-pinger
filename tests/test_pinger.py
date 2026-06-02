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


def test_collect_metrics_structure():
    from unittest.mock import MagicMock, patch

    mock_cpu = 45.0
    mock_ram = MagicMock(used=3 * 1024**3, total=8 * 1024**3, percent=37.5)
    mock_partition = MagicMock(mountpoint="/", fstype="ext4", opts="rw")
    mock_disk_usage = MagicMock(used=40 * 1024**3, total=120 * 1024**3, percent=33.0)
    mock_net = {"eth0": MagicMock(bytes_sent=1024**3, bytes_recv=4 * 1024**3)}
    mock_proc = MagicMock()
    mock_proc.info = {"name": "nginx", "cpu_percent": 12.0, "memory_percent": 2.0}
    mock_temps = {"coretemp": [MagicMock(current=48.0, label="Core 0")]}
    mock_boot_time = 1000.0

    with patch("pinger.psutil.cpu_percent", return_value=mock_cpu), \
         patch("pinger.psutil.virtual_memory", return_value=mock_ram), \
         patch("pinger.psutil.disk_partitions", return_value=[mock_partition]), \
         patch("pinger.psutil.disk_usage", return_value=mock_disk_usage), \
         patch("pinger.psutil.net_io_counters", return_value=mock_net), \
         patch("pinger.psutil.pids", return_value=list(range(150))), \
         patch("pinger.psutil.process_iter", return_value=[mock_proc]), \
         patch("pinger.psutil.sensors_temperatures", return_value=mock_temps, create=True), \
         patch("pinger.psutil.boot_time", return_value=mock_boot_time), \
         patch("pinger.psutil.getloadavg", return_value=(1.2, 0.9, 0.8), create=True), \
         patch("pinger.psutil.cpu_count", return_value=4), \
         patch("pinger.subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(
            stdout="root\n2026-06-02 07:45\npts/0\n192.168.1.10\n",
            returncode=0
        )

        from pinger import collect_metrics
        metrics = collect_metrics()

    assert "cpu_percent" in metrics
    assert "ram" in metrics
    assert "disks" in metrics
    assert "uptime" in metrics
    assert "load_avg" in metrics
    assert "network" in metrics
    assert "process_count" in metrics
    assert "top_processes" in metrics
    assert "temperatures" in metrics
    assert "failed_services" in metrics
    assert "last_login" in metrics
