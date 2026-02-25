# Server Setup Guide

Instructions for deploying the analytics server + dashboard on your Ubuntu/Oracle server.

## 1. Install Python Dependencies

```bash
cd /home/ubuntu/garmin-rowing
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 2. Verify GeoLite2 Database

```bash
ls -la /home/ubuntu/garmin-rowing/backend/GeoLite2-Country.mmdb
```

## 3. Deploy Frontend Files

Copy the `frontend/` directory to the server:
```bash
# From your local machine:
scp -r frontend/ ubuntu@your-server:/home/ubuntu/garmin-rowing/frontend/
```

Or if you're pulling from git:
```bash
cd /home/ubuntu/garmin-rowing && git pull
```

## 4. Update Nginx Configuration

Edit `/etc/nginx/sites-available/garmin-rowing`:

```nginx
server {
    listen 80;
    server_name rowing-nijmegen.duckdns.org;

    # Dashboard frontend (HTML/CSS/JS)
    location / {
        root /home/ubuntu/garmin-rowing/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
        add_header 'Access-Control-Allow-Origin' '*';
    }

    # Privacy page (from repo root)
    location = /privacy.html {
        alias /home/ubuntu/garmin-rowing/privacy.md;
        default_type text/plain;
    }

    # Proxy data.json to Flask analytics app
    location = /data.json {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $host;
    }

    # Proxy API endpoints to Flask
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header Content-Type $content_type;
    }

    # Health check
    location = /health {
        proxy_pass http://127.0.0.1:8001;
    }
}
```

Validate and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 5. Create Systemd Service

Create `/etc/systemd/system/garmin-analytics.service`:

```ini
[Unit]
Description=Garmin Rowing Analytics Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/garmin-rowing
ExecStart=/home/ubuntu/garmin-rowing/venv/bin/gunicorn -b 127.0.0.1:8001 -w 2 --chdir backend analytics_server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable garmin-analytics
sudo systemctl start garmin-analytics
sudo systemctl status garmin-analytics
```

## 6. Add Report Cron Job

Add to crontab (`crontab -e`):

```cron
# Generate analytics summary daily at 03:00
0 3 * * * /home/ubuntu/garmin-rowing/venv/bin/python /home/ubuntu/garmin-rowing/backend/analytics_report.py --days 90 >> /home/ubuntu/garmin-rowing/analytics_report.log 2>&1
```

## 7. Test Everything

```bash
# Test the analytics server directly
curl http://127.0.0.1:8001/data.json
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/api/summary

# Test the suggestion endpoint
curl -X POST http://127.0.0.1:8001/api/suggestions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "suggestion": "Add tide data!"}'

# Test through nginx
curl http://rowing-nijmegen.duckdns.org/data.json
curl http://rowing-nijmegen.duckdns.org/api/summary

# Check logs
ls -la /home/ubuntu/garmin-rowing/backend/analytics/

# Generate an initial report
cd /home/ubuntu/garmin-rowing
venv/bin/python backend/analytics_report.py
```

## 8. Restart After Code Changes

```bash
# After pulling new code:
sudo systemctl restart garmin-analytics
sudo systemctl reload nginx
```

## Directory Structure

```
/home/ubuntu/garmin-rowing/
├── frontend/
│   ├── index.html           # Dashboard page
│   ├── style.css            # Styling
│   └── script.js            # Charts, map, form logic
├── backend/
│   ├── analytics_server.py  # Flask app (serves data.json + API)
│   ├── analytics_report.py  # Summary generator
│   ├── fetch_data.py        # Data fetcher (unchanged)
│   ├── GeoLite2-Country.mmdb
│   ├── suggestions.db       # SQLite (created automatically)
│   ├── analytics/           # Created automatically
│   │   ├── 2026-02-25.jsonl
│   │   ├── .salt_2026-02-25
│   │   └── summary.json
│   └── requirements.txt
├── data.json
└── ...
```
