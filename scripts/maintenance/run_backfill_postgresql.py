"""
PostgreSQL Backfill Runner
Designed to run on Render.com or any server with direct PostgreSQL access
Uses DATABASE_URL environment variable for connection
"""

import os
import sys
import psycopg2
import time
from datetime import datetime

# This script is meant to run on a server (like Render) with direct DB access
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DIRECT_CONNECTION')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    print("This script must run on a server with database access (e.g., Render.com)")
    sys.exit(1)

print("=" * 80)
print("POSTGRESQL DIRECT BACKFILL - Server Mode")
print("=" * 80)
print(f"Starting backfill at {datetime.now()}")
print("This will process all NULL fields in ra_mst_runners table")
print("=" * 80)

# Connect to database
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_session(autocommit=False)

    # Set extended timeouts (should work on direct connection)
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30min'")
        cur.execute("SET lock_timeout = '5min'")
    conn.commit()

    print("✅ Connected to PostgreSQL database")
    print("   Timeouts set: statement=30min, lock=5min\n")

except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Field mappings
FIELDS = [
    ('weight', 'weight_lbs', 'INTEGER', r'^\d+$'),
    ('finishing_time', 'time', 'TEXT', None),
    ('starting_price_decimal', 'sp_dec', 'DECIMAL', r'^\d+\.?\d*$'),
    ('overall_beaten_distance', 'ovr_btn', 'DECIMAL', r'^\d+\.?\d*$'),
    ('jockey_claim_lbs', 'jockey_claim_lbs', 'INTEGER', r'^\d+$'),
    ('weight_stones_lbs', 'weight', 'TEXT', None),
    ('race_comment', 'comment', 'TEXT', None),
    ('jockey_silk_url', 'silk_url', 'TEXT', None),
]

total_updated = 0

for db_field, api_field, sql_cast, pattern in FIELDS:
    print(f"\n{'='*60}")
    print(f"Processing: {db_field}")
    print(f"{'='*60}")

    field_updated = 0
    batch_num = 0
    batch_size = 5000

    while True:
        batch_num += 1

        try:
            with conn.cursor() as cur:
                # Build WHERE clause
                where_parts = [
                    "api_data IS NOT NULL",
                    f"api_data->>'{api_field}' IS NOT NULL",
                    f"api_data->>'{api_field}' != ''",
                    f"{db_field} IS NULL"
                ]

                # Add pattern validation if specified
                if pattern:
                    where_parts.append(f"api_data->>'{api_field}' ~ '{pattern}'")
                    # Also exclude "-" for numeric fields
                    if sql_cast in ('DECIMAL', 'INTEGER'):
                        where_parts.append(f"api_data->>'{api_field}' != '-'")

                where_clause = " AND ".join(where_parts)

                # Build UPDATE query
                if sql_cast == 'TEXT':
                    update_sql = f"""
                        UPDATE ra_mst_runners
                        SET {db_field} = api_data->>'{api_field}', updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_mst_runners
                            WHERE {where_clause}
                            LIMIT {batch_size}
                        )
                    """
                else:
                    update_sql = f"""
                        UPDATE ra_mst_runners
                        SET {db_field} = (api_data->>'{api_field}')::{sql_cast}, updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_mst_runners
                            WHERE {where_clause}
                            LIMIT {batch_size}
                        )
                    """

                # Execute update
                cur.execute(update_sql)
                rows_updated = cur.rowcount
                conn.commit()

                if rows_updated == 0:
                    print(f"  ✅ Complete (no more records)")
                    break

                field_updated += rows_updated
                total_updated += rows_updated
                print(f"  Batch {batch_num}: {rows_updated:,} updated (field total: {field_updated:,})")

                if rows_updated < batch_size:
                    print(f"  ✅ Complete (last batch)")
                    break

        except Exception as e:
            conn.rollback()
            print(f"  ❌ Error in batch {batch_num}: {e}")
            if 'timeout' in str(e).lower():
                print("  Timeout - may need to reduce batch size or increase timeout")
            break

    print(f"✅ {db_field}: {field_updated:,} total updated")

# Cleanup
conn.close()

print("\n" + "=" * 80)
print("BACKFILL COMPLETE")
print("=" * 80)
print(f"Total records updated: {total_updated:,}")
print(f"Completed at {datetime.now()}")
print("=" * 80)
