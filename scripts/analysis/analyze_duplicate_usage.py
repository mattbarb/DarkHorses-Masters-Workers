#!/usr/bin/env python3
"""
Analyze which duplicate columns are actually being used and which should be kept/dropped
"""

import psycopg2
import sys

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("DUPLICATE COLUMN USAGE ANALYSIS")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Sample some recent records to see what data is populated
    cur.execute("""
        SELECT
            -- Weight columns
            weight_lbs,
            weight_stones_lbs,

            -- Starting price columns
            starting_price,
            starting_price_decimal,

            -- Sex columns
            horse_sex,
            horse_sex_code,

            -- Sample identifying info
            runner_id,
            horse_name
        FROM ra_mst_runners
        WHERE updated_at > NOW() - INTERVAL '1 day'
        LIMIT 20;
    """)

    rows = cur.fetchall()

    print(f"Sample of {len(rows)} recent records:")
    print("=" * 100)
    print()

    print("WEIGHT COLUMNS:")
    print(f"{'weight_lbs':<20} {'weight_stones_lbs':<20} {'Horse':<30}")
    print("-" * 70)
    for row in rows[:10]:
        weight_lbs, weight_stones_lbs, sp, sp_dec, sex, sex_code, runner_id, horse_name = row
        print(f"{str(weight_lbs):<20} {str(weight_stones_lbs):<20} {horse_name:<30}")

    print()
    print("STARTING PRICE COLUMNS:")
    print(f"{'starting_price':<20} {'starting_price_decimal':<20} {'Horse':<30}")
    print("-" * 70)
    for row in rows[:10]:
        weight_lbs, weight_stones_lbs, sp, sp_dec, sex, sex_code, runner_id, horse_name = row
        print(f"{str(sp):<20} {str(sp_dec):<20} {horse_name:<30}")

    print()
    print("SEX COLUMNS:")
    print(f"{'horse_sex':<20} {'horse_sex_code':<20} {'Horse':<30}")
    print("-" * 70)
    for row in rows[:10]:
        weight_lbs, weight_stones_lbs, sp, sp_dec, sex, sex_code, runner_id, horse_name = row
        print(f"{str(sex):<20} {str(sex_code):<20} {horse_name:<30}")

    print()
    print("=" * 100)
    print("POPULATION STATISTICS")
    print("=" * 100)
    print()

    # Count non-null values for each duplicate column
    cur.execute("""
        SELECT
            COUNT(*) as total_runners,

            -- Weight
            COUNT(weight_lbs) as weight_lbs_populated,
            COUNT(weight_stones_lbs) as weight_stones_lbs_populated,

            -- Starting price
            COUNT(starting_price) as starting_price_populated,
            COUNT(starting_price_decimal) as starting_price_decimal_populated,

            -- Sex
            COUNT(horse_sex) as horse_sex_populated,
            COUNT(horse_sex_code) as horse_sex_code_populated
        FROM ra_mst_runners;
    """)

    stats = cur.fetchone()
    total = stats[0]

    print(f"Total runners in database: {total:,}")
    print()

    print("WEIGHT COLUMNS:")
    print(f"  weight_lbs:         {stats[1]:>10,} ({stats[1]/total*100:>5.1f}%)")
    print(f"  weight_stones_lbs:  {stats[2]:>10,} ({stats[2]/total*100:>5.1f}%)")
    print()

    print("STARTING PRICE COLUMNS:")
    print(f"  starting_price:          {stats[3]:>10,} ({stats[3]/total*100:>5.1f}%)")
    print(f"  starting_price_decimal:  {stats[4]:>10,} ({stats[4]/total*100:>5.1f}%)")
    print()

    print("SEX COLUMNS:")
    print(f"  horse_sex:       {stats[5]:>10,} ({stats[5]/total*100:>5.1f}%)")
    print(f"  horse_sex_code:  {stats[6]:>10,} ({stats[6]/total*100:>5.1f}%)")
    print()

    # Check if the columns contain the same or different data
    print("=" * 100)
    print("DATA COMPARISON - Are duplicates actually storing the same data?")
    print("=" * 100)
    print()

    # Weight comparison
    cur.execute("""
        SELECT COUNT(*)
        FROM ra_mst_runners
        WHERE weight_lbs IS NOT NULL
          AND weight_stones_lbs IS NOT NULL
          AND weight_lbs::text != weight_stones_lbs::text
        LIMIT 1;
    """)
    weight_diff = cur.fetchone()[0]
    print(f"Weight: Different values found: {weight_diff > 0}")
    if weight_diff > 0:
        cur.execute("""
            SELECT weight_lbs, weight_stones_lbs, horse_name
            FROM ra_mst_runners
            WHERE weight_lbs IS NOT NULL
              AND weight_stones_lbs IS NOT NULL
              AND weight_lbs::text != weight_stones_lbs::text
            LIMIT 5;
        """)
        print("  Examples of differences:")
        for w_lbs, w_st_lbs, h_name in cur.fetchall():
            print(f"    {h_name}: weight_lbs={w_lbs}, weight_stones_lbs={w_st_lbs}")
    print()

    # Starting price comparison
    cur.execute("""
        SELECT COUNT(*)
        FROM ra_mst_runners
        WHERE starting_price IS NOT NULL
          AND starting_price_decimal IS NOT NULL
        LIMIT 1;
    """)
    sp_both = cur.fetchone()[0]
    if sp_both > 0:
        cur.execute("""
            SELECT starting_price, starting_price_decimal, horse_name
            FROM ra_mst_runners
            WHERE starting_price IS NOT NULL
              AND starting_price_decimal IS NOT NULL
            LIMIT 5;
        """)
        print("Starting Price: Both columns populated - showing examples:")
        for sp, sp_dec, h_name in cur.fetchall():
            print(f"  {h_name}: starting_price={sp}, starting_price_decimal={sp_dec}")
    print()

    # Sex comparison
    cur.execute("""
        SELECT COUNT(*)
        FROM ra_mst_runners
        WHERE horse_sex IS NOT NULL
          AND horse_sex_code IS NOT NULL
          AND horse_sex != horse_sex_code
        LIMIT 1;
    """)
    sex_diff = cur.fetchone()[0]
    print(f"Sex: Different values found: {sex_diff > 0}")
    if sex_diff > 0:
        cur.execute("""
            SELECT horse_sex, horse_sex_code, horse_name
            FROM ra_mst_runners
            WHERE horse_sex IS NOT NULL
              AND horse_sex_code IS NOT NULL
              AND horse_sex != horse_sex_code
            LIMIT 10;
        """)
        print("  Examples of differences:")
        for sex, sex_code, h_name in cur.fetchall():
            print(f"    {h_name}: horse_sex={sex}, horse_sex_code={sex_code}")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
