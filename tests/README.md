# Masters Worker Integration Tests

Comprehensive test suite to verify all reference data workers are functioning correctly by querying Supabase tables and checking data integrity.

## Overview

This test suite validates:
- ✅ **Courses Worker** - Racing venues (UK & Ireland)
- ✅ **Races Worker** - Race cards and results
- ✅ **People & Horses Worker** - Jockeys, trainers, owners, horses

## Quick Start

### Run All Tests

```bash
cd tests
python3 run_all_tests.py
```

### Run Individual Worker Tests

```bash
# Test courses worker only
python3 test_courses_worker.py

# Test races worker only
python3 test_races_worker.py

# Test people & horses worker only
python3 test_people_horses_worker.py
```

## Requirements

```bash
pip install supabase colorama python-dotenv
```

**Note**: These dependencies are already in the root `requirements.txt`.

## Environment Variables

Tests require the following environment variables (from `.env` file):

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

Create a `.env` file in the repository root with these values.

## Test Details

### Courses Worker Tests

**File**: `test_courses_worker.py`

**Tests**:
1. ✅ Table exists with data
2. ✅ Regional filtering (UK/Ireland only)
3. ✅ Data freshness (monthly updates)
4. ✅ Required fields populated
5. ✅ Reasonable course count (40-100)

**Expected**: ~50-70 courses for UK/Ireland

### Races Worker Tests

**File**: `test_races_worker.py`

**Tests**:
1. ✅ racing_races table exists
2. ✅ Recent race cards available
3. ✅ Regional filtering (UK/Ireland only)
4. ✅ racing_results table exists
5. ✅ Results coverage (date range)
6. ✅ Data freshness (daily updates)

**Expected**: Daily race cards and historical results

### People & Horses Worker Tests

**File**: `test_people_horses_worker.py`

**Tests**:
1. ✅ All tables exist (jockeys, trainers, owners, horses)
2. ✅ Minimum record counts met
3. ✅ Data freshness (weekly updates)
4. ✅ Required fields populated
5. ✅ Regional filtering applied

**Expected Minimums**:
- Jockeys: 100+
- Trainers: 100+
- Owners: 50+
- Horses: 500+

## Interpreting Results

### Test Status Indicators

- 🟢 **✅ PASS** - Test passed successfully
- 🔴 **❌ FAIL** - Test failed, worker may have issues
- 🟡 **⚠️  WARNING** - Test passed but with caveats

### Common Warnings

**Courses**:
- ⚠️  Data 30+ days old - Monthly updates, acceptable if <35 days
- ⚠️  Low course count - May be acceptable if >40 courses

**Races**:
- ⚠️  No races today - Race calendar varies, check last 7 days
- ⚠️  Results table empty - May be new deployment, daily backfill pending

**People & Horses**:
- ⚠️  Low record count - May be acceptable, depends on Racing API data availability
- ⚠️  Data 7+ days old - Weekly updates, acceptable if <10 days

### Common Failures

**All Workers**:
- ❌ Missing environment variables - Check `.env` file exists with SUPABASE_URL and SUPABASE_SERVICE_KEY
- ❌ Supabase connection failed - Check credentials are correct

**Courses**:
- ❌ Non-UK/Ireland courses found - Regional filtering not working

**Races**:
- ❌ No recent races - Worker hasn't run in 7+ days
- ❌ Non-UK/Ireland races found - Regional filtering not working

**People & Horses**:
- ❌ Tables empty - Worker hasn't run successfully yet
- ❌ NULL names found - Data quality issue

## Update Schedules

Workers run on different schedules:

| Worker | Frequency | Time | Table(s) |
|--------|-----------|------|----------|
| **Courses** | Monthly | 1st @ 3:00 AM | racing_courses |
| **Bookmakers** | Monthly | 1st @ 3:00 AM | racing_bookmakers |
| **Races** | Daily | 1:00 AM | racing_races, racing_results |
| **People & Horses** | Weekly | Sun @ 2:00 AM | racing_jockeys, racing_trainers, racing_owners, racing_horses |

If tests show stale data, wait for next scheduled run or check Render logs for errors.

## CI/CD Integration

### Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

### GitHub Actions Example

```yaml
name: Masters Worker Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python3 tests/run_all_tests.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
```

## Troubleshooting

### Tests Can't Connect to Supabase

```bash
# Verify environment variables are loaded
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); print('SUPABASE_URL:', os.getenv('SUPABASE_URL')); print('SUPABASE_SERVICE_KEY:', bool(os.getenv('SUPABASE_SERVICE_KEY')))"
```

**Common issues**:
- Missing `.env` file - Create from `.env.example` and fill in credentials
- Wrong Supabase service key - Must use service role key (not anon key)
- Network firewall blocking Supabase

### Tests Show Stale Data

Check update schedules above. Data is expected to be:
- **Courses/Bookmakers**: Updated monthly (1st of month)
- **Races/Results**: Updated daily (1 AM)
- **People/Horses**: Updated weekly (Sunday 2 AM)

Wait for next scheduled run or check Render logs for errors.

### All Tests Fail

1. Check workers are running on Render.com
2. Verify environment variables are set correctly in Render dashboard
3. Check Render deployment logs for startup errors
4. Ensure Starter plan (not free tier) to keep workers always-on

## Development

### Adding New Tests

```python
def test_new_feature(self):
    """Test N: Description of what this tests"""
    print(f"\n{Fore.YELLOW}[TEST N]{Style.RESET_ALL} Checking new feature...")

    try:
        # Your test logic here
        response = self.client.table('table_name').select('*').execute()

        if response.data:
            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Test passed")
            self.results['passed'] += 1
            return True
        else:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Test failed")
            self.results['failed'] += 1
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Error: {e}")
        self.results['failed'] += 1
        return False
```

Add the new test method call to `run_all_tests()`.

### Test Best Practices

1. **Be defensive** - Handle missing data gracefully (warnings, not failures)
2. **Provide context** - Print sample data to help debug issues
3. **Time-aware** - Account for scheduled run times (daily/weekly/monthly)
4. **Clear output** - Use colors and emojis for quick visual scanning

## Output Example

```
================================================================================
          DarkHorses Masters Workers - Integration Test Suite
================================================================================

Worker                              Passed     Failed     Warnings   Status
--------------------------------------------------------------------------------
Courses Worker                      5          0          1          ✅ PASS
Races Worker                        6          0          2          ✅ PASS
People & Horses Worker              5          0          3          ✅ PASS
--------------------------------------------------------------------------------
TOTAL                               16         0          6

📊 Overall Pass Rate: 100.0% (16/16 tests)
⚠️  Total Warnings: 6

================================================================================
🎉 ALL WORKERS FUNCTIONING CORRECTLY!
================================================================================

✅ Courses Worker: Collecting venue data
✅ Races Worker: Collecting race cards and results
✅ People & Horses Worker: Collecting jockeys, trainers, owners, horses
```

## Related Documentation

- **Deployment**: See README_WORKER.md for Render.com deployment
- **Worker Architecture**: See README.md for system overview
- **Racing API**: https://theracingapi.com/docs
- **Supabase**: https://supabase.com/docs

## License

Part of the DarkHorses-Masters-Workers project.
