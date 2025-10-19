"""Quick audit using simple queries"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient

def main():
    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    print("Getting sample records from each table...")

    tables = {
        'ra_runners': 'runner_id',
        'ra_races': 'race_id',
        'ra_horses': 'horse_id',
        'ra_horse_pedigree': 'horse_id'
    }

    for table, id_col in tables.items():
        print(f"\n{'='*60}")
        print(f"Table: {table}")
        print(f"{'='*60}")

        try:
            # Get count
            count = client.get_table_count(table)
            print(f"Row Count: {count:,}")

            # Get one sample
            result = client.client.from_(table).select('*').limit(1).execute()

            if hasattr(result, 'data') and result.data:
                sample = result.data[0]
                columns = list(sample.keys())

                print(f"Columns ({len(columns)}):")
                for col in sorted(columns):
                    value = sample[col]
                    # Show type and example value
                    value_preview = str(value)[:50] if value is not None else 'NULL'
                    print(f"  {col}: {value_preview}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
