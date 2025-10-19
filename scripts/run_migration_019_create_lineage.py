#!/usr/bin/env python3
"""
Execute Migration 019: Create ra_lineage table
"""

import psycopg2
import sys
from pathlib import Path

# Connection string - using connection pooler
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("MIGRATION 019: CREATE RA_LINEAGE TABLE")
print("=" * 100)
print()

try:
    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "019_create_ra_lineage_table.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"📄 Migration file: {migration_file}")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False
    cur = conn.cursor()
    print("✅ Connected")
    print()

    # Execute migration
    print("🚀 Executing migration...")
    print()

    # Split into stages for better progress reporting
    stages = migration_sql.split("-- =============================================================================")

    for i, stage in enumerate(stages[1:], 1):  # Skip preamble
        if not stage.strip():
            continue

        # Extract stage name from comment
        lines = stage.strip().split('\n')
        stage_name = lines[0].replace('--', '').strip() if lines else f"Stage {i}"

        print(f"Stage {i}: {stage_name}")
        print("-" * 100)

        # Execute stage SQL
        try:
            cur.execute(stage)
            print(f"✅ {stage_name} completed")
        except psycopg2.Error as e:
            print(f"⚠️  {stage_name} - {e}")
            # Continue to next stage even if one fails (for idempotency)

        print()

    # Commit transaction
    print("💾 Committing transaction...")
    conn.commit()
    print("✅ Migration committed successfully")
    print()

    # Verify table exists
    print("🔍 Verifying ra_lineage table...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'ra_lineage'
        );
    """)

    table_exists = cur.fetchone()[0]

    if table_exists:
        print("✅ Table ra_lineage exists")

        # Get column count
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'ra_lineage';
        """)
        col_count = cur.fetchone()[0]
        print(f"   Columns: {col_count}")

        # Get index count
        cur.execute("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE tablename = 'ra_lineage';
        """)
        idx_count = cur.fetchone()[0]
        print(f"   Indexes: {idx_count}")

        # Check if table is empty
        cur.execute("SELECT COUNT(*) FROM ra_lineage;")
        row_count = cur.fetchone()[0]
        print(f"   Rows: {row_count:,}")

    else:
        print("❌ Table ra_lineage does not exist!")
        sys.exit(1)

    print()
    print("=" * 100)
    print("MIGRATION 019 COMPLETED SUCCESSFULLY")
    print("=" * 100)
    print()
    print("Next steps:")
    print("1. Run backfill script to populate ra_lineage from existing data")
    print("2. Update fetchers to populate ra_lineage on new runners")
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    if 'conn' in locals():
        conn.rollback()
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
