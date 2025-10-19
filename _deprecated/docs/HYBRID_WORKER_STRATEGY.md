# Hybrid Worker Strategy: Complete Data Capture

**Date:** 2025-10-14
**Decision:** Modify workers to capture complete horse data using Pro endpoint
**Rationale:** Better quality data + easier maintenance once complete

---

## Rate Limit Reality (All Plans)

**From API Documentation:**
- **Free Plan:** 2 requests/second
- **Basic Plan:** 2 requests/second
- **Standard Plan:** 2 requests/second
- **Pro Plan:** 2 requests/second ✅ (You have this)

**Conclusion:** Rate limit is the same, BUT Pro gives access to better endpoints with complete data.

---

## Current vs Proposed Approach

### Current Approach (Bulk Only)
```
horses_fetcher.py → /v1/horses/search (bulk)
  ↓
Gets: id, name, sex (basic data)
Missing: dob, colour, pedigree (NULL)
  ↓
Requires: Separate 15.5hr backfill
```

### Proposed Approach (Hybrid)
```
horses_fetcher.py → /v1/horses/search (bulk discovery)
  ↓
For NEW horses only → /v1/horses/{id}/pro (individual)
  ↓
Gets: Complete data (dob, colour, pedigree, breeder)
  ↓
Result: New data complete immediately
```

---

## Time Analysis

### Scenario 1: Initial Run (111,325 horses)
**Current bulk approach:**
- Bulk search: 223 calls × 0.5s = 2 minutes ✅
- **BUT** data incomplete, needs backfill: +15.5 hours

**Hybrid approach:**
- Bulk search: 223 calls × 0.5s = 2 minutes
- Pro enrichment: 111,325 calls × 0.5s = **15.5 hours**
- **Total: 15.5 hours for complete data**

**Verdict:** Same total time, but single process

---

### Scenario 2: Daily Maintenance (50 new horses/day)

**Current bulk approach:**
- Bulk search: 1 call × 0.5s = 0.5 seconds ✅
- Data incomplete until weekly backfill runs

**Hybrid approach:**
- Bulk search: 1 call × 0.5s = 0.5 seconds
- Pro enrichment: 50 calls × 0.5s = **25 seconds**
- **Total: 26 seconds for complete data**

**Verdict:** 26 seconds vs 0.5 seconds, BUT data complete immediately

---

## Benefits of Hybrid Approach

### 1. Immediate Complete Data
- ✅ New horses have pedigree data same day
- ✅ No waiting for weekly backfill
- ✅ ML models get complete data faster

### 2. Simpler Architecture
- ✅ Single worker process (no separate backfill needed for new horses)
- ✅ Less code to maintain
- ✅ No coordination between worker + backfill

### 3. Better Data Quality
- ✅ Always up-to-date pedigree info
- ✅ No gaps in historical data
- ✅ Consistent data capture

### 4. Easier Monitoring
- ✅ One process to monitor
- ✅ Clear success/failure per horse
- ✅ Simple retry logic

---

## Implementation Plan

### Phase 1: Initial Backfill (One-Time)
**Run existing backfill script for historical data:**
```bash
# 15.5 hours, one-time
python3 scripts/backfill_horse_pedigree.py
```

**Result:** All 111,325 existing horses have complete data

---

### Phase 2: Update horses_fetcher.py (Going Forward)
**Add Pro enrichment for new horses:**

```python
def process_horses(self, horses: List[Dict]) -> Tuple[int, int]:
    """Process horses with Pro enrichment for new ones"""

    # Step 1: Get existing horse IDs from database
    existing_ids = self._get_existing_horse_ids()

    # Step 2: Separate new vs existing horses
    new_horses = [h for h in horses if h['id'] not in existing_ids]
    existing_horses = [h for h in horses if h['id'] in existing_ids]

    # Step 3: Process existing horses (basic update)
    for horse in existing_horses:
        horse_record = {
            'horse_id': horse.get('id'),
            'name': horse.get('name'),
            'sex': horse.get('sex'),
            'updated_at': datetime.utcnow().isoformat()
        }
        # Upsert basic data
        self.db_client.upsert('ra_horses', [horse_record], 'horse_id')

    # Step 4: Process NEW horses (complete Pro enrichment)
    for horse in new_horses:
        logger.info(f"New horse discovered: {horse['id']} - Fetching complete data...")

        # Fetch complete data from Pro endpoint
        horse_pro = self._fetch_horse_pro(horse['id'])

        if horse_pro:
            # Insert complete horse data
            horse_record = {
                'horse_id': horse_pro.get('id'),
                'name': horse_pro.get('name'),
                'sex': horse_pro.get('sex'),
                'dob': horse_pro.get('dob'),
                'sex_code': horse_pro.get('sex_code'),
                'colour': horse_pro.get('colour'),
                'colour_code': horse_pro.get('colour_code'),
                'region': horse_pro.get('region'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            self.db_client.upsert('ra_horses', [horse_record], 'horse_id')

            # Insert pedigree if available
            if any([horse_pro.get('sire_id'), horse_pro.get('dam_id')]):
                pedigree_record = {
                    'horse_id': horse_pro.get('id'),
                    'sire_id': horse_pro.get('sire_id'),
                    'sire': horse_pro.get('sire'),
                    'dam_id': horse_pro.get('dam_id'),
                    'dam': horse_pro.get('dam'),
                    'damsire_id': horse_pro.get('damsire_id'),
                    'damsire': horse_pro.get('damsire'),
                    'breeder': horse_pro.get('breeder'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                self.db_client.upsert('ra_horse_pedigree', [pedigree_record], 'horse_id')

            # Rate limiting
            time.sleep(0.5)  # 2 requests/second
        else:
            # Fallback: Insert basic data if Pro fetch fails
            horse_record = {
                'horse_id': horse.get('id'),
                'name': horse.get('name'),
                'sex': horse.get('sex'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            self.db_client.upsert('ra_horses', [horse_record], 'horse_id')

    return len(existing_horses), len(new_horses)

def _fetch_horse_pro(self, horse_id: str) -> Dict:
    """Fetch complete horse data from Pro endpoint"""
    try:
        response = self.api_client.get_horse_details(horse_id, tier='pro')
        return response
    except Exception as e:
        logger.error(f"Error fetching Pro data for {horse_id}: {e}")
        return None

def _get_existing_horse_ids(self) -> set:
    """Get set of existing horse IDs from database"""
    result = self.db_client.client.table('ra_horses').select('horse_id').execute()
    return {row['horse_id'] for row in result.data}
```

---

## Performance Impact

### Daily Worker Run (Typical)
**Assumptions:** 50 new horses discovered per day

**Before (bulk only):**
- Time: 0.5 seconds
- Result: Incomplete data (needs backfill)

**After (hybrid):**
- Bulk search: 0.5 seconds
- Pro enrichment: 50 horses × 0.5s = 25 seconds
- **Total: 26 seconds**
- Result: Complete data immediately

**Impact:** +25.5 seconds per day for complete data ✅ Worth it!

---

### Weekly Worker Run (Less Frequent)
**Assumptions:** 350 new horses per week

**Before:**
- Time: 2 seconds
- Result: Incomplete data

**After:**
- Bulk search: 2 seconds
- Pro enrichment: 350 horses × 0.5s = 175 seconds (3 min)
- **Total: 3 minutes**
- Result: Complete data immediately

**Impact:** +3 minutes per week ✅ Still very manageable

---

## Edge Cases Handled

### 1. Pro Endpoint Failure
```python
# Fallback to basic data if Pro fetch fails
if horse_pro:
    # Insert complete data
else:
    # Insert basic data (can backfill later)
```

### 2. Rate Limiting
```python
# Respect 2 requests/second limit
time.sleep(0.5)  # Between each Pro call
```

### 3. Partial Pedigree Data
```python
# Only insert pedigree if at least sire or dam exists
if any([horse_pro.get('sire_id'), horse_pro.get('dam_id')]):
    # Insert pedigree
```

### 4. Database Conflicts
```python
# Use upsert to handle duplicates
self.db_client.upsert('ra_horses', [horse_record], 'horse_id')
```

---

## Migration Path

### Step 1: Run Historical Backfill (One-Time)
```bash
# Populate all existing horses (15.5 hours)
python3 scripts/backfill_horse_pedigree.py
```

### Step 2: Update horses_fetcher.py
- Add `_fetch_horse_pro()` method
- Add `_get_existing_horse_ids()` method
- Modify `process_horses()` to enrich new horses

### Step 3: Test Updated Worker
```bash
# Test with dry-run or small batch
python3 fetchers/horses_fetcher.py --max 10
```

### Step 4: Deploy Updated Worker
- Replace existing horses_fetcher.py
- Monitor first few runs
- Verify new horses have complete data

---

## Monitoring & Validation

### Daily Checks
```bash
# Check new horses have complete data
python3 scripts/validate_data_completeness.py --recent-only
```

### Key Metrics
- New horses discovered per day
- Pro enrichment success rate
- Pedigree coverage for new horses (target: 90%+)
- Worker execution time

---

## Comparison: Current vs Hybrid

| Aspect | Current (Bulk Only) | Hybrid (Bulk + Pro) |
|--------|---------------------|---------------------|
| **Initial setup** | 2 min + 15.5hr backfill | 15.5hr (single process) |
| **Daily runtime** | 0.5 sec | 26 sec |
| **New horse data** | Incomplete (NULL) | Complete ✅ |
| **Maintenance** | Weekly backfill needed | Self-contained ✅ |
| **Data quality** | Delayed | Immediate ✅ |
| **Complexity** | 2 processes | 1 process ✅ |
| **Pro plan usage** | No | Yes ✅ |

---

## Recommendation

**Switch to Hybrid Approach:**

1. ✅ Run one-time backfill for historical data (15.5 hours)
2. ✅ Update horses_fetcher.py to enrich new horses (26 sec/day)
3. ✅ Eliminate need for ongoing pedigree backfills
4. ✅ Get complete data immediately for new horses

**Result:** Better data quality + simpler architecture + full use of Pro plan

---

## Files to Create/Modify

1. **Update:** `fetchers/horses_fetcher.py` - Add Pro enrichment logic
2. **Keep:** `scripts/backfill_horse_pedigree.py` - Use once for historical data
3. **Create:** `scripts/validate_recent_horses.py` - Validate new horses only
4. **Update:** `docs/WORKER_PEDIGREE_CAPTURE_ANALYSIS.md` - Document new approach

---

**Conclusion:** You're absolutely right! With Pro access, we should capture complete data immediately for new horses. The 25-second overhead per day is worth it for complete, high-quality data.

---

**Next Step:** Update horses_fetcher.py with hybrid approach?
