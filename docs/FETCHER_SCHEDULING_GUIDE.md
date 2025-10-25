# Fetcher Scheduling Guide

## Overview

This guide provides complete instructions for scheduling automated data fetching from the Racing API.

**Master Controller:** `fetchers/master_fetcher_controller.py`

## Scheduling Requirements

### Daily Sync
- **Time:** 1:00 AM UK time
- **Frequency:** Every day
- **Duration:** ~10 minutes
- **Purpose:** Fetch last 3 days of data + current reference data

### Weekly Refresh
- **Time:** 2:00 AM UK time (Sundays)
- **Frequency:** Weekly
- **Duration:** ~5 minutes
- **Purpose:** Refresh master tables (jockeys, trainers, owners)

### Monthly Refresh
- **Time:** 3:00 AM UK time (1st of month)
- **Frequency:** Monthly
- **Duration:** ~2 minutes
- **Purpose:** Refresh courses and bookmakers

## Cron Configuration

### Installation

1. Open crontab editor:
```bash
crontab -e
```

2. Add the following entries:

```bash
# DarkHorses Racing API Data Fetching
# Timezone: UK (adjust for BST/GMT as needed)

# Daily sync at 1:00 AM UK time
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && /usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1

# Weekly master table refresh (Sundays at 2:00 AM)
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && /usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/cron_weekly.log 2>&1

# Monthly course/bookmaker refresh (1st of month at 3:00 AM)
0 3 1 * * cd /path/to/DarkHorses-Masters-Workers && /usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers >> logs/cron_monthly.log 2>&1
```

3. Save and exit (`:wq` in vi/vim)

4. Verify crontab:
```bash
crontab -l
```

### Timezone Handling

**BST (British Summer Time) vs GMT:**
- BST: Last Sunday in March to last Sunday in October (UTC+1)
- GMT: Rest of year (UTC+0)

**Option 1: Use system timezone**
```bash
# Set system timezone to Europe/London
sudo timedatectl set-timezone Europe/London

# Cron will automatically handle BST/GMT
```

**Option 2: Explicit UTC times**
```bash
# GMT (winter): 1am UK = 1am UTC
0 1 * * * command

# BST (summer): 1am UK = 0am UTC (midnight)
# Adjust manually or use system timezone
```

**Recommended:** Use system timezone (Option 1) for automatic BST/GMT handling.

### Environment Variables

Cron doesn't inherit shell environment. Add to crontab:

```bash
# Environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Jobs below...
```

**Or** load from .env.local:

```bash
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && source .env.local && /usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1
```

## Systemd Timer Configuration

### Advantages
- Better logging
- Service management
- Dependency handling
- Easy enable/disable

### Setup

#### 1. Create Timer Unit

`/etc/systemd/system/darkhorses-daily-fetch.timer`:

```ini
[Unit]
Description=DarkHorses Daily Fetch Timer
Requires=darkhorses-daily-fetch.service

[Timer]
OnCalendar=01:00:00
Persistent=true
AccuracySec=1min

[Install]
WantedBy=timers.target
```

#### 2. Create Service Unit

`/etc/systemd/system/darkhorses-daily-fetch.service`:

```ini
[Unit]
Description=DarkHorses Daily Fetch Service
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/DarkHorses-Masters-Workers
EnvironmentFile=/path/to/DarkHorses-Masters-Workers/.env.local
ExecStart=/usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily
StandardOutput=append:/path/to/DarkHorses-Masters-Workers/logs/systemd_daily.log
StandardError=append:/path/to/DarkHorses-Masters-Workers/logs/systemd_daily.log

[Install]
WantedBy=multi-user.target
```

#### 3. Create Weekly Timer/Service

`/etc/systemd/system/darkhorses-weekly-fetch.timer`:

```ini
[Unit]
Description=DarkHorses Weekly Fetch Timer
Requires=darkhorses-weekly-fetch.service

[Timer]
OnCalendar=Sun 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

`/etc/systemd/system/darkhorses-weekly-fetch.service`:

```ini
[Unit]
Description=DarkHorses Weekly Fetch Service
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/DarkHorses-Masters-Workers
EnvironmentFile=/path/to/DarkHorses-Masters-Workers/.env.local
ExecStart=/usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners
StandardOutput=append:/path/to/DarkHorses-Masters-Workers/logs/systemd_weekly.log
StandardError=append:/path/to/DarkHorses-Masters-Workers/logs/systemd_weekly.log

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timers (start on boot)
sudo systemctl enable darkhorses-daily-fetch.timer
sudo systemctl enable darkhorses-weekly-fetch.timer

# Start timers immediately
sudo systemctl start darkhorses-daily-fetch.timer
sudo systemctl start darkhorses-weekly-fetch.timer

# Check status
sudo systemctl status darkhorses-daily-fetch.timer
sudo systemctl list-timers --all | grep darkhorses
```

#### 5. Manual Trigger

```bash
# Trigger service manually (without waiting for timer)
sudo systemctl start darkhorses-daily-fetch.service

# View logs
sudo journalctl -u darkhorses-daily-fetch.service -f
```

## Docker/Container Scheduling

### Docker Compose with Cron

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  fetcher:
    build: .
    volumes:
      - ./logs:/app/logs
      - ./.env.local:/app/.env.local
    environment:
      - TZ=Europe/London
    entrypoint: /bin/sh -c "cron && tail -f /app/logs/cron.log"
```

`Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install cron
RUN apt-get update && apt-get install -y cron

# Add crontab
RUN echo "0 1 * * * cd /app && python3 fetchers/master_fetcher_controller.py --mode daily >> /app/logs/cron_daily.log 2>&1" > /etc/cron.d/darkhorses-cron
RUN chmod 0644 /etc/cron.d/darkhorses-cron
RUN crontab /etc/cron.d/darkhorses-cron

CMD ["cron", "-f"]
```

### Kubernetes CronJob

`k8s/cronjob-daily-fetch.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: darkhorses-daily-fetch
spec:
  schedule: "0 1 * * *"  # 1am daily
  timeZone: "Europe/London"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fetcher
            image: darkhorses-workers:latest
            command:
            - python3
            - fetchers/master_fetcher_controller.py
            - --mode
            - daily
            env:
            - name: RACING_API_USERNAME
              valueFrom:
                secretKeyRef:
                  name: racing-api-credentials
                  key: username
            - name: RACING_API_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: racing-api-credentials
                  key: password
            - name: SUPABASE_URL
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: url
            - name: SUPABASE_SERVICE_KEY
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: service-key
          restartPolicy: OnFailure
```

## Cloud Platform Scheduling

### Render.com

**Cron Jobs:**

```yaml
# render.yaml
services:
  - type: cron
    name: darkhorses-daily-fetch
    env: docker
    schedule: "0 1 * * *"
    dockerCommand: python3 fetchers/master_fetcher_controller.py --mode daily
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
```

### AWS (EventBridge + Lambda/ECS)

**EventBridge Rule:**

```json
{
  "ScheduleExpression": "cron(0 1 * * ? *)",
  "TimeZone": "Europe/London",
  "Target": {
    "Arn": "arn:aws:ecs:region:account:cluster/darkhorses",
    "RoleArn": "arn:aws:iam::account:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "arn:aws:ecs:region:account:task-definition/darkhorses-fetcher",
      "LaunchType": "FARGATE"
    }
  }
}
```

### Google Cloud (Cloud Scheduler + Cloud Run)

```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create http darkhorses-daily-fetch \
  --schedule="0 1 * * *" \
  --time-zone="Europe/London" \
  --uri="https://your-cloud-run-url/run-daily-fetch" \
  --http-method=POST
```

## Monitoring and Alerts

### Log Rotation

`/etc/logrotate.d/darkhorses`:

```
/path/to/DarkHorses-Masters-Workers/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 user user
    sharedscripts
    postrotate
        systemctl reload darkhorses-daily-fetch.service > /dev/null 2>&1 || true
    endscript
}
```

### Health Checks

Create `scripts/health_check.sh`:

```bash
#!/bin/bash

# Check if last fetch was successful
LATEST_LOG=$(ls -t logs/fetcher_daily_*.json 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "ERROR: No fetch logs found"
    exit 1
fi

# Check if log is less than 25 hours old (daily + buffer)
if [ $(find "$LATEST_LOG" -mmin +1500 | wc -l) -gt 0 ]; then
    echo "ERROR: Last fetch is too old"
    exit 1
fi

# Check for success
if ! grep -q '"success": true' "$LATEST_LOG"; then
    echo "ERROR: Last fetch failed"
    exit 1
fi

echo "OK: Last fetch successful"
exit 0
```

Add to cron:
```bash
# Health check at 2am (after daily fetch)
0 2 * * * /path/to/scripts/health_check.sh || mail -s "DarkHorses Fetch Failed" admin@example.com
```

### Email Alerts

Using `mailx` or `sendmail`:

```bash
# Add to cron
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && /usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily 2>&1 | mail -s "DarkHorses Daily Fetch" admin@example.com
```

Using Python (in fetcher):

```python
import smtplib
from email.message import EmailMessage

def send_alert(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = 'fetcher@darkhorses.com'
    msg['To'] = 'admin@example.com'

    smtp = smtplib.SMTP('localhost')
    smtp.send_message(msg)
    smtp.quit()
```

## Testing Schedule

### Test Cron Entry

```bash
# Add test entry (runs every minute)
* * * * * cd /path/to/DarkHorses-Masters-Workers && echo "Test: $(date)" >> logs/cron_test.log

# Watch the log
tail -f logs/cron_test.log

# Remove test entry after verification
```

### Test Systemd Timer

```bash
# Create test timer (runs every 2 minutes)
sudo systemctl edit --force --full darkhorses-test.timer

# Add:
# [Timer]
# OnCalendar=*:0/2

# Start and watch
sudo systemctl start darkhorses-test.timer
sudo journalctl -u darkhorses-test.service -f
```

## Troubleshooting

### Cron Not Running

1. Check cron service:
```bash
sudo systemctl status cron
```

2. Check crontab syntax:
```bash
crontab -l
```

3. Check logs:
```bash
grep CRON /var/log/syslog
```

4. Test command manually:
```bash
cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily
```

### Systemd Timer Issues

```bash
# Check timer status
sudo systemctl status darkhorses-daily-fetch.timer

# Check service status
sudo systemctl status darkhorses-daily-fetch.service

# View logs
sudo journalctl -u darkhorses-daily-fetch.service --since today

# Check next run time
systemctl list-timers --all | grep darkhorses
```

### Environment Variables Not Loading

1. Verify .env.local exists and is readable
2. Check file permissions
3. Use absolute paths
4. Load explicitly in cron/systemd

## Best Practices

1. **Always log to file** - Use `>> logs/file.log 2>&1`
2. **Use absolute paths** - Never rely on relative paths in cron
3. **Set timezone** - Use system timezone or explicit UTC times
4. **Monitor failures** - Set up alerts for failed runs
5. **Test first** - Always test manually before scheduling
6. **Log rotation** - Prevent disk space issues
7. **Health checks** - Verify data freshness
8. **Backup strategy** - Keep logs for troubleshooting

---

**Last Updated:** 2025-10-21
**Version:** 1.0
