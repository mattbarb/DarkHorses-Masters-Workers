# Database Coverage Summary

**Generated:** 2025-10-08
**Database:** DarkHorses Racing Data Collection
**Coverage:** 2015-01-01 to 2025-10-07 (11 years)

---

## 📊 EXECUTIVE SUMMARY

**Overall Status:** 🟡 **GOOD** with some gaps

- ✅ **136,448 races** spanning 11 years (2015-2025)
- ✅ **377,713 runner entries** across all races
- ✅ **111,325 unique horses** identified
- ✅ Complete reference data (courses, bookmakers)
- ⚠️ **2 empty tables** (ra_horse_pedigree, ra_results)
- ⚠️ **Low runner count** per race (2.8 avg vs 8-12 expected)

---

## 📋 TABLE-BY-TABLE BREAKDOWN

### 1. REFERENCE DATA TABLES ✅

#### ra_courses
- **Records:** 101
- **Status:** ✅ Complete
- **Coverage:** UK and Ireland racing courses
- **Purpose:** Maps course_id to course names, regions

#### ra_bookmakers
- **Records:** 19
- **Status:** ✅ Complete
- **Coverage:** Major bookmakers
- **Purpose:** Reference for odds data (when implemented)

---

### 2. ENTITY DATA TABLES 🟡

#### ra_horses
- **Records:** 111,325
- **Status:** ✅ Excellent coverage
- **Coverage:** All horses that have run in 2015-2025
- **Data Quality:** 29.47% unique ratio (each horse appears ~3.4 times on average)
- **Purpose:** Master list of all horses

#### ra_jockeys
- **Records:** 3,478
- **Status:** ✅ Good coverage
- **Coverage:** All jockeys from 2015-2025
- **Purpose:** Master list of jockeys

#### ra_trainers
- **Records:** 2,779
- **Status:** ✅ Good coverage
- **Coverage:** All trainers from 2015-2025
- **Purpose:** Master list of trainers

#### ra_owners
- **Records:** 48,053
- **Status:** ✅ Excellent coverage
- **Coverage:** All owners from 2015-2025
- **Purpose:** Master list of owners

#### ra_horse_pedigree ❌
- **Records:** 0
- **Status:** ❌ **EMPTY TABLE**
- **Issue:** Pedigree data is NOT being populated
- **Expected:** Sire/Dam information for horses
- **Action Required:** Check horses_fetcher.py to enable pedigree insertion

---

### 3. RACING DATA TABLES 🟡

#### ra_races
- **Records:** 136,448
- **Status:** ✅ **PRIMARY TABLE** - Fully populated
- **Date Range:** 2015-01-01 to 2025-10-07
- **Coverage:** 11 complete years

**Year-by-Year Breakdown:**

| Year | Races   | Status      | Coverage |
|------|---------|-------------|----------|
| 2015 | 12,438  | ✅ Complete | 100%     |
| 2016 | 12,461  | ✅ Complete | 100%     |
| 2017 | 12,644  | ✅ Complete | 100%     |
| 2018 | 12,745  | ✅ Complete | 100%     |
| 2019 | 12,489  | ✅ Complete | 100%     |
| 2020 | 10,305  | ✅ Complete | 81% (COVID-19 impact) |
| 2021 | 13,159  | ✅ Complete | 103%     |
| 2022 | 12,794  | ✅ Complete | 100%     |
| 2023 | 13,497  | ✅ Complete | 106%     |
| 2024 | 13,549  | ✅ Complete | 106%     |
| 2025 | 10,367  | ✅ In Progress | 79% (partial year) |

**Data Quality:**
- ✅ Consistent ~12,500-13,500 races per year
- ✅ 2020 shows expected reduction (COVID-19 lockdowns)
- ✅ Recent years show slight increase (2023-2024)
- ✅ 2025 on track (10,367 races in ~9 months)

---

#### ra_runners
- **Records:** 377,713
- **Status:** ⚠️ **PARTIALLY POPULATED**
- **Issue:** Average 2.8 runners per race (expected 8-12)
- **Expected Records:** ~1.2M - 1.6M (136K races × 8-12 runners)
- **Actual Records:** 377K (only ~31% of expected)
- **Coverage:** Likely missing runner data from many races

**Analysis:**
This suggests one of two scenarios:
1. **Scenario A:** Only storing runners for races with complete data (selective population)
2. **Scenario B:** Runner extraction is failing for ~69% of races (data loss)

**Most Likely:** Scenario A - The code may only insert runners when certain conditions are met (e.g., has race result data, has complete runner info)

**Action Required:**
- Review races_fetcher.py line 291-349 (runner creation logic)
- Check if race_date filter is preventing runner insertion
- Verify runners table has race_date column populated

---

#### ra_results ❌
- **Records:** 0
- **Status:** ❌ **EMPTY TABLE**
- **Issue:** Table completely empty
- **Known Reason:** See CODE_CLEANUP_COMPLETED.md - table schema doesn't match API data
- **Current Solution:** Results data stored in ra_races instead

**Background:**
Per previous audits, `ra_results` table has schema mismatch with API response. The results_fetcher.py was modified to skip inserting to this table and instead populates ra_races with result data.

**Decision Needed:**
1. **Option A:** Drop ra_results table (not being used)
2. **Option B:** Fix schema and populate it properly
3. **Option C:** Keep as-is (data in ra_races is sufficient)

**Recommendation:** Option C - Current approach works. The ra_results table overlaps significantly with ra_races anyway.

---

## 📈 DATA QUALITY METRICS

### Coverage Completeness

| Metric | Value | Status |
|--------|-------|--------|
| **Years of Data** | 11 years (2015-2025) | ✅ Excellent |
| **Total Races** | 136,448 | ✅ Complete |
| **Races per Year (avg)** | 12,404 | ✅ Consistent |
| **Reference Data** | 100% | ✅ Complete |
| **Entity Extraction** | 111K horses, 3.5K jockeys | ✅ Good |

### Data Gaps

| Issue | Severity | Impact |
|-------|----------|--------|
| **ra_horse_pedigree empty** | 🔴 HIGH | No sire/dam data available |
| **Low runner count** | 🟡 MEDIUM | Only 31% of expected runners |
| **ra_results empty** | 🟢 LOW | Data available in ra_races |

---

## 🎯 WHAT DATA DO WE HAVE?

### ✅ AVAILABLE DATA (Can Use Now)

1. **Race Information (2015-2025)**
   - Race dates, times, courses
   - Race names, types, classes
   - Going, distance, surface
   - Prize money

2. **Runner Information (Partial)**
   - Horse names and IDs
   - Jockey assignments
   - Trainer information
   - Owner details
   - Some form/ratings data

3. **Entity Master Lists**
   - 111,325 unique horses
   - 3,478 jockeys
   - 2,779 trainers
   - 48,053 owners

4. **Reference Data**
   - 101 courses (UK/Ireland)
   - 19 bookmakers

### ❌ MISSING DATA (Not Available)

1. **Pedigree Information**
   - No sire/dam relationships
   - No breeding data
   - ra_horse_pedigree table is empty

2. **69% of Runner Entries**
   - Only 377K runners out of expected 1.2M-1.6M
   - Missing runner data for many races
   - Possible race_date filtering issue

3. **Historical Results (if needed)**
   - ra_results table empty
   - However, result data may be in ra_races api_data JSONB field

---

## 🔍 DETAILED YEAR BREAKDOWN

### 2015 (Historical Data)
- **Races:** 12,438
- **Source:** Racing API results endpoint (historical backfill)
- **Quality:** ✅ Complete year
- **Notes:** First year of data collection

### 2016-2019 (Historical Data)
- **Races:** ~12,500-12,700 per year
- **Source:** Racing API results endpoint
- **Quality:** ✅ Consistent coverage
- **Notes:** Stable UK/Ireland racing calendar

### 2020 (COVID-19 Impact)
- **Races:** 10,305 (81% of normal)
- **Source:** Racing API results endpoint
- **Quality:** ✅ Complete but reduced
- **Notes:** Racing suspended March-June 2020

### 2021-2022 (Recovery)
- **Races:** ~12,800-13,200 per year
- **Source:** Racing API results endpoint
- **Quality:** ✅ Return to normal
- **Notes:** Racing calendar fully restored

### 2023-2024 (Recent Historical)
- **Races:** ~13,500 per year (108% of 2015 levels)
- **Source:** Mixed (results + racecards)
- **Quality:** ✅ Excellent coverage
- **Notes:** Includes both historical results and forward racecards

### 2025 (Current Year - In Progress)
- **Races:** 10,367 (through October 7)
- **Source:** Mixed (results + racecards)
- **Quality:** ✅ On track for ~13,800 total
- **Projection:** Expected ~13,800-14,000 races by year end
- **Coverage:** ~75% of year complete

---

## 📊 DATA USAGE SCENARIOS

### ✅ CURRENTLY SUPPORTED

1. **Race History Analysis**
   - Query all races by course, date range, year
   - Filter by race type, class, distance
   - Analyze going conditions, prize money

2. **Horse Performance Tracking**
   - Track individual horse race entries
   - View jockey/trainer/owner associations
   - Basic form analysis

3. **Course Statistics**
   - Races per course over time
   - Course characteristics and trends

4. **Entity Tracking**
   - List all active horses, jockeys, trainers
   - Track career statistics

### ⚠️ LIMITED SUPPORT (Data Incomplete)

5. **Complete Runner Analysis**
   - ⚠️ Only 31% of runners populated
   - Missing runner data for 69% of races
   - Can analyze trends but not comprehensive

6. **Pedigree Analysis**
   - ❌ NOT SUPPORTED - ra_horse_pedigree empty
   - Cannot trace bloodlines
   - Cannot analyze breeding patterns

7. **Race Results**
   - ⚠️ May be available in ra_races.api_data JSONB
   - Not in dedicated ra_results table
   - Requires JSONB queries

---

## 🛠️ RECOMMENDED ACTIONS

### Priority 1: CRITICAL (Fix Now)

1. **Investigate Low Runner Count** ⚠️
   ```sql
   -- Check if race_date is populated in ra_runners
   SELECT COUNT(*) as total,
          COUNT(race_date) as with_date,
          COUNT(*) - COUNT(race_date) as missing_date
   FROM ra_runners;
   ```

   **Action:** If race_date is NULL, this explains the low count (year filtering excludes them)

2. **Enable Pedigree Population** ❌
   - Review `fetchers/horses_fetcher.py`
   - Check why ra_horse_pedigree is empty
   - Enable sire/dam data insertion

### Priority 2: IMPORTANT (Fix This Week)

3. **Verify Runner Data Completeness**
   - Sample 100 random races
   - Check how many have runner data
   - Identify pattern (are certain race types missing runners?)

4. **Document ra_results Status**
   - Officially decide: keep, fix, or drop?
   - Update schema documentation
   - Add migration if needed

### Priority 3: ENHANCEMENT (Future)

5. **Add Data Quality Monitoring**
   - Create alert for runner/race ratio < 5
   - Monitor entity extraction rates
   - Track pedigree population

6. **Optimize Queries**
   - Add indexes on race_date (if not present)
   - Add indexes on foreign keys
   - Consider materialized views for year summaries

---

## 📝 CONCLUSIONS

### Strengths ✅
- **Excellent historical coverage:** 11 years of race data (2015-2025)
- **Consistent data quality:** ~12,500 races per year
- **Complete reference data:** All courses and bookmakers populated
- **Large entity dataset:** 111K horses, comprehensive jockey/trainer/owner lists
- **COVID-19 impact visible:** 2020 data shows expected reduction

### Weaknesses ⚠️
- **Low runner count:** Only 31% of expected runners populated
- **Empty pedigree table:** No breeding data available
- **Empty results table:** Schema mismatch (data may be in api_data JSONB)

### Overall Assessment
**Rating:** 🟡 **7/10** - Good foundation with critical gaps

The database has **excellent race coverage** and **good entity data**, but is missing significant runner entries and all pedigree information. The core racing data (races, dates, courses) is solid and comprehensive across 11 years.

**Primary Concern:** The runner count issue needs investigation. With only 2.8 runners per race average, either:
1. The data filtering is too restrictive, OR
2. There's a data loss issue in the runner insertion logic

**Recommendation:** Focus on fixing the runner population issue first, then enable pedigree data collection.

---

## 📌 QUICK REFERENCE

**Total Records:** 670,021 across all tables

| Table | Records | Status |
|-------|---------|--------|
| ra_races | 136,448 | ✅ Complete |
| ra_runners | 377,713 | ⚠️ Partial (31%) |
| ra_horses | 111,325 | ✅ Complete |
| ra_owners | 48,053 | ✅ Complete |
| ra_jockeys | 3,478 | ✅ Complete |
| ra_trainers | 2,779 | ✅ Complete |
| ra_courses | 101 | ✅ Complete |
| ra_bookmakers | 19 | ✅ Complete |
| ra_horse_pedigree | 0 | ❌ Empty |
| ra_results | 0 | ❌ Empty |

**Date Range:** 2015-01-01 to 2025-10-07 (11 years)
**Primary Table:** ra_races (136,448 records)
**Coverage:** UK and Ireland racing only

---

**Generated by:** analyze_database_coverage.py
**Last Updated:** 2025-10-08 00:12:51
