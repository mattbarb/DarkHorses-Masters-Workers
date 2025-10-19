#!/usr/bin/env python3
"""
Execute Migration 020: Create ancestor statistics tables
"""

import psycopg2
import sys
from pathlib import Path

print("=" * 100)
print("EXECUTING MIGRATION 020: CREATE ANCESTOR STATISTICS TABLES")
print("=" * 100)
print()

# Database connection
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

# Read migration file
migration_file = Path(__file__).parent.parent / "migrations" / "020_create_ancestor_stats_tables.sql"
print(f"Reading migration file: {migration_file}")
print()

with open(migration_file, 'r') as f:
    migration_sql = f.read()

try:
    print("Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cur = conn.cursor()

    print("✓ Connected")
    print()

    print("Executing migration SQL...")
    print("-" * 100)

    # Execute the migration
    cur.execute(migration_sql)

    print("✓ Migration executed successfully")
    print()

    # Verify tables were created
    print("Verifying tables...")
    print("-" * 100)

    tables_to_check = ['ra_sire_stats', 'ra_dam_stats', 'ra_damsire_stats']

    for table_name in tables_to_check:
        cur.execute(f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)

        columns = cur.fetchall()

        if columns:
            print(f"✓ Table {table_name} created with {len(columns)} columns:")
            for col_name, data_type, max_length, nullable, default in columns[:5]:  # Show first 5
                type_info = f"{data_type}"
                if max_length:
                    type_info += f"({max_length})"
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"    - {col_name:<30} {type_info:<20} {nullable_str}")
            if len(columns) > 5:
                print(f"    ... and {len(columns) - 5} more columns")
            print()
        else:
            print(f"✗ Table {table_name} NOT found!")
            print()

    # Check indexes
    print("Checking indexes...")
    print("-" * 100)

    for table_name in tables_to_check:
        cur.execute(f"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = '{table_name}'
            AND schemaname = 'public'
            ORDER BY indexname;
        """)

        indexes = cur.fetchall()
        print(f"{table_name}: {len(indexes)} indexes")
        for idx_name, idx_def in indexes[:3]:  # Show first 3
            print(f"    - {idx_name}")
        if len(indexes) > 3:
            print(f"    ... and {len(indexes) - 3} more")
        print()

    # Check table comments
    print("Checking table comments...")
    print("-" * 100)

    for table_name in tables_to_check:
        cur.execute(f"""
            SELECT obj_description('{table_name}'::regclass, 'pg_class') as comment;
        """)

        result = cur.fetchone()
        if result and result[0]:
            print(f"{table_name}:")
            print(f"    {result[0]}")
        print()

    cur.close()
    conn.close()

    print("=" * 100)
    print("✓ MIGRATION 020 COMPLETED SUCCESSFULLY")
    print("=" * 100)
    print()
    print("Tables created:")
    print("  - ra_sire_stats (sire own career + progeny statistics)")
    print("  - ra_dam_stats (dam own career + progeny statistics)")
    print("  - ra_damsire_stats (damsire own career + grandoffspring statistics)")
    print()
    print("Next step: Run backfill script to populate ancestor statistics")
    print()

except Exception as e:
    print(f"✗ Error executing migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
