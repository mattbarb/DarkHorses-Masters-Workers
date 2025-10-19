"""
Comprehensive Data Quality Audit
Uses SupabaseReferenceClient to analyze database schema and data population
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

def get_schema_info(client, table_name):
    """Query schema information from information_schema"""
    query = f"""
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length,
        numeric_precision,
        numeric_scale
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """

    try:
        result = client.client.rpc('exec_sql', {'query': query}).execute()
        return result.data if hasattr(result, 'data') else []
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
        # Try alternative approach
        try:
            result = client.client.table('information_schema.columns').select('*').eq('table_name', table_name).execute()
            return result.data if hasattr(result, 'data') else []
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
            return []

def get_population_stats(client, table_name, column_name):
    """Get population statistics for a single column"""
    query = f"""
    SELECT
        COUNT(*) as total_rows,
        COUNT({column_name}) as non_null_count,
        COUNT(*) - COUNT({column_name}) as null_count,
        ROUND(
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE (COUNT({column_name})::numeric / COUNT(*)::numeric * 100)
            END,
            2
        ) as population_pct
    FROM {table_name};
    """

    try:
        result = client.client.rpc('exec_sql', {'query': query}).execute()
        if hasattr(result, 'data') and result.data:
            return result.data[0]
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

    return None

def get_table_row_count(client, table_name):
    """Get total row count for table"""
    try:
        result = client.client.from_(table_name).select('*', count='exact').limit(0).execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        print(f"Error getting row count for {table_name}: {e}")
        return 0

def analyze_table(client, table_name):
    """Comprehensive analysis of a single table"""
    print(f"\n{'='*80}")
    print(f"ANALYZING TABLE: {table_name}")
    print(f"{'='*80}")

    # Get row count
    row_count = get_table_row_count(client, table_name)
    print(f"Total Rows: {row_count:,}")

    if row_count == 0:
        print("⚠️  TABLE IS EMPTY - Skipping column analysis")
        return {
            'table_name': table_name,
            'row_count': row_count,
            'columns': [],
            'population_stats': {},
            'status': 'empty'
        }

    # Get schema
    print(f"\nFetching schema...")
    schema = get_schema_info(client, table_name)
    print(f"Columns Found: {len(schema)}")

    if not schema:
        print("⚠️  Could not retrieve schema")
        return {
            'table_name': table_name,
            'row_count': row_count,
            'columns': [],
            'population_stats': {},
            'status': 'schema_error'
        }

    # Analyze each column
    print(f"\nAnalyzing column population...")
    population_stats = {}

    for idx, col in enumerate(schema, 1):
        col_name = col.get('column_name', 'unknown')
        data_type = col.get('data_type', 'unknown')

        # Show progress
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(schema)} columns analyzed...")

        # Get population stats
        stats = get_population_stats(client, table_name, col_name)

        if stats:
            population_stats[col_name] = {
                'data_type': data_type,
                'is_nullable': col.get('is_nullable', 'YES'),
                'total_rows': stats.get('total_rows', 0),
                'non_null_count': stats.get('non_null_count', 0),
                'null_count': stats.get('null_count', 0),
                'population_pct': float(stats.get('population_pct', 0))
            }

    # Print summary
    print(f"\n{'-'*80}")
    print(f"COLUMN POPULATION SUMMARY ({table_name})")
    print(f"{'-'*80}")

    # Sort by population percentage
    sorted_cols = sorted(
        population_stats.items(),
        key=lambda x: x[1]['population_pct'],
        reverse=True
    )

    # Categorize columns
    fully_populated = []  # 100%
    mostly_populated = []  # 75-99%
    partially_populated = []  # 1-74%
    empty_columns = []  # 0%

    for col_name, stats in sorted_cols:
        pct = stats['population_pct']

        if pct == 100.0:
            fully_populated.append(col_name)
        elif pct >= 75.0:
            mostly_populated.append(col_name)
        elif pct > 0:
            partially_populated.append(col_name)
        else:
            empty_columns.append(col_name)

    print(f"\n✓ Fully Populated (100%): {len(fully_populated)} columns")
    if fully_populated:
        for col in fully_populated[:10]:  # Show first 10
            print(f"    {col}")
        if len(fully_populated) > 10:
            print(f"    ... and {len(fully_populated) - 10} more")

    print(f"\n⚠ Mostly Populated (75-99%): {len(mostly_populated)} columns")
    for col in mostly_populated:
        pct = population_stats[col]['population_pct']
        print(f"    {col}: {pct}%")

    print(f"\n⚠ Partially Populated (1-74%): {len(partially_populated)} columns")
    for col in partially_populated:
        pct = population_stats[col]['population_pct']
        print(f"    {col}: {pct}%")

    print(f"\n❌ Empty Columns (0%): {len(empty_columns)} columns")
    for col in empty_columns:
        print(f"    {col}")

    return {
        'table_name': table_name,
        'row_count': row_count,
        'columns': schema,
        'population_stats': population_stats,
        'summary': {
            'fully_populated': len(fully_populated),
            'mostly_populated': len(mostly_populated),
            'partially_populated': len(partially_populated),
            'empty_columns': len(empty_columns),
            'total_columns': len(schema)
        },
        'status': 'analyzed'
    }

def main():
    """Main audit execution"""
    print("="*80)
    print("DATA QUALITY AUDIT - DarkHorses Racing Database")
    print("="*80)

    # Initialize client
    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Tables to audit
    tables = ['ra_runners', 'ra_races', 'ra_results', 'ra_horses', 'ra_horse_pedigree']

    # Analyze each table
    audit_results = {}

    for table in tables:
        try:
            result = analyze_table(client, table)
            audit_results[table] = result
        except Exception as e:
            print(f"\n❌ ERROR analyzing {table}: {str(e)}")
            audit_results[table] = {
                'table_name': table,
                'error': str(e),
                'status': 'error'
            }

    # Save results
    output_file = Path(__file__).parent / 'data_quality_audit_report.json'
    with open(output_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"AUDIT COMPLETE")
    print(f"{'='*80}")
    print(f"\nFull results saved to: {output_file}")

    # Print overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")

    for table, result in audit_results.items():
        if result['status'] == 'analyzed':
            summary = result['summary']
            row_count = result['row_count']
            print(f"\n{table}:")
            print(f"  Rows: {row_count:,}")
            print(f"  Columns: {summary['total_columns']}")
            print(f"  Fully Populated: {summary['fully_populated']}")
            print(f"  Mostly Populated: {summary['mostly_populated']}")
            print(f"  Partially Populated: {summary['partially_populated']}")
            print(f"  Empty: {summary['empty_columns']}")
        elif result['status'] == 'empty':
            print(f"\n{table}: EMPTY TABLE")
        else:
            print(f"\n{table}: ERROR - {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    main()
