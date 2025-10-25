"""
Direct Data Quality Audit
Uses direct table queries to analyze data population
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient

# Expected schema based on migrations
EXPECTED_SCHEMAS = {
    'ra_runners': [
        # Core identification
        'runner_id', 'race_id', 'horse_id', 'jockey_id', 'trainer_id', 'owner_id',
        # Race entry details
        'draw', 'headgear', 'lbs', 'number', 'form', 'age',
        # Result fields (from migration 005/006)
        'position', 'distance_beaten', 'prize_won', 'starting_price', 'finishing_time', 'result_updated_at',
        # Enhanced fields (from migration 011)
        'starting_price_decimal', 'race_comment', 'jockey_silk_url',
        'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs',
        # Horse details (from migration 003)
        'dob', 'colour', 'breeder',
        'dam_region', 'sire_region', 'damsire_region',
        # Trainer details (from migration 003)
        'trainer_location', 'trainer_rtf', 'trainer_14_days_data',
        # Premium content (from migration 003)
        'spotlight',
        # Medical (from migration 003)
        'wind_surgery', 'wind_surgery_run',
        # Array fields (from migration 003)
        'past_results_flags', 'quotes_data', 'stable_tour_data', 'medical_data',
        # Metadata
        'created_at', 'updated_at'
    ],
    'ra_races': [
        # Core identification
        'race_id', 'course_id',
        # Race details
        'off_time', 'date', 'region_code', 'race_name', 'distance', 'age_band',
        'race_class', 'rating_band', 'race_type', 'surface', 'pattern',
        # Classification (from migration 003)
        'sex_restriction', 'jumps', 'stalls',
        # Prize money
        'prize_money', 'currency',
        # Premium content (from migration 003)
        'tip', 'verdict', 'betting_forecast',
        # Metadata
        'created_at', 'updated_at'
    ],
    'ra_horses': [
        # Core identification
        'horse_id', 'name', 'sex',
        # Enriched fields (from migration 008)
        'dob', 'sex_code', 'colour', 'colour_code', 'region',
        # Metadata
        'created_at', 'updated_at'
    ],
    'ra_horse_pedigree': [
        # Core identification
        'horse_id',
        # Pedigree (from migration 008)
        'sire', 'sire_id', 'dam', 'dam_id',
        'damsire', 'damsire_id', 'breeder', 'region',
        # Metadata
        'created_at', 'updated_at'
    ]
}

def get_sample_record(client, table_name, limit=1):
    """Get a sample record to infer schema"""
    try:
        result = client.client.from_(table_name).select('*').limit(limit).execute()
        if hasattr(result, 'data') and result.data:
            return result.data[0]
    except Exception as e:
        print(f"Error getting sample from {table_name}: {e}")
    return None

def analyze_column_sample(client, table_name, column_name, sample_size=1000):
    """Analyze a column by sampling records"""
    try:
        # Get total count
        total = client.get_table_count(table_name)

        # Get sample with non-null values
        result_non_null = client.client.from_(table_name).select(column_name).not_.is_(column_name, 'null').limit(sample_size).execute()
        non_null_sample = len(result_non_null.data) if hasattr(result_non_null, 'data') else 0

        # Get sample with null values
        result_null = client.client.from_(table_name).select(column_name).is_(column_name, 'null').limit(sample_size).execute()
        null_sample = len(result_null.data) if hasattr(result_null, 'data') else 0

        # Estimate population percentage
        if sample_size >= total:
            # We have all records
            population_pct = (non_null_sample / total * 100) if total > 0 else 0
        else:
            # Estimate from sample
            population_pct = (non_null_sample / (non_null_sample + null_sample) * 100) if (non_null_sample + null_sample) > 0 else 0

        return {
            'total_rows': total,
            'non_null_sample': non_null_sample,
            'null_sample': null_sample,
            'estimated_population_pct': round(population_pct, 2)
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_table_comprehensive(client, table_name):
    """Comprehensive table analysis using sampling"""
    print(f"\n{'='*80}")
    print(f"ANALYZING TABLE: {table_name}")
    print(f"{'='*80}")

    # Get row count
    row_count = client.get_table_count(table_name)
    print(f"Total Rows: {row_count:,}")

    if row_count == 0:
        print("⚠️  TABLE IS EMPTY")
        return {
            'table_name': table_name,
            'row_count': 0,
            'status': 'empty'
        }

    # Get sample record to infer schema
    print("Fetching sample record to infer schema...")
    sample = get_sample_record(client, table_name)

    if not sample:
        print("⚠️  Could not get sample record")
        return {
            'table_name': table_name,
            'row_count': row_count,
            'status': 'error',
            'error': 'Could not get sample record'
        }

    actual_columns = list(sample.keys())
    expected_columns = EXPECTED_SCHEMAS.get(table_name, [])

    print(f"\nActual Columns: {len(actual_columns)}")
    print(f"Expected Columns: {len(expected_columns)}")

    # Check for missing or extra columns
    missing_columns = set(expected_columns) - set(actual_columns)
    extra_columns = set(actual_columns) - set(expected_columns)

    if missing_columns:
        print(f"\n⚠️ MISSING COLUMNS ({len(missing_columns)}):")
        for col in sorted(missing_columns):
            print(f"    {col}")

    if extra_columns:
        print(f"\n⚠️ EXTRA COLUMNS ({len(extra_columns)}):")
        for col in sorted(extra_columns):
            print(f"    {col}")

    # Analyze each actual column (using smaller sample for speed)
    print(f"\nAnalyzing column population (sampling approach)...")
    column_analysis = {}

    for idx, col in enumerate(actual_columns, 1):
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(actual_columns)} columns...")

        # Sample-based analysis
        stats = analyze_column_sample(client, table_name, col, sample_size=1000)
        column_analysis[col] = stats

    # Categorize columns
    fully_populated = []  # ~100%
    mostly_populated = []  # 75-99%
    partially_populated = []  # 1-74%
    empty_columns = []  # ~0%

    print(f"\n{'-'*80}")
    print("COLUMN POPULATION ANALYSIS (Sample-based estimates)")
    print(f"{'-'*80}")

    for col, stats in column_analysis.items():
        if 'error' in stats:
            continue

        pct = stats.get('estimated_population_pct', 0)

        if pct >= 99.0:
            fully_populated.append((col, pct))
        elif pct >= 75.0:
            mostly_populated.append((col, pct))
        elif pct > 0:
            partially_populated.append((col, pct))
        else:
            empty_columns.append((col, pct))

    # Print summaries
    print(f"\n✓ Fully Populated (~100%): {len(fully_populated)} columns")
    for col, pct in sorted(fully_populated, key=lambda x: x[1], reverse=True)[:15]:
        print(f"    {col}: {pct}%")
    if len(fully_populated) > 15:
        print(f"    ... and {len(fully_populated) - 15} more")

    print(f"\n⚠ Mostly Populated (75-99%): {len(mostly_populated)} columns")
    for col, pct in sorted(mostly_populated, key=lambda x: x[1], reverse=True):
        print(f"    {col}: {pct}%")

    print(f"\n⚠ Partially Populated (1-74%): {len(partially_populated)} columns")
    for col, pct in sorted(partially_populated, key=lambda x: x[1], reverse=True):
        print(f"    {col}: {pct}%")

    print(f"\n❌ Empty Columns (~0%): {len(empty_columns)} columns")
    for col, pct in sorted(empty_columns):
        print(f"    {col}")

    return {
        'table_name': table_name,
        'row_count': row_count,
        'actual_columns': actual_columns,
        'expected_columns': expected_columns,
        'missing_columns': list(missing_columns),
        'extra_columns': list(extra_columns),
        'column_analysis': column_analysis,
        'summary': {
            'total_columns': len(actual_columns),
            'fully_populated': len(fully_populated),
            'mostly_populated': len(mostly_populated),
            'partially_populated': len(partially_populated),
            'empty_columns': len(empty_columns)
        },
        'status': 'analyzed'
    }

def main():
    """Main audit"""
    print("="*80)
    print("DATA QUALITY AUDIT - DarkHorses Racing Database")
    print("Direct Query Approach with Sampling")
    print("="*80)

    # Initialize
    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Tables to audit (note: ra_results doesn't exist according to earlier error)
    tables = ['ra_runners', 'ra_races', 'ra_horses', 'ra_horse_pedigree']

    audit_results = {}

    for table in tables:
        try:
            result = analyze_table_comprehensive(client, table)
            audit_results[table] = result
        except Exception as e:
            print(f"\n❌ ERROR analyzing {table}: {str(e)}")
            import traceback
            traceback.print_exc()
            audit_results[table] = {
                'table_name': table,
                'error': str(e),
                'status': 'error'
            }

    # Save results
    output_file = Path(__file__).parent / 'data_quality_audit_comprehensive.json'
    with open(output_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}")
    print(f"\nFull results saved to: {output_file}")

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")

    for table, result in audit_results.items():
        if result.get('status') == 'analyzed':
            summary = result['summary']
            print(f"\n{table}:")
            print(f"  Rows: {result['row_count']:,}")
            print(f"  Actual Columns: {summary['total_columns']}")
            print(f"  Fully Populated: {summary['fully_populated']}")
            print(f"  Mostly Populated: {summary['mostly_populated']}")
            print(f"  Partially Populated: {summary['partially_populated']}")
            print(f"  Empty: {summary['empty_columns']}")

            if result.get('missing_columns'):
                print(f"  ⚠️  Missing {len(result['missing_columns'])} expected columns")
            if result.get('extra_columns'):
                print(f"  ⚠️  Has {len(result['extra_columns'])} unexpected columns")
        else:
            print(f"\n{table}: {result.get('status', 'UNKNOWN').upper()}")

if __name__ == '__main__':
    main()
