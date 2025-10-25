# Course Coordinates Implementation

**Status:** ✅ Production Ready
**Date:** 2025-10-22
**Coverage:** 100% (101/101 UK & Ireland courses)

## Overview

This document describes the automatic course coordinate assignment system that ensures all UK and Ireland racing courses have accurate latitude/longitude data from a validated source.

## Key Features

1. **Automatic Assignment:** Coordinates are automatically assigned when courses are fetched from the Racing API
2. **Coordinate Protection:** Existing coordinates are NEVER overwritten - they are static validated data
3. **UK/Ireland Only:** System defaults to fetching only GB and IRE courses
4. **100% Coverage:** All 101 UK/Ireland courses have validated coordinates

## Architecture

### Data Source

**File:** `fetchers/ra_courses_final_validated.json`
- Contains 91 validated course records
- Hyper-precise coordinates (verified manually)
- Includes all major UK/Ireland courses
- Handles course name variations (AW tracks, alternative names, etc.)

### Core Components

#### 1. Coordinate Helper Module
**File:** `utils/course_coordinates.py`

**Functions:**
- `load_coordinates_data()` - Loads and caches coordinates from JSON
- `get_course_coordinates(name, region)` - Looks up coordinates for a course
- `assign_coordinates_to_course(record)` - Assigns coordinates to course record
- `normalize_course_name(name)` - Handles name variations

**Name Normalization:**
Handles these variations:
- `Bangor-on-Dee` → `bangor`
- `Wexford-RH` → `wexford`
- `Wolverhampton-AW` → `wolverhampton`
- `Newmarket-July` → `newmarket`
- `Limerick Junction` → `limerick`

#### 2. Updated Fetchers

**Files:**
- `fetchers/courses_fetcher.py` - Standalone courses fetcher
- `fetchers/masters_fetcher.py` - Consolidated masters fetcher

**Changes:**
- Import `assign_coordinates_to_course` and `get_coordinates_stats`
- Default `region_codes` to `['gb', 'ire']`
- Call `assign_coordinates_to_course()` for each course record
- Log coordinate assignment statistics

#### 3. Database Client Protection

**File:** `utils/supabase_client.py`

**Method:** `insert_courses(courses)`

**Protection Mechanism:**
1. Fetch existing courses with coordinates
2. For courses that already have coordinates:
   - Remove `latitude` and `longitude` from update record
   - This prevents Supabase UPSERT from overwriting them
3. Only new courses or courses with NULL coordinates get updates

## Usage

### Fetching Courses

```python
# Using standalone fetcher
from fetchers.courses_fetcher import CoursesFetcher

fetcher = CoursesFetcher()
result = fetcher.fetch_and_store()  # Defaults to UK and Ireland

# Using masters fetcher
from fetchers.masters_fetcher import MastersFetcher

fetcher = MastersFetcher()
result = fetcher.fetch_courses()  # Defaults to UK and Ireland
```

### Manual Coordinate Update

If you need to update coordinates from the JSON file:

```bash
# Preview changes
python3 scripts/update_mst_courses_coordinates.py --dry-run

# Apply updates
python3 scripts/update_mst_courses_coordinates.py
```

## Data Flow

```
Racing API (/v1/courses?region=gb,ire)
    ↓
Fetcher (courses_fetcher.py or masters_fetcher.py)
    ↓
For each course:
  ├─ Extract basic data (id, name, region)
  ├─ Call assign_coordinates_to_course()
  │   ├─ Normalize course name
  │   ├─ Lookup in validated JSON cache
  │   └─ Assign latitude/longitude if found
  └─ Add to batch
    ↓
Database Client (insert_courses)
  ├─ Check existing courses for coordinates
  ├─ Remove lat/lon from records with existing coordinates
  └─ UPSERT batch to ra_mst_courses
    ↓
Result: New courses get coordinates, existing ones preserved
```

## Testing

**Test Script:** `tests/test_course_coordinate_protection.py`

Verifies:
1. ✓ Coordinate helper works correctly
2. ✓ New courses get coordinates assigned
3. ✓ Existing coordinates are preserved from overwrite

Run tests:
```bash
python3 tests/test_course_coordinate_protection.py
```

## Current Coverage

**Database:** `ra_mst_courses`

| Region | Courses | With Coordinates | Coverage |
|--------|---------|------------------|----------|
| GB     | 73      | 73               | 100%     |
| IRE    | 28      | 28               | 100%     |
| **Total** | **101** | **101**          | **100%** |

## Important Notes

### DO NOT Overwrite Coordinates

Coordinates in `ra_mst_courses` are **static validated data** sourced from:
- Manual verification
- Official racecourse locations
- Multiple data source cross-validation

They should NEVER be overwritten by:
- API responses (API doesn't provide coordinates)
- Automated updates
- Database migrations

### Protection Mechanisms

1. **Fetcher Level:** Coordinates assigned from validated JSON only
2. **Database Level:** `insert_courses()` preserves existing coordinates
3. **Default Behavior:** Only UK and Ireland courses are fetched

### Adding New Courses

If a new course is added to the Racing API:

1. It will be fetched automatically
2. If it exists in `ra_courses_final_validated.json`, coordinates will be assigned
3. If not in the file:
   - Coordinate will be NULL
   - Add to `ra_courses_final_validated.json` manually
   - Run `update_mst_courses_coordinates.py` to populate

## Related Files

- `fetchers/ra_courses_final_validated.json` - Validated coordinate data
- `utils/course_coordinates.py` - Coordinate helper module
- `fetchers/courses_fetcher.py` - Standalone courses fetcher
- `fetchers/masters_fetcher.py` - Consolidated masters fetcher
- `utils/supabase_client.py` - Database client with protection
- `scripts/update_mst_courses_coordinates.py` - Manual update script
- `tests/test_course_coordinate_protection.py` - Protection tests

## Maintenance

### Monthly Review
- Check for new courses added to the API
- Verify coordinate coverage remains at 100%
- Update validated JSON if new courses found

### Validation
```bash
# Check coordinate coverage
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
client = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key, 100)

response = client.client.table('ra_mst_courses').select('id, name, latitude, longitude, region_code').in_('region_code', ['GB', 'IRE', 'gb', 'ire']).execute()

total = len(response.data)
with_coords = sum(1 for c in response.data if c.get('latitude') and c.get('longitude'))

print(f'Coverage: {with_coords}/{total} ({with_coords/total*100:.1f}%)')
"
```

## Version History

- **2025-10-22:** Initial implementation with 100% coverage
- All 101 UK/Ireland courses populated
- Protection mechanism implemented and tested
- Automatic assignment integrated into fetchers
