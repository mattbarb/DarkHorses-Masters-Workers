"""
Complete Column Audit for All RA_ Tables vs Fetchers

This script:
1. Extracts all columns from all ra_ tables
2. Analyzes which fetcher populates each table
3. Checks if fetchers capture all available columns
4. Identifies missing fields in fetchers
5. Generates comprehensive audit report

Usage:
    python3 scripts/audit_fetcher_columns.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
import json
from collections import defaultdict


# Define which fetcher populates which table
FETCHER_TABLE_MAPPING = {
    'courses_fetcher.py': ['ra_courses'],
    'bookmakers_fetcher.py': ['ra_bookmakers'],
    'races_fetcher.py': ['ra_races', 'ra_runners'],
    'results_fetcher.py': ['ra_races', 'ra_runners'],
    'entity_extractor.py': ['ra_horses', 'ra_jockeys', 'ra_trainers', 'ra_owners', 'ra_sires', 'ra_dams', 'ra_damsires']
}


def get_table_columns(db_client):
    """Get all columns for all ra_ tables"""
    query = """
    SELECT
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name LIKE 'ra_%'
      AND table_name NOT LIKE '%backup%'
    ORDER BY table_name, ordinal_position;
    """

    result = db_client.client.rpc('exec_sql', {'query': query}).execute()
    return result.data if result.data else []


def get_table_columns_direct(config):
    """Get columns directly via psycopg2"""
    import psycopg2

    conn = psycopg2.connect(
        host="aws-0-eu-west-2.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.amsjvmlaknnvppxsgpfk",
        password="R0pMr1L58WH3hUkpVtPcwYnw"
    )

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name LIKE 'ra_%'
          AND table_name NOT LIKE '%backup%'
        ORDER BY table_name, ordinal_position;
    """)

    columns = cursor.fetchall()
    cursor.close()
    conn.close()

    return columns


def parse_fetcher_fields(fetcher_file):
    """Extract fields being set in a fetcher file"""
    fields = []

    with open(fetcher_file, 'r') as f:
        content = f.read()

    # Look for dictionary assignments like 'field_name': value
    import re
    pattern = r"'([a-z_]+)':\s*(?:runner|racecard|race|result|jockey|trainer|owner|horse|sire|dam|damsire)\.get\("
    matches = re.findall(pattern, content)
    fields.extend(matches)

    # Also look for direct assignments
    pattern2 = r"'([a-z_]+)':\s*[^,\}]+"
    matches2 = re.findall(pattern2, content)
    fields.extend(matches2)

    return list(set(fields))


def analyze_table(table_name, columns, fetcher_name=None):
    """Analyze a single table's columns"""

    # Categorize columns
    auto_columns = ['id', 'created_at', 'updated_at']
    foreign_keys = [col for col in columns if col.endswith('_id')]
    data_columns = [col for col in columns if col not in auto_columns and col not in foreign_keys]

    return {
        'table': table_name,
        'total_columns': len(columns),
        'auto_columns': auto_columns,
        'foreign_keys': foreign_keys,
        'data_columns': data_columns,
        'fetcher': fetcher_name
    }


def generate_comprehensive_report(config):
    """Generate complete audit report"""

    print("=" * 100)
    print("COMPREHENSIVE COLUMN AUDIT: RA_ TABLES vs FETCHERS")
    print("=" * 100)
    print()

    # Get all table columns
    print("Fetching table schemas from database...")
    columns_data = get_table_columns_direct(config)

    # Organize by table
    tables_dict = defaultdict(list)
    for row in columns_data:
        table_name, column_name, data_type, is_nullable, column_default = row
        tables_dict[table_name].append({
            'column': column_name,
            'type': data_type,
            'nullable': is_nullable,
            'default': column_default
        })

    print(f"Found {len(tables_dict)} tables\n")

    # Analyze each table
    report = {}

    for table_name in sorted(tables_dict.keys()):
        columns = tables_dict[table_name]
        column_names = [c['column'] for c in columns]

        # Find which fetcher populates this table
        fetcher_name = None
        for fetcher, tables in FETCHER_TABLE_MAPPING.items():
            if table_name in tables:
                fetcher_name = fetcher
                break

        analysis = analyze_table(table_name, column_names, fetcher_name)
        report[table_name] = {
            'analysis': analysis,
            'columns': columns
        }

    # Print report
    print("\n" + "=" * 100)
    print("TABLE-BY-TABLE ANALYSIS")
    print("=" * 100)

    for table_name in sorted(report.keys()):
        data = report[table_name]
        analysis = data['analysis']
        columns = data['columns']

        print(f"\n📊 {table_name.upper()}")
        print("-" * 100)
        print(f"Total Columns: {analysis['total_columns']}")
        print(f"Populated By: {analysis['fetcher'] or 'UNKNOWN/MANUAL'}")
        print()

        # Show all columns
        print("ALL COLUMNS:")
        for col in columns:
            nullable_str = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
            default_str = f" DEFAULT {col['default']}" if col['default'] else ""
            print(f"  • {col['column']:30} {col['type']:20} {nullable_str:10}{default_str}")

        print()

    # Summary by fetcher
    print("\n" + "=" * 100)
    print("SUMMARY BY FETCHER")
    print("=" * 100)

    for fetcher, tables in FETCHER_TABLE_MAPPING.items():
        print(f"\n📝 {fetcher}")
        print("-" * 100)
        for table in tables:
            if table in report:
                analysis = report[table]['analysis']
                print(f"  → {table}: {analysis['total_columns']} columns")
        print()

    # Identify tables without fetchers
    print("\n" + "=" * 100)
    print("TABLES WITHOUT FETCHERS (Manual/System Tables)")
    print("=" * 100)

    orphan_tables = []
    for table_name in sorted(report.keys()):
        analysis = report[table_name]['analysis']
        if not analysis['fetcher']:
            orphan_tables.append(table_name)
            print(f"  • {table_name}: {analysis['total_columns']} columns")

    if not orphan_tables:
        print("  (None - all tables have assigned fetchers)")

    print()

    # Save detailed JSON report
    output_file = Path(__file__).parent.parent / 'docs' / 'COMPLETE_COLUMN_INVENTORY.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✅ Detailed JSON report saved to: {output_file}")
    print()

    return report


def compare_fetcher_to_schema(fetcher_file, table_name, schema_columns):
    """Compare what a fetcher sets vs what schema has"""

    print(f"\n🔍 Analyzing: {fetcher_file} → {table_name}")
    print("-" * 100)

    # Get fields from fetcher
    fetcher_fields = parse_fetcher_fields(Path(__file__).parent.parent / 'fetchers' / fetcher_file)

    # Schema columns (excluding auto fields)
    auto_fields = {'id', 'created_at', 'updated_at'}
    schema_fields = set(col['column'] for col in schema_columns if col['column'] not in auto_fields)

    # Compare
    captured = set(fetcher_fields) & schema_fields
    missing = schema_fields - set(fetcher_fields)
    extra = set(fetcher_fields) - schema_fields

    print(f"Schema Columns: {len(schema_fields)}")
    print(f"Fetcher Sets: {len(fetcher_fields)}")
    print(f"Captured: {len(captured)} ({len(captured)/len(schema_fields)*100:.1f}%)")
    print(f"Missing from Fetcher: {len(missing)}")

    if missing:
        print("\n⚠️  MISSING FIELDS:")
        for field in sorted(missing):
            print(f"  • {field}")

    if extra:
        print("\n❓ EXTRA FIELDS (not in schema):")
        for field in sorted(extra):
            print(f"  • {field}")

    print()

    return {
        'schema_fields': len(schema_fields),
        'fetcher_fields': len(fetcher_fields),
        'captured': len(captured),
        'missing': list(missing),
        'coverage_pct': len(captured)/len(schema_fields)*100 if schema_fields else 0
    }


def main():
    """Main execution"""
    config = get_config()

    # Generate comprehensive report
    report = generate_comprehensive_report(config)

    # Now compare specific fetchers to their tables
    print("\n" + "=" * 100)
    print("FETCHER vs SCHEMA COMPARISON")
    print("=" * 100)

    comparisons = {}

    # Races fetcher
    if 'ra_races' in report:
        comparisons['races_fetcher→ra_races'] = compare_fetcher_to_schema(
            'races_fetcher.py',
            'ra_races',
            report['ra_races']['columns']
        )

    if 'ra_runners' in report:
        comparisons['races_fetcher→ra_runners'] = compare_fetcher_to_schema(
            'races_fetcher.py',
            'ra_runners',
            report['ra_runners']['columns']
        )

    # Results fetcher
    if 'ra_runners' in report:
        comparisons['results_fetcher→ra_runners'] = compare_fetcher_to_schema(
            'results_fetcher.py',
            'ra_runners',
            report['ra_runners']['columns']
        )

    # Courses fetcher
    if 'ra_courses' in report:
        comparisons['courses_fetcher→ra_courses'] = compare_fetcher_to_schema(
            'courses_fetcher.py',
            'ra_courses',
            report['ra_courses']['columns']
        )

    # Summary
    print("\n" + "=" * 100)
    print("COVERAGE SUMMARY")
    print("=" * 100)

    for name, stats in comparisons.items():
        coverage = stats['coverage_pct']
        status = "✅" if coverage >= 90 else "⚠️" if coverage >= 70 else "❌"
        print(f"{status} {name:40} Coverage: {coverage:.1f}% ({stats['captured']}/{stats['schema_fields']})")

    print()
    print("=" * 100)
    print("AUDIT COMPLETE")
    print("=" * 100)

    return 0


if __name__ == '__main__':
    exit(main())
