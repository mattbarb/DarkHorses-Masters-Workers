#!/usr/bin/env python3
"""
Apply SQL migration to Supabase database
Uses psycopg2 to execute SQL directly
"""

import psycopg2
import sys
from pathlib import Path

def apply_migration(migration_file: str):
    """Apply a SQL migration file to the database"""

    # Supabase connection string
    # Format: postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
    # URL-encode special characters in password: @ -> %40, ! -> %21
    from urllib.parse import quote_plus
    password = "Tanner@barber01!"
    encoded_password = quote_plus(password)
    conn_string = f"postgresql://postgres.amsjvmlaknnvppxsgpfk:{encoded_password}@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

    # Read migration SQL
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"Error: Migration file not found: {migration_file}")
        return False

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    print(f"Applying migration: {migration_path.name}")
    print(f"SQL size: {len(migration_sql)} bytes")

    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        conn.autocommit = False
        cursor = conn.cursor()

        print("Connected to database successfully")

        # Execute migration
        cursor.execute(migration_sql)

        # Commit transaction
        conn.commit()

        print("Migration applied successfully!")

        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ra_runners'
            AND column_name IN ('position', 'distance_beaten', 'prize_won', 'starting_price', 'result_updated_at')
            ORDER BY column_name
        """)

        columns = cursor.fetchall()
        if columns:
            print("\nVerified new columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
        else:
            print("\nWarning: Could not verify columns were added")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
    else:
        migration_file = 'migrations/005_add_position_fields_to_runners.sql'

    success = apply_migration(migration_file)
    sys.exit(0 if success else 1)
