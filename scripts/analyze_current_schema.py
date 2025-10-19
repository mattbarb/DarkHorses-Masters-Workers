#!/usr/bin/env python3
"""
Analyze current ra_runners schema for duplicates and inconsistencies
"""

import psycopg2
import sys
from collections import defaultdict

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("RA_RUNNERS SCHEMA ANALYSIS - COMPLETE REVIEW")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Get all columns with details
    cur.execute("""
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_name = 'ra_runners'
        ORDER BY ordinal_position;
    """)

    columns = cur.fetchall()

    print(f"Total Columns: {len(columns)}")
    print()
    print("=" * 100)
    print("ALL COLUMNS (in table order)")
    print("=" * 100)
    print(f"{'#':<4} {'Column Name':<35} {'Type':<20} {'Length':<8} {'Nullable':<10}")
    print("-" * 100)

    for i, (col_name, data_type, max_len, nullable, default, pos) in enumerate(columns, 1):
        type_str = f"{data_type}"
        if max_len and data_type in ('character varying', 'character'):
            type_str += f"({max_len})"
        nullable_str = "YES" if nullable == "YES" else "NO"
        print(f"{pos:<4} {col_name:<35} {type_str:<20} {str(max_len) if max_len else '-':<8} {nullable_str:<10}")

    print()
    print("=" * 100)
    print("DUPLICATE ANALYSIS")
    print("=" * 100)
    print()

    # Analyze for potential duplicates by grouping similar names
    column_groups = defaultdict(list)

    for col_name, data_type, max_len, nullable, default, pos in columns:
        # Group by base name patterns
        base_name = col_name.lower()

        # Remove common prefixes/suffixes for grouping
        for prefix in ['horse_', 'jockey_', 'trainer_', 'owner_', 'sire_', 'dam_', 'damsire_']:
            if base_name.startswith(prefix):
                base_name = base_name[len(prefix):]
                break

        for suffix in ['_data', '_lbs', '_decimal', '_code', '_id', '_name', '_url']:
            if base_name.endswith(suffix):
                base_name = base_name[:-len(suffix)]
                break

        column_groups[base_name].append({
            'name': col_name,
            'type': data_type,
            'max_len': max_len,
            'nullable': nullable
        })

    # Find groups with multiple columns (potential duplicates)
    print("POTENTIAL DUPLICATE GROUPS:")
    print("-" * 100)

    duplicate_groups = []
    for base_name, cols in sorted(column_groups.items()):
        if len(cols) > 1:
            duplicate_groups.append((base_name, cols))
            print(f"\n'{base_name}' base → {len(cols)} columns:")
            for col in cols:
                type_str = col['type']
                if col['max_len'] and col['type'] in ('character varying', 'character'):
                    type_str += f"({col['max_len']})"
                print(f"  • {col['name']:<35} {type_str:<25} {'NULL' if col['nullable'] == 'YES' else 'NOT NULL'}")

    if not duplicate_groups:
        print("No obvious duplicate groups found!")

    print()
    print("=" * 100)
    print("SPECIFIC DUPLICATE CHECKS")
    print("=" * 100)
    print()

    # Check for specific known duplicates
    col_dict = {col[0]: col for col in columns}

    checks = [
        # Weight columns
        (['weight', 'weight_lbs', 'weight_stones_lbs'], 'Weight'),
        # Price columns
        (['starting_price', 'starting_price_decimal', 'sp', 'sp_decimal'], 'Starting Price'),
        # Distance beaten
        (['distance_beaten', 'overall_beaten_distance', 'btn', 'ovr_btn'], 'Distance Beaten'),
        # Rating columns
        (['rpr', 'racing_post_rating'], 'RPR Rating'),
        # Jockey claim
        (['jockey_claim', 'jockey_claim_lbs', 'apprentice_allowance'], 'Jockey Claim'),
        # Age
        (['age', 'horse_age'], 'Horse Age'),
        # Sex
        (['sex', 'horse_sex', 'horse_sex_code'], 'Horse Sex'),
        # Colour
        (['colour', 'horse_colour', 'colour_code', 'horse_colour_code'], 'Horse Colour'),
        # DOB
        (['dob', 'horse_dob'], 'Horse DOB'),
        # Region
        (['region', 'horse_region'], 'Horse Region'),
        # Comment
        (['comment', 'race_comment'], 'Comment'),
        # Silk
        (['silk_url', 'jockey_silk_url'], 'Silk URL'),
        # Trainer data
        (['trainer_14_days', 'trainer_14_days_data'], 'Trainer 14 Days'),
        # Quotes
        (['quotes', 'quotes_data'], 'Quotes'),
        # Medical
        (['medical', 'medical_data'], 'Medical'),
        # Stable tour
        (['stable_tour', 'stable_tour_data'], 'Stable Tour'),
    ]

    found_issues = []

    for col_list, description in checks:
        existing = [c for c in col_list if c in col_dict]
        if len(existing) > 1:
            found_issues.append((description, existing))
            print(f"⚠️  {description}: {len(existing)} columns found")
            for col_name in existing:
                col_data = col_dict[col_name]
                type_str = col_data[1]
                if col_data[2] and col_data[1] in ('character varying', 'character'):
                    type_str += f"({col_data[2]})"
                print(f"     • {col_name:<35} {type_str}")
            print()

    if not found_issues:
        print("✅ No duplicate columns found in specific checks!")

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total columns analyzed: {len(columns)}")
    print(f"Potential duplicate groups: {len(duplicate_groups)}")
    print(f"Specific issues found: {len(found_issues)}")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
