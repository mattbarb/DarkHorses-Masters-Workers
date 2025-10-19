#!/usr/bin/env python3
"""
Backfill ra_lineage table from existing ra_runners data

This script populates ra_lineage by extracting pedigree data from ra_runners.
For each runner, it creates lineage records for:
- Generation 1: sire, dam
- Generation 2: damsire (maternal grandsire)

Note: Currently we only have damsire from the API, not all 4 grandparents.
"""

import psycopg2
import sys
from datetime import datetime

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("BACKFILL RA_LINEAGE FROM RA_RUNNERS")
print("=" * 100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False
    cur = conn.cursor()

    # =========================================================================
    # Step 1: Check current state
    # =========================================================================
    print("📊 Current state:")
    print("-" * 100)

    cur.execute("SELECT COUNT(*) FROM ra_runners;")
    total_runners = cur.fetchone()[0]
    print(f"  Runners in ra_runners: {total_runners:,}")

    cur.execute("SELECT COUNT(*) FROM ra_lineage;")
    current_lineage = cur.fetchone()[0]
    print(f"  Records in ra_lineage: {current_lineage:,}")

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE sire_id IS NOT NULL) as with_sire,
            COUNT(*) FILTER (WHERE dam_id IS NOT NULL) as with_dam,
            COUNT(*) FILTER (WHERE damsire_id IS NOT NULL) as with_damsire
        FROM ra_runners;
    """)
    sire_count, dam_count, damsire_count = cur.fetchone()

    print(f"  Runners with sire_id:    {sire_count:,} ({sire_count/total_runners*100:.1f}%)")
    print(f"  Runners with dam_id:     {dam_count:,} ({dam_count/total_runners*100:.1f}%)")
    print(f"  Runners with damsire_id: {damsire_count:,} ({damsire_count/total_runners*100:.1f}%)")
    print()

    # =========================================================================
    # Step 2: Extract sires (Generation 1)
    # =========================================================================
    print("🔹 Extracting sires (Generation 1)...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_lineage (
            lineage_id,
            runner_id,
            horse_id,
            generation,
            lineage_path,
            relation_type,
            ancestor_horse_id,
            ancestor_name,
            ancestor_region
        )
        SELECT
            run.runner_id || '_1_sire' as lineage_id,
            run.runner_id,
            run.horse_id,
            1 as generation,
            'sire' as lineage_path,
            'sire' as relation_type,
            run.sire_id as ancestor_horse_id,
            run.sire_name as ancestor_name,
            run.sire_region as ancestor_region
        FROM ra_runners run
        WHERE run.sire_id IS NOT NULL
        ON CONFLICT (runner_id, lineage_path) DO NOTHING;
    """)

    sire_inserted = cur.rowcount
    print(f"✅ Inserted {sire_inserted:,} sire records")
    conn.commit()
    print()

    # =========================================================================
    # Step 3: Extract dams (Generation 1)
    # =========================================================================
    print("🔹 Extracting dams (Generation 1)...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_lineage (
            lineage_id,
            runner_id,
            horse_id,
            generation,
            lineage_path,
            relation_type,
            ancestor_horse_id,
            ancestor_name,
            ancestor_region
        )
        SELECT
            run.runner_id || '_1_dam' as lineage_id,
            run.runner_id,
            run.horse_id,
            1 as generation,
            'dam' as lineage_path,
            'dam' as relation_type,
            run.dam_id as ancestor_horse_id,
            run.dam_name as ancestor_name,
            run.dam_region as ancestor_region
        FROM ra_runners run
        WHERE run.dam_id IS NOT NULL
        ON CONFLICT (runner_id, lineage_path) DO NOTHING;
    """)

    dam_inserted = cur.rowcount
    print(f"✅ Inserted {dam_inserted:,} dam records")
    conn.commit()
    print()

    # =========================================================================
    # Step 4: Extract damsires (Generation 2 - maternal grandsire)
    # =========================================================================
    print("🔹 Extracting damsires (Generation 2 - maternal grandsire)...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_lineage (
            lineage_id,
            runner_id,
            horse_id,
            generation,
            lineage_path,
            relation_type,
            ancestor_horse_id,
            ancestor_name,
            ancestor_region
        )
        SELECT
            run.runner_id || '_2_dam.sire' as lineage_id,
            run.runner_id,
            run.horse_id,
            2 as generation,
            'dam.sire' as lineage_path,
            'grandsire_maternal' as relation_type,
            run.damsire_id as ancestor_horse_id,
            run.damsire_name as ancestor_name,
            run.damsire_region as ancestor_region
        FROM ra_runners run
        WHERE run.damsire_id IS NOT NULL
        ON CONFLICT (runner_id, lineage_path) DO NOTHING;
    """)

    damsire_inserted = cur.rowcount
    print(f"✅ Inserted {damsire_inserted:,} damsire records")
    conn.commit()
    print()

    # =========================================================================
    # Step 5: Verify results
    # =========================================================================
    print("🔍 Verification:")
    print("-" * 100)

    cur.execute("SELECT COUNT(*) FROM ra_lineage;")
    total_lineage = cur.fetchone()[0]
    print(f"  Total lineage records: {total_lineage:,}")

    cur.execute("""
        SELECT
            generation,
            relation_type,
            COUNT(*) as count
        FROM ra_lineage
        GROUP BY generation, relation_type
        ORDER BY generation, relation_type;
    """)

    print()
    print("  Breakdown by generation and relation:")
    for gen, rel_type, count in cur.fetchall():
        print(f"    Gen {gen} - {rel_type:<25} {count:>12,}")

    print()

    # Check for duplicate lineage_ids
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT lineage_id
            FROM ra_lineage
            GROUP BY lineage_id
            HAVING COUNT(*) > 1
        ) duplicates;
    """)

    dup_count = cur.fetchone()[0]
    if dup_count > 0:
        print(f"  ⚠️  Found {dup_count} duplicate lineage_ids!")
    else:
        print(f"  ✅ No duplicate lineage_ids")

    # Sample data
    print()
    print("  Sample lineage records:")
    cur.execute("""
        SELECT
            lineage_id,
            generation,
            relation_type,
            ancestor_name
        FROM ra_lineage
        ORDER BY RANDOM()
        LIMIT 5;
    """)

    for lid, gen, rel, name in cur.fetchall():
        print(f"    {lid[:50]:<50} | Gen {gen} | {rel:<25} | {name}")

    print()
    print("=" * 100)
    print("BACKFILL COMPLETED SUCCESSFULLY")
    print("=" * 100)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Summary:")
    print(f"  Sires inserted:    {sire_inserted:>12,}")
    print(f"  Dams inserted:     {dam_inserted:>12,}")
    print(f"  Damsires inserted: {damsire_inserted:>12,}")
    print(f"  Total inserted:    {sire_inserted + dam_inserted + damsire_inserted:>12,}")
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    if 'conn' in locals():
        conn.rollback()
    import traceback
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
