"""
Simple sample audit - just pull records and examine them
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient

def analyze_records(records, fields_to_check):
    """Analyze a list of records"""
    if not records:
        return {}

    total = len(records)
    stats = {}

    for field in fields_to_check:
        non_null = sum(1 for r in records if r.get(field) is not None and r.get(field) != '')
        stats[field] = {
            'total': total,
            'non_null': non_null,
            'null': total - non_null,
            'population_pct': round((non_null / total * 100) if total > 0 else 0, 2)
        }

    return stats

def main():
    """Main function"""
    print("="*80)
    print("SIMPLE SAMPLE AUDIT - Pull Records Directly")
    print("="*80)

    config = get_config()
    client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    print("\nFetching 1000 recent runner records...")

    try:
        # Just pull 1000 records with ALL fields
        result = client.client.from_('ra_runners').select('*').limit(1000).execute()

        if not hasattr(result, 'data') or not result.data:
            print("❌ No data returned")
            return

        records = result.data
        print(f"✓ Retrieved {len(records)} records\n")

        # Define fields to check
        fields_to_check = {
            'Core ID': ['runner_id', 'race_id', 'horse_id', 'jockey_id', 'trainer_id'],
            'Race Entry': ['draw', 'number', 'form', 'weight', 'headgear'],
            'Results (Original)': ['position', 'distance_beaten', 'prize_won', 'starting_price', 'finishing_time'],
            'Results (Enhanced - Migration 011)': ['starting_price_decimal', 'race_comment', 'jockey_silk_url',
                                                   'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs'],
            'Pedigree in Runners': ['sire_id', 'sire_name', 'dam_id', 'dam_name', 'damsire_id', 'damsire_name'],
            'Duplicate Check': ['silk_url', 'jockey_silk_url']
        }

        # Analyze each category
        all_stats = {}

        for category, fields in fields_to_check.items():
            print(f"\n{category.upper()}")
            print("-" * 70)

            stats = analyze_records(records, fields)
            all_stats[category] = stats

            for field, field_stats in stats.items():
                pop_pct = field_stats['population_pct']

                if pop_pct >= 99:
                    icon = "✓"
                elif pop_pct >= 75:
                    icon = "⚠"
                elif pop_pct > 0:
                    icon = "⚠"
                else:
                    icon = "❌"

                non_null = field_stats['non_null']
                total = field_stats['total']

                print(f"{icon} {field:.<40} {pop_pct:>6.2f}% ({non_null}/{total})")

        # Special checks
        print(f"\n{'='*80}")
        print("SPECIAL CHECKS")
        print(f"{'='*80}\n")

        # Check if silk_url and jockey_silk_url have same values
        print("1. Duplicate Column Check (silk_url vs jockey_silk_url):")
        silk_populated = [r for r in records if r.get('silk_url')]
        jockey_silk_populated = [r for r in records if r.get('jockey_silk_url')]

        print(f"   silk_url populated: {len(silk_populated)}/{len(records)}")
        print(f"   jockey_silk_url populated: {len(jockey_silk_populated)}/{len(records)}")

        if silk_populated and jockey_silk_populated:
            # Check if values are identical
            sample = records[0]
            if sample.get('silk_url') == sample.get('jockey_silk_url'):
                print("   → Both fields have IDENTICAL values (duplicate)")
            else:
                print("   → Fields have DIFFERENT values")
        elif silk_populated:
            print("   → Use silk_url (jockey_silk_url is empty)")
            print(f"   Example silk_url: {silk_populated[0]['silk_url']}")
        elif jockey_silk_populated:
            print("   → Use jockey_silk_url (silk_url is empty)")
            print(f"   Example jockey_silk_url: {jockey_silk_populated[0]['jockey_silk_url']}")
        else:
            print("   → Both fields are empty")

        # Check if enhanced fields are truly empty
        print("\n2. Enhanced Fields Check (Migration 011 - Added 2025-10-17):")
        enhanced_fields = ['starting_price_decimal', 'race_comment', 'jockey_silk_url',
                          'overall_beaten_distance', 'jockey_claim_lbs', 'weight_stones_lbs']

        for field in enhanced_fields:
            populated = [r for r in records if r.get(field) is not None and r.get(field) != '']
            if populated:
                print(f"   {field}: HAS DATA")
                print(f"      Example: {str(populated[0][field])[:60]}")
            else:
                print(f"   {field}: EMPTY (NULL or '')")

        # Save full report
        output = {
            'sample_size': len(records),
            'timestamp': str(Path(__file__).parent),
            'statistics': all_stats
        }

        output_file = Path(__file__).parent / 'simple_audit_results.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
