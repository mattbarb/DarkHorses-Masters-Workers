#!/usr/bin/env python3
"""
Simplified Database Audit - Uses direct queries instead of RPC
"""

import sys
from pathlib import Path
sys.path.insert(0, '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers')

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

def main():
    print("="*80)
    print("DARKHORSES RACING DATABASE AUDIT (Simplified)")
    print("="*80)
    print()

    # Connect to database
    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
    print("Connected to Supabase database\n")

    # Tables to audit
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

    print("="*80)
    print("TABLE ROW COUNTS")
    print("="*80)

    for table_name in tables:
        try:
            count = db.get_table_count(table_name)
            print(f"{table_name:<25} {count:>15,} rows")
        except Exception as e:
            print(f"{table_name:<25} ERROR: {e}")

    print()
    print("="*80)
    print("SAMPLING TABLE DATA")
    print("="*80)

    # Sample each table to see what fields are actually populated
    for table_name in tables:
        print(f"\n{table_name}:")
        print("-"*80)
        try:
            # Get first 5 rows
            response = db.client.table(table_name).select('*').limit(5).execute()
            if response.data and len(response.data) > 0:
                # Print column names
                columns = list(response.data[0].keys())
                print(f"Columns ({len(columns)} total):")
                for col in sorted(columns):
                    print(f"  - {col}")

                # Check for NULL counts in first row
                sample_row = response.data[0]
                null_cols = [k for k, v in sample_row.items() if v is None]
                if null_cols:
                    print(f"\nNULL in first row ({len(null_cols)} columns):")
                    for col in sorted(null_cols):
                        print(f"  - {col}")

                # Check if api_data exists
                if 'api_data' in sample_row:
                    has_api_data = sample_row['api_data'] is not None
                    print(f"\napi_data column: {'POPULATED' if has_api_data else 'NULL'}")

            else:
                print("  (No data in table)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print()
    print("="*80)
    print("CHECKING FOR ENTRY_ID IN RA_RUNNERS")
    print("="*80)

    # Special check for entry_id issue mentioned by user
    try:
        response = db.client.table('ra_runners').select('*').limit(1).execute()
        if response.data and len(response.data) > 0:
            sample = response.data[0]
            columns = list(sample.keys())

            if 'entry_id' in columns:
                print("entry_id column EXISTS")
                if sample['entry_id'] is not None:
                    print(f"  Sample value: {sample['entry_id']}")
                else:
                    print("  Sample value: NULL")
            else:
                print("entry_id column DOES NOT EXIST")
                print(f"\nExisting columns in ra_runners ({len(columns)}):")
                for col in sorted(columns):
                    print(f"  - {col}")
        else:
            print("No data in ra_runners table to check")
    except Exception as e:
        print(f"ERROR checking entry_id: {e}")

    print()
    print("="*80)
    print("DATE RANGE ANALYSIS")
    print("="*80)

    # Check date ranges for ra_races
    try:
        response = db.client.table('ra_races')\
            .select('race_date')\
            .order('race_date', desc=False)\
            .limit(1)\
            .execute()
        min_date = response.data[0]['race_date'] if response.data else None

        response = db.client.table('ra_races')\
            .select('race_date')\
            .order('race_date', desc=True)\
            .limit(1)\
            .execute()
        max_date = response.data[0]['race_date'] if response.data else None

        print(f"\nra_races date range:")
        print(f"  Earliest: {min_date}")
        print(f"  Latest:   {max_date}")
    except Exception as e:
        print(f"ERROR getting race date range: {e}")

    print()
    print("="*80)
    print("AUDIT COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
