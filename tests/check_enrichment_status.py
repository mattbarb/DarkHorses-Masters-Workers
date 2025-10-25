#!/usr/bin/env python3
"""
Quick diagnostic to check if **TEST** horses have enrichment fields populated

IMPORTANT: Based on code review, enrichment fields (dob, sex_code, breeder, pedigree)
are stored in ra_horse_pedigree table, NOT ra_mst_horses table.

ra_mst_horses only has: id, name, sex, created_at, updated_at
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

def main():
    """Check enrichment status of test horses"""

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    print("\n" + "=" * 80)
    print("CHECKING ENRICHMENT STATUS OF **TEST** HORSES")
    print("=" * 80 + "\n")

    # Query horses with **TEST** marker
    # Note: Column is 'name' not 'horse_name', key is 'id' not 'horse_id'
    result = db_client.client.table('ra_mst_horses').select('*').like('name', '%**TEST**%').limit(10).execute()

    if not result.data:
        print("❌ No **TEST** horses found in ra_mst_horses")
        print("\nThis means:")
        print("- Either no test has been run yet")
        print("- OR the test data was already cleaned up")
        return

    print(f"Found {len(result.data)} **TEST** horses in ra_mst_horses\n")

    # Show what ra_mst_horses contains (should only be basic fields)
    print("ra_mst_horses fields (basic identification only):")
    for horse in result.data[:3]:  # Show first 3
        print(f"  ID: {horse.get('id')}")
        print(f"  Name: {horse.get('name', 'NULL')[:60]}")
        print(f"  Sex: {horse.get('sex', 'NULL')}")
        print()

    # Now check ra_horse_pedigree for enrichment data
    print("=" * 80)
    print("CHECKING ra_horse_pedigree FOR ENRICHMENT DATA")
    print("=" * 80 + "\n")

    # Get horse IDs
    horse_ids = [h['id'] for h in result.data]

    # Query pedigree table
    pedigree_result = db_client.client.table('ra_horse_pedigree').select('*').in_('horse_id', horse_ids).execute()

    if not pedigree_result.data:
        print("❌ NO pedigree records found for **TEST** horses")
        print("\n⚠️  ENRICHMENT DID NOT RUN")
        print("\nPossible causes:")
        print("1. Horses already existed in database (enrichment only for NEW horses)")
        print("2. API enrichment call failed or was skipped")
        print("3. EntityExtractor not receiving api_client parameter")
        print("4. Test script ran before enrichment process completed")
    else:
        print(f"✅ Found {len(pedigree_result.data)} pedigree records for **TEST** horses\n")

        for pedigree in pedigree_result.data:
            print(f"Horse ID: {pedigree.get('horse_id')}")
            print(f"  DOB: {pedigree.get('dob', 'NULL')}")
            print(f"  Sex Code: {pedigree.get('sex_code', 'NULL')}")
            print(f"  Colour: {pedigree.get('colour', 'NULL')}")
            print(f"  Region: {pedigree.get('region', 'NULL')}")
            print(f"  Breeder: {pedigree.get('breeder', 'NULL')[:50] if pedigree.get('breeder') else 'NULL'}")
            print(f"  Sire: {pedigree.get('sire', 'NULL')[:40] if pedigree.get('sire') else 'NULL'}")
            print(f"  Dam: {pedigree.get('dam', 'NULL')[:40] if pedigree.get('dam') else 'NULL'}")
            print(f"  Damsire: {pedigree.get('damsire', 'NULL')[:40] if pedigree.get('damsire') else 'NULL'}")
            print()

        print("=" * 80)
        print("✅ ENRICHMENT IS WORKING")
        print("=" * 80)
        print("\nHorses have pedigree records, meaning enrichment process ran successfully.")
        print("\nAbout the 87.5% coverage in ra_mst_horses:")
        print("- This is EXPECTED behavior")
        print("- ra_mst_horses only has 5 basic fields (id, name, sex, created_at, updated_at)")
        print("- Enrichment data (dob, breeder, pedigree) is stored in ra_horse_pedigree")
        print("- The test script adds **TEST** markers to ra_mst_horses fields only")
        print("- Pedigree data populated separately, doesn't get **TEST** markers")

    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()
