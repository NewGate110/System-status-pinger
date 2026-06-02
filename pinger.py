import os
import sys
import logging
import socket
import time
import subprocess
from datetime import datetime, timezone

import psutil
import requests
from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)
    if not chat_id:
        print("ERROR: TELEGRAM_CHAT_ID is not set.", file=sys.stderr)
        sys.exit(1)
    return {"token": token, "chat_id": chat_id}


def setup_logging(log_path: str = "/var/log/pinger.log") -> logging.Logger:
    logger = logging.getLogger("pinger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


def check_connectivity(retries: int = 3, wait: int = 30) -> bool:
    for attempt in range(1, retries + 1):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            if attempt < retries:
                time.sleep(wait)
    return False


def get_emoji(value: float, warn: float, crit: float) -> str:
    if value > crit:
        return "🔴"
    if value > warn:
        return "⚠️"
    return "✅"


def collect_metrics() -> dict:
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()

    ram = psutil.virtual_memory()

    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "mount": part.mountpoint,
                "used": usage.used,
                "total": usage.total,
                "percent": usage.percent,
            })
        except PermissionError:
            continue

    boot_time = psutil.boot_time()
    uptime_delta = datetime.now(timezone.utc) - datetime.fromtimestamp(boot_time, timezone.utc)

    load_1, load_5, load_15 = psutil.getloadavg()

    net = psutil.net_io_counters(pernic=True)
    network = {
        iface: {"sent": counters.bytes_sent, "recv": counters.bytes_recv}
        for iface, counters in net.items()
        if not iface.startswith("lo")
    }

    process_count = len(psutil.pids())
    procs = []
    for proc in psutil.process_iter(attrs=["name", "cpu_percent", "memory_percent"]):
        procs.append(proc.info)
    top_procs = sorted(procs, key=lambda p: p.get("cpu_percent") or 0, reverse=True)[:3]

    temps_raw = psutil.sensors_temperatures()
    temperatures = []
    if temps_raw:
        for key, entries in temps_raw.items():
            for entry in entries:
                temperatures.append({"label": entry.label or key, "current": entry.current})
            break

    result = subprocess.run(
        ["systemctl", "list-units", "--state=failed", "--no-legend", "--plain"],
        capture_output=True, text=True
    )
    failed_lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
    failed_services = [l.split()[0] for l in failed_lines] if failed_lines else []

    last_result = subprocess.run(["last", "-n", "1", "-w"], capture_output=True, text=True)
    last_login = last_result.stdout.strip().splitlines()[0] if last_result.stdout.strip() else "N/A"

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "ram": {
            "used": ram.used,
            "total": ram.total,
            "percent": ram.percent,
        },
        "disks": disks,
        "uptime": str(uptime_delta).split(".")[0],
        "load_avg": (load_1, load_5, load_15),
        "network": network,
        "process_count": process_count,
        "top_processes": top_procs,
        "temperatures": temperatures,
        "failed_services": failed_services,
        "last_login": last_login,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _fmt_bytes(n: int) -> str:
    gb = n / 1024**3
    return f"{gb:.1f} GB"


def format_message(metrics: dict) -> str:
    cpu = metrics["cpu_percent"]
    cpu_emoji = get_emoji(cpu, warn=70, crit=90)
    load_1, load_5, load_15 = metrics["load_avg"]
    cores = metrics["cpu_count"]
    load_emoji = get_emoji(load_1, warn=cores, crit=cores * 2)

    ram = metrics["ram"]
    ram_emoji = get_emoji(ram["percent"], warn=75, crit=90)

    lines = [
        f"🖥️ *System Status Report*",
        f"🕐 {metrics['timestamp']} | ⏱️ Uptime: {metrics['uptime']}",
        "",
        f"*📊 CPU*",
        f"Usage: {cpu_emoji} {cpu:.1f}% | Load avg: {load_emoji} {load_1:.2f} / {load_5:.2f} / {load_15:.2f}",
        "",
        f"*🧠 RAM*",
        f"Used: {ram_emoji} {_fmt_bytes(ram['used'])} / {_fmt_bytes(ram['total'])} ({ram['percent']:.1f}%)",
        "",
        f"*💾 Disk*",
    ]
    for disk in metrics["disks"]:
        disk_emoji = get_emoji(disk["percent"], warn=75, crit=90)
        lines.append(
            f"{disk['mount']} → {disk_emoji} {_fmt_bytes(disk['used'])} / {_fmt_bytes(disk['total'])} ({disk['percent']:.1f}%)"
        )

    lines += ["", "*🌐 Network*"]
    if metrics["network"]:
        for iface, counts in metrics["network"].items():
            lines.append(f"{iface}: ↑ {_fmt_bytes(counts['sent'])} sent | ↓ {_fmt_bytes(counts['recv'])} recv")
    else:
        lines.append("No external interfaces detected")

    top = metrics["top_processes"]
    top_str = " | ".join(f"{p['name']} ({p.get('cpu_percent', 0):.1f}%)" for p in top) if top else "N/A"
    lines += [
        "",
        f"*⚙️ Processes*",
        f"Running: {metrics['process_count']} | Top CPU: {top_str}",
    ]

    if metrics["temperatures"]:
        lines += ["", "*🌡️ Temperature*"]
        for t in metrics["temperatures"]:
            temp_emoji = get_emoji(t["current"], warn=70, crit=85)
            lines.append(f"{t['label']}: {temp_emoji} {t['current']:.1f}°C")

    failed = metrics["failed_services"]
    if failed:
        svc_str = ", ".join(failed)
        lines += ["", f"*🔧 Systemd Services*", f"Failed: 🔴 {len(failed)} ({svc_str})"]
    else:
        lines += ["", f"*🔧 Systemd Services*", f"Failed: ✅ None"]

    lines += [
        "",
        f"*👤 Last Login*",
        metrics["last_login"],
        "",
        f"*🔌 Connectivity check: ✅ Online*",
    ]

    return "\n".join(lines)
