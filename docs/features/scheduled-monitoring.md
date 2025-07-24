# Scheduled Monitoring with Celery Beat

This guide explains how to set up and run automated category monitoring using Celery Beat.

## Overview

The system uses Celery Beat to run scheduled monitoring tasks automatically. Schedules are stored in the database and can be managed via the Settings page in the UI.

## Prerequisites

1. **Redis** must be running (used as message broker):
   ```bash
   # Install Redis if not already installed
   brew install redis  # macOS
   # or
   sudo apt-get install redis-server  # Ubuntu

   # Start Redis
   redis-server
   ```

2. **Database schema** must be applied:
   ```bash
   # Run in Supabase SQL Editor
   scripts/create_monitoring_schedules_table.sql
   ```

## Quick Start

### 1. Start Redis (if not running)
```bash
redis-server
```

### 2. Start Celery Worker
In a new terminal:
```bash
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
python3 run_celery_worker.py
```

### 3. Start Celery Beat Scheduler
In another terminal:
```bash
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
python3 run_celery_beat.py
```

### 4. Configure Schedules in UI
1. Open the web interface: `http://localhost:3000`
2. Navigate to **Settings** → **Schedules** tab
3. Click **Add Schedule** to create a new monitoring schedule
4. Configure the schedule interval (e.g., every 6 hours)

## Managing Schedules

### Via Web UI (Recommended)

1. **View Schedules**: Settings → Schedules tab
2. **Add Schedule**: Click "Add Schedule" button
3. **Edit Schedule**: Click edit icon next to schedule
4. **Enable/Disable**: Toggle the switch
5. **Run Now**: Click play button to run immediately
6. **Delete**: Click delete icon

### Via API

```bash
# List all schedules
curl http://localhost:8000/api/monitoring/schedules

# Create a new schedule
curl -X POST http://localhost:8000/api/monitoring/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "monitor_all_6h",
    "task_type": "category_monitor",
    "description": "Monitor all retailers every 6 hours",
    "schedule_type": "interval",
    "schedule_value": {"hours": 6},
    "enabled": true
  }'

# Run a schedule immediately
curl -X POST http://localhost:8000/api/monitoring/schedules/{schedule_id}/run
```

## Default Schedules

The system comes with these default schedules (can be modified):

1. **category_monitor_all** - Monitor all retailers every 6 hours
2. **category_monitor_hp** - Monitor HomePro every 4 hours
3. **daily_price_update** - Update prices daily at 2 AM

## Schedule Types

### Interval Schedules
Run tasks at regular intervals:
- Days: 0-365
- Hours: 0-23
- Minutes: 0-59
- Seconds: 0-59

Example: Every 6 hours = `{"hours": 6}`

### Cron Schedules (Coming Soon)
Run tasks at specific times using cron expressions.

## Monitoring Task Output

When a scheduled task runs, it:
1. Monitors categories for the specified retailer(s)
2. Detects changes (new/removed/modified categories)
3. Updates health scores
4. Creates alerts for critical issues
5. Records results in the database

## Viewing Results

### Execution History
```bash
# Get schedule execution history
curl http://localhost:8000/api/monitoring/schedules/{schedule_id}/history
```

### In the UI
1. **Monitoring Page**: Shows real-time category health
2. **Settings → Schedules**: Shows last run time and status
3. **Recent Changes**: View detected changes

## Troubleshooting

### Celery Worker Not Processing Tasks
1. Check Redis is running: `redis-cli ping` (should return PONG)
2. Check worker logs for errors
3. Verify database connection

### Schedules Not Running
1. Check Celery Beat is running
2. Verify schedule is enabled in UI
3. Check `next_run` time in database

### Tasks Failing
1. Check worker logs: Look for error messages
2. View task history in UI
3. Check API server is running

### Common Issues

**"No module named 'app'"**
- Ensure you're in the project directory
- Activate virtual environment: `source venv/bin/activate`

**"Connection refused" to Redis**
- Start Redis: `redis-server`
- Check Redis port (default: 6379)

**Schedule not appearing in UI**
- Refresh the page
- Check browser console for errors
- Verify API is running

## Production Deployment

For production, use supervisor or systemd to manage Celery processes:

### Supervisor Example
```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A app.config.celery_config worker --loglevel=info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A app.config.celery_config beat --loglevel=info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  worker:
    build: .
    command: celery -A app.config.celery_config worker --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  beat:
    build: .
    command: celery -A app.config.celery_config beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
```

## Advanced Configuration

### Custom Task Parameters
When creating a schedule, you can pass parameters:
```json
{
  "task_params": {
    "retailer_code": "HP",
    "force_full_scan": true
  }
}
```

### Multiple Workers
Run workers on different queues:
```bash
# Monitoring queue worker
celery -A app.config.celery_config worker -Q monitoring --loglevel=info

# Scraping queue worker  
celery -A app.config.celery_config worker -Q scraping --loglevel=info
```

### Performance Tuning
- Adjust worker concurrency: `--concurrency=4`
- Set task time limits in schedule configuration
- Monitor Redis memory usage

## Monitoring Celery

### Flower (Web UI for Celery)
```bash
pip install flower
celery -A app.config.celery_config flower
# Open http://localhost:5555
```

### Command Line
```bash
# Check active tasks
celery -A app.config.celery_config inspect active

# Check scheduled tasks
celery -A app.config.celery_config inspect scheduled

# Check worker stats
celery -A app.config.celery_config inspect stats
```

## Best Practices

1. **Start Small**: Begin with longer intervals (e.g., 12 hours) and decrease if needed
2. **Monitor Performance**: Check execution times in history
3. **Stagger Schedules**: Avoid running all tasks at the same time
4. **Set Appropriate Timeouts**: Prevent tasks from running too long
5. **Regular Maintenance**: Clean up old history records periodically

---

For more information, see:
- [Celery Documentation](https://docs.celeryproject.org/)
- [Category Monitoring Guide](CATEGORY_MONITORING.md)
- [API Documentation](docs/api/schedules.md)