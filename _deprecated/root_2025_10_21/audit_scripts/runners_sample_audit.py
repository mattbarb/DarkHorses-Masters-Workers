"""
Sample-based audit for ra_runners table
Uses small samples to estimate field population
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient

# Fields to check
RUNNERS_FIELDS = {
    'race_entry': ['draw', 'number', 'form', 'weight', 'headgear'],
    'results_original': ['position', 'distance_beaten', 'prize_won', 'starting_price', 'finishing_time'],
    'results_enhanced': ['starting_price_decimal', 'race_comment', 'jockey_silk_url',
                       'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs'],
    'pedigree': ['sire_id', 'sire_name', 'dam_id', 'dam_name', 'damsire_id', 'damsire_name'],
    'duplicates': ['silk_url', 'jockey_silk_url']
}

def sample_field_population(client, field, sample_size=5000):
    """Sample records to estimate field population"""
    try:
        # Get records ordered by most recent
        result = client.client.from_('ra_runners').select(field).order('created_at', desc=True).limit(sample_size).execute()

        if not hasattr(result, 'data') or not result.data:
            return {'error': 'No data returned'}

        data = result.data
        total = len(data)
        non_null = sum(1 for row in data if row.get(field) is not None and row.get(field) != '')

        return {
            'sample_size': total,
            'non_null': non_null,
            'null': total - non_null,
            'population_pct': round((non_null / total * 100) if total > 0 else 0, 2)
        }
    except Exception as e:
        return {'error': str(e)[:100]}

def main():
    """Main audit"""
    print("="*80)
    print("RA_RUNNERS SAMPLE-BASED AUDIT")
    print("Analyzing recent 5,000 records per field")
    print("="*80)

    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    total_rows = client.get_table_count('ra_runners')
    print(f"\nTotal ra_runners rows: {total_rows:,}")
    print(f"Sample size per field: 5,000 (most recent records)\n")

    all_results = {}

    for category, fields in RUNNERS_FIELDS.items():
        print(f"\n{category.upper()} FIELDS:")
        print("-" * 70)

        category_results = {}

        for field in fields:
            stats = sample_field_population(client, field)

            if 'error' not in stats:
                pop_pct = stats['population_pct']

                # Status icon
                if pop_pct >= 99:
                    icon = "✓"
                elif pop_pct >= 75:
                    icon = "⚠"
                elif pop_pct > 0:
                    icon = "⚠"
                else:
                    icon = "❌"

                null_count = stats['null']
                non_null = stats['non_null']

                print(f"{icon} {field:.<45} {pop_pct:>6.2f}% ({non_null:,}/{stats['sample_size']:,} non-null)")
                category_results[field] = stats
            else:
                print(f"❌ {field:.<45} ERROR: {stats['error']}")
                category_results[field] = stats

        all_results[category] = category_results

    # Check for data in sample records
    print(f"\n{'='*80}")
    print("SAMPLE DATA INSPECTION")
    print(f"{'='*80}\n")

    try:
        # Get one full record to see what's actually there
        result = client.client.from_('ra_runners').select('*').order('created_at', desc=True).limit(1).execute()

        if hasattr(result, 'data') and result.data:
            record = result.data[0]

            print("Checking duplicate fields in sample record:")
            print(f"  silk_url value: {record.get('silk_url', 'NULL')[:80] if record.get('silk_url') else 'NULL'}")
            print(f"  jockey_silk_url value: {record.get('jockey_silk_url', 'NULL')[:80] if record.get('jockey_silk_url') else 'NULL'}")

            if record.get('silk_url') and not record.get('jockey_silk_url'):
                print("  → FINDING: silk_url is populated, jockey_silk_url is NULL")
            elif record.get('jockey_silk_url') and not record.get('silk_url'):
                print("  → FINDING: jockey_silk_url is populated, silk_url is NULL")
            elif record.get('silk_url') and record.get('jockey_silk_url'):
                if record['silk_url'] == record['jockey_silk_url']:
                    print("  → FINDING: DUPLICATE - Both fields have IDENTICAL values")
                else:
                    print("  → FINDING: Both fields populated with DIFFERENT values")
            else:
                print("  → FINDING: Both fields are NULL")

    except Exception as e:
        print(f"Error inspecting sample: {e}")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    for category, results in all_results.items():
        fully_pop = sum(1 for s in results.values() if 'error' not in s and s.get('population_pct', 0) >= 99)
        mostly_pop = sum(1 for s in results.values() if 'error' not in s and 75 <= s.get('population_pct', 0) < 99)
        partial = sum(1 for s in results.values() if 'error' not in s and 0 < s.get('population_pct', 0) < 75)
        empty = sum(1 for s in results.values() if 'error' not in s and s.get('population_pct', 0) == 0)
        errors = sum(1 for s in results.values() if 'error' in s)

        print(f"{category.upper()}:")
        print(f"  ✓ Fully populated (≥99%): {fully_pop}")
        print(f"  ⚠ Mostly populated (75-98%): {mostly_pop}")
        print(f"  ⚠ Partially populated (1-74%): {partial}")
        print(f"  ❌ Empty (0%): {empty}")
        if errors > 0:
            print(f"  ❌ Errors: {errors}")
        print()

if __name__ == '__main__':
    main()
