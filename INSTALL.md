# Installation

## 1. Copy files to server

```bash
sudo mkdir -p /opt/pinger
sudo cp pinger.py requirements.txt .env.example /opt/pinger/
```

## 2. Install dependencies

```bash
cd /opt/pinger
sudo pip3 install -r requirements.txt
```

## 3. Create `.env`

```bash
sudo cp /opt/pinger/.env.example /opt/pinger/.env
sudo nano /opt/pinger/.env
```

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## 4. Set permissions

```bash
sudo chmod 600 /opt/pinger/.env
sudo touch /var/log/pinger.log
sudo chmod 644 /var/log/pinger.log
```

## 5. Install systemd units

```bash
sudo cp pinger.service pinger.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pinger.timer
```

## 6. Verify timer is active

```bash
sudo systemctl list-timers pinger.timer
```

## 7. Run manually to test

```bash
sudo systemctl start pinger.service
sudo journalctl -u pinger.service -n 20
cat /var/log/pinger.log
```
