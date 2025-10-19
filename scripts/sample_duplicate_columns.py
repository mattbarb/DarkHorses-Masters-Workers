"""
Sample-based analysis of duplicate columns in ra_runners
Uses small sample to avoid timeouts
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import get_config
from supabase import create_client
from utils.logger import get_logger

logger = get_logger('sample_duplicates')

# Duplicate column groups
DUPLICATE_GROUPS = [
    {
        'name': 'Weight (integer)',
        'columns': ['weight', 'weight_lbs'],
        'api_field': 'weight_lbs'
    },
    {
        'name': 'Comment',
        'columns': ['comment', 'race_comment'],
        'api_field': 'comment'
    },
    {
        'name': 'Silk URL',
        'columns': ['silk_url', 'jockey_silk_url'],
        'api_field': 'silk_url'
    }
]


def main():
    logger.info("=" * 80)
    logger.info("SAMPLE-BASED DUPLICATE COLUMN ANALYSIS")
    logger.info("=" * 80)

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"Connected to: {config.supabase.url}\n")

    sample_size = 1000

    for group in DUPLICATE_GROUPS:
        logger.info(f"\n{'='*60}")
        logger.info(f"Group: {group['name']}")
        logger.info(f"API Field: {group['api_field']}")
        logger.info(f"Columns: {', '.join(group['columns'])}")
        logger.info(f"{'='*60}")

        # Fetch sample with all columns
        try:
            columns = ['runner_id'] + group['columns']
            result = supabase.table('ra_runners') \
                .select(','.join(columns)) \
                .limit(sample_size) \
                .execute()

            records = result.data
            logger.info(f"\nFetched {len(records)} sample records")

            # Count non-null values for each column
            stats = {col: 0 for col in group['columns']}

            for record in records:
                for col in group['columns']:
                    if record.get(col) is not None:
                        stats[col] += 1

            # Display stats
            logger.info(f"\nNon-NULL counts in sample of {len(records)}:")
            for col, count in stats.items():
                pct = (count / len(records) * 100) if len(records) > 0 else 0
                logger.info(f"  {col:20s}: {count:4d} ({pct:5.1f}%)")

            # Recommendation
            col1, col2 = group['columns']
            count1, count2 = stats[col1], stats[col2]

            logger.info(f"\n📊 Analysis:")
            if count1 == 0 and count2 == 0:
                logger.info(f"  Both columns are empty in sample")
                logger.info(f"  ⚠️  Likely both are empty across entire table")
                logger.info(f"  💡 Recommendation: Keep {col1}, drop {col2}")
                logger.info(f"     Reason: Backfill script populates {col1}")
            elif count1 > 0 and count2 == 0:
                logger.info(f"  {col1} has data, {col2} is empty")
                logger.info(f"  ✅ Recommendation: DROP {col2}")
                logger.info(f"     Reason: {col2} is unused")
            elif count2 > 0 and count1 == 0:
                logger.info(f"  {col2} has data, {col1} is empty")
                logger.info(f"  ✅ Recommendation: DROP {col1}")
                logger.info(f"     Reason: {col1} is unused")
            elif count1 == count2:
                logger.info(f"  Both columns have identical population ({count1} records)")
                logger.info(f"  🔍 Need to check if values are identical...")

                # Sample a few to check if values match
                identical_count = 0
                different_count = 0
                for record in records[:50]:  # Check first 50
                    val1 = record.get(col1)
                    val2 = record.get(col2)
                    if val1 is not None and val2 is not None:
                        if val1 == val2:
                            identical_count += 1
                        else:
                            different_count += 1

                if identical_count > 0 and different_count == 0:
                    logger.info(f"  Values are identical across samples")
                    logger.info(f"  ✅ Recommendation: Keep {col1}, DROP {col2}")
                    logger.info(f"     Reason: Duplicate data")
                elif different_count > 0:
                    logger.info(f"  ⚠️  Values differ! Both columns have unique data")
                    logger.info(f"  🔧 Recommendation: MERGE {col2} into {col1}, then drop {col2}")
                    logger.info(f"     SQL: UPDATE ra_runners SET {col1} = COALESCE({col1}, {col2})")
            else:
                logger.info(f"  Both columns have data but different amounts")
                logger.info(f"  🔧 Recommendation: MERGE {col2} into {col1}, then drop {col2}")
                logger.info(f"     SQL: UPDATE ra_runners SET {col1} = COALESCE({col1}, {col2})")

        except Exception as e:
            logger.error(f"Error analyzing group: {e}", exc_info=True)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CLEANUP RECOMMENDATIONS")
    logger.info("=" * 80)
    logger.info("\nBased on sample analysis, recommended approach:")
    logger.info("\n1. Check current backfill script usage:")
    logger.info("   - scripts/backfill_runners_optimized.py populates these fields:")
    logger.info("     • weight (not weight_lbs)")
    logger.info("     • race_comment (not comment)")
    logger.info("     • jockey_silk_url (not silk_url)")
    logger.info("\n2. Recommended actions:")
    logger.info("   a. If duplicates have no data: DROP unused column")
    logger.info("   b. If duplicates have different data: MERGE then DROP")
    logger.info("   c. If duplicates have identical data: DROP one")
    logger.info("\n3. Create migration SQL after confirming which columns to keep")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
