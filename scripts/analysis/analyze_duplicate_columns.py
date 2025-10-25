"""
Analyze duplicate columns in ra_runners table
Identifies which duplicates have data vs which are empty
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import get_config
from supabase import create_client
from utils.logger import get_logger

logger = get_logger('analyze_duplicates')

# Potential duplicate column groups based on field mappings
DUPLICATE_GROUPS = [
    {
        'name': 'Weight (integer)',
        'columns': ['weight', 'weight_lbs'],
        'description': 'Both map to API field weight_lbs (integer)'
    },
    {
        'name': 'Comment',
        'columns': ['comment', 'race_comment'],
        'description': 'Both map to API field comment (text)'
    },
    {
        'name': 'Silk URL',
        'columns': ['silk_url', 'jockey_silk_url'],
        'description': 'Both map to API field silk_url (text)'
    }
]


def analyze_column_usage(supabase, column_name: str):
    """
    Analyze how much data a column has

    Returns:
        dict with counts
    """
    try:
        # Get total records
        total_result = supabase.table('ra_runners') \
            .select('runner_id', count='exact') \
            .limit(1) \
            .execute()

        total_records = total_result.count if hasattr(total_result, 'count') else 0

        # Get non-null records for this column
        non_null_result = supabase.table('ra_runners') \
            .select('runner_id', count='exact') \
            .not_.is_(column_name, 'null') \
            .limit(1) \
            .execute()

        non_null_count = non_null_result.count if hasattr(non_null_result, 'count') else 0

        # Calculate percentage
        pct = (non_null_count / total_records * 100) if total_records > 0 else 0

        return {
            'column': column_name,
            'total_records': total_records,
            'non_null_count': non_null_count,
            'null_count': total_records - non_null_count,
            'non_null_pct': pct
        }

    except Exception as e:
        logger.error(f"Error analyzing {column_name}: {e}")
        return {
            'column': column_name,
            'error': str(e)
        }


def main():
    logger.info("=" * 80)
    logger.info("DUPLICATE COLUMN ANALYSIS FOR ra_runners")
    logger.info("=" * 80)

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"Connected to: {config.supabase.url}\n")

    recommendations = []

    for group in DUPLICATE_GROUPS:
        logger.info(f"\n{'='*60}")
        logger.info(f"Group: {group['name']}")
        logger.info(f"Description: {group['description']}")
        logger.info(f"{'='*60}")

        group_results = []

        for column in group['columns']:
            logger.info(f"\nAnalyzing: {column}")
            result = analyze_column_usage(supabase, column)

            if 'error' in result:
                logger.error(f"  ❌ Error: {result['error']}")
            else:
                logger.info(f"  Total records: {result['total_records']:,}")
                logger.info(f"  Non-NULL: {result['non_null_count']:,} ({result['non_null_pct']:.2f}%)")
                logger.info(f"  NULL: {result['null_count']:,}")

                group_results.append(result)

        # Determine recommendation
        if len(group_results) == 2:
            col1, col2 = group_results

            if col1['non_null_count'] > 0 and col2['non_null_count'] == 0:
                recommendation = {
                    'action': 'DROP',
                    'column': col2['column'],
                    'reason': f"{col2['column']} is empty, keep {col1['column']}"
                }
            elif col2['non_null_count'] > 0 and col1['non_null_count'] == 0:
                recommendation = {
                    'action': 'DROP',
                    'column': col1['column'],
                    'reason': f"{col1['column']} is empty, keep {col2['column']}"
                }
            elif col1['non_null_count'] == 0 and col2['non_null_count'] == 0:
                recommendation = {
                    'action': 'DROP_BOTH_OR_ONE',
                    'column': f"{col1['column']} OR {col2['column']}",
                    'reason': f"Both empty, drop one or both"
                }
            elif col1['non_null_count'] > col2['non_null_count']:
                recommendation = {
                    'action': 'MERGE_AND_DROP',
                    'column': col2['column'],
                    'reason': f"{col1['column']} has more data ({col1['non_null_count']:,} vs {col2['non_null_count']:,}), merge {col2['column']} into {col1['column']} and drop"
                }
            elif col2['non_null_count'] > col1['non_null_count']:
                recommendation = {
                    'action': 'MERGE_AND_DROP',
                    'column': col1['column'],
                    'reason': f"{col2['column']} has more data ({col2['non_null_count']:,} vs {col1['non_null_count']:,}), merge {col1['column']} into {col2['column']} and drop"
                }
            else:
                recommendation = {
                    'action': 'MANUAL_REVIEW',
                    'column': f"{col1['column']} and {col2['column']}",
                    'reason': f"Both have equal data ({col1['non_null_count']:,}), need manual review"
                }

            recommendations.append(recommendation)
            logger.info(f"\n✅ Recommendation: {recommendation['action']}")
            logger.info(f"   {recommendation['reason']}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CLEANUP RECOMMENDATIONS SUMMARY")
    logger.info("=" * 80)

    for rec in recommendations:
        logger.info(f"\n{rec['action']}: {rec['column']}")
        logger.info(f"  Reason: {rec['reason']}")

    logger.info("\n" + "=" * 80)
    logger.info("Next Steps:")
    logger.info("1. Review recommendations above")
    logger.info("2. Create migration to drop unused duplicate columns")
    logger.info("3. If needed, merge data before dropping")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
