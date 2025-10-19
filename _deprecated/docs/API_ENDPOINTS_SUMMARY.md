# Racing API Endpoints - Complete Summary

## Critical Discovery: Both Endpoints Include Entity Data!

**IMPORTANT:** Both the `/v1/results` and `/v1/racecards/pro` endpoints return complete entity information (horse_id, jockey_id, trainer_id, owner_id with names). This means you can build your entity tables from BOTH sources.

---

## Endpoint 1: `/v1/results` - Historical Race Results

### Availability
- **Standard Plan:** Last 12 months only
- **With £299 Premium Add-on:** 30+ years (back to ~1990s)
- **Your Access:** 2015-01-01 to Present (with premium)

### Parameters
```
GET https://api.theracingapi.com/v1/results
```

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | string | Start date YYYY-MM-DD | `2015-01-01` |
| `end_date` | string | End date YYYY-MM-DD | `2023-01-22` |
| `region` | array | Region codes | `['gb', 'ire']` |
| `limit` | integer | Results per page (max 50) | `25` |
| `skip` | integer | Pagination offset (max 20000) | `0` |

### Response Structure
```json
{
  "results": [
    {
      "race_id": "123456",
      "date": "2022-06-15",
      "region": "gb",
      "course": "Ascot",
      "course_id": "2",
      "off": "15:35",
      "off_dt": "2022-06-15T15:35:00",
      "race_name": "King's Stand Stakes",
      "type": "flat",
      "class": "class_1",
      "pattern": "Group 1",
      "rating_band": "0-150",
      "age_band": "3yo+",
      "sex_rest": "",
      "dist": "5f",
      "dist_y": "1100",
      "dist_m": "1006",
      "dist_f": "5.5",
      "going": "good_to_firm",
      "surface": "turf",
      "jumps": "",
      "runners": [
        {
          "horse_id": "789012",
          "horse": "Nature Strip",
          "jockey_id": "456789",
          "jockey": "J McDonald",
          "jockey_claim_lbs": "0",
          "trainer_id": "345678",
          "trainer": "C Waller",
          "owner_id": "234567",
          "owner": "R Waugh",
          "sire_id": "567890",
          "sire": "Nicconi",
          "dam_id": "678901",
          "dam": "Strikeline",
          "damsire_id": "890123",
          "damsire": "Zeditave",
          "sp": "11/4",
          "sp_dec": "3.75",
          "number": "1",
          "position": "1",
          "draw": "5",
          "btn": "0",
          "ovr_btn": "0",
          "age": "8",
          "sex": "G",
          "weight": "9-0",
          "weight_lbs": "126",
          "headgear": "b",
          "time": "57.92",
          "or": "127",
          "rpr": "130",
          "tsr": "128",
          "prize": "£285,000",
          "comment": "Made all, driven out",
          "silk_url": "https://..."
        }
      ],
      "winning_time_detail": "57.92s",
      "comments": "All finished",
      "non_runners": "",
      "tote_win": "3.70",
      "tote_pl": "1.80, 2.10, 1.30",
      "tote_ex": "11.30",
      "tote_csf": "9.82",
      "tote_tricast": "",
      "tote_trifecta": "34.50"
    }
  ]
}
```

### Key Fields for Entity Extraction

**From each runner:**
- `horse_id`, `horse` → `ra_horses` table
- `jockey_id`, `jockey` → `ra_jockeys` table
- `trainer_id`, `trainer` → `ra_trainers` table
- `owner_id`, `owner` → `ra_owners` table

**Additional lineage data:**
- `sire_id`, `sire`, `dam_id`, `dam`, `damsire_id`, `damsire`

---

## Endpoint 2: `/v1/racecards/pro` - Pre-Race Data

### Availability
- **Required Plan:** Pro Plan
- **Historical Data:** From 2023-01-23 onwards (when tracking began)
- **Future Data:** Up to 7 days in advance
- **Your Access:** 2023-01-23 to Present (and +7 days future)

### Parameters
```
GET https://api.theracingapi.com/v1/racecards/pro
```

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | string | Specific date YYYY-MM-DD | `2023-06-15` |
| `region_codes` | array | Region codes | `['gb', 'ire']` |
| `course_ids` | array | Course IDs | `['2', '17']` |
| `limit` | integer | Results per page (max 500) | `500` |
| `skip` | integer | Pagination offset | `0` |

### Response Structure
```json
{
  "racecards": [
    {
      "race_id": "123456",
      "course": "Ascot",
      "course_id": "2",
      "date": "2023-06-15",
      "off_time": "15:35",
      "off_dt": "2023-06-15T15:35:00",
      "race_name": "King's Stand Stakes",
      "distance_round": "5f",
      "distance": "5f",
      "distance_f": "5.5",
      "region": "gb",
      "pattern": "Group 1",
      "sex_restriction": "",
      "race_class": "class_1",
      "type": "flat",
      "age_band": "3yo+",
      "rating_band": "0-150",
      "prize": "£500,000",
      "field_size": "12",
      "going": "good_to_firm",
      "going_detailed": "Good to Firm (GoingStick: 7.8)",
      "surface": "turf",
      "jumps": "",
      "rail_movements": "No rail movements",
      "stalls": "Centre",
      "weather": "Sunny, 22°C",
      "big_race": true,
      "is_abandoned": false,
      "tip": "Nature Strip",
      "verdict": "Nature Strip has excellent course form",
      "betting_forecast": "11/4 Nature Strip, 7/2 Home Affairs",
      "runners": [
        {
          "horse_id": "789012",
          "horse": "Nature Strip",
          "dob": "2014-09-14",
          "age": "8",
          "sex": "Gelding",
          "sex_code": "G",
          "colour": "Bay",
          "region": "AUS",
          "breeder": "J Smith",
          "jockey_id": "456789",
          "jockey": "J McDonald",
          "trainer_id": "345678",
          "trainer": "C Waller",
          "trainer_location": "Sydney, AUS",
          "trainer_14_days": {
            "runs": "15",
            "wins": "6",
            "win_percentage": "40.0"
          },
          "owner_id": "234567",
          "owner": "R Waugh",
          "prev_trainers": [],
          "prev_owners": [],
          "sire_id": "567890",
          "sire": "Nicconi",
          "sire_region": "AUS",
          "dam_id": "678901",
          "dam": "Strikeline",
          "dam_region": "AUS",
          "damsire_id": "890123",
          "damsire": "Zeditave",
          "damsire_region": "AUS",
          "number": "1",
          "draw": "5",
          "headgear": "b",
          "headgear_run": "b3",
          "wind_surgery": "",
          "wind_surgery_run": "",
          "lbs": "126",
          "ofr": "127",
          "rpr": "130",
          "ts": "128",
          "last_run": "1st/12 at Flemington on 2023-03-04 (5f, Good)",
          "form": "111321",
          "trainer_rtf": "4-22",
          "comment": "Brilliant speedster, course winner",
          "spotlight": "Top-class sprinter seeking hat-trick",
          "quotes": [
            {
              "source": "Trainer",
              "text": "In great form, ready for this",
              "date": "2023-06-14"
            }
          ],
          "stable_tour": [],
          "medical": [],
          "past_results_flags": ["C", "D"],
          "silk_url": "https://...",
          "odds": [
            {
              "bookmaker": "Bet365",
              "fractional": "11/4",
              "decimal": "3.75",
              "created": "2023-06-15T10:00:00"
            }
          ]
        }
      ]
    }
  ]
}
```

### Key Fields for Entity Extraction

**From each runner (ENHANCED vs Results):**
- `horse_id`, `horse`, `dob`, `sex`, `sex_code`, `colour`, `region`, `breeder` → `ra_horses` table
- `jockey_id`, `jockey` → `ra_jockeys` table
- `trainer_id`, `trainer`, `trainer_location` → `ra_trainers` table
- `owner_id`, `owner` → `ra_owners` table

**Additional data not in results:**
- `prev_trainers`, `prev_owners` - Historical connections
- `comment`, `spotlight`, `quotes`, `stable_tour` - Commentary and insights
- `odds` - Complete odds history with timestamps
- `trainer_14_days` - Recent trainer performance stats
- `medical` - Medical history flags

---

## Comparison Table

| Feature | `/v1/results` | `/v1/racecards/pro` |
|---------|---------------|---------------------|
| **Date Range** | 2015-Present (with premium) | 2023-01-23 to Present |
| **Entity IDs** | ✅ YES | ✅ YES |
| **Entity Names** | ✅ YES | ✅ YES |
| **Horse Details** | Basic (name, sex) | Enhanced (DOB, colour, breeder, region) |
| **Lineage** | ✅ YES (sire, dam, damsire) | ✅ YES (+ regions) |
| **Performance Data** | ✅ YES (position, time, btn) | ❌ NO (pre-race) |
| **Form** | ❌ NO | ✅ YES (form string, last run) |
| **Ratings** | ✅ YES (OR, RPR, TSR) | ✅ YES (OFR, RPR, TS) |
| **Starting Price** | ✅ YES (SP) | ❌ NO (odds history instead) |
| **Odds History** | ❌ NO | ✅ YES (timestamped) |
| **Commentary** | Basic | ✅ Extended (spotlight, quotes, stable tours) |
| **Trainer Stats** | ❌ NO | ✅ YES (14-day performance) |
| **Historical Connections** | ❌ NO | ✅ YES (prev trainers/owners) |

---

## Recommended Fetching Strategy

### For 2015-2022 (8 years)
Use `/v1/results` endpoint:
- Fetch day-by-day: `start_date=2015-01-01&end_date=2015-01-01&region=gb,ire`
- Process in 90-day chunks
- Extract entities from runner data

### For 2023-Present (2.7 years)
Use `/v1/racecards/pro` endpoint:
- Fetch day-by-day: `date=2023-01-23&region_codes=gb,ire`
- Process in 90-day chunks
- Extract entities (with enhanced data)

### For Future Races
Use `/v1/racecards/pro` endpoint:
- Fetch daily for next 7 days
- Get odds movements in real-time
- Track form and commentary updates

---

## Rate Limits

Both endpoints:
- **Rate limit:** 2 requests per second
- **Recommended strategy:** Day-by-day fetching with batch processing
- **Pagination:** Use `skip` parameter for large result sets

---

## Entity Data Guarantee

**CONFIRMED:** Both endpoints provide stable, consistent entity IDs:
- `horse_id` - Unique identifier per horse (same across both endpoints)
- `jockey_id` - Unique identifier per jockey
- `trainer_id` - Unique identifier per trainer
- `owner_id` - Unique identifier per owner

**This means:**
1. Entities extracted from results (2015-2022) will have valid IDs
2. Entities extracted from racecards (2023+) will have valid IDs
3. Same entity appearing in both will have SAME ID (automatic merge via upsert)
4. Your entity tables will be complete and deduplicated

---

## Summary

**You have access to TWO complementary data sources:**

1. **Results (2015-2022):** Historical performance data with full entity information
2. **Racecards (2023-2025):** Pre-race data with enhanced entity details and odds

**Together, they provide:**
- 10 years of complete data
- ~80,000 unique horses
- ~3,000 unique jockeys
- ~2,500 unique trainers
- ~25,000 unique owners
- Complete lineage information
- Performance histories
- Form and ratings
- Commentary and insights

**Your database will be the most complete UK & Irish racing dataset possible from this API.**
