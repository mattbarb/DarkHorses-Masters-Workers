# Jockey Data Enrichment Research Report

**Date:** 2025-10-17
**Purpose:** Comprehensive analysis of ALL possible jockey data sources in The Racing API
**Scope:** Identify every field, endpoint, and enrichment opportunity for jockey information

---

## Executive Summary

After comprehensive research of The Racing API, actual API responses, and existing system architecture, this report documents:

1. **Current State:** We capture only 3 basic jockey fields (ID, name, claim)
2. **Available Data:** API provides minimal jockey-specific data
3. **Key Finding:** **No dedicated jockey profile/statistics endpoints exist**
4. **Recommendation:** Jockey enrichment must come from **aggregating race participation data** (ra_mst_runners)

---

## Section 1: Complete Endpoint Inventory

### A. Jockey-Specific Endpoints

#### `/v1/jockeys/search` (NAME SEARCH ONLY)
- **Method:** GET
- **Plan:** Standard and above
- **Required Parameter:** `name` (cannot bulk list)
- **Purpose:** Name-based lookup ONLY

**Response Structure:**
```json
{
  "jockeys": [
    {
      "id": "jky_250764",
      "name": "Kieran O'Neill"
    }
  ]
}
```

**Fields Available:**
- ✅ `id` - Jockey ID
- ✅ `name` - Jockey name
- ❌ **No additional fields** (no age, weight, nationality, statistics, etc.)

**Limitations:**
- Requires exact/partial name match
- Cannot bulk list all jockeys
- Returns ONLY id and name
- No profile information
- No statistics
- No biographical data

**Current Implementation:** `fetchers/jockeys_fetcher.py` (functional but limited)

---

### B. Individual Jockey Endpoint

#### `/v1/jockeys/{jockey_id}` - **DOES NOT EXIST**
- Tested: 404 Not Found
- No Pro/Standard/Basic tiers available
- No individual jockey profile endpoint

**What We Expected But Doesn't Exist:**
- Jockey profile page
- Career statistics
- Biographical information
- Physical attributes
- License information
- Trainer relationships
- Historical performance

---

### C. Statistics Endpoints - **NONE EXIST**

All tested and returned 404:
- ❌ `/v1/statistics`
- ❌ `/v1/stats`
- ❌ `/v1/jockeys/statistics`
- ❌ `/v1/jockeys/{id}/statistics`
- ❌ `/v1/jockeys/{id}/form`
- ❌ `/v1/jockeys/{id}/performance`

**Conclusion:** The Racing API provides NO jockey statistics endpoints.

---

## Section 2: Jockey Data in Other Endpoints

### A. Racecards Endpoint (`/v1/racecards/pro`)

**Jockey Fields Per Runner:**
```json
{
  "jockey": "Kieran O'Neill",           // Name (string)
  "jockey_id": "jky_250764",            // ID (string)
  "jockey_claim_lbs": "0"               // Claim in pounds (string/int)
}
```

**Additional Context Fields:**
- `jockey_allowance` - Apprentice allowance (sometimes present)
- `weight_lbs` - Total weight (includes jockey + allowance)

**What's NOT Included:**
- ❌ Physical attributes (actual jockey weight, height)
- ❌ Career statistics (wins, rides, win rate)
- ❌ Biographical info (age, nationality, debut date)
- ❌ License type (flat, jumps, conditional)
- ❌ Trainer relationships (retained jockey status)
- ❌ Rankings or ratings
- ❌ Form data

**Current Capture:** ✅ We extract these fields from racecards via `EntityExtractor`

---

### B. Results Endpoint (`/v1/results`)

**Jockey Fields Per Runner:**
```json
{
  "jockey": "Kieran O'Neill",
  "jockey_id": "jky_250764",
  "jockey_claim_lbs": "0"
}
```

**Identical to Racecards:**
- Same 3 fields only
- No additional jockey information in results
- No performance metrics beyond race outcome

**Current Capture:** ✅ We extract these fields from results via `EntityExtractor`

---

### C. Big Races Endpoint (`/v1/racecards/big-races`)

**Findings:**
- Same jockey fields as regular racecards
- 106 total fields per race (richest endpoint)
- **BUT** jockey data still limited to: id, name, claim

**No Additional Jockey Enrichment Available**

---

## Section 3: Jockey Data Matrix

### Current vs. Available vs. Desired

| Data Field | Available in API | Current Capture | Source | Priority |
|------------|-----------------|----------------|---------|----------|
| **Basic Identity** |
| `jockey_id` | ✅ Yes | ✅ Yes | All endpoints | - |
| `name` | ✅ Yes | ✅ Yes | All endpoints | - |
| `jockey_claim_lbs` | ✅ Yes | ✅ Yes | Racecards/Results | - |
| `jockey_allowance` | ⚠️ Sometimes | ❌ No | Racecards (inconsistent) | P2 |
| **Physical Attributes** |
| `weight` (jockey's actual weight) | ❌ No | ❌ No | Not in API | - |
| `height` | ❌ No | ❌ No | Not in API | - |
| `nationality` | ❌ No | ❌ No | Not in API | - |
| `age` / `dob` | ❌ No | ❌ No | Not in API | - |
| **Career Information** |
| `debut_date` | ❌ No | ❌ No | Not in API | - |
| `license_type` (flat/jumps) | ❌ No | ❌ No | Not in API | - |
| `conditional_status` | ❌ No | ❌ No | Not in API | - |
| `apprentice_status` | ⚠️ Implied | ⚠️ Via claim | Claim > 0 implies apprentice | - |
| **Professional Relationships** |
| `retained_by_trainer` | ❌ No | ❌ No | Not in API | - |
| `stable_affiliation` | ❌ No | ❌ No | Not in API | - |
| **Statistics (Career)** |
| `total_rides` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `total_wins` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `total_places` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `total_seconds` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `total_thirds` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `win_rate` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| `place_rate` | ❌ No | ✅ Calculated | Database aggregation | ✅ Implemented |
| **Statistics (Recent Form)** |
| `recent_14d_rides` | ❌ No | ⚠️ Can Calculate | Database aggregation | P1 |
| `recent_14d_wins` | ❌ No | ⚠️ Can Calculate | Database aggregation | P1 |
| `recent_30d_rides` | ❌ No | ⚠️ Can Calculate | Database aggregation | P1 |
| `recent_30d_win_rate` | ❌ No | ⚠️ Can Calculate | Database aggregation | P1 |
| `last_win_date` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |
| `days_since_last_win` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |
| **Contextual Statistics** |
| `win_rate_by_surface` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |
| `win_rate_by_distance` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |
| `win_rate_by_class` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |
| `win_rate_by_course` | ❌ No | ⚠️ Can Calculate | Database aggregation | P3 |
| `win_rate_by_going` | ❌ No | ⚠️ Can Calculate | Database aggregation | P3 |
| **Partnerships** |
| `best_trainer_partnership` | ❌ No | ⚠️ Can Calculate | Database analysis | P3 |
| `best_horse_partnership` | ❌ No | ⚠️ Can Calculate | Database analysis | P3 |
| `frequent_trainers` | ❌ No | ⚠️ Can Calculate | Database analysis | P3 |
| **Media & Profile** |
| `profile_image_url` | ❌ No | ❌ No | Not in API | - |
| `biography` | ❌ No | ❌ No | Not in API | - |
| `social_media_links` | ❌ No | ❌ No | Not in API | - |
| **Rankings** |
| `official_championship_position` | ❌ No | ❌ No | Not in API | - |
| `prize_money_earned` | ❌ No | ⚠️ Can Calculate | Database aggregation | P2 |

**Legend:**
- ✅ **Yes** - Available and captured
- ⚠️ **Can Calculate** - Can derive from existing data
- ❌ **No** - Not available anywhere

---

## Section 4: Database Schema Analysis

### Current ra_jockeys Table Structure

**Basic Fields (Always Present):**
```sql
jockey_id       VARCHAR(50) PRIMARY KEY
name            TEXT
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

**Calculated Statistics Fields (Migration 007):**
```sql
-- Career Statistics
total_rides         INTEGER        -- Calculated from ra_mst_runners
total_wins          INTEGER        -- Position = 1
total_places        INTEGER        -- Position <= 3
total_seconds       INTEGER        -- Position = 2
total_thirds        INTEGER        -- Position = 3
win_rate            DECIMAL(5,2)   -- Percentage (0-100)
place_rate          DECIMAL(5,2)   -- Percentage (0-100)
stats_updated_at    TIMESTAMP      -- Last calculation time
```

**Available via Database View (jockey_statistics):**
```sql
CREATE OR REPLACE VIEW jockey_statistics AS
SELECT
    j.jockey_id,
    j.name,
    COUNT(r.runner_id) as calculated_total_rides,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as calculated_total_wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as calculated_total_places,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as calculated_total_seconds,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as calculated_total_thirds,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_place_rate
FROM ra_jockeys j
LEFT JOIN ra_mst_runners r ON r.jockey_id = j.jockey_id AND r.position IS NOT NULL
GROUP BY j.jockey_id, j.name;
```

**Update Function Available:**
```sql
SELECT * FROM update_entity_statistics();
```

This function updates all jockey statistics from ra_mst_runners data.

---

## Section 5: Runner Data Analysis

### Fields Available in ra_mst_runners (Jockey Context)

From `fetchers/races_fetcher.py` transformation:

```python
runner_record = {
    # Jockey Identity
    'jockey_id': runner.get('jockey_id'),
    'racing_api_jockey_id': runner.get('jockey_id'),
    'jockey_name': runner.get('jockey'),

    # Jockey Attributes in Race Context
    'jockey_claim': runner.get('jockey_claim'),          # String
    'apprentice_allowance': runner.get('jockey_allowance'),  # Integer (lbs)

    # Race Outcome (jockey's performance)
    'position': runner.get('position'),
    'finishing_time': runner.get('time'),
    'btn': runner.get('btn'),  # Beaten by (lengths)

    # Weight Carried
    'weight': runner.get('weight'),      # String like "8-10"
    'weight_lbs': runner.get('lbs'),     # Integer total weight

    # Race Context
    'race_id': race_id,
    'horse_id': runner.get('horse_id'),
    'trainer_id': runner.get('trainer_id'),
    'owner_id': runner.get('owner_id'),

    # Race Metadata (joined via race_id)
    # Available: course, surface, distance, going, race_type, class, date
}
```

**Key Insight:** Every race ride creates a runner record with jockey context. This is our PRIMARY source for:
1. Ride count
2. Win/place statistics
3. Performance by context (surface, distance, going, course, class)
4. Partnerships (with trainers, horses, owners)
5. Form trends over time

---

## Section 6: Missing Data Gaps

### What We CANNOT Get From API or Database

**Biographical Information:**
- ❌ Date of birth / Age
- ❌ Nationality / Country of origin
- ❌ Debut date (first ride)
- ❌ Retirement status
- ❌ Physical measurements (height, weight)
- ❌ Biography text
- ❌ Profile images
- ❌ Social media profiles

**Licensing & Professional Status:**
- ❌ License type (Flat, National Hunt, Conditional)
- ❌ License status (Active, Suspended, Retired)
- ❌ Apprentice status (beyond claim inference)
- ❌ Championship rankings (official)
- ❌ Official ratings or grades

**Relationships:**
- ❌ Retained jockey agreements (official)
- ❌ Stable affiliations
- ❌ Agent information
- ❌ Family connections (father/son jockeys)

**Financial:**
- ❌ Prize money earned (API provides per-race, but not career totals)
- ❌ Riding fees
- ❌ Sponsorships

**These would require:**
1. External data sources (Racing Post, BHA, etc.)
2. Web scraping
3. Manual data entry
4. Third-party APIs

---

## Section 7: Enrichment Opportunities

### Priority 1: Implement NOW (High Value, Easy)

#### A. Recent Form Statistics
**What:** Add recent performance metrics to ra_jockeys table

**New Fields:**
```sql
ALTER TABLE ra_jockeys
ADD COLUMN recent_14d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN recent_30d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN last_ride_date DATE DEFAULT NULL,
ADD COLUMN days_since_last_ride INTEGER DEFAULT NULL;
```

**Calculation Logic:**
```sql
-- Recent 14-day statistics
SELECT
    j.jockey_id,
    COUNT(CASE WHEN race.race_date >= CURRENT_DATE - 14 THEN 1 END) as recent_14d_rides,
    COUNT(CASE WHEN race.race_date >= CURRENT_DATE - 14 AND r.position = 1 THEN 1 END) as recent_14d_wins,
    -- Similar for 30-day
FROM ra_jockeys j
LEFT JOIN ra_mst_runners r ON r.jockey_id = j.jockey_id
LEFT JOIN ra_mst_races race ON race.race_id = r.race_id
GROUP BY j.jockey_id;
```

**Implementation Effort:** Low (extend existing statistics function)
**Value:** High (shows current form vs. career)
**Rate Limit Impact:** None (database calculation)

---

#### B. Prize Money Aggregation
**What:** Calculate total prize money won by jockey

**New Field:**
```sql
ALTER TABLE ra_jockeys
ADD COLUMN total_prize_money DECIMAL(12,2) DEFAULT NULL,
ADD COLUMN recent_30d_prize_money DECIMAL(12,2) DEFAULT NULL;
```

**Calculation Logic:**
```sql
SELECT
    j.jockey_id,
    SUM(r.prize_money_won) as total_prize_money,
    SUM(CASE WHEN race.race_date >= CURRENT_DATE - 30 THEN r.prize_money_won ELSE 0 END) as recent_30d_prize_money
FROM ra_jockeys j
LEFT JOIN ra_mst_runners r ON r.jockey_id = j.jockey_id AND r.position = 1  -- Winners only
LEFT JOIN ra_mst_races race ON race.race_id = r.race_id
GROUP BY j.jockey_id;
```

**Implementation Effort:** Low
**Value:** Medium-High
**Rate Limit Impact:** None

---

#### C. Activity Tracking
**What:** Track when jockey last rode

**New Fields:**
```sql
ALTER TABLE ra_jockeys
ADD COLUMN first_ride_date DATE DEFAULT NULL,
ADD COLUMN last_ride_date DATE DEFAULT NULL,
ADD COLUMN days_since_last_ride INTEGER DEFAULT NULL,
ADD COLUMN active_last_30d BOOLEAN DEFAULT FALSE;
```

**Implementation Effort:** Low
**Value:** Medium (identify active vs. inactive jockeys)
**Rate Limit Impact:** None

---

### Priority 2: Consider Implementing (Medium Value)

#### A. Contextual Win Rates
**What:** Win rates by surface, distance, class, etc.

**Implementation Options:**
1. **Materialized View:** Pre-calculate and store
2. **On-Demand Query:** Calculate when needed
3. **Separate Stats Table:** `ra_jockey_context_stats`

**New Table Structure:**
```sql
CREATE TABLE ra_jockey_context_stats (
    stat_id SERIAL PRIMARY KEY,
    jockey_id VARCHAR(50) REFERENCES ra_jockeys(jockey_id),
    context_type VARCHAR(20), -- 'surface', 'distance_band', 'class', 'going', 'course'
    context_value VARCHAR(50), -- 'AW', 'Turf', '5f-7f', 'Class 2', 'Good', 'Ascot'
    total_rides INTEGER,
    total_wins INTEGER,
    win_rate DECIMAL(5,2),
    total_places INTEGER,
    place_rate DECIMAL(5,2),
    stats_updated_at TIMESTAMP
);
```

**Example Queries:**
```sql
-- Win rate on All-Weather vs. Turf
SELECT surface, COUNT(*), COUNT(CASE WHEN position = 1 THEN 1 END)
FROM ra_mst_runners r
JOIN ra_mst_races rc ON rc.race_id = r.race_id
WHERE jockey_id = 'jky_250764'
GROUP BY surface;

-- Win rate by distance band
SELECT
    CASE
        WHEN distance_meters < 1200 THEN 'Sprint (< 6f)'
        WHEN distance_meters BETWEEN 1200 AND 2000 THEN 'Mile (6f-10f)'
        ELSE 'Distance (> 10f)'
    END as distance_band,
    COUNT(*) as rides,
    COUNT(CASE WHEN position = 1 THEN 1 END) as wins
FROM ra_mst_runners r
JOIN ra_mst_races rc ON rc.race_id = r.race_id
WHERE r.jockey_id = 'jky_250764'
GROUP BY distance_band;
```

**Implementation Effort:** Medium
**Value:** High for ML models
**Rate Limit Impact:** None

---

#### B. Partnership Analysis
**What:** Identify successful jockey-trainer and jockey-horse partnerships

**Implementation:**
```sql
-- Best trainer partnerships
SELECT
    r.jockey_id,
    r.trainer_id,
    COUNT(*) as rides_together,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins_together,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as partnership_win_rate
FROM ra_mst_runners r
WHERE r.jockey_id = 'jky_250764'
GROUP BY r.jockey_id, r.trainer_id
HAVING COUNT(*) >= 5  -- Minimum 5 rides together
ORDER BY partnership_win_rate DESC;

-- Best horse partnerships
SELECT
    r.jockey_id,
    r.horse_id,
    h.name as horse_name,
    COUNT(*) as rides_together,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins_together,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as partnership_win_rate
FROM ra_mst_runners r
JOIN ra_horses h ON h.horse_id = r.horse_id
WHERE r.jockey_id = 'jky_250764'
GROUP BY r.jockey_id, r.horse_id, h.name
HAVING COUNT(*) >= 3
ORDER BY wins_together DESC;
```

**Implementation Effort:** Medium
**Value:** Medium-High
**Rate Limit Impact:** None

---

### Priority 3: Future Enhancements

#### A. External Data Integration
**Potential Sources:**
- Racing Post API (if available)
- British Horseracing Authority (BHA) data
- Professional Jockeys Association (PJA)
- Wikipedia / Wikidata

**Fields We Could Add:**
- Date of birth
- Nationality
- Debut date
- Biography
- Championship titles
- Major race wins
- Profile images

**Implementation Effort:** High (legal, technical, maintenance)
**Value:** Medium (nice-to-have, not critical for predictions)

---

## Section 8: Current System Assessment

### What's Working Well

✅ **Entity Extraction**
- `EntityExtractor` successfully captures jockey data from runners
- Basic identification (id, name) working perfectly
- Jockey claim field captured

✅ **Statistics Calculation**
- Migration 007 provides excellent foundation
- Career statistics (wins, places, win rate) implemented
- Database view and update function working

✅ **Data Discovery**
- Jockeys discovered through race participation
- No need for bulk listing (which API doesn't support anyway)
- Automatic capture of active jockeys

---

### What's Missing

❌ **Jockey Allowance Field**
- **Field:** `jockey_allowance` or `apprentice_allowance`
- **Available In:** Racecards API (sometimes)
- **Currently Captured:** ❌ No
- **Fix:** Add to runner transformation in `races_fetcher.py`

**Code Change Needed:**
```python
# In races_fetcher.py, _transform_racecard() method
runner_record = {
    # ... existing fields ...
    'jockey_claim': runner.get('jockey_claim'),
    'apprentice_allowance': runner.get('jockey_allowance'),  # ADD THIS
    # ... rest of fields ...
}
```

❌ **Recent Form Statistics**
- No 14-day / 30-day statistics
- No "last ride date" tracking
- No activity flags

**Fix:** Extend migration 007 or create new migration 011

❌ **Contextual Statistics**
- No win rates by context (surface, distance, class)
- No partnership analysis built in

**Fix:** Create ra_jockey_context_stats table or materialized views

---

## Section 9: Recommendations

### Immediate Actions (This Sprint)

#### 1. Capture Missing API Field
**Task:** Add `apprentice_allowance` to runner extraction

**Files to Modify:**
- `fetchers/races_fetcher.py` - Add field to transformation
- `fetchers/results_fetcher.py` - Add field to transformation

**Effort:** 5 minutes
**Value:** Complete API data capture
**Risk:** None

---

#### 2. Implement Recent Form Statistics
**Task:** Add 14-day and 30-day statistics to ra_jockeys

**Files to Create:**
- `migrations/011_add_jockey_recent_form_stats.sql`

**Files to Modify:**
- `migrations/007_add_entity_table_enhancements.sql` (extend function)

**Effort:** 1-2 hours
**Value:** High (shows current form vs. career)
**Risk:** Low

**SQL Template:**
```sql
-- Add recent form fields
ALTER TABLE ra_jockeys
ADD COLUMN recent_14d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN recent_30d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN last_ride_date DATE DEFAULT NULL,
ADD COLUMN days_since_last_ride INTEGER DEFAULT NULL,
ADD COLUMN active_last_30d BOOLEAN DEFAULT FALSE;

-- Update view to include recent stats
-- (Modify existing jockey_statistics view)

-- Update function to calculate recent stats
-- (Modify existing update_entity_statistics() function)
```

---

#### 3. Add Prize Money Tracking
**Task:** Calculate and store prize money won

**Effort:** 30 minutes
**Value:** Medium-High
**Risk:** Low

---

### Medium-Term Actions (Next Month)

#### 4. Build Contextual Statistics System
**Options:**
1. **Materialized Views** (recommended for performance)
2. **Separate Stats Table** (recommended for flexibility)
3. **On-Demand Queries** (simplest, but slower)

**Recommendation:** Create `ra_jockey_context_stats` table

**Effort:** 4-6 hours
**Value:** Very High for ML models
**Risk:** Low

---

#### 5. Create Partnership Analysis Views
**Task:** Build views for jockey-trainer and jockey-horse partnerships

**Effort:** 2-3 hours
**Value:** High for insights
**Risk:** Low

---

### Long-Term Considerations

#### 6. External Data Integration
**Only if needed for:**
- Public-facing jockey profiles
- Biographical content
- Media assets

**NOT needed for:**
- Prediction models
- Statistical analysis
- Performance tracking

**Decision:** **DEFER** until specific use case identified

---

## Section 10: Code Examples

### Example 1: Extend Statistics Update Function

```sql
-- In migrations/011_add_jockey_recent_form.sql

-- Modify existing update function
CREATE OR REPLACE FUNCTION update_entity_statistics()
RETURNS TABLE(
    jockeys_updated INTEGER,
    trainers_updated INTEGER,
    owners_updated INTEGER
) AS $$
DECLARE
    jockey_count INTEGER;
    trainer_count INTEGER;
    owner_count INTEGER;
BEGIN
    -- Update jockey statistics (EXTENDED)
    UPDATE ra_jockeys j
    SET
        -- Career stats (existing)
        total_rides = s.calculated_total_rides,
        total_wins = s.calculated_total_wins,
        total_places = s.calculated_total_places,
        total_seconds = s.calculated_total_seconds,
        total_thirds = s.calculated_total_thirds,
        win_rate = s.calculated_win_rate,
        place_rate = s.calculated_place_rate,

        -- NEW: Recent form stats
        recent_14d_rides = (
            SELECT COUNT(*)
            FROM ra_mst_runners r
            JOIN ra_mst_races rc ON rc.race_id = r.race_id
            WHERE r.jockey_id = j.jockey_id
              AND rc.race_date >= CURRENT_DATE - INTERVAL '14 days'
              AND r.position IS NOT NULL
        ),
        recent_14d_wins = (
            SELECT COUNT(*)
            FROM ra_mst_runners r
            JOIN ra_mst_races rc ON rc.race_id = r.race_id
            WHERE r.jockey_id = j.jockey_id
              AND rc.race_date >= CURRENT_DATE - INTERVAL '14 days'
              AND r.position = 1
        ),
        recent_30d_rides = (
            SELECT COUNT(*)
            FROM ra_mst_runners r
            JOIN ra_mst_races rc ON rc.race_id = r.race_id
            WHERE r.jockey_id = j.jockey_id
              AND rc.race_date >= CURRENT_DATE - INTERVAL '30 days'
              AND r.position IS NOT NULL
        ),
        recent_30d_wins = (
            SELECT COUNT(*)
            FROM ra_mst_runners r
            JOIN ra_mst_races rc ON rc.race_id = r.race_id
            WHERE r.jockey_id = j.jockey_id
              AND rc.race_date >= CURRENT_DATE - INTERVAL '30 days'
              AND r.position = 1
        ),
        last_ride_date = (
            SELECT MAX(rc.race_date)
            FROM ra_mst_runners r
            JOIN ra_mst_races rc ON rc.race_id = r.race_id
            WHERE r.jockey_id = j.jockey_id
        ),

        stats_updated_at = NOW()
    FROM jockey_statistics s
    WHERE j.jockey_id = s.jockey_id;

    -- Calculate derived fields
    UPDATE ra_jockeys
    SET
        recent_14d_win_rate = ROUND(100.0 * recent_14d_wins / NULLIF(recent_14d_rides, 0), 2),
        recent_30d_win_rate = ROUND(100.0 * recent_30d_wins / NULLIF(recent_30d_rides, 0), 2),
        days_since_last_ride = CURRENT_DATE - last_ride_date,
        active_last_30d = (last_ride_date >= CURRENT_DATE - INTERVAL '30 days')
    WHERE stats_updated_at = NOW();  -- Only update rows we just modified

    GET DIAGNOSTICS jockey_count = ROW_COUNT;

    -- (trainers and owners updates unchanged)
    -- ...

    RETURN QUERY SELECT jockey_count, trainer_count, owner_count;
END;
$$ LANGUAGE plpgsql;
```

---

### Example 2: Contextual Statistics Table

```sql
-- Create contextual statistics table
CREATE TABLE ra_jockey_context_stats (
    stat_id SERIAL PRIMARY KEY,
    jockey_id VARCHAR(50) REFERENCES ra_jockeys(jockey_id) ON DELETE CASCADE,
    context_type VARCHAR(20) NOT NULL,  -- 'surface', 'distance', 'class', 'going', 'course'
    context_value VARCHAR(50) NOT NULL, -- Actual value for that context
    total_rides INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_places INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    place_rate DECIMAL(5,2),
    avg_finishing_position DECIMAL(5,2),
    stats_updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(jockey_id, context_type, context_value)
);

-- Create indexes
CREATE INDEX idx_jockey_context_jockey ON ra_jockey_context_stats(jockey_id);
CREATE INDEX idx_jockey_context_type ON ra_jockey_context_stats(context_type);
CREATE INDEX idx_jockey_context_value ON ra_jockey_context_stats(context_value);
CREATE INDEX idx_jockey_context_win_rate ON ra_jockey_context_stats(win_rate) WHERE win_rate IS NOT NULL;

-- Function to populate contextual stats
CREATE OR REPLACE FUNCTION update_jockey_context_statistics()
RETURNS INTEGER AS $$
DECLARE
    rows_inserted INTEGER := 0;
BEGIN
    -- Clear existing stats
    TRUNCATE ra_jockey_context_stats;

    -- Surface statistics
    INSERT INTO ra_jockey_context_stats (jockey_id, context_type, context_value, total_rides, total_wins, total_places, win_rate, place_rate, avg_finishing_position)
    SELECT
        r.jockey_id,
        'surface' as context_type,
        rc.surface as context_value,
        COUNT(*) as total_rides,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
        COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
        ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as win_rate,
        ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as place_rate,
        ROUND(AVG(r.position), 2) as avg_finishing_position
    FROM ra_mst_runners r
    JOIN ra_mst_races rc ON rc.race_id = r.race_id
    WHERE r.position IS NOT NULL AND rc.surface IS NOT NULL
    GROUP BY r.jockey_id, rc.surface
    HAVING COUNT(*) >= 5;  -- Minimum 5 rides for statistical significance

    GET DIAGNOSTICS rows_inserted = ROW_COUNT;

    -- Distance band statistics
    INSERT INTO ra_jockey_context_stats (jockey_id, context_type, context_value, total_rides, total_wins, total_places, win_rate, place_rate, avg_finishing_position)
    SELECT
        r.jockey_id,
        'distance' as context_type,
        CASE
            WHEN rc.distance_meters < 1200 THEN 'Sprint (<6f)'
            WHEN rc.distance_meters BETWEEN 1200 AND 1609 THEN 'Mile (6f-8f)'
            WHEN rc.distance_meters BETWEEN 1610 AND 2400 THEN 'Middle (8f-12f)'
            ELSE 'Distance (>12f)'
        END as context_value,
        COUNT(*) as total_rides,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
        COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
        ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as win_rate,
        ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as place_rate,
        ROUND(AVG(r.position), 2) as avg_finishing_position
    FROM ra_mst_runners r
    JOIN ra_mst_races rc ON rc.race_id = r.race_id
    WHERE r.position IS NOT NULL AND rc.distance_meters IS NOT NULL
    GROUP BY r.jockey_id, context_value
    HAVING COUNT(*) >= 5;

    -- Class statistics
    INSERT INTO ra_jockey_context_stats (jockey_id, context_type, context_value, total_rides, total_wins, total_places, win_rate, place_rate, avg_finishing_position)
    SELECT
        r.jockey_id,
        'class' as context_type,
        rc.race_class as context_value,
        COUNT(*) as total_rides,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
        COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
        ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as win_rate,
        ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as place_rate,
        ROUND(AVG(r.position), 2) as avg_finishing_position
    FROM ra_mst_runners r
    JOIN ra_mst_races rc ON rc.race_id = r.race_id
    WHERE r.position IS NOT NULL AND rc.race_class IS NOT NULL
    GROUP BY r.jockey_id, rc.race_class
    HAVING COUNT(*) >= 5;

    -- Going statistics
    INSERT INTO ra_jockey_context_stats (jockey_id, context_type, context_value, total_rides, total_wins, total_places, win_rate, place_rate, avg_finishing_position)
    SELECT
        r.jockey_id,
        'going' as context_type,
        rc.going as context_value,
        COUNT(*) as total_rides,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
        COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
        ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as win_rate,
        ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as place_rate,
        ROUND(AVG(r.position), 2) as avg_finishing_position
    FROM ra_mst_runners r
    JOIN ra_mst_races rc ON rc.race_id = r.race_id
    WHERE r.position IS NOT NULL AND rc.going IS NOT NULL
    GROUP BY r.jockey_id, rc.going
    HAVING COUNT(*) >= 5;

    RETURN rows_inserted;
END;
$$ LANGUAGE plpgsql;
```

**Query Examples:**
```sql
-- Get jockey's performance on different surfaces
SELECT *
FROM ra_jockey_context_stats
WHERE jockey_id = 'jky_250764'
  AND context_type = 'surface'
ORDER BY win_rate DESC;

-- Find jockeys who perform best on All-Weather
SELECT j.name, cs.win_rate, cs.total_rides
FROM ra_jockey_context_stats cs
JOIN ra_jockeys j ON j.jockey_id = cs.jockey_id
WHERE cs.context_type = 'surface'
  AND cs.context_value = 'AW'
  AND cs.total_rides >= 20
ORDER BY cs.win_rate DESC
LIMIT 10;

-- Compare jockey's performance across distance bands
SELECT context_value, total_rides, win_rate, place_rate
FROM ra_jockey_context_stats
WHERE jockey_id = 'jky_250764'
  AND context_type = 'distance'
ORDER BY context_value;
```

---

### Example 3: Partnership Analysis View

```sql
-- Create view for jockey-trainer partnerships
CREATE OR REPLACE VIEW jockey_trainer_partnerships AS
SELECT
    r.jockey_id,
    j.name as jockey_name,
    r.trainer_id,
    t.name as trainer_name,
    COUNT(*) as rides_together,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins_together,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as places_together,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as partnership_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as partnership_place_rate,
    MAX(rc.race_date) as last_ride_together,
    MIN(rc.race_date) as first_ride_together
FROM ra_mst_runners r
JOIN ra_jockeys j ON j.jockey_id = r.jockey_id
JOIN ra_trainers t ON t.trainer_id = r.trainer_id
JOIN ra_mst_races rc ON rc.race_id = r.race_id
WHERE r.position IS NOT NULL
GROUP BY r.jockey_id, j.name, r.trainer_id, t.name
HAVING COUNT(*) >= 5;  -- Minimum 5 rides together

COMMENT ON VIEW jockey_trainer_partnerships IS 'Jockey-trainer partnership statistics (min 5 rides together)';

-- Create view for jockey-horse partnerships
CREATE OR REPLACE VIEW jockey_horse_partnerships AS
SELECT
    r.jockey_id,
    j.name as jockey_name,
    r.horse_id,
    h.name as horse_name,
    COUNT(*) as rides_together,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins_together,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as places_together,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / COUNT(*), 2) as partnership_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / COUNT(*), 2) as partnership_place_rate,
    MAX(rc.race_date) as last_ride_together,
    MIN(rc.race_date) as first_ride_together,
    CURRENT_DATE - MAX(rc.race_date) as days_since_last_ride
FROM ra_mst_runners r
JOIN ra_jockeys j ON j.jockey_id = r.jockey_id
JOIN ra_horses h ON h.horse_id = r.horse_id
JOIN ra_mst_races rc ON rc.race_id = r.race_id
WHERE r.position IS NOT NULL
GROUP BY r.jockey_id, j.name, r.horse_id, h.name
HAVING COUNT(*) >= 3;  -- Minimum 3 rides together

COMMENT ON VIEW jockey_horse_partnerships IS 'Jockey-horse partnership statistics (min 3 rides together)';
```

**Query Examples:**
```sql
-- Find jockey's best trainer partnerships
SELECT *
FROM jockey_trainer_partnerships
WHERE jockey_id = 'jky_250764'
ORDER BY partnership_win_rate DESC, rides_together DESC;

-- Find trainer's preferred jockeys
SELECT *
FROM jockey_trainer_partnerships
WHERE trainer_id = 'trn_234891'
  AND rides_together >= 10
ORDER BY partnership_win_rate DESC;

-- Identify successful jockey-horse partnerships
SELECT *
FROM jockey_horse_partnerships
WHERE wins_together >= 2
ORDER BY partnership_win_rate DESC, wins_together DESC
LIMIT 50;
```

---

## Section 11: Testing Strategy

### Unit Tests Needed

```python
# tests/test_jockey_statistics.py

import pytest
from datetime import datetime, timedelta
from utils.supabase_client import SupabaseReferenceClient

class TestJockeyStatistics:
    """Test jockey statistics calculation"""

    def test_career_statistics_calculation(self, db_client):
        """Test that career statistics are calculated correctly"""
        # Create test jockey
        jockey_id = "test_jky_001"
        db_client.insert_jockeys([{
            'jockey_id': jockey_id,
            'name': 'Test Jockey',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }])

        # Create test runners with various positions
        runners = [
            # 3 wins
            {'jockey_id': jockey_id, 'position': 1},
            {'jockey_id': jockey_id, 'position': 1},
            {'jockey_id': jockey_id, 'position': 1},
            # 2 seconds
            {'jockey_id': jockey_id, 'position': 2},
            {'jockey_id': jockey_id, 'position': 2},
            # 1 third
            {'jockey_id': jockey_id, 'position': 3},
            # 4 unplaced
            {'jockey_id': jockey_id, 'position': 5},
            {'jockey_id': jockey_id, 'position': 7},
            {'jockey_id': jockey_id, 'position': 10},
            {'jockey_id': jockey_id, 'position': 12},
        ]
        # Insert runners (with proper race_id, etc.)
        # ...

        # Run statistics update
        db_client.client.rpc('update_entity_statistics').execute()

        # Verify statistics
        jockey = db_client.client.table('ra_jockeys').select('*').eq('jockey_id', jockey_id).single().execute()

        assert jockey.data['total_rides'] == 10
        assert jockey.data['total_wins'] == 3
        assert jockey.data['total_places'] == 6  # 3+2+1
        assert jockey.data['win_rate'] == 30.0  # 3/10 * 100
        assert jockey.data['place_rate'] == 60.0  # 6/10 * 100

    def test_recent_form_statistics(self, db_client):
        """Test that recent form statistics are calculated correctly"""
        jockey_id = "test_jky_002"

        # Create rides across different date ranges
        today = datetime.utcnow().date()

        rides = [
            # Recent wins (last 14 days)
            {'date': today - timedelta(days=5), 'position': 1},
            {'date': today - timedelta(days=10), 'position': 1},
            # Recent rides outside 14 days but within 30
            {'date': today - timedelta(days=20), 'position': 1},
            {'date': today - timedelta(days=25), 'position': 5},
            # Old rides (> 30 days)
            {'date': today - timedelta(days=40), 'position': 1},
            {'date': today - timedelta(days=60), 'position': 1},
        ]

        # Insert test data
        # ...

        # Run statistics update
        db_client.client.rpc('update_entity_statistics').execute()

        # Verify recent form stats
        jockey = db_client.client.table('ra_jockeys').select('*').eq('jockey_id', jockey_id).single().execute()

        assert jockey.data['recent_14d_rides'] == 2
        assert jockey.data['recent_14d_wins'] == 2
        assert jockey.data['recent_14d_win_rate'] == 100.0
        assert jockey.data['recent_30d_rides'] == 4
        assert jockey.data['recent_30d_wins'] == 3
        assert jockey.data['recent_30d_win_rate'] == 75.0
        assert jockey.data['active_last_30d'] == True

    def test_contextual_statistics(self, db_client):
        """Test contextual statistics (surface, distance, class)"""
        jockey_id = "test_jky_003"

        # Create rides on different surfaces
        rides = [
            # AW: 2 rides, 1 win
            {'surface': 'AW', 'position': 1},
            {'surface': 'AW', 'position': 5},
            # Turf: 3 rides, 2 wins
            {'surface': 'Turf', 'position': 1},
            {'surface': 'Turf', 'position': 1},
            {'surface': 'Turf', 'position': 4},
        ]

        # Insert test data
        # ...

        # Run contextual statistics update
        db_client.client.rpc('update_jockey_context_statistics').execute()

        # Verify contextual stats
        aw_stats = db_client.client.table('ra_jockey_context_stats')\
            .select('*')\
            .eq('jockey_id', jockey_id)\
            .eq('context_type', 'surface')\
            .eq('context_value', 'AW')\
            .single()\
            .execute()

        assert aw_stats.data['total_rides'] == 2
        assert aw_stats.data['total_wins'] == 1
        assert aw_stats.data['win_rate'] == 50.0

        turf_stats = db_client.client.table('ra_jockey_context_stats')\
            .select('*')\
            .eq('jockey_id', jockey_id)\
            .eq('context_type', 'surface')\
            .eq('context_value', 'Turf')\
            .single()\
            .execute()

        assert turf_stats.data['total_rides'] == 3
        assert turf_stats.data['total_wins'] == 2
        assert turf_stats.data['win_rate'] == 66.67
```

---

## Section 12: Performance Considerations

### Database Indexing

**Current Indexes (from Migration 007):**
```sql
CREATE INDEX IF NOT EXISTS idx_jockeys_win_rate ON ra_jockeys(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_total_rides ON ra_jockeys(total_rides) WHERE total_rides IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_stats_updated ON ra_jockeys(stats_updated_at);
```

**Recommended Additional Indexes:**
```sql
-- For recent form queries
CREATE INDEX IF NOT EXISTS idx_jockeys_recent_win_rate ON ra_jockeys(recent_14d_win_rate) WHERE recent_14d_win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_active ON ra_jockeys(active_last_30d) WHERE active_last_30d = TRUE;
CREATE INDEX IF NOT EXISTS idx_jockeys_last_ride ON ra_jockeys(last_ride_date DESC);

-- For runner lookups
CREATE INDEX IF NOT EXISTS idx_runners_jockey_position ON ra_mst_runners(jockey_id, position) WHERE position IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_runners_jockey_race ON ra_mst_runners(jockey_id, race_id);

-- For contextual stats
CREATE INDEX IF NOT EXISTS idx_context_stats_lookup ON ra_jockey_context_stats(jockey_id, context_type, context_value);
```

---

### Statistics Update Frequency

**Recommendations:**

1. **Career Statistics:** Update daily (after results fetching)
2. **Recent Form Statistics:** Update daily (critical for form tracking)
3. **Contextual Statistics:** Update weekly (computationally expensive)
4. **Partnership Analysis:** Update weekly

**Scheduled Jobs:**
```bash
# Daily at 02:00 (after results fetch at 01:00)
0 2 * * * psql $SUPABASE_URL -c "SELECT * FROM update_entity_statistics();"

# Weekly on Sunday at 03:00
0 3 * * 0 psql $SUPABASE_URL -c "SELECT update_jockey_context_statistics();"
```

---

### Query Performance

**Expected Query Times (with proper indexes):**

- Jockey career stats: < 10ms
- Recent form stats: < 50ms
- Contextual stats (single jockey): < 100ms
- Partnership analysis: < 200ms
- Bulk statistics update: 10-30 seconds (depends on data volume)

**Optimization Tips:**
1. Use partial indexes (WHERE clauses) for common queries
2. Materialized views for expensive aggregations
3. Denormalized stats tables for fast lookups
4. Batch updates during low-traffic hours

---

## Section 13: Summary & Action Plan

### Key Findings

1. ✅ **API Provides Minimal Jockey Data**
   - Only 3 fields: id, name, claim (allowance sometimes)
   - No profile, biography, or statistics endpoints
   - No individual jockey detail endpoint exists

2. ✅ **Database Aggregation is Primary Enrichment Method**
   - All meaningful jockey statistics calculated from ra_mst_runners
   - Migration 007 provides excellent foundation
   - Partnership and contextual analysis possible through joins

3. ❌ **Small Gap: Missing apprentice_allowance Field**
   - Available in API responses
   - Not currently captured
   - Easy 5-minute fix

4. ⚠️ **Medium Gap: No Recent Form Tracking**
   - 14-day and 30-day statistics not tracked
   - Last ride date not tracked
   - Activity status not tracked
   - Medium effort (2-3 hours) to implement

5. ⚠️ **Large Gap: No Contextual Statistics**
   - Win rates by surface, distance, class not calculated
   - Partnership analysis not built-in
   - Higher effort (4-6 hours) but high value

---

### Immediate Actions (Today/Tomorrow)

| Priority | Task | Effort | Impact | Files |
|----------|------|--------|--------|-------|
| P1 | Capture `apprentice_allowance` field | 5 min | Low | `fetchers/races_fetcher.py`, `fetchers/results_fetcher.py` |
| P1 | Document current jockey extraction | 30 min | High | This document |

---

### Short-Term Actions (This Week)

| Priority | Task | Effort | Impact | Files |
|----------|------|--------|--------|-------|
| P1 | Add recent form statistics | 2-3 hrs | High | `migrations/011_add_jockey_recent_form.sql` |
| P1 | Add prize money tracking | 30 min | Medium | Extend migration 011 |
| P2 | Add activity tracking fields | 1 hr | Medium | Extend migration 011 |

---

### Medium-Term Actions (This Month)

| Priority | Task | Effort | Impact | Files |
|----------|------|--------|--------|-------|
| P2 | Create contextual statistics table | 4-6 hrs | Very High | `migrations/012_add_context_stats.sql` |
| P2 | Build partnership analysis views | 2-3 hrs | High | `migrations/013_add_partnership_views.sql` |
| P3 | Create automated testing | 3-4 hrs | Medium | `tests/test_jockey_statistics.py` |

---

### Long-Term Considerations

| Priority | Task | Effort | Impact | Decision |
|----------|------|--------|--------|----------|
| P4 | External data integration | High | Low-Medium | DEFER until specific need identified |
| P4 | Profile images & media | Medium | Low | DEFER (not needed for predictions) |
| P4 | Biographical content | High | Low | DEFER (not needed for core functionality) |

---

## Conclusion

**The Racing API provides minimal jockey-specific data.** All meaningful jockey enrichment must come from aggregating race participation data (ra_mst_runners). The good news: we already have:

1. ✅ Solid foundation (Migration 007)
2. ✅ All necessary raw data (ra_mst_runners with jockey context)
3. ✅ Working extraction and storage

**Quick wins available:**
1. Capture missing `apprentice_allowance` field (5 min)
2. Add recent form statistics (2-3 hours)
3. Add contextual statistics (4-6 hours)

**These enhancements will provide:**
- Complete API data capture
- Current form vs. career performance tracking
- Context-aware statistics (surface, distance, class)
- Partnership analysis (jockey-trainer, jockey-horse)

**NO external APIs or web scraping needed for core functionality.**

---

## Appendices

### Appendix A: Full API Response Sample (Results Runner)

```json
{
  "horse_id": "hrs_30455194",
  "horse": "Create (IRE)",
  "sp": "9/4",
  "sp_dec": "3.25",
  "number": "7",
  "position": "1",
  "draw": "8",
  "btn": "0",
  "ovr_btn": "0",
  "age": "5",
  "sex": "M",
  "weight": "8-10",
  "weight_lbs": "122",
  "headgear": "p",
  "time": "1:43.25",
  "or": "47",
  "rpr": "57",
  "tsr": "2",
  "prize": "3245.08",
  "jockey": "Kieran O'Neill",
  "jockey_claim_lbs": "0",
  "jockey_id": "jky_250764",
  "trainer": "Scott Dixon",
  "trainer_id": "trn_234891",
  "owner": "Dixon Wylam M Baldry Js Harrod",
  "owner_id": "own_1309284",
  "sire": "Harry Angel (IRE)",
  "sire_id": "sir_7013188",
  "dam": "Patent Joy (IRE)",
  "dam_id": "dam_5801159",
  "damsire": "Pivotal",
  "damsire_id": "dsi_753900",
  "comment": "Held up in rear - in touch with leaders after 3f - headway to lead over 1f out - edged left but kept on well inside final furlong(tchd 5/2)",
  "silk_url": "https://www.rp-assets.com/svg/1/2/3/327321.svg"
}
```

**Jockey-specific fields:** `jockey`, `jockey_id`, `jockey_claim_lbs`
**That's it.** No other jockey data in API responses.

---

### Appendix B: Database Schema Reference

**ra_jockeys table (current):**
```sql
CREATE TABLE ra_jockeys (
    jockey_id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,

    -- Career Statistics (Migration 007)
    total_rides INTEGER DEFAULT NULL,
    total_wins INTEGER DEFAULT NULL,
    total_places INTEGER DEFAULT NULL,
    total_seconds INTEGER DEFAULT NULL,
    total_thirds INTEGER DEFAULT NULL,
    win_rate DECIMAL(5,2) DEFAULT NULL,
    place_rate DECIMAL(5,2) DEFAULT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    stats_updated_at TIMESTAMP DEFAULT NULL
);
```

**Recommended additions (Migration 011):**
```sql
ALTER TABLE ra_jockeys
ADD COLUMN recent_14d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN recent_30d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN last_ride_date DATE DEFAULT NULL,
ADD COLUMN days_since_last_ride INTEGER DEFAULT NULL,
ADD COLUMN active_last_30d BOOLEAN DEFAULT FALSE,
ADD COLUMN total_prize_money DECIMAL(12,2) DEFAULT NULL,
ADD COLUMN recent_30d_prize_money DECIMAL(12,2) DEFAULT NULL;
```

---

### Appendix C: Related Documentation

**Existing Documentation:**
- `/docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md` - Full endpoint testing results
- `/docs/audit/DATABASE_SCHEMA_AUDIT_DETAILED.md` - Schema documentation
- `/migrations/007_add_entity_table_enhancements.sql` - Current statistics implementation

**This Document:**
- `/docs/api/JOCKEY_DATA_ENRICHMENT_RESEARCH.md` - YOU ARE HERE

---

**Report Complete.**
**Next Steps:** Review recommendations and prioritize implementation.
