# Linux System Status Pinger

A Python script that collects Linux system metrics and sends a formatted report to a Telegram bot every 12 hours via a systemd timer.

## Features

Monitors and reports on 10 system metrics:

| Metric | Details |
|---|---|
| CPU | Usage % and 1/5/15 min load averages |
| RAM | Used / total / percentage |
| Disk | Usage per mount point |
| Uptime | Time since last boot |
| Network | Bytes sent/received per interface |
| Processes | Count and top CPU consumers |
| Temperature | CPU/GPU temps (skipped if sensors unavailable) |
| Systemd Services | Any failed services |
| Last Login | User, time, and source IP |
| Connectivity | Online status confirmed before sending |

Each metric is colour-coded with ✅ / ⚠️ / 🔴 based on thresholds:

| Metric | ⚠️ Warning | 🔴 Critical |
|---|---|---|
| CPU | > 70% | > 90% |
| RAM | > 75% | > 90% |
| Disk | > 75% | > 90% |
| Load avg (1m) | > CPU core count | > 2× core count |
| Temperature | > 70°C | > 85°C |
| Failed services | — | ≥ 1 |

### Example Telegram Message

```
🖥️ *System Status Report*
🕐 2026-06-02 08:00:01 | ⏱️ Uptime: 14 days, 3:22:10

*📊 CPU*
Usage: ⚠️ 73% | Load avg: 1.2 / 0.9 / 0.8

*🧠 RAM*
Used: ✅ 3.1 GB / 8.0 GB (39%)

*💾 Disk*
/ → ✅ 42 GB / 120 GB (35%)

*🌐 Network*
eth0: ↑ 1.2 GB sent | ↓ 4.5 GB recv

*⚙️ Processes*
Running: 183 | Top CPU: nginx (12%), python (8%)

*🌡️ Temperature*
CPU: ✅ 48°C

*🔧 Systemd Services*
Failed: ✅ None

*👤 Last Login*
root — 2026-06-02 07:45 from 192.168.1.10

*🔌 Connectivity check: ✅ Online*
```

## Requirements

- Python 3.9+
- Linux with systemd
- A Telegram bot token and chat ID

**Python dependencies:**
```
psutil>=5.9
requests>=2.28
python-dotenv>=1.0
```

## Configuration

Create a `.env` file (use `.env.example` as a template):

```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

The `.env` file is never committed to git.

## Reliability

- **Connectivity check** — tests socket connection to 8.8.8.8:53 before sending; retries 3 times with 30s backoff
- **Send retry** — retries Telegram delivery up to 3 times with 10s backoff
- **Logging** — every run logged to `/var/log/pinger.log` with timestamp and outcome

## Installation

### 1. Copy files to server

```bash
sudo mkdir -p /opt/pinger
sudo cp pinger.py requirements.txt .env.example /opt/pinger/
```

### 2. Install dependencies

```bash
cd /opt/pinger
sudo pip3 install -r requirements.txt
```

### 3. Create `.env`

```bash
sudo cp /opt/pinger/.env.example /opt/pinger/.env
sudo nano /opt/pinger/.env
```

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

### 4. Set permissions

```bash
sudo chmod 600 /opt/pinger/.env
sudo touch /var/log/pinger.log
sudo chmod 644 /var/log/pinger.log
```

### 5. Install systemd units

```bash
sudo cp pinger.service pinger.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pinger.timer
```

### 6. Verify timer is active

```bash
sudo systemctl list-timers pinger.timer
```

### 7. Run manually to test

```bash
sudo systemctl start pinger.service
sudo journalctl -u pinger.service -n 20
cat /var/log/pinger.log
```

## Project Structure

```
├── pinger.py          # Main script
├── pinger.service     # Systemd service unit
├── pinger.timer       # Systemd timer unit (every 12h)
├── requirements.txt   # Python dependencies
├── .env.example       # Config template
└── tests/
    └── test_pinger.py # Unit tests (19 tests)
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
