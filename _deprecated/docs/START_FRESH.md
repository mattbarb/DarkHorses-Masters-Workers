# 🧹 Clean Up & Start Fresh - Step-by-Step Guide

## Current Situation
You have partial/test data from previous attempts. Let's clean it up and start fresh with the correct 2015-2025 strategy.

---

## 📋 Step-by-Step Process (5 Steps)

### Step 1: Navigate to Project Directory
```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
```

### Step 2: Preview What Will Be Deleted (Dry Run)
```bash
python3 cleanup_and_reset.py
```

**What this does:**
- Shows current record counts for all tables
- Shows what WOULD be deleted (but doesn't actually delete)
- Safe to run - just a preview

**Expected output:**
```
Current Database State
============================================================

✓ ra_courses              101 records
✓ ra_bookmakers            19 records
✗ ra_results                0 records
✓ ra_races                345 records
✓ ra_runners            3,473 records
✓ ra_horses             3,367 records
✓ ra_jockeys              494 records
✓ ra_trainers             658 records
✓ ra_owners             2,674 records

Total Records: 11,131
```

### Step 3: Actually Clean Up (Delete Old Data)
```bash
python3 cleanup_and_reset.py --confirm
```

**What this does:**
- Asks you to type 'DELETE' to confirm
- Deletes ALL records from ALL tables
- Preserves table schemas (structure remains)
- Shows before/after counts

**You'll see:**
```
Type 'DELETE' to confirm deletion:
```

**Type exactly:** `DELETE` (all caps) and press Enter

**Expected result:**
```
✓ Truncated ra_runners (3,473 records deleted)
✓ Truncated ra_results (0 records deleted)
✓ Truncated ra_races (345 records deleted)
✓ Truncated ra_horses (3,367 records deleted)
✓ Truncated ra_jockeys (494 records deleted)
✓ Truncated ra_trainers (658 records deleted)
✓ Truncated ra_owners (2,674 records deleted)
✓ Truncated ra_courses (101 records deleted)
✓ Truncated ra_bookmakers (19 records deleted)

All tables are now empty.
```

### Step 4: Verify Clean State
```bash
python3 cleanup_and_reset.py
```

**Expected output (all zeros):**
```
○ ra_courses                0 records
○ ra_bookmakers             0 records
○ ra_results                0 records
○ ra_races                  0 records
○ ra_runners                0 records
○ ra_horses                 0 records
○ ra_jockeys                0 records
○ ra_trainers               0 records
○ ra_owners                 0 records

Total Records: 0
```

### Step 5a: Start Fresh Initialization (Terminal 1)
```bash
python3 initialize_data.py
```

**What this does:**
- Fetches ALL data from 2015-01-01 to today
- Populates ALL 9 tables
- Takes 11-16 hours
- Logs progress to `logs/initialization_*.log`

**You'll see:**
```
================================================================================
DARKHORSES MASTERS WORKER - INITIALIZATION
================================================================================
Results start date: 2015-01-01 (Premium: True)
Racecards start date: 2023-01-23 (API limitation)
End date: 2025-10-06
Results period: 3931 days
Racecards period: 1018 days
================================================================================

PHASE 1: REFERENCE DATA COLLECTION
PHASE 2A: HISTORICAL RESULTS (2015-2025)
PHASE 2B: HISTORICAL RACECARDS (2023-2025)
```

### Step 5b: Monitor Progress (Terminal 2 - WHILE Step 5a is running)

**Open a NEW terminal window** and run:
```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 monitor_data_progress.py
```

**What this does:**
- Shows live progress dashboard
- Updates every 2 seconds
- Shows year-by-year completion
- Shows progress bars
- Press Ctrl+C to exit (won't stop the initialization)

---

## ⏱️ Timeline

| Step | Duration | Status |
|------|----------|--------|
| 1. Navigate | 5 seconds | Ready |
| 2. Dry run preview | 10 seconds | Ready |
| 3. Actual cleanup | 2-5 minutes | Ready |
| 4. Verify clean | 10 seconds | Ready |
| 5a. Start initialization | 11-16 hours | Ready |
| 5b. Monitor (optional) | Continuous | Ready |

---

## 🎯 Quick Command Summary

Copy and paste these commands in order:

```bash
# Step 1: Navigate
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers

# Step 2: Preview (safe - doesn't delete)
python3 cleanup_and_reset.py

# Step 3: Clean up (WILL delete - requires typing 'DELETE')
python3 cleanup_and_reset.py --confirm

# Step 4: Verify clean
python3 cleanup_and_reset.py

# Step 5a: Start fresh (Terminal 1)
python3 initialize_data.py
```

**Then in a NEW terminal:**
```bash
# Step 5b: Monitor (Terminal 2)
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 monitor_data_progress.py
```

---

## ✅ What You'll Have After Completion

```
ra_courses         ~150 records     ✅
ra_bookmakers       ~50 records     ✅
ra_results       ~55,000 records    ✅  (2015-2025)
ra_races         ~15,000 records    ✅  (2023-2025)
ra_runners      ~600,000 records    ✅  (2023-2025)
ra_horses        ~80,000 records    ✅  (2015-2025)
ra_jockeys        ~3,000 records    ✅  (2015-2025)
ra_trainers       ~2,500 records    ✅  (2015-2025)
ra_owners        ~25,000 records    ✅  (2015-2025)
───────────────────────────────────────────
TOTAL:          ~781,700 records    ✅
```

**Complete 2015-2025 UK & Irish racing database!**

---

## 🚨 Important Notes

1. **Don't close Terminal 1** while initialization is running (11-16 hours)
2. **You CAN close Terminal 2** (monitor) - it doesn't affect the process
3. **Process is resumable** - if it crashes, just run Step 5a again (it won't duplicate data)
4. **Check progress** - Open monitor anytime to see current status
5. **Be patient** - 11-16 hours is normal due to API rate limits

---

## 🎉 Ready to Start?

Run the commands above in order. Start with Step 1!

When you're at Step 5, you'll have:
- Terminal 1: Running initialization (don't close)
- Terminal 2: Monitoring progress (can close/reopen anytime)

Good luck! 🚀
