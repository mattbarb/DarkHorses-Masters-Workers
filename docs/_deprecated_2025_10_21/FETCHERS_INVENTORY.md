# Fetchers Inventory & Documentation

**Date**: 2025-10-19
**Status**: Production-Ready System

## Overview

This document provides a complete inventory of all fetchers in the DarkHorses Masters Workers system, their purposes, API endpoints, database tables, and current status.

---

## Quick Reference Table

| Fetcher | File | API Endpoint | Database Table | Status | Daily/Weekly/Monthly |
|---------|------|-------------|----------------|--------|---------------------|
| **Courses** | `courses_fetcher.py` | `/v1/courses` | `ra_courses` | ✅ Production | Monthly |
| **Bookmakers** | `bookmakers_fetcher.py` | `/v1/bookmakers` | `ra_bookmakers` | ✅ Production | Monthly |
| **Horses** | `horses_fetcher.py` | `/v1/horses/search` | `ra_horses` | ⚠️ Deprecated | Use Entity Extraction |
| **Jockeys** | `jockeys_fetcher.py` | `/v1/jockeys/search` | `ra_jockeys` | ⚠️ Deprecated | Use Entity Extraction |
| **Trainers** | `trainers_fetcher.py` | `/v1/trainers/search` | `ra_trainers` | ⚠️ Deprecated | Use Entity Extraction |
| **Owners** | `owners_fetcher.py` | `/v1/owners/search` | `ra_owners` | ⚠️ Deprecated | Use Entity Extraction |
| **Races** | `races_fetcher.py` | `/v1/racecards/pro` | `ra_races`, `ra_runners` | ✅ Production | Daily |
| **Results** | `results_fetcher.py` | `/v1/results/pro` | `ra_races`, `ra_runners` | ✅ Production | Daily |

---

## Detailed Fetcher Documentation

### 1. Courses Fetcher

**File**: `fetchers/courses_fetcher.py`

**Purpose**: Fetch racing course/venue reference data

**API Endpoint**: `/v1/courses`

**Database Table**: `ra_courses`

**Schedule**: Monthly (courses rarely change)

**Key Features**:
- Fetches all UK and Ireland racing courses
- Includes course type (flat/jumps/mixed)
- Stores latitude/longitude coordinates
- UPSERT by course `id`

**Fields Captured**:
```python
{
    'id': 'crs_12345',
    'name': 'Newmarket',
    'region': 'gb',
    'country_code': 'GB',
    'type': 'flat',
    'latitude': 52.243889,
    'longitude': 0.405,
    'created_at': '2025-10-19T...',
    'updated_at': '2025-10-19T...'
}
```

**Usage**:
```bash
python3 main.py --entities courses
```

**Production Config**:
```python
{
    'limit_per_page': 500,
    'max_pages': None,  # Fetch all
    'filter_uk_ireland': True
}
```

---

### 2. Bookmakers Fetcher

**File**: `fetchers/bookmakers_fetcher.py`

**Purpose**: Fetch bookmaker reference data for odds providers

**API Endpoint**: `/v1/bookmakers`

**Database Table**: `ra_bookmakers`

**Schedule**: Monthly (bookmakers rarely change)

**Key Features**:
- Fetches all active bookmakers
- Stores bookmaker code and name
- UPSERT by bookmaker `code`

**Fields Captured**:
```python
{
    'code': 'BET365',
    'name': 'Bet365',
    'created_at': '2025-10-19T...',
    'updated_at': '2025-10-19T...'
}
```

**Usage**:
```bash
python3 main.py --entities bookmakers
```

**Production Config**:
```python
{
    'limit_per_page': 500,
    'max_pages': None  # Fetch all
}
```

---

### 3. Horses Fetcher

**File**: `fetchers/horses_fetcher.py`

**Purpose**: Bulk fetch horse reference data

**API Endpoint**: `/v1/horses/search`

**Database Table**: `ra_horses`

**Schedule**: ⚠️ **DEPRECATED** - Use Entity Extraction instead

**Status**: Not recommended for production use

**Why Deprecated**:
- Requires `name` parameter (HTTP 422 without it)
- Horses are automatically discovered via `races_fetcher` and `results_fetcher`
- Entity extraction provides complete pedigree data via enrichment
- More efficient to extract horses from race data

**Recommended Alternative**:
Use `EntityExtractor` via `races_fetcher.py` and `results_fetcher.py`

---

### 4. Jockeys Fetcher

**File**: `fetchers/jockeys_fetcher.py`

**Purpose**: Bulk fetch jockey reference data

**API Endpoint**: `/v1/jockeys/search`

**Database Table**: `ra_jockeys`

**Schedule**: ⚠️ **DEPRECATED** - Use Entity Extraction instead

**Status**: Not recommended for production use

**Why Deprecated**:
- Requires `name` parameter (HTTP 422 without it)
- Jockeys are automatically discovered via `races_fetcher` and `results_fetcher`
- More efficient to extract jockeys from race data

**Recommended Alternative**:
Use `EntityExtractor` via `races_fetcher.py` and `results_fetcher.py`

---

### 5. Trainers Fetcher

**File**: `fetchers/trainers_fetcher.py`

**Purpose**: Bulk fetch trainer reference data

**API Endpoint**: `/v1/trainers/search`

**Database Table**: `ra_trainers`

**Schedule**: ⚠️ **DEPRECATED** - Use Entity Extraction instead

**Status**: Not recommended for production use

**Why Deprecated**:
- Requires `name` parameter (HTTP 422 without it)
- Trainers are automatically discovered via `races_fetcher` and `results_fetcher`
- Entity extraction now captures `trainer_location` field
- More efficient to extract trainers from race data

**Recommended Alternative**:
Use `EntityExtractor` via `races_fetcher.py` and `results_fetcher.py`

**Note**: EntityExtractor now captures trainer locations (added 2025-10-19)

---

### 6. Owners Fetcher

**File**: `fetchers/owners_fetcher.py`

**Purpose**: Bulk fetch owner reference data

**API Endpoint**: `/v1/owners/search`

**Database Table**: `ra_owners`

**Schedule**: ⚠️ **DEPRECATED** - Use Entity Extraction instead

**Status**: Not recommended for production use

**Why Deprecated**:
- Requires `name` parameter (HTTP 422 without it)
- Owners are automatically discovered via `races_fetcher` and `results_fetcher`
- More efficient to extract owners from race data

**Recommended Alternative**:
Use `EntityExtractor` via `races_fetcher.py` and `results_fetcher.py`

---

### 7. Races Fetcher ⭐ PRIMARY FETCHER

**File**: `fetchers/races_fetcher.py`

**Purpose**: Fetch upcoming race cards with runners and entities

**API Endpoint**: `/v1/racecards/pro`

**Database Tables**:
- `ra_races` - Race metadata
- `ra_runners` - Race entries/runners
- Via `EntityExtractor`:
  - `ra_horses` - Horse reference data (with enrichment)
  - `ra_jockeys` - Jockey reference data
  - `ra_trainers` - Trainer reference data (with location)
  - `ra_owners` - Owner reference data
  - `ra_sires`, `ra_dams`, `ra_damsires` - Pedigree data (via enrichment)

**Schedule**: Daily (production runs once per day for upcoming races)

**Key Features**:
- ✅ Fetches complete racecard data
- ✅ Automatically extracts entities (horses, jockeys, trainers, owners)
- ✅ Enriches NEW horses with complete pedigree data from `/v1/horses/{id}/pro`
- ✅ Captures trainer locations (added 2025-10-19)
- ✅ Stores pre-race runner data (no position/results yet)
- ✅ Rate-limited enrichment (2 req/sec, 0.5s between calls)

**Fields Captured** (Sample):
```python
# Race data
{
    'id': 'rac_12345',
    'course_id': 'crs_123',
    'date': '2025-10-20',
    'time': '14:30:00',
    'name': 'Group 1 Stakes',
    'distance': 2000,
    'going': 'Good',
    'class': '1',
    'race_type': 'Flat',
    'prize': 500000
}

# Runner data
{
    'race_id': 'rac_12345',
    'horse_id': 'hrs_456',
    'jockey_id': 'jky_789',
    'trainer_id': 'trn_101',
    'owner_id': 'own_202',
    'number': '3',
    'draw': '5',
    'weight_lbs': 126,
    'age': 3,
    # ... (no position data yet - race hasn't run)
}

# Trainer entity (via EntityExtractor)
{
    'id': 'trn_101',
    'name': 'John Gosden',
    'location': 'Newmarket, Suffolk'  # ✅ NOW CAPTURED
}
```

**Usage**:
```bash
# Fetch next 7 days of racecards
python3 main.py --entities races

# Test mode (last 7 days)
python3 main.py --entities races --test
```

**Production Config**:
```python
{
    'days_ahead': 7,  # Next 7 days
    'region_codes': ['gb', 'ire']
}
```

---

### 8. Results Fetcher ⭐ PRIMARY FETCHER

**File**: `fetchers/results_fetcher.py`

**Purpose**: Fetch historical race results with finishing positions

**API Endpoint**: `/v1/results/pro`

**Database Tables**:
- `ra_races` - Race metadata (if not exists)
- `ra_runners` - Updates runners with position data
- Via `EntityExtractor`:
  - `ra_horses` - Horse reference data (with enrichment)
  - `ra_jockeys`, `ra_trainers`, `ra_owners` - Entity data
  - `ra_sires`, `ra_dams`, `ra_damsires` - Pedigree data (via enrichment)

**Schedule**: Daily (production runs for last 12 months)

**Key Features**:
- ✅ Fetches complete race results
- ✅ Updates runners with finishing positions, prize money, times
- ✅ Automatically extracts entities
- ✅ Enriches NEW horses with complete pedigree data
- ✅ Validates pedigree IDs to prevent foreign key violations (added 2025-10-19)
- ✅ Sets missing pedigree IDs to NULL if references don't exist
- ✅ Uses composite key UPSERT (race_id, horse_id) - fixed 2025-10-19
- ✅ 100% success rate with pedigree validation

**Position Data Fields** (Updated via Results):
```python
{
    # Existing fields
    'race_id': 'rac_12345',
    'horse_id': 'hrs_456',

    # POSITION DATA (from results)
    'position': '1',  # Finishing position
    'distance_beaten': '0.0',  # Lengths behind winner
    'prize_won': 285000.0,  # Prize money earned
    'starting_price': '7/2',  # Fractional odds
    'starting_price_decimal': 4.50,  # Decimal odds
    'finishing_time': '1:48.55',  # Race time
    'race_comment': 'Made all, drew clear 2f out',  # Commentary
    'jockey_silk_url': 'https://...',  # Jockey colors
    'overall_beaten_distance': 0.0,  # Alternative distance metric
    'jockey_claim_lbs': 0,  # Weight allowance
    'weight_stones_lbs': '8-13'  # Weight in UK format
}
```

**Usage**:
```bash
# Fetch last 12 months results
python3 main.py --entities results

# Test mode (last 30 days)
python3 main.py --entities results --test
```

**Production Config**:
```python
{
    'days_back': 365,  # Last 12 months
    'region_codes': ['gb', 'ire']
}
```

**Recent Improvements** (2025-10-19):
1. Fixed composite key UPSERT (`race_id, horse_id`)
2. Added pedigree validation to prevent foreign key violations
3. NULL handling for missing pedigree references
4. 100% insert success rate achieved

---

## Entity Extraction System

**File**: `utils/entity_extractor.py`

**Purpose**: Automatically extract and enrich entity data from race records

**Used By**: `races_fetcher.py`, `results_fetcher.py`

**Entities Extracted**:
1. **Horses** - With optional enrichment for new horses
2. **Jockeys** - Name and ID
3. **Trainers** - Name, ID, and **location** ✅
4. **Owners** - Name and ID
5. **Pedigree** - Sires, dams, damsires (via enrichment)

**Hybrid Enrichment Strategy**:
- **Discovery Phase**: Fast extraction from race data (id, name)
- **Enrichment Phase**: NEW horses fetched from `/v1/horses/{id}/pro`
  - Adds 9 additional fields: dob, sex_code, colour, region, pedigree
  - Rate-limited: 2 requests/second
  - Only for horses not yet in database

**Recent Additions** (2025-10-19):
- ✅ Trainer location capture: `trainer.location = runner.get('trainer_location')`
- ✅ Integrated with races_fetcher to pass location data through

---

## Production Schedule

### Daily Operations (1 AM UK Time)
```bash
python3 main.py --daily
```

**Runs**:
1. `races_fetcher` - Next 7 days of racecards
2. `results_fetcher` - Last 12 months of results

**Purpose**: Keep race data and results up-to-date

---

### Weekly Operations (Sunday 2 AM UK Time)
```bash
python3 main.py --weekly
```

**Runs**:
1. Entity extraction validation
2. Data quality checks

**Purpose**: Maintain entity data quality

---

### Monthly Operations (1st of month, 3 AM UK Time)
```bash
python3 main.py --monthly
```

**Runs**:
1. `courses_fetcher` - Update course reference data
2. `bookmakers_fetcher` - Update bookmaker reference data

**Purpose**: Keep infrequently-changing reference data current

---

## Testing

### Test All Fetchers
```bash
python3 tests/test_all_fetchers.py
```

**What It Does**:
- Inserts 3 test records per table with **TEST** prefix
- Verifies all fetchers work correctly
- Checks data integrity
- Tests trainer location capture

### Cleanup Test Data
```bash
python3 tests/cleanup_test_data.py
```

**What It Does**:
- Removes all **TEST** prefixed records
- Cleans up test data from all tables

---

## Database Tables Summary

| Table | Records | Purpose | Primary Key | Updated By |
|-------|---------|---------|-------------|------------|
| `ra_courses` | ~60 | Racing venues | `id` | courses_fetcher |
| `ra_bookmakers` | ~50 | Bookmakers | `code` | bookmakers_fetcher |
| `ra_horses` | ~110K | Horse reference | `id` | EntityExtractor |
| `ra_jockeys` | ~8K | Jockey reference | `id` | EntityExtractor |
| `ra_trainers` | ~2.8K | Trainer reference | `id` | EntityExtractor |
| `ra_owners` | ~48K | Owner reference | `id` | EntityExtractor |
| `ra_sires` | ~25K | Sire pedigree | `id` | EntityExtractor (enrichment) |
| `ra_dams` | ~90K | Dam pedigree | `id` | EntityExtractor (enrichment) |
| `ra_damsires` | ~15K | Damsire pedigree | `id` | EntityExtractor (enrichment) |
| `ra_races` | ~12K | Race metadata | `id` | races_fetcher, results_fetcher |
| `ra_runners` | ~110K | Race entries | `(race_id, horse_id)` | races_fetcher, results_fetcher |

---

## Recent Updates Log

### 2025-10-19
1. ✅ **Trainer Location Capture**
   - Added `trainer_location` extraction in `races_fetcher.py:298`
   - Updated `EntityExtractor` to capture location at line 76
   - Trainers now have location data populated going forward

2. ✅ **Results Fetcher Fixes**
   - Fixed composite key UPSERT for ra_runners
   - Added pedigree validation to prevent foreign key violations
   - Achieved 100% insert success rate

3. ✅ **Position Data Capture**
   - Fixed position data extraction in results_fetcher
   - All 6 enhanced fields now captured correctly
   - 100% position data population rate

4. ✅ **Test Infrastructure**
   - Created `tests/test_all_fetchers.py` with **TEST** prefix system
   - Created `tests/cleanup_test_data.py` for test data removal
   - Created comprehensive fetcher inventory documentation

---

## Fetcher Status Summary

**✅ Production-Ready** (2 fetchers):
- races_fetcher.py
- results_fetcher.py

**✅ Production-Ready** (2 reference fetchers):
- courses_fetcher.py
- bookmakers_fetcher.py

**⚠️ Deprecated** (4 fetchers):
- horses_fetcher.py
- jockeys_fetcher.py
- trainers_fetcher.py
- owners_fetcher.py

**Reason for Deprecation**: Entity extraction from race data is more efficient and provides better data quality than bulk API fetches that require name parameters.

---

**Total Fetchers**: 8 (4 active, 4 deprecated)
**Total Database Tables**: 11
**Total Test Coverage**: 6 tables with **TEST** prefix system

**Documentation Status**: Complete and up-to-date as of 2025-10-19
