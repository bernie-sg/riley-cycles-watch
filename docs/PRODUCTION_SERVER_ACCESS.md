# Production Server Access Guide

**Last Updated:** 30-Dec-2025

---

## Server Details

**Hostname:** cycles.cosmicsignals.net
**IP Address:** 82.25.105.47
**Provider:** Hostinger VPS
**OS:** Ubuntu/Debian Linux

---

## SSH Access

### Credentials

**Username:** `raysudo`
**Password:** `Element92**&`
**SSH Port:** 22 (default)

### Connection Methods

#### Method 1: Password Authentication
```bash
ssh raysudo@82.25.105.47
# Enter password when prompted: Element92**&
```

#### Method 2: Using SSH Config (Recommended)

Add to `~/.ssh/config`:
```
Host hostinger-vps
  HostName 82.25.105.47
  User raysudo
  IdentityFile ~/.ssh/id_ed25519
  StrictHostKeyChecking no
```

Then connect with:
```bash
ssh hostinger-vps
```

#### Method 3: Direct SSH with Key
```bash
ssh -i ~/.ssh/id_ed25519 raysudo@82.25.105.47
```

### SSH Key Setup

**Public Key (already added to server):**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF/Zrf/ZaqxKOK9EgbhwIvrLb0TNpZXjR6GN437LAnv0 sia.bernard@gmail.com
```

**Key Location (local):** `~/.ssh/id_ed25519`

**Server authorized_keys:** `/home/raysudo/.ssh/authorized_keys`

---

## Riley Project Locations

### Main Directory
```
/home/raysudo/riley-cycles/
```

### Key Paths
```
/home/raysudo/riley-cycles/
├── app/
│   ├── Home.py                      ← Main Streamlit app
│   └── pages/
│       ├── 2_System_Status.py
│       └── 3_Cycles_Detector.py     ← Cycles Detector page
│
├── cycles-detector/
│   ├── app.py                        ← Flask server
│   ├── data_manager.py
│   └── templates/
│
├── data/
│   └── price_history/               ← CSV price data
│
├── db/
│   └── riley.sqlite                 ← Main database
│
├── logs/
│   ├── riley.log                    ← Streamlit logs
│   └── flask.log                    ← Flask logs
│
└── venv/                             ← Python virtual environment
```

---

## Services

### Riley (Streamlit)

**Port:** 8081
**Service:** `riley.service`
**Access:** https://cycles.cosmicsignals.net:8081

**Commands:**
```bash
# Check status
sudo systemctl status riley.service

# Start service
sudo systemctl start riley.service

# Stop service
sudo systemctl stop riley.service

# Restart service
sudo systemctl restart riley.service

# View logs
sudo journalctl -u riley.service -f
# or
tail -f /home/raysudo/riley-cycles/logs/riley.log
```

### Cycles Detector (Flask)

**Port:** 8082
**Service:** `riley-flask.service`
**Access:** http://localhost:8082 (embedded in Riley)

**Commands:**
```bash
# Check status
sudo systemctl status riley-flask.service

# Start service
sudo systemctl start riley-flask.service

# Stop service
sudo systemctl stop riley-flask.service

# Restart service
sudo systemctl restart riley-flask.service

# View logs
sudo journalctl -u riley-flask.service -f
# or
tail -f /home/raysudo/riley-cycles/logs/flask.log
```

---

## Auto-Start Configuration

Both services are configured to:
- ✅ Start automatically on server boot
- ✅ Restart automatically if they crash
- ✅ Wait 10 seconds before restarting
- ✅ Log to respective log files

**Service files location:**
- `/etc/systemd/system/riley.service`
- `/etc/systemd/system/riley-flask.service`

---

## Common Operations

### Check Service Status
```bash
# Quick check if services are running
lsof -i :8081  # Riley
lsof -i :8082  # Flask

# or
ps aux | grep streamlit
ps aux | grep "python3 app.py"
```

### Restart Both Services
```bash
sudo systemctl restart riley.service riley-flask.service
```

### View Recent Logs
```bash
# Riley logs (last 50 lines)
tail -50 /home/raysudo/riley-cycles/logs/riley.log

# Flask logs (last 50 lines)
tail -50 /home/raysudo/riley-cycles/logs/flask.log

# Follow logs in real-time
tail -f /home/raysudo/riley-cycles/logs/riley.log
```

### Update Code
```bash
cd /home/raysudo/riley-cycles

# Pull latest changes (if using git)
git pull

# Restart services to apply changes
sudo systemctl restart riley.service riley-flask.service
```

### Check Port Usage
```bash
# See what's listening on all ports
sudo lsof -i -P -n | grep LISTEN

# Check specific ports
netstat -tlnp | grep -E '8081|8082'
```

---

## Firewall Configuration

### Check Firewall Status
```bash
sudo ufw status
```

### Allow SSH Access (if blocked)
```bash
# Add specific IP
sudo ufw allow from YOUR_IP to any port 22

# Or allow from anywhere (less secure)
sudo ufw allow 22
```

### Required Open Ports
- **22** - SSH access
- **80** - HTTP (nginx)
- **443** - HTTPS (nginx)
- **8081** - Riley/Streamlit
- **8082** - Flask (localhost only, accessed via Riley)

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
sudo journalctl -u riley.service -n 50
sudo journalctl -u riley-flask.service -n 50
```

**Check permissions:**
```bash
ls -la /home/raysudo/riley-cycles/
ls -la /home/raysudo/riley-cycles/logs/
```

**Fix log permissions if needed:**
```bash
touch /home/raysudo/riley-cycles/logs/riley.log
touch /home/raysudo/riley-cycles/logs/flask.log
chmod 644 /home/raysudo/riley-cycles/logs/*.log
chown raysudo:raysudo /home/raysudo/riley-cycles/logs/*.log
```

### Port Already in Use

**Find what's using the port:**
```bash
sudo lsof -i :8081
sudo lsof -i :8082
```

**Kill the process:**
```bash
sudo kill -9 <PID>
```

### Can't Connect via SSH

**Check if SSH service is running:**
```bash
sudo systemctl status ssh
```

**Restart SSH:**
```bash
sudo systemctl restart ssh
```

**Check firewall:**
```bash
sudo ufw status
```

---

## Virtual Environment

**Location:** `/home/raysudo/riley-cycles/venv/`

**Activate:**
```bash
cd /home/raysudo/riley-cycles
source venv/bin/activate
```

**Install/Update packages:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Deactivate:**
```bash
deactivate
```

---

## Database

**Location:** `/home/raysudo/riley-cycles/db/riley.sqlite`

**Backup database:**
```bash
cp /home/raysudo/riley-cycles/db/riley.sqlite \
   /home/raysudo/riley-cycles/db/riley.sqlite.backup.$(date +%Y%m%d)
```

**Access database:**
```bash
cd /home/raysudo/riley-cycles
sqlite3 db/riley.sqlite
```

---

## Emergency Contacts

**Hostinger Support:** https://www.hostinger.com/support
**VPS Control Panel:** https://hpanel.hostinger.com/

---

## Quick Reference Commands

```bash
# SSH into server
ssh raysudo@82.25.105.47

# Check service status
sudo systemctl status riley.service riley-flask.service

# Restart services
sudo systemctl restart riley.service riley-flask.service

# View logs
tail -f /home/raysudo/riley-cycles/logs/riley.log

# Check if ports are open
lsof -i :8081 && lsof -i :8082

# Update and restart
cd /home/raysudo/riley-cycles
git pull
sudo systemctl restart riley.service riley-flask.service
```

---

**End of Server Access Guide**
