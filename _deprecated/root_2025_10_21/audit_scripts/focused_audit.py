"""
Focused Data Quality Audit
Checks NULL population for critical fields using filtered queries
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient

# Fields to check for each table
FIELDS_TO_CHECK = {
    'ra_runners': {
        'core': ['runner_id', 'race_id', 'horse_id', 'jockey_id', 'trainer_id'],
        'race_entry': ['draw', 'number', 'form', 'weight'],
        'results_original': ['position', 'distance_beaten', 'prize_won', 'starting_price', 'finishing_time'],
        'results_enhanced': ['starting_price_decimal', 'race_comment', 'jockey_silk_url',
                           'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs'],
        'pedigree': ['sire_id', 'sire_name', 'dam_id', 'dam_name', 'damsire_id', 'damsire_name'],
        'duplicates': ['silk_url', 'jockey_silk_url']  # Potential duplicate columns
    },
    'ra_races': {
        'core': ['race_id', 'course_id', 'race_date', 'off_time'],
        'details': ['race_name', 'distance', 'race_class', 'race_type', 'surface'],
        'classification': ['age_band', 'going', 'prize_money']
    },
    'ra_horses': {
        'core': ['horse_id', 'name', 'sex'],
        'enriched': ['dob', 'sex_code', 'colour', 'colour_code', 'region']
    },
    'ra_horse_pedigree': {
        'core': ['horse_id'],
        'pedigree': ['sire', 'sire_id', 'dam', 'dam_id', 'damsire', 'damsire_id'],
        'breeder': ['breeder', 'region']
    }
}

def get_null_percentage(client, table, field):
    """Get percentage of NULL values for a field"""
    try:
        # Get total count
        total = client.get_table_count(table)

        if total == 0:
            return {'total': 0, 'null_count': 0, 'non_null_count': 0, 'null_pct': 0, 'population_pct': 0}

        # Count non-null
        result = client.client.from_(table).select(field, count='exact').not_.is_(field, 'null').limit(0).execute()
        non_null = result.count if hasattr(result, 'count') else 0

        # Calculate percentages
        null_count = total - non_null
        null_pct = (null_count / total * 100) if total > 0 else 0
        population_pct = (non_null / total * 100) if total > 0 else 0

        return {
            'total': total,
            'null_count': null_count,
            'non_null_count': non_null,
            'null_pct': round(null_pct, 2),
            'population_pct': round(population_pct, 2)
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_table_focused(client, table_name, fields_dict):
    """Analyze specific fields in a table"""
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")

    # Get total count
    total = client.get_table_count(table_name)
    print(f"Total Rows: {total:,}\n")

    if total == 0:
        print("⚠️  TABLE IS EMPTY\n")
        return {'table': table_name, 'total_rows': 0, 'status': 'empty'}

    results = {
        'table': table_name,
        'total_rows': total,
        'categories': {}
    }

    # Analyze each category of fields
    for category, fields in fields_dict.items():
        print(f"\n{category.upper()} FIELDS:")
        print("-" * 60)

        category_results = {}

        for field in fields:
            stats = get_null_percentage(client, table_name, field)

            if 'error' not in stats:
                pop_pct = stats['population_pct']
                null_pct = stats['null_pct']

                # Determine status icon
                if pop_pct == 100:
                    icon = "✓"
                elif pop_pct >= 75:
                    icon = "⚠"
                elif pop_pct > 0:
                    icon = "⚠"
                else:
                    icon = "❌"

                print(f"{icon} {field:.<40} {pop_pct:>6.2f}% populated ({null_pct:.2f}% NULL)")

                category_results[field] = stats
            else:
                print(f"❌ {field:.<40} ERROR: {stats['error'][:40]}")
                category_results[field] = stats

        results['categories'][category] = category_results

    return results

def identify_duplicates(results):
    """Identify duplicate columns by comparing field values"""
    print(f"\n{'='*80}")
    print("DUPLICATE COLUMN ANALYSIS")
    print(f"{'='*80}\n")

    # Check ra_runners silk_url vs jockey_silk_url
    if 'ra_runners' in results:
        runner_cats = results['ra_runners'].get('categories', {})
        dup_cat = runner_cats.get('duplicates', {})

        if 'silk_url' in dup_cat and 'jockey_silk_url' in dup_cat:
            silk_pop = dup_cat['silk_url'].get('population_pct', 0)
            jockey_silk_pop = dup_cat['jockey_silk_url'].get('population_pct', 0)

            print("ra_runners - Potential Duplicate:")
            print(f"  silk_url: {silk_pop}% populated")
            print(f"  jockey_silk_url: {jockey_silk_pop}% populated")

            if silk_pop > 0 and jockey_silk_pop == 0:
                print("  ✓ RECOMMENDATION: Use silk_url (populated), jockey_silk_url is empty duplicate")
            elif jockey_silk_pop > 0 and silk_pop == 0:
                print("  ✓ RECOMMENDATION: Use jockey_silk_url (populated), silk_url is empty duplicate")
            elif silk_pop > 0 and jockey_silk_pop > 0:
                print("  ⚠️  RECOMMENDATION: Check if values match - may need data comparison")
            else:
                print("  ❌ Both columns are empty")
            print()

def generate_summary(results):
    """Generate overall summary"""
    print(f"\n{'='*80}")
    print("EXECUTIVE SUMMARY")
    print(f"{'='*80}\n")

    for table, data in results.items():
        if data.get('status') == 'empty':
            print(f"{table}: EMPTY TABLE")
            continue

        print(f"\n{table.upper()}")
        print("-" * 60)

        total_rows = data.get('total_rows', 0)
        print(f"Total Rows: {total_rows:,}")

        for category, fields_data in data.get('categories', {}).items():
            # Count field statuses
            fully_pop = sum(1 for f, s in fields_data.items() if 'error' not in s and s.get('population_pct') == 100)
            mostly_pop = sum(1 for f, s in fields_data.items() if 'error' not in s and 75 <= s.get('population_pct', 0) < 100)
            partial_pop = sum(1 for f, s in fields_data.items() if 'error' not in s and 0 < s.get('population_pct', 0) < 75)
            empty = sum(1 for f, s in fields_data.items() if 'error' not in s and s.get('population_pct') == 0)
            errors = sum(1 for f, s in fields_data.items() if 'error' in s)

            print(f"\n  {category.upper()}:")
            print(f"    ✓ Fully populated (100%): {fully_pop}")
            print(f"    ⚠ Mostly populated (75-99%): {mostly_pop}")
            print(f"    ⚠ Partially populated (1-74%): {partial_pop}")
            print(f"    ❌ Empty (0%): {empty}")
            if errors > 0:
                print(f"    ❌ Errors: {errors}")

def main():
    """Main audit"""
    print("="*80)
    print("FOCUSED DATA QUALITY AUDIT")
    print("DarkHorses Racing Database - Critical Fields Analysis")
    print("="*80)

    # Initialize
    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Run analysis
    all_results = {}

    for table, fields_dict in FIELDS_TO_CHECK.items():
        try:
            result = analyze_table_focused(client, table, fields_dict)
            all_results[table] = result
        except Exception as e:
            print(f"\n❌ ERROR analyzing {table}: {e}")
            import traceback
            traceback.print_exc()
            all_results[table] = {'table': table, 'error': str(e), 'status': 'error'}

    # Analyze duplicates
    identify_duplicates(all_results)

    # Generate summary
    generate_summary(all_results)

    # Save results
    output_file = Path(__file__).parent / 'focused_audit_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"Full results saved to: {output_file}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
