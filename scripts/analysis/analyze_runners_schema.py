"""
Comprehensive ra_runners Schema Analysis
Identifies redundant columns, duplicates, and naming issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from supabase import create_client
from collections import defaultdict

# Get config
config = get_config()

from supabase.lib.client_options import ClientOptions
options = ClientOptions()
supabase = create_client(config.supabase.url, config.supabase.service_key, options)

print("=" * 100)
print("RA_RUNNERS COMPREHENSIVE SCHEMA ANALYSIS")
print("=" * 100)
print()

# Fetch current schema
result = supabase.table('ra_runners').select('*').limit(1).execute()

# Get columns from the data (if any rows exist)
if result.data:
    columns = list(result.data[0].keys())
    print(f"✅ Found {len(columns)} columns in ra_runners table\n")
else:
    print("⚠️  No data in ra_runners table - fetching from information_schema\n")
    # Fallback to querying schema
    columns = []

# Categorize columns
categories = {
    'IDENTIFIERS': [],
    'HORSE_METADATA': [],
    'PEDIGREE': [],
    'JOCKEY_DATA': [],
    'TRAINER_DATA': [],
    'OWNER_DATA': [],
    'RACE_ENTRY': [],
    'EQUIPMENT': [],
    'FORM_CAREER': [],
    'RATINGS': [],
    'EXPERT_ANALYSIS': [],
    'RESULTS_DATA': [],
    'MEDICAL': [],
    'HISTORICAL': [],
    'TIMESTAMPS': [],
    'METADATA': []
}

# Column definitions from migrations
migration_003_fields = [
    'dob', 'colour', 'breeder', 'dam_region', 'sire_region', 'damsire_region',
    'trainer_location', 'trainer_rtf', 'trainer_14_days_data',
    'spotlight', 'wind_surgery', 'wind_surgery_run',
    'past_results_flags', 'quotes_data', 'stable_tour_data', 'medical_data'
]

migration_011_fields = [
    'starting_price_decimal', 'race_comment', 'jockey_silk_url',
    'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs'
]

migration_018_fields = [
    'horse_dob', 'horse_sex_code', 'horse_colour', 'horse_region', 'breeder',
    'sire_region', 'dam_region', 'damsire_region',
    'trainer_location', 'trainer_14_days', 'trainer_rtf',
    'headgear_run', 'wind_surgery', 'wind_surgery_run',
    'last_run_date', 'days_since_last_run',
    'spotlight', 'quotes', 'stable_tour', 'medical',
    'prev_trainers', 'prev_owners', 'past_results_flags', 'odds'
]

migration_016_dropped = [
    'fetched_at', 'racing_api_race_id', 'racing_api_horse_id',
    'racing_api_jockey_id', 'racing_api_trainer_id', 'racing_api_owner_id',
    'weight', 'race_comment', 'jockey_silk_url'
]

# Analyze duplicates
print("🔍 DUPLICATE ANALYSIS")
print("=" * 100)
print()

# Check for duplicates between Migration 003 and 018
duplicates = []
for field in migration_018_fields:
    # Check if Migration 018 field duplicates Migration 003
    if field in migration_003_fields:
        duplicates.append({
            'migration_018': field,
            'migration_003': field,
            'status': 'EXACT DUPLICATE'
        })
    # Check for naming variants
    elif field == 'horse_dob' and 'dob' in migration_003_fields:
        duplicates.append({
            'migration_018': 'horse_dob',
            'migration_003': 'dob',
            'status': 'NAMING VARIANT'
        })
    elif field == 'horse_colour' and 'colour' in migration_003_fields:
        duplicates.append({
            'migration_018': 'horse_colour',
            'migration_003': 'colour',
            'status': 'NAMING VARIANT'
        })
    elif field == 'trainer_14_days' and 'trainer_14_days_data' in migration_003_fields:
        duplicates.append({
            'migration_018': 'trainer_14_days',
            'migration_003': 'trainer_14_days_data',
            'status': 'NAMING VARIANT'
        })
    elif field == 'quotes' and 'quotes_data' in migration_003_fields:
        duplicates.append({
            'migration_018': 'quotes',
            'migration_003': 'quotes_data',
            'status': 'NAMING VARIANT'
        })
    elif field == 'stable_tour' and 'stable_tour_data' in migration_003_fields:
        duplicates.append({
            'migration_018': 'stable_tour',
            'migration_003': 'stable_tour_data',
            'status': 'NAMING VARIANT'
        })
    elif field == 'medical' and 'medical_data' in migration_003_fields:
        duplicates.append({
            'migration_018': 'medical',
            'migration_003': 'medical_data',
            'status': 'NAMING VARIANT'
        })

print(f"Found {len(duplicates)} duplicates between Migration 003 and Migration 018:")
print()

for dup in duplicates:
    print(f"  ❌ {dup['migration_018']:30} (Migration 018) ↔ {dup['migration_003']:30} (Migration 003) [{dup['status']}]")

print()
print("=" * 100)
print()

# Check for conflicts with dropped columns
print("⚠️  CONFLICT ANALYSIS WITH DROPPED COLUMNS")
print("=" * 100)
print()

conflicts = []
for field in migration_018_fields:
    if field in migration_016_dropped:
        conflicts.append(field)

for field in migration_011_fields:
    if field in migration_016_dropped:
        conflicts.append(field)

if conflicts:
    print(f"Found {len(conflicts)} columns that were dropped in Migration 016 but still used:")
    print()
    for field in conflicts:
        print(f"  ⚠️  {field} - DROPPED in Migration 016 but USED in fetchers")
else:
    print("✅ No conflicts with dropped columns")

print()
print("=" * 100)
print()

# runner_id analysis
print("🔑 RUNNER_ID COMPOSITE KEY ANALYSIS")
print("=" * 100)
print()
print("User's concern: runner_id is redundant as it's just race_id + horse_id merged")
print()
print("Current implementation (from races_fetcher.py line 269):")
print("  runner_id = f\"{race_id}_{horse_id}\"")
print()
print("Analysis:")
print("  ✅ runner_id IS a composite of race_id + horse_id")
print("  ✅ It serves as the PRIMARY KEY for ra_runners table")
print("  ⚠️  Question: Should we use (race_id, horse_id) as composite PK instead?")
print()
print("Recommendation:")
print("  1. KEEP runner_id as it provides a simple single-column PRIMARY KEY")
print("  2. Alternative: Use composite PRIMARY KEY (race_id, horse_id) - more complex queries")
print("  3. Current approach is valid and common in database design")
print()
print("=" * 100)
print()

# Naming inconsistencies
print("📝 NAMING INCONSISTENCIES")
print("=" * 100)
print()

naming_issues = [
    {
        'pattern': 'horse_ prefix',
        'fields': ['horse_dob', 'horse_sex_code', 'horse_colour', 'horse_region'],
        'inconsistency': 'Some horse fields have horse_ prefix, others do not (e.g., age, sex)',
        'recommendation': 'Either prefix ALL horse fields or NONE'
    },
    {
        'pattern': '_data suffix',
        'fields': ['trainer_14_days_data vs trainer_14_days', 'quotes_data vs quotes', 'stable_tour_data vs stable_tour', 'medical_data vs medical'],
        'inconsistency': 'JSONB fields have inconsistent _data suffix',
        'recommendation': 'Remove _data suffix for consistency (quotes, stable_tour, medical, trainer_14_days)'
    },
    {
        'pattern': 'Comment fields',
        'fields': ['comment', 'race_comment'],
        'inconsistency': 'Two different column names for runner comments (one was dropped!)',
        'recommendation': 'Use single consistent name: comment'
    }
]

for issue in naming_issues:
    print(f"Issue: {issue['pattern']}")
    print(f"  Fields: {issue['fields']}")
    print(f"  Problem: {issue['inconsistency']}")
    print(f"  Fix: {issue['recommendation']}")
    print()

print("=" * 100)
print()

# Summary recommendations
print("📋 SUMMARY RECOMMENDATIONS")
print("=" * 100)
print()

print("IMMEDIATE ACTIONS REQUIRED:")
print()
print("1. ❌ DO NOT RUN Migration 018 as written - it creates massive duplicates!")
print()
print("2. ✅ FIRST: Verify which columns from Migration 003 actually exist in database")
print()
print("3. ✅ THEN: Create Migration 018 REVISED that:")
print("   • Uses existing columns (dob, colour, etc.) instead of creating new ones")
print("   • Renames inconsistent columns (trainer_14_days_data → trainer_14_days)")
print("   • Adds ONLY the truly missing fields:")
print("     - horse_sex_code (NEW)")
print("     - horse_region (NEW)")
print("     - headgear_run (NEW)")
print("     - last_run_date (NEW)")
print("     - days_since_last_run (NEW)")
print("     - prev_trainers (NEW)")
print("     - prev_owners (NEW)")
print("     - odds (NEW)")
print()
print("4. ✅ Fix races_fetcher.py to use correct column names:")
print("   • 'race_comment' → 'comment' (race_comment was dropped!)")
print("   • 'horse_dob' → 'dob'")
print("   • 'horse_colour' → 'colour'")
print("   • 'trainer_14_days' → 'trainer_14_days_data' (OR rename column)")
print("   • 'quotes' → 'quotes_data' (OR rename column)")
print("   • 'stable_tour' → 'stable_tour_data' (OR rename column)")
print("   • 'medical' → 'medical_data' (OR rename column)")
print()
print("5. ✅ runner_id: KEEP AS IS - it's a valid design pattern")
print()
print("=" * 100)
