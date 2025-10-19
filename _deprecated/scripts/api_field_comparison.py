"""
API Field Comparison Script
Compares what the Racing API provides vs what we're extracting
"""

import json
from pathlib import Path

# Load OpenAPI spec
spec_file = Path(__file__).parent / 'docs' / 'racing_api_openapi.json'
with open(spec_file, 'r') as f:
    spec = json.load(f)

components = spec.get('components', {}).get('schemas', {})

print("="*100)
print("COMPREHENSIVE API FIELD ANALYSIS - What We're Missing")
print("="*100)

# ===================================
# RACECARDS/PRO ENDPOINT ANALYSIS
# ===================================
print("\n" + "="*100)
print("1. RACECARDS/PRO ENDPOINT (/v1/racecards/pro)")
print("="*100)

racecard_schema = components.get('RacecardOddsPro', {})
racecard_fields = set(racecard_schema.get('properties', {}).keys())

# What we're currently extracting (from races_fetcher.py)
extracted_race_fields = {
    'race_id', 'course_id', 'course', 'region', 'race_name', 'date', 'off_dt',
    'off_time', 'type', 'race_class', 'distance', 'distance_f', 'distance_round',
    'age_band', 'surface', 'going', 'going_detailed', 'weather', 'rail_movements',
    'stalls_position', 'prize', 'big_race', 'is_abandoned', 'field_size'
}

# What API provides but we're NOT extracting
missing_race_fields = racecard_fields - extracted_race_fields

print(f"\nAPI Provides: {len(racecard_fields)} fields")
print(f"We Extract:   {len(extracted_race_fields)} fields")
print(f"Missing:      {len(missing_race_fields)} fields")

if missing_race_fields:
    print("\n❌ MISSING RACE FIELDS (API provides but we don't extract):")
    for field in sorted(missing_race_fields):
        print(f"  - {field}")

# ===================================
# RUNNER (RACECARDS) ANALYSIS
# ===================================
print("\n" + "="*100)
print("2. RUNNER FIELDS (from /v1/racecards/pro)")
print("="*100)

runner_schema = components.get('RunnerOddsPro', {})
runner_fields = set(runner_schema.get('properties', {}).keys())

# What we're currently extracting (from races_fetcher.py _transform_racecard)
extracted_runner_fields = {
    'horse_id', 'horse', 'age', 'sex', 'number', 'draw', 'stall',
    'jockey_id', 'jockey', 'jockey_claim', 'jockey_allowance',
    'trainer_id', 'trainer', 'owner_id', 'owner',
    'lbs', 'headgear', 'headgear_run',
    'sire_id', 'sire', 'dam_id', 'dam', 'damsire_id', 'damsire',
    'form', 'form_string', 'days_since_last_run', 'last_run',
    'career_total', 'prize_money', 'ofr', 'rpr', 'ts', 'comment', 'silk_url'
}

missing_runner_fields = runner_fields - extracted_runner_fields

print(f"\nAPI Provides: {len(runner_fields)} fields")
print(f"We Extract:   {len(extracted_runner_fields)} fields")
print(f"Missing:      {len(missing_runner_fields)} fields")

if missing_runner_fields:
    print("\n❌ MISSING RUNNER FIELDS (API provides but we don't extract):")
    for field in sorted(missing_runner_fields):
        field_spec = runner_schema.get('properties', {}).get(field, {})
        field_type = field_spec.get('type', 'unknown')
        is_required = '(REQUIRED)' if field in runner_schema.get('required', []) else ''
        print(f"  - {field:35s} {field_type:15s} {is_required}")

# ===================================
# HORSES ENDPOINT ANALYSIS
# ===================================
print("\n" + "="*100)
print("3. HORSE DETAILS (GET /horses/{id}/pro)")
print("="*100)

horse_schema = components.get('HorsePro', {})
horse_fields = set(horse_schema.get('properties', {}).keys())

# What we're extracting from /horses/search (horses_fetcher.py)
extracted_horse_fields = {
    'id', 'name', 'dob', 'sex', 'sex_code', 'colour', 'region',
    'sire_id', 'sire', 'sire_region', 'dam_id', 'dam', 'dam_region',
    'damsire_id', 'damsire', 'damsire_region', 'breeder'
}

missing_horse_fields = horse_fields - extracted_horse_fields

print(f"\nAPI Provides: {len(horse_fields)} fields")
print(f"We Extract:   {len(extracted_horse_fields)} fields")
print(f"Missing:      {len(missing_horse_fields)} fields")

print("\n⚠️  CRITICAL ISSUE:")
print("  - We use /horses/search which returns basic horse list")
print("  - We should ALSO use GET /horses/{id}/pro for detailed data")
print("  - This would populate ra_horse_pedigree and horse detail fields")

if missing_horse_fields:
    print("\n❌ MISSING HORSE FIELDS:")
    for field in sorted(missing_horse_fields):
        print(f"  - {field}")

# ===================================
# RESULTS ENDPOINT ANALYSIS
# ===================================
print("\n" + "="*100)
print("4. RESULTS ENDPOINT (GET /results)")
print("="*100)

results_schema = components.get('Result', {})
results_fields = set(results_schema.get('properties', {}).keys())

# What we're extracting (from results_fetcher.py)
extracted_result_fields = {
    'race_id', 'course_id', 'course', 'race_name', 'date', 'off_dt', 'off',
    'type', 'class', 'distance', 'dist_f', 'surface', 'going',
    'prize', 'currency', 'region', 'results_status', 'is_abandoned', 'runners'
}

missing_result_fields = results_fields - extracted_result_fields

print(f"\nAPI Provides: {len(results_fields)} fields")
print(f"We Extract:   {len(extracted_result_fields)} fields")
print(f"Missing:      {len(missing_result_fields)} fields")

if missing_result_fields:
    print("\n❌ MISSING RESULT FIELDS:")
    for field in sorted(missing_result_fields):
        print(f"  - {field}")

# ===================================
# PREMIUM ENDPOINTS NOT BEING USED
# ===================================
print("\n" + "="*100)
print("5. PREMIUM/PRO ENDPOINTS NOT BEING USED")
print("="*100)

endpoints_used = {
    '/v1/courses': 'USED (courses_fetcher.py)',
    '/v1/courses/regions': 'USED (courses_fetcher.py)',
    '/v1/racecards/pro': 'USED (races_fetcher.py)',
    '/v1/results': 'USED (results_fetcher.py)',
    '/v1/horses/search': 'USED (horses_fetcher.py)',
    '/v1/jockeys/search': 'USED (jockeys_fetcher.py)',
    '/v1/trainers/search': 'USED (trainers_fetcher.py)',
    '/v1/owners/search': 'USED (owners_fetcher.py)',
}

premium_endpoints_available = [
    '/v1/horses/{horse_id}/pro',
    '/v1/horses/{horse_id}/results',
    '/v1/horses/{horse_id}/standard',
    '/v1/horses/{horse_id}/analysis/distance-times',
    '/v1/trainers/{trainer_id}/results',
    '/v1/trainers/{trainer_id}/analysis/horse-age',
    '/v1/trainers/{trainer_id}/analysis/courses',
    '/v1/trainers/{trainer_id}/analysis/distances',
    '/v1/trainers/{trainer_id}/analysis/jockeys',
    '/v1/trainers/{trainer_id}/analysis/owners',
    '/v1/jockeys/{jockey_id}/results',
    '/v1/jockeys/{jockey_id}/analysis/courses',
    '/v1/jockeys/{jockey_id}/analysis/distances',
    '/v1/jockeys/{jockey_id}/analysis/owners',
    '/v1/jockeys/{jockey_id}/analysis/trainers',
    '/v1/owners/{owner_id}/results',
    '/v1/owners/{owner_id}/analysis/courses',
    '/v1/owners/{owner_id}/analysis/distances',
    '/v1/owners/{owner_id}/analysis/jockeys',
    '/v1/owners/{owner_id}/analysis/trainers',
    '/v1/sires/{sire_id}/results',
    '/v1/sires/{sire_id}/analysis/classes',
    '/v1/sires/{sire_id}/analysis/distances',
    '/v1/dams/{dam_id}/results',
    '/v1/dams/{dam_id}/analysis/classes',
    '/v1/dams/{dam_id}/analysis/distances',
    '/v1/damsires/{damsire_id}/results',
    '/v1/odds/{race_id}/{horse_id}',
]

print("\n❌ PREMIUM ENDPOINTS AVAILABLE BUT NOT USED:")
for endpoint in premium_endpoints_available:
    print(f"  - {endpoint}")

print(f"\nTOTAL: {len(premium_endpoints_available)} premium endpoints available")
print(f"USED:  {len(endpoints_used)} endpoints")
print(f"\n⚠️  We're only using {len(endpoints_used)} out of {len(endpoints_used) + len(premium_endpoints_available)} available endpoints!")

# ===================================
# SPECIFIC RECOMMENDATIONS
# ===================================
print("\n" + "="*100)
print("6. SPECIFIC RECOMMENDATIONS TO FIX DATA GAPS")
print("="*100)

recommendations = [
    {
        "issue": "ra_horse_pedigree is EMPTY (0 records)",
        "cause": "Not extracting pedigree fields correctly from runners",
        "fix": "The pedigree data IS in the runner data from /racecards/pro. Fix extraction logic in races_fetcher.py lines 116-132",
        "priority": "CRITICAL",
        "file": "horses_fetcher.py lines 116-132"
    },
    {
        "issue": "Missing runner fields: dob, sex_code, colour, region, breeder, trainer_location",
        "cause": "API provides these in RunnerOddsPro but we don't extract them",
        "fix": "Add extraction in races_fetcher.py _transform_racecard() function",
        "priority": "HIGH",
        "file": "fetchers/races_fetcher.py line 281+"
    },
    {
        "issue": "Missing race fields: pattern, sex_restriction, rating_band, tip, verdict, betting_forecast",
        "cause": "API provides these but we don't extract them",
        "fix": "Add to race_record dictionary in races_fetcher.py line 236+",
        "priority": "HIGH",
        "file": "fetchers/races_fetcher.py line 236+"
    },
    {
        "issue": "Missing advanced runner data: trainer_14_days, prev_trainers, prev_owners, quotes, stable_tour, medical, wind_surgery",
        "cause": "Pro plan provides these nested objects but we ignore them",
        "fix": "Add separate tables for these or store in api_data JSONB",
        "priority": "MEDIUM",
        "file": "New tables or enhanced JSONB extraction"
    },
    {
        "issue": "Missing results fields: winning_time_detail, comments, non_runners, tote data",
        "cause": "Results API provides but we don't extract",
        "fix": "Enhance results_fetcher.py to extract all fields",
        "priority": "MEDIUM",
        "file": "fetchers/results_fetcher.py line 207+"
    },
    {
        "issue": "Low runner count (2.77 avg vs 8-12 expected)",
        "cause": "Likely filtering issue or API limitation",
        "fix": "Check if racecards include non-runners, withdrawn horses. May need to use /results instead",
        "priority": "CRITICAL",
        "file": "Investigation needed"
    },
    {
        "issue": "ra_horses missing dob, sex_code, colour, region (all NULL)",
        "cause": "/horses/search returns basic data. Need detailed endpoint",
        "fix": "After initial horse search, fetch GET /horses/{id}/pro for each horse",
        "priority": "HIGH",
        "file": "fetchers/horses_fetcher.py - add fetch_horse_details() method"
    },
    {
        "issue": "Not using premium analysis endpoints",
        "cause": "No code to fetch trainer/jockey/owner statistics",
        "fix": "Add analysis fetchers for statistics (optional enhancement)",
        "priority": "LOW",
        "file": "New fetchers needed"
    },
]

for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. {rec['issue']}")
    print(f"   Priority: {rec['priority']}")
    print(f"   Cause:    {rec['cause']}")
    print(f"   Fix:      {rec['fix']}")
    print(f"   File:     {rec['file']}")

print("\n" + "="*100)
print("END OF ANALYSIS")
print("="*100)
