# Riley Cycles Watch - Production Deployment Guide

**Last Updated:** December 24, 2025
**Version:** 1.0
**Domain:** https://cycles.cosmicsignals.net

---

## Overview

Riley Cycles Watch is a Streamlit-based trading cycles analysis application deployed on Hostinger VPS. It provides real-time cycle window tracking, desk notes, and calendar visualization for multiple trading instruments.

---

## Server Information

### Hostinger VPS Details
- **IP Address:** 82.25.105.47
- **SSH User:** raysudo
- **SSH Key:** `~/.ssh/berryfit_key`
- **OS:** Linux (CloudPanel)
- **Python Version:** 3.12

### SSH Access
```bash
ssh -i ~/.ssh/berryfit_key raysudo@82.25.105.47
```

### Deployed Applications on This Server
1. **Riley Cycles Watch:** https://cycles.cosmicsignals.net (port 8081)
2. **Perfect Storm:** https://theperfectstorm.cosmicsignals.net (port 8501)
3. **CalorieBot/n8n:** https://n8n.rayasher.com (Docker containers)

---

## Riley Cycles Installation

### Directory Structure
```
/home/raysudo/riley-cycles/
├── app/                    # Streamlit application
│   ├── Home.py            # Main entrypoint
│   ├── app.py             # Compatibility wrapper
│   ├── db.py              # Database access layer
│   └── config.py          # Configuration
├── src/                   # Core library
│   └── riley/             # Riley protocol implementation
├── scripts/               # Utility scripts
│   └── cycles_run_scan.py # Daily scan script
├── db/                    # Database files
│   └── riley.sqlite       # Main database (397KB)
├── media/                 # Uploaded chart images
│   └── [SYMBOL]/         # Per-instrument folders
├── venv/                  # Python virtual environment
├── logs/                  # Application logs
│   ├── riley.log         # Main log
│   └── riley_debug.log   # Debug log
├── .streamlit/           # Streamlit configuration
│   └── config.toml       # Server config
├── run_riley.sh          # Startup script
└── requirements.txt      # Python dependencies
```

### Installed Dependencies
```
pandas==2.3.3
numpy==2.4.0
matplotlib==3.10.8
pytz==2025.2
pytest==9.0.2
pyarrow==22.0.0
ib-insync==0.9.86
streamlit==1.52.2
streamlit-calendar==1.4.0
python-dateutil==2.9.0.post0
```

---

## Application Management

### Check Status
```bash
# Check if Riley Cycles is running
ps aux | grep streamlit | grep riley-cycles

# Check logs
tail -f ~/riley-cycles/logs/riley.log
tail -f ~/riley-cycles/logs/riley_debug.log

# Check port
lsof -i :8081
```

### Start Application
```bash
cd ~/riley-cycles
nohup ./run_riley.sh > logs/riley.log 2>&1 < /dev/null &
```

### Stop Application
```bash
# Find the process
ps aux | grep streamlit | grep riley-cycles

# Kill by process name
pkill -f 'streamlit.*riley-cycles'

# Or kill by PID
kill <PID>
```

### Restart Application
```bash
# Stop
pkill -f 'streamlit.*riley-cycles'

# Wait
sleep 3

# Start
cd ~/riley-cycles
nohup ./run_riley.sh > logs/riley.log 2>&1 < /dev/null &
```

---

## Nginx Configuration

### Config File Location
```
/etc/nginx/sites-enabled/cycles.cosmicsignals.net.conf
```

### Key Settings
- **Port:** Proxies to 127.0.0.1:8081 (Streamlit)
- **SSL:** Enabled with certificates
- **WebSocket:** Configured for Streamlit's real-time updates

### View Config
```bash
sudo cat /etc/nginx/sites-enabled/cycles.cosmicsignals.net.conf
```

### Reload Nginx
```bash
sudo systemctl reload nginx
```

---

## Database

### Location
```
/home/raysudo/riley-cycles/db/riley.sqlite
```

### Access Database
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 << 'EOF'
from app.db import CyclesDB
db = CyclesDB()
# Run queries...
EOF
```

### Run Daily Scan
```bash
cd ~/riley-cycles
source venv/bin/activate
python scripts/cycles_run_scan.py --asof 2025-12-24
```

---

## Troubleshooting

### App Not Loading (White Page)

**Symptoms:** Blank page with "Streamlit" in title but no content

**Check:**
1. Is Streamlit process running?
   ```bash
   ps aux | grep streamlit | grep riley
   ```

2. Check logs for errors:
   ```bash
   tail -100 ~/riley-cycles/logs/riley_debug.log
   ```

3. Test database connection:
   ```bash
   cd ~/riley-cycles && source venv/bin/activate
   python3 -c "from app.db import CyclesDB; db = CyclesDB(); print(db.get_latest_scan_date())"
   ```

4. Check if port 8081 is accessible:
   ```bash
   curl http://127.0.0.1:8081/_stcore/health
   # Should return: ok
   ```

### Port Already in Use

**Error:** `Port 8081 is already in use`

**Solution:**
```bash
# Find and kill the process
lsof -i :8081
kill <PID>

# Or kill all streamlit processes
pkill -f streamlit

# Restart
cd ~/riley-cycles
nohup ./run_riley.sh > logs/riley.log 2>&1 < /dev/null &
```

### Import Errors

**Error:** `ModuleNotFoundError` or import failures

**Solution:**
```bash
# Activate virtual environment
cd ~/riley-cycles
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Restart app
pkill -f streamlit
nohup ./run_riley.sh > logs/riley.log 2>&1 < /dev/null &
```

### Database Errors

**Error:** `No scan data found` or database connection issues

**Solution:**
```bash
# Check database exists
ls -lh ~/riley-cycles/db/riley.sqlite

# Run a scan to populate data
cd ~/riley-cycles
source venv/bin/activate
python scripts/cycles_run_scan.py --asof $(date +%Y-%m-%d)
```

---

## Deployment History

### December 24, 2025
- **Replaced:** Cycles Detector V14
- **Deployed:** Riley Cycles Watch v1.0
- **Backup:** Old detector saved to `~/cycles-detector-v14-backup`
- **Domain:** Configured cycles.cosmicsignals.net
- **Status:** Deployed and running

---

## Updating the Application

### From Local Development

1. **Prepare update package:**
   ```bash
   cd "/Users/bernie/Documents/AI/Riley Project"
   tar -czf /tmp/riley-update.tar.gz app/ src/ scripts/ db/ requirements.txt
   ```

2. **Upload to server:**
   ```bash
   scp -i ~/.ssh/berryfit_key /tmp/riley-update.tar.gz raysudo@82.25.105.47:~/
   ```

3. **On server - backup and extract:**
   ```bash
   ssh -i ~/.ssh/berryfit_key raysudo@82.25.105.47
   cd ~/riley-cycles

   # Backup current version
   tar -czf ../riley-backup-$(date +%Y%m%d).tar.gz .

   # Stop app
   pkill -f 'streamlit.*riley-cycles'

   # Extract update
   tar -xzf ~/riley-update.tar.gz

   # Update dependencies if needed
   source venv/bin/activate
   pip install -r requirements.txt

   # Restart
   nohup ./run_riley.sh > logs/riley.log 2>&1 < /dev/null &
   ```

4. **Verify:**
   ```bash
   # Check process
   ps aux | grep streamlit | grep riley

   # Check logs
   tail -f logs/riley.log

   # Test access
   curl http://127.0.0.1:8081/_stcore/health
   ```

---

## Monitoring

### Log Locations
- **Application Log:** `~/riley-cycles/logs/riley.log`
- **Debug Log:** `~/riley-cycles/logs/riley_debug.log`
- **Nginx Access:** `/home/cosmicsignals-cycles/logs/nginx/access.log`
- **Nginx Error:** `/home/cosmicsignals-cycles/logs/nginx/error.log`

### Health Checks
```bash
# App health
curl http://127.0.0.1:8081/_stcore/health

# Public access
curl -I https://cycles.cosmicsignals.net

# Process status
ps aux | grep streamlit | grep riley
```

---

## Backup

### Database Backup
```bash
cd ~/riley-cycles
cp db/riley.sqlite db/backups/riley-$(date +%Y%m%d).sqlite
```

### Full Application Backup
```bash
cd ~
tar -czf riley-backup-$(date +%Y%m%d).tar.gz riley-cycles/
```

---

## Security Notes

- **SSH:** Key-based authentication only (`~/.ssh/berryfit_key`)
- **Streamlit:** Running on localhost only (127.0.0.1:8081)
- **Nginx:** Handles SSL/TLS termination and public access
- **Firewall:** Managed by CloudPanel
- **Updates:** Keep dependencies updated regularly

---

## Support Contacts

For issues or questions:
1. Check this documentation first
2. Review logs: `~/riley-cycles/logs/`
3. Test database: Verify scan data exists
4. Restart application: Follow restart procedure

---

## Quick Reference Commands

```bash
# SSH into server
ssh -i ~/.ssh/berryfit_key raysudo@82.25.105.47

# Check status
ps aux | grep streamlit | grep riley

# View logs
tail -f ~/riley-cycles/logs/riley.log

# Restart app
pkill -f 'streamlit.*riley'; cd ~/riley-cycles && nohup ./run_riley.sh > logs/riley.log 2>&1 &

# Run daily scan
cd ~/riley-cycles && source venv/bin/activate && python scripts/cycles_run_scan.py --asof $(date +%Y-%m-%d)

# Check health
curl http://127.0.0.1:8081/_stcore/health
```

---

**End of Documentation**
