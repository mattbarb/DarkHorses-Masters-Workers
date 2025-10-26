#!/usr/bin/env python3
"""
Analyze current pedigree/lineage data structure
"""

import psycopg2
import sys

conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("CURRENT PEDIGREE/LINEAGE DATA ANALYSIS")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Check ra_horse_pedigree structure
    print("RA_HORSE_PEDIGREE TABLE STRUCTURE:")
    print("-" * 100)
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'ra_horse_pedigree'
        ORDER BY ordinal_position;
    """)

    for col, dtype, nullable in cur.fetchall():
        null_str = "NULL" if nullable == "YES" else "NOT NULL"
        print(f"  {col:<30} {dtype:<25} {null_str}")

    print()

    # Check population
    cur.execute("SELECT COUNT(*) FROM ra_horse_pedigree;")
    pedigree_count = cur.fetchone()[0]
    print(f"Total pedigree records: {pedigree_count:,}")
    print()

    # Sample data
    print("SAMPLE PEDIGREE DATA:")
    print("-" * 100)
    cur.execute("""
        SELECT horse_id, sire_id, sire, dam_id, dam, damsire_id, damsire, breeder
        FROM ra_horse_pedigree
        LIMIT 5;
    """)

    for row in cur.fetchall():
        horse_id, sire_id, sire, dam_id, dam, damsire_id, damsire, breeder = row
        print(f"  Horse: {horse_id}")
        print(f"    Sire: {sire} ({sire_id})")
        print(f"    Dam: {dam} ({dam_id})")
        print(f"    Damsire: {damsire} ({damsire_id})")
        print(f"    Breeder: {breeder}")
        print()

    # Check ra_mst_runners pedigree columns
    print("RA_RUNNERS PEDIGREE COLUMNS:")
    print("-" * 100)
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'ra_mst_runners'
        AND column_name IN ('sire_id', 'sire', 'sire_region', 'dam_id', 'dam', 'dam_region', 'damsire_id', 'damsire', 'damsire_region', 'breeder')
        ORDER BY ordinal_position;
    """)

    for col, dtype in cur.fetchall():
        print(f"  {col:<30} {dtype}")

    print()

    # Check population in ra_mst_runners
    cur.execute("""
        SELECT
            COUNT(*) as total_runners,
            COUNT(sire_id) as has_sire_id,
            COUNT(dam_id) as has_dam_id,
            COUNT(damsire_id) as has_damsire_id,
            COUNT(sire) as has_sire,
            COUNT(dam) as has_dam,
            COUNT(damsire) as has_damsire,
            COUNT(sire_region) as has_sire_region,
            COUNT(dam_region) as has_dam_region,
            COUNT(damsire_region) as has_damsire_region
        FROM ra_mst_runners;
    """)

    stats = cur.fetchone()
    total = stats[0]

    print("RA_RUNNERS PEDIGREE DATA POPULATION:")
    print(f"  Total runners:      {total:>12,}")
    print(f"  With sire_id:       {stats[1]:>12,} ({stats[1]/total*100:>5.1f}%)")
    print(f"  With dam_id:        {stats[2]:>12,} ({stats[2]/total*100:>5.1f}%)")
    print(f"  With damsire_id:    {stats[3]:>12,} ({stats[3]/total*100:>5.1f}%)")
    print(f"  With sire:     {stats[4]:>12,} ({stats[4]/total*100:>5.1f}%)")
    print(f"  With dam:      {stats[5]:>12,} ({stats[5]/total*100:>5.1f}%)")
    print(f"  With damsire:  {stats[6]:>12,} ({stats[6]/total*100:>5.1f}%)")
    print(f"  With sire_region:   {stats[7]:>12,} ({stats[7]/total*100:>5.1f}%)")
    print(f"  With dam_region:    {stats[8]:>12,} ({stats[8]/total*100:>5.1f}%)")
    print(f"  With damsire_region:{stats[9]:>12,} ({stats[9]/total*100:>5.1f}%)")
    print()

    # Check relationship between ra_mst_runners and ra_horse_pedigree
    print("RELATIONSHIP CHECK:")
    print("-" * 100)
    cur.execute("""
        SELECT
            COUNT(DISTINCT run.horse_id) as unique_horses_in_runners,
            COUNT(DISTINCT ped.horse_id) as unique_horses_in_pedigree,
            COUNT(DISTINCT run.horse_id) FILTER (
                WHERE EXISTS (SELECT 1 FROM ra_horse_pedigree ped WHERE ped.horse_id = run.horse_id)
            ) as horses_with_pedigree
        FROM ra_mst_runners run;
    """)

    horses_in_runners, horses_in_pedigree, horses_with_ped = cur.fetchone()

    print(f"  Unique horses in ra_mst_runners:        {horses_in_runners:>12,}")
    print(f"  Unique horses in ra_horse_pedigree: {horses_in_pedigree:>12,}")
    print(f"  Horses with pedigree records:       {horses_with_ped:>12,} ({horses_with_ped/horses_in_runners*100:>5.1f}%)")
    print()

    # Check if sire/dam/damsire IDs in ra_mst_runners link to ra_horses
    print("LINEAGE REFERENCE VALIDATION:")
    print("-" * 100)

    cur.execute("""
        SELECT
            COUNT(DISTINCT sire_id) FILTER (WHERE sire_id IS NOT NULL) as unique_sires,
            COUNT(DISTINCT dam_id) FILTER (WHERE dam_id IS NOT NULL) as unique_dams,
            COUNT(DISTINCT damsire_id) FILTER (WHERE damsire_id IS NOT NULL) as unique_damsires
        FROM ra_mst_runners;
    """)

    unique_sires, unique_dams, unique_damsires = cur.fetchone()

    print(f"  Unique sires in ra_mst_runners:    {unique_sires:>12,}")
    print(f"  Unique dams in ra_mst_runners:     {unique_dams:>12,}")
    print(f"  Unique damsires in ra_mst_runners: {unique_damsires:>12,}")
    print()

    # Check if these exist in ra_horses
    cur.execute("""
        SELECT
            COUNT(DISTINCT run.sire_id) FILTER (
                WHERE run.sire_id IS NOT NULL
                AND EXISTS (SELECT 1 FROM ra_horses h WHERE h.horse_id = run.sire_id)
            ) as sires_in_horses,
            COUNT(DISTINCT run.dam_id) FILTER (
                WHERE run.dam_id IS NOT NULL
                AND EXISTS (SELECT 1 FROM ra_horses h WHERE h.horse_id = run.dam_id)
            ) as dams_in_horses,
            COUNT(DISTINCT run.damsire_id) FILTER (
                WHERE run.damsire_id IS NOT NULL
                AND EXISTS (SELECT 1 FROM ra_horses h WHERE h.horse_id = run.damsire_id)
            ) as damsires_in_horses
        FROM ra_mst_runners run;
    """)

    sires_in_horses, dams_in_horses, damsires_in_horses = cur.fetchone()

    print(f"  Sires also in ra_horses:    {sires_in_horses:>12,} ({sires_in_horses/unique_sires*100 if unique_sires else 0:>5.1f}%)")
    print(f"  Dams also in ra_horses:     {dams_in_horses:>12,} ({dams_in_horses/unique_dams*100 if unique_dams else 0:>5.1f}%)")
    print(f"  Damsires also in ra_horses: {damsires_in_horses:>12,} ({damsires_in_horses/unique_damsires*100 if unique_damsires else 0:>5.1f}%)")
    print()

    print("=" * 100)
    print("DESIGN CONSIDERATIONS FOR LINEAGE TABLE")
    print("=" * 100)
    print()

    print("CURRENT STATE:")
    print("  • ra_mst_runners has pedigree columns (sire_id, dam_id, damsire_id, etc.)")
    print("  • ra_horse_pedigree has same data (horse_id → sire/dam/damsire)")
    print("  • Both tables store similar pedigree information")
    print()

    print("OPTION 1: Keep Current (Denormalized)")
    print("  Pros: Fast queries, no JOINs needed")
    print("  Cons: Duplicate data, harder to maintain")
    print()

    print("OPTION 2: Create ra_lineage table linked to runner_id")
    print("  Structure:")
    print("    ra_lineage")
    print("      - lineage_id (PK)")
    print("      - runner_id (FK to ra_mst_runners)")
    print("      - generation (1=sire/dam, 2=grandsire/granddam, 3=great-grand, etc.)")
    print("      - relation_type (sire/dam/damsire/grandsire_paternal/etc.)")
    print("      - ancestor_horse_id (FK to ra_horses)")
    print("      - ancestor_name")
    print("      - ancestor_region")
    print("  Pros: Can store unlimited generations, normalized")
    print("  Cons: Complex queries, need JOINs")
    print()

    print("OPTION 3: Enhance ra_horse_pedigree (link via horse_id, not runner_id)")
    print("  Structure:")
    print("    ra_horse_pedigree (existing, enhanced)")
    print("      - horse_id (PK)")
    print("      - sire_id, dam_id, damsire_id (existing)")
    print("      + grandsire_paternal_id, granddam_paternal_id")
    print("      + grandsire_maternal_id, granddam_maternal_id")
    print("      + great_grandsire_ids (JSONB for 4th generation)")
    print("  Pros: Horse-centric (pedigree is property of horse, not runner)")
    print("  Cons: ra_mst_runners still needs sire/dam/damsire for convenience")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
