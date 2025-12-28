# Cycles Detector - Production Deployment Guide

## Quick Start (Development)

```bash
python3 app.py
```
Access at: http://localhost:5001

**Note:** This is for development only!

## Production Deployment

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Start Production Server

```bash
chmod +x start_production.sh
./start_production.sh
```

### 3. Using Gunicorn Directly

```bash
# Create logs directory
mkdir -p logs

# Start with config file
gunicorn -c gunicorn_config.py wsgi:app

# Or use command line options
gunicorn --bind 0.0.0.0:5001 \
         --workers 4 \
         --timeout 300 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         wsgi:app
```

### 4. Background/Daemon Mode

```bash
# Start in background
gunicorn -c gunicorn_config.py wsgi:app &

# Or use screen/tmux
screen -S cycles_detector
gunicorn -c gunicorn_config.py wsgi:app
# Press Ctrl+A, then D to detach
```

### 5. Systemd Service (Recommended for servers)

Create `/etc/systemd/system/cycles-detector.service`:

```ini
[Unit]
Description=Cycles Detector Web Application
After=network.target

[Service]
Type=notify
User=your_username
Group=your_groupname
WorkingDirectory=/path/to/Cycles Detector V14/webapp
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn -c gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cycles-detector
sudo systemctl start cycles-detector
sudo systemctl status cycles-detector
```

## Configuration

### Worker Count
Default: 4 workers
Adjust based on CPU cores: `workers = (2 * CPU_CORES) + 1`

### Timeout
Default: 300 seconds (5 minutes)
Analysis can take time, so keep this high.

### Port
Default: 5001
Change in `gunicorn_config.py` if needed.

## Monitoring

```bash
# View access logs
tail -f logs/access.log

# View error logs
tail -f logs/error.log

# Check if running
ps aux | grep gunicorn
```

## Stopping the Server

```bash
# Find the PID
cat logs/gunicorn.pid

# Kill gracefully
kill $(cat logs/gunicorn.pid)

# Or force kill if needed
pkill -f gunicorn
```

## Nginx Reverse Proxy (Optional)

For production with domain name and SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## Troubleshooting

### Import Errors
Make sure all Python dependencies are installed:
```bash
pip3 install -r requirements.txt
```

### Permission Errors
```bash
chmod +x start_production.sh
mkdir -p logs
chmod 755 logs
```

### Port Already in Use
```bash
# Find what's using port 5001
lsof -i :5001

# Kill it
kill <PID>
```

### Worker Timeout
If analysis takes too long, increase timeout in `gunicorn_config.py`:
```python
timeout = 600  # 10 minutes
```

## Security Notes

1. **Do not expose Flask development server** (`python3 app.py`) to the internet
2. Use Gunicorn or similar WSGI server for production
3. Consider adding Nginx as a reverse proxy for SSL and load balancing
4. Set up firewall rules to restrict access
5. Use environment variables for sensitive configuration

## Performance Tips

1. Adjust worker count based on CPU cores
2. Use `--worker-class gevent` for async operations if needed
3. Enable keepalive for persistent connections
4. Monitor memory usage and adjust workers accordingly
