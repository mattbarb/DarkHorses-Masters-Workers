#!/usr/bin/env python3
"""
Comprehensive Database Audit Script for DarkHorses Racing Database
"""

import sys
from pathlib import Path
from collections import defaultdict
import json

sys.path.insert(0, '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers')

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

def get_table_schema(db, table_name):
    """Get complete schema information for a table"""
    query = f"""
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    response = db.client.rpc('exec_sql', {'query': query}).execute()
    return response.data if response.data else []

def get_table_constraints(db, table_name):
    """Get constraints (PK, FK, unique) for a table"""
    query = f"""
    SELECT
        tc.constraint_name,
        tc.constraint_type,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    LEFT JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.table_schema = 'public'
    AND tc.table_name = '{table_name}';
    """
    response = db.client.rpc('exec_sql', {'query': query}).execute()
    return response.data if response.data else []

def get_row_count(db, table_name):
    """Get total row count for a table"""
    response = db.client.table(table_name).select('*', count='exact').limit(1).execute()
    return response.count

def analyze_null_percentages(db, table_name, columns):
    """Analyze NULL percentages for each column"""
    # Build a query that counts NULLs for each column
    null_checks = []
    for col in columns:
        col_name = col['column_name']
        null_checks.append(f"COUNT(CASE WHEN {col_name} IS NULL THEN 1 END) as {col_name}_nulls")

    query = f"""
    SELECT
        COUNT(*) as total_count,
        {', '.join(null_checks)}
    FROM {table_name};
    """

    try:
        response = db.client.rpc('exec_sql', {'query': query}).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error analyzing NULLs for {table_name}: {e}")
        return None

def get_date_range(db, table_name, date_column):
    """Get date range for a date column"""
    query = f"""
    SELECT
        MIN({date_column}) as min_date,
        MAX({date_column}) as max_date,
        COUNT(DISTINCT {date_column}) as unique_dates
    FROM {table_name}
    WHERE {date_column} IS NOT NULL;
    """
    try:
        response = db.client.rpc('exec_sql', {'query': query}).execute()
        return response.data[0] if response.data else None
    except:
        return None

def check_foreign_key_integrity(db, table_name, fk_column, ref_table, ref_column):
    """Check if all foreign key values exist in referenced table"""
    query = f"""
    SELECT COUNT(*) as orphaned_count
    FROM {table_name} t
    WHERE t.{fk_column} IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM {ref_table} r
        WHERE r.{ref_column} = t.{fk_column}
    );
    """
    try:
        response = db.client.rpc('exec_sql', {'query': query}).execute()
        return response.data[0]['orphaned_count'] if response.data else 0
    except Exception as e:
        print(f"Error checking FK integrity: {e}")
        return -1

def sample_api_data(db, table_name):
    """Sample api_data JSONB column if it exists"""
    query = f"""
    SELECT
        COUNT(*) FILTER (WHERE api_data IS NOT NULL) as populated_count,
        COUNT(*) as total_count
    FROM {table_name};
    """
    try:
        response = db.client.rpc('exec_sql', {'query': query}).execute()
        return response.data[0] if response.data else None
    except:
        return None

def main():
    print("="*80)
    print("DARKHORSES RACING DATABASE AUDIT")
    print("="*80)
    print()

    # Connect to database
    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
    print("✓ Connected to Supabase database")
    print()

    # Define tables to audit
    tables = [
        'ra_courses',
        'ra_bookmakers',
        'ra_horses',
        'ra_jockeys',
        'ra_trainers',
        'ra_owners',
        'ra_races',
        'ra_runners',
        'ra_results',
        'ra_horse_pedigree'
    ]

    audit_results = {}

    for table_name in tables:
        print(f"\n{'='*80}")
        print(f"ANALYZING TABLE: {table_name}")
        print(f"{'='*80}")

        try:
            # Get schema
            schema = get_table_schema(db, table_name)
            if not schema:
                print(f"⚠ Table {table_name} does not exist or has no columns")
                continue

            print(f"\n✓ Found {len(schema)} columns")

            # Get constraints
            constraints = get_table_constraints(db, table_name)
            print(f"✓ Found {len(constraints)} constraints")

            # Get row count
            row_count = get_row_count(db, table_name)
            print(f"✓ Row count: {row_count:,}")

            # Analyze NULLs
            print(f"\nAnalyzing NULL percentages...")
            null_analysis = analyze_null_percentages(db, table_name, schema)

            # Store results
            audit_results[table_name] = {
                'schema': schema,
                'constraints': constraints,
                'row_count': row_count,
                'null_analysis': null_analysis
            }

            # Print schema details
            print(f"\nCOLUMN DETAILS:")
            print(f"{'Column Name':<35} {'Type':<20} {'Nullable':<10}")
            print("-"*70)
            for col in schema:
                print(f"{col['column_name']:<35} {col['data_type']:<20} {col['is_nullable']:<10}")

            # Print NULL analysis
            if null_analysis:
                total = null_analysis['total_count']
                print(f"\nNULL ANALYSIS (Total rows: {total:,}):")
                print(f"{'Column Name':<35} {'NULL Count':<15} {'NULL %':<10}")
                print("-"*70)
                for col in schema:
                    col_name = col['column_name']
                    null_key = f"{col_name}_nulls"
                    if null_key in null_analysis:
                        null_count = null_analysis[null_key]
                        null_pct = (null_count / total * 100) if total > 0 else 0
                        status = "✗" if null_pct == 100 else ("⚠" if null_pct > 90 else "✓")
                        print(f"{status} {col_name:<33} {null_count:<15,} {null_pct:>6.1f}%")

            # Check for api_data column
            has_api_data = any(col['column_name'] == 'api_data' for col in schema)
            if has_api_data:
                api_data_stats = sample_api_data(db, table_name)
                if api_data_stats:
                    populated = api_data_stats['populated_count']
                    total = api_data_stats['total_count']
                    pct = (populated / total * 100) if total > 0 else 0
                    print(f"\nAPI_DATA USAGE: {populated:,} / {total:,} rows ({pct:.1f}%) have data")

            # Check date ranges for date columns
            date_columns = [col['column_name'] for col in schema if 'date' in col['data_type'].lower() or 'timestamp' in col['data_type'].lower()]
            if date_columns:
                print(f"\nDATE RANGE ANALYSIS:")
                for date_col in date_columns:
                    date_range = get_date_range(db, table_name, date_col)
                    if date_range and date_range.get('min_date'):
                        print(f"  {date_col}: {date_range['min_date']} to {date_range['max_date']} ({date_range['unique_dates']:,} unique dates)")

        except Exception as e:
            print(f"✗ Error analyzing {table_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}")

    # Save results to file
    output_file = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/audit_results.json'
    with open(output_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)
    print(f"\n✓ Detailed results saved to: {output_file}")

if __name__ == '__main__':
    main()
