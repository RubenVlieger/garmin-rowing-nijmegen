# Server Setup Guide

Instructions for deploying the analytics server on your Ubuntu/Oracle server.

## 1. Install Python Dependencies

```bash
cd /home/ubuntu/garmin-rowing
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 2. Verify GeoLite2 Database

Confirm the database is in place:
```bash
ls -la /home/ubuntu/garmin-rowing/backend/GeoLite2-Country.mmdb
```

## 3. Update Nginx Configuration

Edit `/etc/nginx/sites-available/garmin-rowing`:

```nginx
server {
    listen 80;
    server_name rowing-nijmegen.duckdns.org;

    # Proxy data.json requests to the analytics Flask app
    location = /data.json {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $host;
    }

    # Serve everything else statically (if needed in future)
    location / {
        root /home/ubuntu/garmin-rowing;
        add_header 'Access-Control-Allow-Origin' '*';
    }
}
```

Validate and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 4. Create Systemd Service

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

## 5. Add Report Cron Job

Add to crontab (`crontab -e`):

```cron
# Generate analytics summary daily at 03:00
0 3 * * * /home/ubuntu/garmin-rowing/venv/bin/python /home/ubuntu/garmin-rowing/backend/analytics_report.py --days 90 >> /home/ubuntu/garmin-rowing/analytics_report.log 2>&1
```

## 6. Test Everything

```bash
# Test the analytics server directly
curl http://127.0.0.1:8001/data.json
curl http://127.0.0.1:8001/health

# Test through nginx
curl http://rowing-nijmegen.duckdns.org/data.json

# Check logs were created
ls -la /home/ubuntu/garmin-rowing/backend/analytics/

# Generate a report
cd /home/ubuntu/garmin-rowing
venv/bin/python backend/analytics_report.py
cat backend/analytics/summary.json
```

## Directory Structure After Setup

```
/home/ubuntu/garmin-rowing/
├── backend/
│   ├── analytics_server.py      # Flask app (serves data.json + logs analytics)
│   ├── analytics_report.py      # Summary generator
│   ├── fetch_data.py            # Existing data fetcher (unchanged)
│   ├── GeoLite2-Country.mmdb    # GeoIP database
│   ├── analytics/               # Created automatically
│   │   ├── 2026-02-25.jsonl     # Daily log files
│   │   ├── .salt_2026-02-25     # Daily salts (hidden)
│   │   └── summary.json         # Generated report
│   └── requirements.txt
├── data.json                    # Weather/water data (unchanged)
└── ...
```
