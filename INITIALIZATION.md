# Database Initialization Guide

## Overview

After deploying the Masters Worker on Render.com, you need to run an **initial data collection** to populate the database with historical data from 2015 to present.

The worker's scheduled runs (daily/weekly/monthly) only collect recent data. This initialization script backfills all historical data.

---

## What Gets Initialized

### Phase 1: Reference Data
- **Courses** (~60 UK/Ireland venues)
- **Bookmakers** (~10-15 bookmakers)
- **Jockeys** (~500-1000 active jockeys)
- **Trainers** (~300-500 trainers)
- **Owners** (~500-1000 owners)
- **Horses** (~5,000-10,000 horses)

### Phase 2: Historical Data
- **Races** (from 2015-01-01 to today)
- **Results** (from 2015-01-01 to today)

---

## Running the Initialization

### Option 1: Full Initialization (Recommended)

Backfills everything from 2015-01-01 to today:

```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 initialize_data.py
```

**Expected Duration:** 2-4 hours (depending on API speed)

### Option 2: Custom Start Date

Start backfill from a specific date:

```bash
python3 initialize_data.py --from 2020-01-01
```

### Option 3: Skip Reference Data

If reference data is already populated, only backfill races/results:

```bash
python3 initialize_data.py --skip-reference
```

### Option 4: Test Mode

Test the initialization with limited data (last 7 days only):

```bash
python3 initialize_data.py --test
```

---

## What Happens During Initialization

### 1. Reference Data Collection

```
PHASE 1: REFERENCE DATA COLLECTION
==================================================
STEP 1: COURSES & BOOKMAKERS
  ✅ Courses: 62 records
  ✅ Bookmakers: 12 records

STEP 2: JOCKEYS, TRAINERS, OWNERS & HORSES
  ✅ Jockeys: 847 records
  ✅ Trainers: 423 records
  ✅ Owners: 612 records
  ✅ Horses: 8,342 records
```

### 2. Historical Data Backfill

The script processes data in **90-day chunks** to manage API load:

```
PHASE 2: HISTORICAL RACES & RESULTS BACKFILL
==================================================
Date range: 2015-01-01 to 2025-10-06
Total days: 3,932 days
Processing in 44 chunks of ~90 days each

CHUNK 1/44: 2015-01-01 to 2015-03-31
  ✅ Races: 1,247 records
  ✅ Results: 9,832 records
  📊 Progress: 90/3,932 days (2.3%)
  ⏸️  Pausing 5 seconds before next chunk...

CHUNK 2/44: 2015-04-01 to 2015-06-29
  ✅ Races: 1,198 records
  ✅ Results: 9,541 records
  📊 Progress: 180/3,932 days (4.6%)
  ...
```

### 3. Completion Summary

```
INITIALIZATION COMPLETE
==================================================
Total duration: 8,423.45 seconds (140.39 minutes)

📋 Reference Data:
   ✅ Courses: 62 records
   ✅ Bookmakers: 12 records
   ✅ Jockeys: 847 records
   ✅ Trainers: 423 records
   ✅ Owners: 612 records
   ✅ Horses: 8,342 records

📊 Historical Data:
   Date range: 2015-01-01 to 2025-10-06
   Total days: 3,932
   Chunks processed: 44

   Races: 54,783 records
   Results: 437,264 records

🎉 Initialization complete! Database is ready.
```

---

## Running on Render.com

Since this is a long-running process, you have two options:

### Option 1: Run Locally (Recommended)

Run the initialization from your local machine:

```bash
# Make sure .env.local has production credentials
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 initialize_data.py
```

**Advantages:**
- You can monitor progress in real-time
- No timeout issues
- Can pause/resume if needed

### Option 2: Run on Render.com

SSH into the Render service or create a one-time job:

```bash
# Via Render dashboard: Shell tab
python3 initialize_data.py
```

**Note:** Render may have timeout limits. For very long-running processes, local execution is safer.

---

## Monitoring Progress

The script provides detailed progress updates:

```
📊 Progress: 1,800/3,932 days (45.8%)
⏱️  Chunks completed: 20/44
```

Logs are also written to `logs/initialize_data.log` for review.

---

## Error Handling

### If Initialization Fails Mid-Way

The script can be resumed from where it left off:

```bash
# If it failed at 2018-06-15, resume from there
python3 initialize_data.py --from 2018-06-15 --skip-reference
```

### Common Errors

**API Rate Limiting:**
- Script includes 5-second pauses between chunks
- If you hit rate limits, increase the pause duration in the script

**Database Connection Issues:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env.local`
- Check Supabase service is running

**Memory Issues:**
- Script processes in 90-day chunks to avoid memory problems
- If still issues, reduce chunk size in the script

---

## After Initialization

### 1. Verify Data

Run the deployment tests to verify everything loaded correctly:

```bash
cd tests
python3 run_deployment_tests.py
```

Expected result: All tables should have data and pass freshness checks.

### 2. Monitor Scheduled Runs

The worker will now run on schedule:
- **Daily 1:00 AM UTC:** Update races & results
- **Weekly Sunday 2:00 AM UTC:** Update people & horses
- **Monthly 1st @ 3:00 AM UTC:** Update courses & bookmakers

Check Render.com logs to verify scheduled runs are working.

---

## Estimated Database Sizes

After full initialization (2015-present):

| Table | Approximate Records |
|-------|-------------------|
| ra_courses | ~60 |
| ra_bookmakers | ~12 |
| ra_jockeys | ~1,000 |
| ra_trainers | ~500 |
| ra_owners | ~1,000 |
| ra_horses | ~10,000 |
| ra_races | ~50,000 |
| ra_results | ~400,000 |

**Total:** ~462,000 records

---

## Cost Considerations

**API Usage:**
- The Racing API may have rate limits or usage costs
- Check your Racing API plan for limits
- Initialization makes ~3,932 API calls (one per day)

**Database Storage:**
- Supabase free tier: 500MB
- Full initialization: ~100-200MB (well within free tier)
- Paid plans available if needed

**Processing Time:**
- Local execution: Free (uses your machine)
- Render execution: Counted toward service hours

---

## Troubleshooting

### Script Takes Too Long

Reduce the date range:
```bash
python3 initialize_data.py --from 2020-01-01  # Last 5 years only
```

### API Errors

Check Racing API status and credentials:
```bash
curl -u USERNAME:PASSWORD https://theracingapi.com/api/v1/courses
```

### Database Full

Check Supabase dashboard for storage usage. Upgrade plan if needed.

---

## Next Steps

After successful initialization:

1. ✅ Run deployment tests
2. ✅ Verify data in Supabase dashboard
3. ✅ Monitor scheduled worker runs
4. ✅ Set up alerts for failures (optional)

Your database is now fully populated and ready for use!
