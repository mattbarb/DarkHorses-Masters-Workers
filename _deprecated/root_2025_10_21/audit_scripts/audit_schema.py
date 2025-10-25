"""
Data Quality Audit Script
Queries Supabase database to analyze schema and data population
"""

import os
import json
from supabase import create_client
from collections import defaultdict

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://amsjvmlaknnvppxsgpfk.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tables to audit
TABLES = ['ra_runners', 'ra_races', 'ra_results', 'ra_horses', 'ra_horse_pedigree']

def get_table_schema(table_name):
    """Get column information for a table"""
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
    result = supabase.rpc('exec_sql', {'query': query}).execute()
    return result.data

def get_column_population(table_name, columns):
    """Get population statistics for each column"""
    stats = {}

    # First get total row count
    count_result = supabase.from_(table_name).select('*', count='exact').limit(1).execute()
    total_rows = count_result.count

    print(f"\n{table_name}: {total_rows:,} total rows")

    if total_rows == 0:
        print(f"  Table {table_name} is empty!")
        return stats

    # For each column, query population stats
    for col in columns[:10]:  # Limit to first 10 columns to avoid too many queries
        col_name = col['column_name']

        try:
            # Count non-null values
            query = f"""
            SELECT
                COUNT(*) as total_rows,
                COUNT({col_name}) as non_null_count,
                COUNT(*) - COUNT({col_name}) as null_count,
                ROUND(COUNT({col_name})::numeric / NULLIF(COUNT(*), 0)::numeric * 100, 2) as population_pct
            FROM {table_name};
            """

            result = supabase.rpc('exec_sql', {'query': query}).execute()

            if result.data:
                stats[col_name] = result.data[0]
                pct = stats[col_name]['population_pct']
                print(f"  {col_name}: {pct}% populated")
        except Exception as e:
            print(f"  Error checking {col_name}: {str(e)}")
            stats[col_name] = {'error': str(e)}

    return stats

def main():
    """Main audit function"""
    audit_results = {}

    print("=" * 80)
    print("DATA QUALITY AUDIT - DarkHorses Racing Database")
    print("=" * 80)

    for table_name in TABLES:
        print(f"\n\nAuditing {table_name}...")
        print("-" * 80)

        try:
            # Get schema
            schema = get_table_schema(table_name)
            print(f"Schema: {len(schema)} columns")

            # Get population stats
            population = get_column_population(table_name, schema)

            audit_results[table_name] = {
                'schema': schema,
                'population': population,
                'total_columns': len(schema)
            }

        except Exception as e:
            print(f"ERROR auditing {table_name}: {str(e)}")
            audit_results[table_name] = {'error': str(e)}

    # Save results
    output_file = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/audit_results.json'
    with open(output_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print(f"Audit complete. Results saved to: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
