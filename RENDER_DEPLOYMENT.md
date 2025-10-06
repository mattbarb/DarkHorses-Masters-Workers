# Render.com Deployment Instructions

## Masters Worker Deployment

### Step 1: Create New Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Find and select **"DarkHorses-Masters-Workers"**

### Step 2: Service Configuration

Render will auto-detect `render.yaml` and show:

```
Service Name: darkhorses-masters-worker
Environment: Python 3
Build Command: pip install --upgrade pip && pip install -r requirements.txt
Start Command: python3 start_worker.py
Plan: Starter ($7/month) ⚠️ IMPORTANT - NOT Free tier
```

Click **"Apply"**

### Step 3: Add Environment Variables

Go to **"Environment"** tab and add these 5 variables:

```bash
RACING_API_USERNAME=l2fC3sZFIZmvpiMt6DdUCpEv
RACING_API_PASSWORD=R0pMr1L58WH3hUkpVtPcwYnw
SUPABASE_URL=https://amsjvmlaknnvppxsgpfk.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI
LOG_LEVEL=INFO
```

**How to add:**
- Click **"Add Environment Variable"**
- Paste the **Key** (e.g., `RACING_API_USERNAME`)
- Paste the **Value** (e.g., `l2fC3sZFIZmvpiMt6DdUCpEv`)
- Repeat for all 5 variables
- Click **"Save Changes"**

### Step 4: Verify Deployment

Go to **"Logs"** tab and look for:

```
📍 Starting Masters Worker Scheduler...
📍 Loaded configuration from environment
📍 Racing API: ✓ Connected
📍 Supabase: ✓ Connected
📍 Schedule configured:
  - Courses & Bookmakers: Monthly (1st @ 03:00)
  - People & Horses: Weekly (Sunday @ 02:00)
  - Races & Results: Daily (01:00)
🚀 Scheduler running...
```

### Step 5: Test Locally (Optional)

```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/tests
python3 run_all_tests.py
```

This will verify data is being collected correctly.

---

## Update Schedule

The worker runs on this schedule:

| Entity | Frequency | Time | Table(s) |
|--------|-----------|------|----------|
| Courses & Bookmakers | Monthly | 1st @ 3:00 AM | `racing_courses`, `racing_bookmakers` |
| People & Horses | Weekly | Sun @ 2:00 AM | `racing_jockeys`, `racing_trainers`, `racing_owners`, `racing_horses` |
| Races & Results | Daily | 1:00 AM | `racing_races`, `racing_results` |

**Note**: Initial run happens immediately on deployment to populate data.

---

## Database Tables

This worker populates these Supabase tables:

- `racing_courses` - Racing venues (UK & Ireland)
- `racing_bookmakers` - Bookmakers list
- `racing_jockeys` - Jockey profiles
- `racing_trainers` - Trainer profiles
- `racing_owners` - Owner profiles
- `racing_horses` - Horse profiles
- `racing_races` - Race cards with runners
- `racing_results` - Historical race results

---

## Troubleshooting

### Service won't start
- Check **"Logs"** tab for errors
- Verify all 5 environment variables are set
- Ensure **Starter plan** is selected (not Free tier)

### No data being collected
- Check Racing API credentials are correct
- Verify Supabase URL and service key
- Check that database tables exist in Supabase
- Review logs for API errors

### Environment variable errors
```
❌ Error: Missing SUPABASE_URL
```
Solution: Add the missing environment variable in Environment tab

---

## Cost

- **Plan**: Render Starter - $7/month
- **Why not Free?**: Free tier spins down after 15 min of inactivity, which would stop the scheduler

---

## Related Services

- **DarkHorses-Odds-Workers**: https://github.com/mattbarb/DarkHorses-Odds-Workers
  - Live & historical odds collection
  - Separate Render service ($7/month)
  - Total system cost: $14/month

---

## Support

For issues:
1. Check Render deployment logs
2. Run local tests: `python3 tests/run_all_tests.py`
3. Review `README.md` and `README_WORKER.md`
4. Check Racing API status: https://theracingapi.com
