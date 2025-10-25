"""
Comprehensive Database and Fetcher Audit Script
Analyzes all ra_* tables, their columns, and associated fetchers
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config


def get_all_ra_tables(db_client) -> Dict[str, List[str]]:
    """
    Get all ra_* tables and their columns

    Returns:
        Dict mapping table name to list of column names
    """
    tables = {}

    # Known ra_* tables based on supabase_client methods and project knowledge
    known_tables = [
        'ra_mst_courses', 'ra_mst_horses', 'ra_mst_jockeys', 'ra_mst_trainers',
        'ra_mst_owners', 'ra_mst_bookmakers', 'ra_mst_regions',
        'ra_mst_sires', 'ra_mst_dams', 'ra_mst_damsires',
        'ra_races', 'ra_runners', 'ra_results', 'ra_race_results',
        'ra_horse_pedigree', 'ra_metadata_tracking'
    ]

    print("Discovering tables and their columns...")

    for table in known_tables:
        try:
            # Query table with limit 0 to get column structure
            result = db_client.client.table(table).select('*').limit(0).execute()

            # Get column names from the data structure
            # For empty result, check if table exists by trying count
            count_result = db_client.client.table(table).select('*', count='exact').limit(1).execute()

            # Table exists, now get columns by fetching one row
            sample = db_client.client.table(table).select('*').limit(1).execute()

            if sample.data and len(sample.data) > 0:
                columns = list(sample.data[0].keys())
            else:
                # Table is empty, need to infer from schema
                # This is a limitation - we'll mark it
                columns = ['<EMPTY_TABLE - COLUMNS UNKNOWN>']

            tables[table] = {
                'columns': columns,
                'row_count': count_result.count if hasattr(count_result, 'count') else 0
            }

            print(f"  ✓ {table}: {len(columns)} columns, {tables[table]['row_count']} rows")

        except Exception as e:
            print(f"  ✗ {table}: {e}")
            continue

    return tables


def analyze_fetcher_file(file_path: str) -> Dict:
    """
    Analyze a fetcher file to extract:
    - Target tables
    - Field mappings
    - API endpoints used
    """
    with open(file_path, 'r') as f:
        content = f.read()

    analysis = {
        'file': os.path.basename(file_path),
        'path': file_path,
        'target_tables': [],
        'field_mappings': {},
        'api_endpoints': [],
        'has_error_handling': 'try:' in content and 'except' in content,
        'has_logging': 'logger.' in content,
        'uses_entity_extractor': 'EntityExtractor' in content,
        'lines_of_code': len(content.split('\n'))
    }

    # Find insert/upsert calls to identify target tables
    insert_methods = [
        'insert_courses', 'insert_horses', 'insert_jockeys', 'insert_trainers',
        'insert_owners', 'insert_sires', 'insert_dams', 'insert_damsires',
        'insert_pedigree', 'insert_races', 'insert_runners', 'insert_results',
        'insert_bookmakers', 'insert_regions', 'insert_race_results'
    ]

    for method in insert_methods:
        if method in content:
            # Map method to table name
            table_map = {
                'insert_courses': 'ra_mst_courses',
                'insert_horses': 'ra_mst_horses',
                'insert_jockeys': 'ra_mst_jockeys',
                'insert_trainers': 'ra_mst_trainers',
                'insert_owners': 'ra_mst_owners',
                'insert_sires': 'ra_mst_sires',
                'insert_dams': 'ra_mst_dams',
                'insert_damsires': 'ra_mst_damsires',
                'insert_pedigree': 'ra_horse_pedigree',
                'insert_races': 'ra_races',
                'insert_runners': 'ra_runners',
                'insert_results': 'ra_results',
                'insert_bookmakers': 'ra_mst_bookmakers',
                'insert_regions': 'ra_mst_regions',
                'insert_race_results': 'ra_race_results'
            }

            if method in table_map:
                analysis['target_tables'].append(table_map[method])

    # Find API endpoints
    if '/v1/' in content:
        import re
        endpoints = re.findall(r'/v1/[\w\-/{}]+', content)
        analysis['api_endpoints'] = list(set(endpoints))

    return analysis


def main():
    # Load configuration
    load_dotenv('.env.local')
    config = get_config()

    # Initialize database client
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    print("="*80)
    print("DARKHORSE MASTERS-WORKERS FETCHER AUDIT")
    print("="*80)
    print()

    # Phase 1: Database Discovery
    print("\n" + "="*80)
    print("PHASE 1: DATABASE TABLE DISCOVERY")
    print("="*80)
    tables = get_all_ra_tables(db_client)

    # Save tables to JSON
    output_dir = Path(__file__).parent.parent / 'docs'
    tables_file = output_dir / 'COMPLETE_DATABASE_TABLES_AUDIT.json'

    with open(tables_file, 'w') as f:
        json.dump(tables, f, indent=2)

    print(f"\n✓ Saved table inventory to: {tables_file}")
    print(f"  Total ra_* tables found: {len(tables)}")

    # Phase 2: Fetcher Discovery
    print("\n" + "="*80)
    print("PHASE 2: FETCHER FILE INVENTORY")
    print("="*80)

    fetchers_dir = Path(__file__).parent.parent / 'fetchers'
    fetcher_files = list(fetchers_dir.glob('*_fetcher.py'))

    print(f"Found {len(fetcher_files)} fetcher files:")

    fetcher_analyses = {}
    for fetcher_file in fetcher_files:
        print(f"\n  Analyzing: {fetcher_file.name}")
        analysis = analyze_fetcher_file(str(fetcher_file))
        fetcher_analyses[fetcher_file.name] = analysis

        print(f"    Target tables: {', '.join(analysis['target_tables']) if analysis['target_tables'] else 'NONE'}")
        print(f"    API endpoints: {len(analysis['api_endpoints'])}")
        print(f"    Lines of code: {analysis['lines_of_code']}")
        print(f"    Error handling: {'✓' if analysis['has_error_handling'] else '✗'}")
        print(f"    Logging: {'✓' if analysis['has_logging'] else '✗'}")

    # Save fetcher inventory to JSON
    fetchers_file = output_dir / 'COMPLETE_FETCHER_INVENTORY.json'
    with open(fetchers_file, 'w') as f:
        json.dump(fetcher_analyses, f, indent=2)

    print(f"\n✓ Saved fetcher inventory to: {fetchers_file}")

    # Phase 3: Gap Analysis
    print("\n" + "="*80)
    print("PHASE 3: GAP ANALYSIS")
    print("="*80)

    # Build table -> fetcher mapping
    table_to_fetcher = {}
    for fetcher_name, analysis in fetcher_analyses.items():
        for table in analysis['target_tables']:
            if table not in table_to_fetcher:
                table_to_fetcher[table] = []
            table_to_fetcher[table].append(fetcher_name)

    # Find tables without fetchers
    tables_without_fetchers = []
    for table in tables.keys():
        if table not in table_to_fetcher:
            tables_without_fetchers.append(table)

    print(f"\n📊 COVERAGE SUMMARY:")
    print(f"  Total tables: {len(tables)}")
    print(f"  Tables with fetchers: {len(table_to_fetcher)}")
    print(f"  Tables WITHOUT fetchers: {len(tables_without_fetchers)}")

    if tables_without_fetchers:
        print(f"\n⚠️  TABLES WITHOUT FETCHERS:")
        for table in sorted(tables_without_fetchers):
            row_count = tables[table]['row_count']
            print(f"    - {table} ({row_count} rows)")

    # Find tables with multiple fetchers
    tables_with_multiple = {t: f for t, f in table_to_fetcher.items() if len(f) > 1}
    if tables_with_multiple:
        print(f"\n📝 TABLES WITH MULTIPLE FETCHERS:")
        for table, fetchers in tables_with_multiple.items():
            print(f"    - {table}: {', '.join(fetchers)}")

    # Save gap analysis
    gap_analysis = {
        'summary': {
            'total_tables': len(tables),
            'tables_with_fetchers': len(table_to_fetcher),
            'tables_without_fetchers': len(tables_without_fetchers)
        },
        'table_to_fetcher_mapping': table_to_fetcher,
        'tables_without_fetchers': tables_without_fetchers,
        'tables_with_multiple_fetchers': tables_with_multiple
    }

    gap_file = output_dir / 'FETCHER_GAP_ANALYSIS.json'
    with open(gap_file, 'w') as f:
        json.dump(gap_analysis, f, indent=2)

    print(f"\n✓ Saved gap analysis to: {gap_file}")

    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print(f"  1. {tables_file}")
    print(f"  2. {fetchers_file}")
    print(f"  3. {gap_file}")
    print()


if __name__ == '__main__':
    main()
