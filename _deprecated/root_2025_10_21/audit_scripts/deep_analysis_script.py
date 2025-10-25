#!/usr/bin/env python3
"""
Deep Analysis Script - Sample data and additional checks
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient


def deep_analysis():
    """Perform deep analysis with sample data"""
    config = get_config()
    db = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    results = {
        'timestamp': datetime.now().isoformat(),
        'sample_data': {},
        'duplicate_analysis': {},
        'null_pattern_analysis': {}
    }

    tables = ['ra_jockeys', 'ra_trainers', 'ra_owners', 'ra_courses', 'ra_bookmakers']

    for table in tables:
        print(f"\n{'='*80}")
        print(f"Deep Analysis: {table}")
        print(f"{'='*80}")

        # Get sample data
        print(f"  [1/3] Getting sample data...")
        sample = db.client.from_(table).select('*').limit(5).execute()
        results['sample_data'][table] = sample.data

        # Check for duplicate names
        print(f"  [2/3] Checking for duplicate names...")
        all_records = db.client.from_(table).select('*').execute()
        names = [r.get('name') or r.get('bookmaker_name', '') for r in all_records.data]
        name_counts = {}
        for name in names:
            name_counts[name] = name_counts.get(name, 0) + 1

        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        results['duplicate_analysis'][table] = {
            'total_records': len(all_records.data),
            'unique_names': len(set(names)),
            'duplicate_names': duplicates,
            'duplicate_count': len(duplicates)
        }

        if duplicates:
            print(f"        Found {len(duplicates)} duplicate names")
        else:
            print(f"        No duplicate names")

        # Analyze NULL patterns for statistics fields
        if table in ['ra_jockeys', 'ra_trainers', 'ra_owners']:
            print(f"  [3/3] Analyzing NULL patterns in statistics...")

            # Get records with NULL win_rate
            null_win_rate = db.client.from_(table).select('*').is_('win_rate', 'null').limit(10).execute()

            null_patterns = {
                'null_win_rate_sample': null_win_rate.data[:3] if null_win_rate.data else [],
                'null_win_rate_count': len(null_win_rate.data)
            }

            results['null_pattern_analysis'][table] = null_patterns
            print(f"        Found {len(null_win_rate.data)} records with NULL win_rate")
        else:
            print(f"  [3/3] No statistics fields for this table")

    # Save results
    filepath = os.path.join(os.path.dirname(__file__), 'deep_analysis_results.json')
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"Deep analysis saved to: {filepath}")
    print(f"{'='*80}")

    return results


if __name__ == '__main__':
    deep_analysis()
