# Manual Migration Required: Drop Unused Tables

**Date**: 2025-10-16
**Migration**: 007_drop_unused_tables.sql
**Status**: ⚠️ Requires manual execution via Supabase Dashboard

## Background

Two tables are unused by this codebase and should be dropped:

### Table 1: `ra_results` (0 records)

The `ra_results` table is unused and serves no purpose:

1. The Racing API `/v1/results` endpoint returns race records with embedded runner results
2. Position/results data is correctly stored in the `ra_runners` table
3. The `ra_results` table was planned but never actually implemented
4. No code uses this table (insert_results() method never called)

See: `/docs/RESULTS_DATA_ARCHITECTURE.md` for complete explanation.

### Table 2: `om_weather_hourly_forecast` (528 records, stale)

This was an early weather implementation that has been replaced:

1. Last updated: 2025-08-07 (2+ months stale)
2. No code in DarkHorses-Masters-Workers references it
3. Replaced by `dh_weather_forecast` and `dh_weather_history` (actively maintained)
4. "om_" prefix (OpenMeteo) replaced by "dh_" (DarkHorses) naming convention

## Required Action

Execute the following SQL via Supabase Dashboard SQL Editor:

```sql
-- Drop unused tables
DROP TABLE IF EXISTS ra_results;
DROP TABLE IF EXISTS om_weather_hourly_forecast;
```

### Steps:

1. Go to https://supabase.com/dashboard/project/amsjvmlaknnvppxsgpfk
2. Navigate to SQL Editor
3. Create new query
4. Paste: `DROP TABLE IF EXISTS ra_results;`
5. Click "Run" or press Cmd+Enter
6. Verify: Table should no longer appear in Table Editor

## Verification

After running, verify both tables are gone:

```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

tables_to_check = ['ra_results', 'om_weather_hourly_forecast']

for table in tables_to_check:
    try:
        supabase.table(table).select('*').limit(1).execute()
        print(f'❌ {table} still exists')
    except Exception as e:
        print(f'✅ {table} successfully dropped')
```

## Code Changes

The following code has been updated:

1. ✅ `utils/supabase_client.py` - `insert_results()` method commented out with deprecation notice
2. ✅ `migrations/007_drop_unused_ra_results.sql` - Migration SQL created
3. ✅ `docs/RESULTS_DATA_ARCHITECTURE.md` - Architecture documented

## Impact

**ra_results:**
- ✅ **Zero impact** - table has 0 records and no code uses it
- ✅ No data loss - results data is in `ra_runners` table
- ✅ No breaking changes - no code references this table

**om_weather_hourly_forecast:**
- ✅ **Low impact** - table has stale data (2+ months old)
- ✅ No data loss - current weather data is in `dh_weather_forecast` and `dh_weather_history`
- ✅ No breaking changes - no code in this repo references this table
- ⚠️ **Note**: Verify that DarkHorses-Weather-Race-Worker and DarkHorses-API don't use this table

## Why Manual?

Supabase Python client doesn't support raw DDL execution, and psql connection requires additional authentication. Manual execution via dashboard is the safest and most reliable method.

---

**After completing this migration, delete this file.**
