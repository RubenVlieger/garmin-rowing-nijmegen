# Hassle-Free Docker Deployment 🐳

This guide replaces the manual steps from `server_setup.md`. With Docker and Docker Compose, your entire stack (Nginx, Flask backend, SQLite, Python Cron Scheduler) spins up in seconds, on any machine, without touching the host OS.

## 1. Prerequisites
Ensure you have Docker and Docker Compose installed on your host Ubuntu server:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

## 2. Prepare the Directory
On your server, clone the repository or pull the latest changes, and ensure the `.mmdb` file is present:
```bash
cd /home/ubuntu/garmin-rowing
git pull

# Verify MaxMind GeoLite2 database is present
ls -la backend/GeoLite2-Country.mmdb
```

## 3. Stop the Old Setup (If Applicable)
If you previously followed the manual `server_setup.md` guide, stop the host Nginx and host Systemd service so ports don't clash:
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx

sudo systemctl stop garmin-analytics
sudo systemctl disable garmin-analytics

# (Optional) Remove the old host python venv
rm -rf venv/
```

## 4. Spin it Up 🚀
From the repository root `/home/ubuntu/garmin-rowing/`, simply run:

```bash
sudo docker compose up -d
```

Docker will intelligently build your Python image utilizing `uv` (for blazing fast dependency resolution) and start three containers:
1. `garmin_nginx`: Serves HTML/JS/CSS on port `80` and proxies API requests.
2. `garmin_backend`: Runs the Flask `gunicorn` server handling `/data.json` and API routes.
3. `garmin_scheduler`: A custom Python loop replacing host `cron` to fetch data every 15 mins and generate reports daily.

## 5. Helpful Commands

### View live logs
```bash
sudo docker compose logs -f
```
*(This lets you watch the scheduler hit the RWS/weather APIs in real-time!)*

### Check status
```bash
sudo docker compose ps
```

### Apply a code update
If you push changes to GitHub, pull them down and restart:
```bash
git pull
sudo docker compose up -d --build
```

### Where is my data?
Everything mounts via volume streams. `data.json`, `backend/suggestions.db`, and `backend/analytics/` stay safely sync'd to your host machine folder. Even if you destroy the containers, your data persists!
