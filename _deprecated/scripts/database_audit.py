"""
Comprehensive Database and API Audit Script
Analyzes:
1. NULL columns in all tables
2. API endpoint usage vs available endpoints
3. Premium feature utilization
4. Missing data opportunities
"""

import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from collections import defaultdict

def analyze_table_nulls(db_client, table_name, sample_size=100):
    """Analyze NULL columns in a table"""
    print(f"\n{'='*80}")
    print(f"Analyzing table: {table_name}")
    print(f"{'='*80}")

    try:
        # Get sample records
        result = db_client.client.table(table_name).select('*').limit(sample_size).execute()

        if not result.data:
            print(f"WARNING: No data found in {table_name}")
            return

        records = result.data
        total_records = len(records)
        print(f"Sample size: {total_records} records")

        # Get total count
        count_result = db_client.client.table(table_name).select('*', count='exact').limit(1).execute()
        total_count = count_result.count if hasattr(count_result, 'count') else total_records
        print(f"Total records in table: {total_count:,}")

        # Analyze each column
        if records:
            all_columns = list(records[0].keys())
            null_stats = {}

            for column in all_columns:
                null_count = sum(1 for record in records if record.get(column) is None or record.get(column) == '')
                null_percentage = (null_count / total_records) * 100
                null_stats[column] = {
                    'null_count': null_count,
                    'total': total_records,
                    'null_percentage': null_percentage
                }

            # Sort by null percentage (descending)
            sorted_stats = sorted(null_stats.items(), key=lambda x: x[1]['null_percentage'], reverse=True)

            # Report columns with issues
            print(f"\nCOLUMN NULL ANALYSIS:")
            print(f"{'-'*80}")

            entirely_null = []
            mostly_null = []
            partially_null = []

            for column, stats in sorted_stats:
                null_pct = stats['null_percentage']

                if null_pct == 100:
                    entirely_null.append(column)
                    status = "❌ ENTIRELY NULL"
                elif null_pct >= 90:
                    mostly_null.append(column)
                    status = "⚠️  MOSTLY NULL"
                elif null_pct >= 50:
                    partially_null.append(column)
                    status = "⚠️  PARTIALLY NULL"
                else:
                    continue  # Skip columns with less than 50% nulls

                print(f"{column:35s} | {stats['null_count']:4d}/{stats['total']:4d} ({null_pct:5.1f}%) | {status}")

            # Summary
            print(f"\n{'-'*80}")
            print(f"SUMMARY:")
            print(f"  Entirely NULL (100%):     {len(entirely_null):3d} columns")
            print(f"  Mostly NULL (90-99%):     {len(mostly_null):3d} columns")
            print(f"  Partially NULL (50-89%):  {len(partially_null):3d} columns")
            print(f"  Total columns analyzed:   {len(all_columns):3d} columns")

            if entirely_null:
                print(f"\n⚠️  ENTIRELY NULL COLUMNS (should be removed or fixed):")
                for col in entirely_null:
                    print(f"    - {col}")

            return {
                'table': table_name,
                'total_records': total_count,
                'sample_size': total_records,
                'entirely_null': entirely_null,
                'mostly_null': mostly_null,
                'partially_null': partially_null
            }

    except Exception as e:
        print(f"ERROR analyzing {table_name}: {e}")
        return None


def analyze_runner_data(db_client):
    """Special analysis for runner data"""
    print(f"\n{'='*80}")
    print(f"SPECIAL ANALYSIS: Runner Data Completeness")
    print(f"{'='*80}")

    try:
        # Get race count
        races_result = db_client.client.table('ra_races').select('*', count='exact').limit(1).execute()
        total_races = races_result.count if hasattr(races_result, 'count') else 0

        # Get runner count
        runners_result = db_client.client.table('ra_runners').select('*', count='exact').limit(1).execute()
        total_runners = runners_result.count if hasattr(runners_result, 'count') else 0

        # Calculate average runners per race
        avg_runners = total_runners / total_races if total_races > 0 else 0

        print(f"Total races:        {total_races:,}")
        print(f"Total runners:      {total_runners:,}")
        print(f"Avg runners/race:   {avg_runners:.2f}")
        print(f"\nEXPECTED:          8-12 runners per race")
        print(f"EXPECTED TOTAL:    {total_races * 10:,} runners (at 10 avg)")

        if avg_runners < 8:
            print(f"\n❌ ISSUE: Low runner count detected!")
            print(f"   Missing approximately {(total_races * 10) - total_runners:,} runners")
            print(f"   Possible causes:")
            print(f"   - Filtering logic removing valid runners")
            print(f"   - API not returning all runners")
            print(f"   - Extraction logic skipping some runners")

        # Check race_date column in runners
        print(f"\n{'='*80}")
        print(f"Checking if race_date is populated in ra_runners...")
        sample = db_client.client.table('ra_runners').select('race_id, race_date').limit(100).execute()

        if sample.data:
            null_race_date = sum(1 for r in sample.data if not r.get('race_date'))
            pct_null = (null_race_date / len(sample.data)) * 100
            print(f"Sample: {len(sample.data)} runners")
            print(f"NULL race_date: {null_race_date} ({pct_null:.1f}%)")

            if pct_null > 50:
                print(f"❌ ISSUE: race_date not being populated in ra_runners!")

    except Exception as e:
        print(f"ERROR in runner analysis: {e}")


def analyze_pedigree_data(db_client):
    """Special analysis for pedigree data"""
    print(f"\n{'='*80}")
    print(f"SPECIAL ANALYSIS: Pedigree Data Population")
    print(f"{'='*80}")

    try:
        # Get horse count
        horses_result = db_client.client.table('ra_horses').select('*', count='exact').limit(1).execute()
        total_horses = horses_result.count if hasattr(horses_result, 'count') else 0

        # Get pedigree count
        pedigree_result = db_client.client.table('ra_horse_pedigree').select('*', count='exact').limit(1).execute()
        total_pedigrees = pedigree_result.count if hasattr(pedigree_result, 'count') else 0

        print(f"Total horses:       {total_horses:,}")
        print(f"Total pedigrees:    {total_pedigrees:,}")
        print(f"Coverage:           {(total_pedigrees/total_horses*100) if total_horses > 0 else 0:.1f}%")

        if total_pedigrees == 0:
            print(f"\n❌ CRITICAL ISSUE: ra_horse_pedigree is EMPTY!")
            print(f"   Possible causes:")
            print(f"   1. API endpoint not returning pedigree data")
            print(f"   2. Code not extracting pedigree fields")
            print(f"   3. insert_pedigree() not being called")
            print(f"   4. Need to use GET /horses/{{id}} for detailed data")
        elif total_pedigrees < (total_horses * 0.5):
            print(f"\n⚠️  WARNING: Low pedigree coverage!")
            print(f"   Expected: ~80-90% of horses should have pedigree data")

        # Sample pedigree data to see what's populated
        if total_pedigrees > 0:
            sample = db_client.client.table('ra_horse_pedigree').select('*').limit(10).execute()
            if sample.data:
                print(f"\nSample pedigree record:")
                print(json.dumps(sample.data[0], indent=2, default=str))

    except Exception as e:
        print(f"ERROR in pedigree analysis: {e}")


def parse_openapi_endpoints():
    """Parse OpenAPI spec to extract available endpoints"""
    print(f"\n{'='*80}")
    print(f"ANALYZING AVAILABLE API ENDPOINTS")
    print(f"{'='*80}")

    openapi_file = Path(__file__).parent / 'docs' / 'racing_api_openapi.json'

    if not openapi_file.exists():
        print(f"ERROR: OpenAPI spec not found at {openapi_file}")
        return

    try:
        with open(openapi_file, 'r') as f:
            spec = json.load(f)

        paths = spec.get('paths', {})

        endpoints_by_plan = defaultdict(list)

        for path, methods in paths.items():
            for method, details in methods.items():
                if method == 'get':
                    description = details.get('description', '')
                    summary = details.get('summary', '')

                    # Extract required plan
                    required_plan = 'Unknown'
                    if 'Free' in description:
                        required_plan = 'Free'
                    elif 'Basic' in description:
                        required_plan = 'Basic'
                    elif 'Standard' in description:
                        required_plan = 'Standard'
                    elif 'Pro' in description:
                        required_plan = 'Pro'

                    endpoints_by_plan[required_plan].append({
                        'path': path,
                        'summary': summary,
                        'method': method.upper()
                    })

        # Print endpoints by plan
        plan_order = ['Free', 'Basic', 'Standard', 'Pro', 'Unknown']
        for plan in plan_order:
            if plan in endpoints_by_plan:
                print(f"\n{plan.upper()} PLAN ENDPOINTS:")
                print(f"{'-'*80}")
                for endpoint in endpoints_by_plan[plan]:
                    print(f"  {endpoint['method']:6s} {endpoint['path']:40s} | {endpoint['summary']}")

        return endpoints_by_plan

    except Exception as e:
        print(f"ERROR parsing OpenAPI spec: {e}")
        return None


def main():
    """Main audit execution"""
    print("=" * 80)
    print("DARKHORSES DATABASE & API AUDIT")
    print("=" * 80)
    print("\nThis audit will:")
    print("1. Analyze NULL columns in all tables")
    print("2. Check data completeness (runners, pedigrees)")
    print("3. Review available API endpoints")
    print("4. Identify missing data opportunities")

    # Initialize database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Test connection
    if not db_client.verify_connection():
        print("ERROR: Cannot connect to database")
        return

    # List of tables to analyze
    tables = [
        'ra_races',
        'ra_runners',
        'ra_horses',
        'ra_horse_pedigree',
        'ra_jockeys',
        'ra_trainers',
        'ra_owners',
        'ra_courses'
    ]

    # Analyze each table
    results = {}
    for table in tables:
        result = analyze_table_nulls(db_client, table, sample_size=100)
        if result:
            results[table] = result

    # Special analyses
    analyze_runner_data(db_client)
    analyze_pedigree_data(db_client)

    # Parse API endpoints
    endpoints = parse_openapi_endpoints()

    # Final summary
    print(f"\n{'='*80}")
    print(f"AUDIT COMPLETE")
    print(f"{'='*80}")

    total_entirely_null = sum(len(r.get('entirely_null', [])) for r in results.values())
    total_mostly_null = sum(len(r.get('mostly_null', [])) for r in results.values())

    print(f"\nTOTAL ISSUES FOUND:")
    print(f"  Entirely NULL columns:  {total_entirely_null}")
    print(f"  Mostly NULL columns:    {total_mostly_null}")

    if total_entirely_null > 0:
        print(f"\n⚠️  ACTION REQUIRED:")
        print(f"  - Review entirely NULL columns and either populate or remove")
        print(f"  - Check if API responses include these fields")
        print(f"  - Verify extraction logic is capturing all available data")

    print(f"\nRECOMMENDED NEXT STEPS:")
    print(f"  1. Review horses_fetcher.py pedigree extraction (ra_horse_pedigree is empty)")
    print(f"  2. Check runner count logic (avg runners per race seems low)")
    print(f"  3. Verify we're using /racecards/pro endpoint (Pro plan)")
    print(f"  4. Compare API response fields vs extracted fields")
    print(f"  5. Consider using GET /horses/{{id}} for detailed horse data")


if __name__ == '__main__':
    main()
