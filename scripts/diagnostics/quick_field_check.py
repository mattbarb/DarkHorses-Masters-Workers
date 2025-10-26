"""Quick check of runner field population"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import get_config
from supabase import create_client

config = get_config()
supabase = create_client(config.supabase.url, config.supabase.service_key)

# Get 3 recent runners from a specific race to avoid timeout
# First get a recent race
race_result = supabase.table('ra_mst_races') \
    .select('race_id') \
    .order('created_at', desc=True) \
    .limit(1) \
    .execute()

if not race_result.data:
    print("No races found!")
    sys.exit(1)

race_id = race_result.data[0]['race_id']
print(f"Checking runners from race: {race_id}\n")

# Get runners from that race
result = supabase.table('ra_mst_runners') \
    .select('*') \
    .eq('race_id', race_id) \
    .limit(5) \
    .execute()

runners = result.data

FIELDS = [
    'draw', 'jockey_claim', 'apprentice_allowance', 'form', 'form_string',
    'days_since_last_run', 'last_run_performance', 'career_runs', 'career_wins',
    'career_places', 'prize_money_won', 'racing_post_rating', 'race_comment',
    'silk_url', 'starting_price_decimal', 'overall_beaten_distance',
    'jockey_claim_lbs', 'weight_stones_lbs'
]

print("\nQUICK FIELD POPULATION CHECK")
print("=" * 80)
print(f"Checked {len(runners)} runners\n")

for i, runner in enumerate(runners, 1):
    print(f"Runner {i}: {runner.get('horse_name')} ({runner.get('runner_id')})")
    populated = sum(1 for f in FIELDS if runner.get(f) is not None)
    print(f"  Fields populated: {populated}/{len(FIELDS)} ({populated/len(FIELDS)*100:.1f}%)")

    # Show which fields are NULL
    null_fields = [f for f in FIELDS if runner.get(f) is None]
    if null_fields:
        print(f"  NULL fields: {', '.join(null_fields)}")
    print()

# Summary
all_stats = {}
for field in FIELDS:
    count = sum(1 for r in runners if r.get(field) is not None)
    all_stats[field] = count

print("\nField Population Summary:")
print("-" * 80)
for field, count in sorted(all_stats.items(), key=lambda x: -x[1]):
    pct = count / len(runners) * 100
    status = "✅" if pct == 100 else "❌"
    print(f"{status} {field:30s}: {count}/{len(runners)} ({pct:5.1f}%)")
