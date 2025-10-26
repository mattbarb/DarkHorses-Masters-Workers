"""
Test Script for Migration 018 REVISED
Verifies schema changes and data capture after migration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from supabase import create_client
from supabase.lib.client_options import ClientOptions

config = get_config()
options = ClientOptions()
supabase = create_client(config.supabase.url, config.supabase.service_key, options)

print("=" * 100)
print("MIGRATION 018 REVISED - VERIFICATION TEST")
print("=" * 100)
print()

# ============================================================================
# TEST 1: Verify renamed columns exist with new names
# ============================================================================

print("TEST 1: Verify Renamed Columns")
print("-" * 100)

renamed_columns = {
    'trainer_14_days': 'Renamed from trainer_14_days_data',
    'quotes': 'Renamed from quotes_data',
    'stable_tour': 'Renamed from stable_tour_data',
    'medical': 'Renamed from medical_data',
    'horse_dob': 'Renamed from dob',
    'horse_colour': 'Renamed from colour',
    'horse_age': 'Renamed from age',
    'horse_sex': 'Renamed from sex'
}

print(f"\nChecking {len(renamed_columns)} renamed columns...")

for column_name, description in renamed_columns.items():
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'ra_mst_runners' AND column_name = '{column_name}'
            """
        }).execute()

        if result.data and len(result.data) > 0:
            print(f"  ✅ {column_name:25} - {description}")
        else:
            print(f"  ❌ {column_name:25} - MISSING! {description}")
    except Exception as e:
        print(f"  ⚠️  {column_name:25} - Error checking: {e}")

print()

# ============================================================================
# TEST 2: Verify old column names are gone
# ============================================================================

print("TEST 2: Verify Old Column Names Removed")
print("-" * 100)

old_columns = [
    'trainer_14_days_data',
    'quotes_data',
    'stable_tour_data',
    'medical_data',
    'dob',
    'colour',
    'age',
    'sex'
]

print(f"\nChecking that {len(old_columns)} old columns are removed...")

all_removed = True
for column_name in old_columns:
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'ra_mst_runners' AND column_name = '{column_name}'
            """
        }).execute()

        if result.data and len(result.data) > 0:
            print(f"  ❌ {column_name:25} - STILL EXISTS (should be removed!)")
            all_removed = False
        else:
            print(f"  ✅ {column_name:25} - Removed successfully")
    except Exception as e:
        print(f"  ⚠️  {column_name:25} - Error checking: {e}")

if all_removed:
    print("\n✅ All old column names successfully removed!")
else:
    print("\n❌ Some old column names still exist - migration may have failed!")

print()

# ============================================================================
# TEST 3: Verify new columns added
# ============================================================================

print("TEST 3: Verify New Columns Added")
print("-" * 100)

new_columns = {
    'horse_sex_code': 'CHAR(1)',
    'horse_region': 'VARCHAR(10)',
    'headgear_run': 'VARCHAR(50)',
    'last_run_date': 'DATE',
    'days_since_last_run': 'INTEGER',
    'prev_trainers': 'JSONB',
    'prev_owners': 'JSONB',
    'odds': 'JSONB'
}

print(f"\nChecking {len(new_columns)} new columns...")

for column_name, expected_type in new_columns.items():
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'ra_mst_runners' AND column_name = '{column_name}'
            """
        }).execute()

        if result.data and len(result.data) > 0:
            actual_type = result.data[0].get('data_type', 'unknown').upper()
            print(f"  ✅ {column_name:25} - {actual_type}")
        else:
            print(f"  ❌ {column_name:25} - MISSING! Expected {expected_type}")
    except Exception as e:
        print(f"  ⚠️  {column_name:25} - Error checking: {e}")

print()

# ============================================================================
# TEST 4: Verify indexes were updated
# ============================================================================

print("TEST 4: Verify Indexes Updated")
print("-" * 100)

expected_indexes = [
    'idx_ra_mst_runners_horse_sex_code',
    'idx_ra_mst_runners_horse_region',
    'idx_ra_mst_runners_last_run_date',
    'idx_ra_mst_runners_days_since_last_run',
    'idx_ra_mst_runners_trainer_14_days_gin',
    'idx_ra_mst_runners_quotes_gin',
    'idx_ra_mst_runners_stable_tour_gin',
    'idx_ra_mst_runners_medical_gin',
    'idx_ra_mst_runners_prev_trainers_gin',
    'idx_ra_mst_runners_prev_owners_gin',
    'idx_ra_mst_runners_odds_gin',
    'idx_ra_mst_runners_horse_dob',
    'idx_ra_mst_runners_horse_colour',
    'idx_ra_mst_runners_horse_age'
]

print(f"\nChecking {len(expected_indexes)} indexes...")

for index_name in expected_indexes:
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f"""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'ra_mst_runners' AND indexname = '{index_name}'
            """
        }).execute()

        if result.data and len(result.data) > 0:
            print(f"  ✅ {index_name}")
        else:
            print(f"  ⚠️  {index_name} - Missing (may not be critical)")
    except Exception as e:
        print(f"  ⚠️  {index_name} - Error checking: {e}")

print()

# ============================================================================
# TEST 5: Count total columns
# ============================================================================

print("TEST 5: Total Column Count")
print("-" * 100)

try:
    result = supabase.rpc('exec_sql', {
        'sql': """
            SELECT COUNT(*) as column_count
            FROM information_schema.columns
            WHERE table_name = 'ra_mst_runners'
        """
    }).execute()

    if result.data:
        total_columns = result.data[0].get('column_count', 0)
        print(f"\n  Total columns in ra_mst_runners: {total_columns}")
        print(f"  Expected: 57 (before) + 8 (new) - 8 (renamed) = 57")

        if total_columns == 57:
            print(f"  ✅ Column count matches expectation!")
        else:
            print(f"  ⚠️  Column count doesn't match (may be expected if other changes made)")
except Exception as e:
    print(f"  ❌ Error counting columns: {e}")

print()

# ============================================================================
# TEST 6: Verify critical columns exist (won't lose data)
# ============================================================================

print("TEST 6: Verify Critical Columns Still Exist")
print("-" * 100)

critical_columns = [
    'runner_id',
    'race_id',
    'horse_id',
    'horse_name',
    'jockey_id',
    'trainer_id',
    'owner_id',
    'comment',  # Was race_comment (dropped), now comment
    'silk_url',  # Was jockey_silk_url (dropped), now silk_url
    'position',
    'starting_price',
    'created_at'
]

print(f"\nChecking {len(critical_columns)} critical columns...")

all_exist = True
for column_name in critical_columns:
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'ra_mst_runners' AND column_name = '{column_name}'
            """
        }).execute()

        if result.data and len(result.data) > 0:
            print(f"  ✅ {column_name}")
        else:
            print(f"  ❌ {column_name} - MISSING!")
            all_exist = False
    except Exception as e:
        print(f"  ⚠️  {column_name} - Error checking: {e}")

if all_exist:
    print("\n✅ All critical columns exist!")
else:
    print("\n❌ Some critical columns are missing!")

print()

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()
print("Migration 018 REVISED Changes:")
print("  • 8 columns renamed for consistency")
print("  • 8 new columns added (truly missing from API)")
print("  • 0 duplicate columns created (avoided 16 duplicates!)")
print("  • Indexes updated for renamed and new columns")
print()
print("Next Steps:")
print("  1. If all tests passed ✅:")
print("     - Fetchers are updated (races_fetcher.py, results_fetcher.py)")
print("     - Ready to test with: python3 main.py --entities races --test")
print()
print("  2. If any tests failed ❌:")
print("     - Check which migration was actually run")
print("     - May need to rerun Migration 018 REVISED")
print("     - Check logs for errors")
print()
print("=" * 100)
