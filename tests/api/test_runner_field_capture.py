"""
Test Runner Field Capture - Validate ALL 18 fields with real data
This script fetches real racecards, stores them, and verifies field population
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import get_config
from utils.logger import get_logger
from fetchers.races_fetcher import RacesFetcher
from supabase import create_client

logger = get_logger('test_runner_fields')

# The 18 fields we're validating (note: jockey_silk_url doesn't exist in DB, using silk_url instead)
FIELDS_TO_CHECK = [
    'draw',
    'jockey_claim',
    'apprentice_allowance',
    'form',
    'form_string',
    'days_since_last_run',
    'last_run_performance',
    'career_runs',
    'career_wins',
    'career_places',
    'prize_money_won',
    'racing_post_rating',
    'race_comment',
    'silk_url',  # Note: DB has silk_url, not jockey_silk_url (Migration 011 incomplete)
    'starting_price_decimal',
    'overall_beaten_distance',
    'jockey_claim_lbs',
    'weight_stones_lbs'
]


def fetch_test_data():
    """Fetch a small amount of test data"""
    logger.info("=" * 80)
    logger.info("STEP 1: Fetch Test Racecards")
    logger.info("=" * 80)

    fetcher = RacesFetcher()

    # Fetch just 2 days of data (today and yesterday)
    result = fetcher.fetch_and_store(
        days_back=2,
        region_codes=['gb', 'ire']
    )

    logger.info(f"Fetched {result.get('races_fetched', 0)} races")
    logger.info(f"Fetched {result.get('runners_fetched', 0)} runners")
    logger.info(f"Inserted {result.get('runners_inserted', 0)} runner records")

    return result


def validate_runners():
    """Query database and validate runner records"""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Validate Runner Records in Database")
    logger.info("=" * 80)

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    # Get 5 recent runners
    logger.info("Fetching 5 most recent runner records...")
    result = supabase.table('ra_runners') \
        .select('*') \
        .order('created_at', desc=True) \
        .limit(5) \
        .execute()

    runners = result.data

    if not runners:
        logger.error("❌ No runners found in database!")
        return None

    logger.info(f"Found {len(runners)} runners to validate")

    # Validate each runner
    validation_results = []

    for i, runner in enumerate(runners, 1):
        logger.info(f"\n{'-' * 80}")
        logger.info(f"Runner {i}: {runner.get('horse_name')} (ID: {runner.get('runner_id')})")
        logger.info(f"Race: {runner.get('race_id')}")
        logger.info(f"{'-' * 80}")

        runner_validation = {
            'runner_id': runner.get('runner_id'),
            'horse_name': runner.get('horse_name'),
            'race_id': runner.get('race_id'),
            'fields_populated': {},
            'fields_missing': [],
            'api_data_keys': []
        }

        # Check each field
        for field in FIELDS_TO_CHECK:
            value = runner.get(field)
            is_populated = value is not None
            status = "✅" if is_populated else "❌"

            # Format value for display
            if value is None:
                display_value = "NULL"
            elif isinstance(value, (int, float)):
                display_value = str(value)
            elif isinstance(value, str):
                display_value = f'"{value[:50]}..."' if len(str(value)) > 50 else f'"{value}"'
            else:
                display_value = str(value)

            logger.info(f"{status} {field:30s}: {display_value}")

            runner_validation['fields_populated'][field] = is_populated
            if not is_populated:
                runner_validation['fields_missing'].append(field)

        # Check api_data to see what was available
        api_data = runner.get('api_data', {})
        if api_data:
            runner_validation['api_data_keys'] = list(api_data.keys())
            logger.info(f"\n📋 API data keys available ({len(api_data.keys())} total):")
            logger.info(f"   {', '.join(sorted(api_data.keys()))}")

        validation_results.append(runner_validation)

    return validation_results


def generate_summary(validation_results):
    """Generate summary statistics"""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Summary Statistics")
    logger.info("=" * 80)

    if not validation_results:
        logger.error("No validation results to summarize")
        return

    # Count field population across all runners
    field_stats = {}
    for field in FIELDS_TO_CHECK:
        populated_count = sum(
            1 for r in validation_results
            if r['fields_populated'].get(field, False)
        )
        total_count = len(validation_results)
        percentage = (populated_count / total_count * 100) if total_count > 0 else 0

        field_stats[field] = {
            'populated': populated_count,
            'total': total_count,
            'percentage': percentage
        }

    # Display summary
    logger.info(f"\nField Population Summary ({len(validation_results)} runners tested):\n")

    fully_populated = []
    partially_populated = []
    not_populated = []

    for field, stats in field_stats.items():
        pct = stats['percentage']
        status = "✅" if pct == 100 else ("⚠️" if pct > 0 else "❌")
        logger.info(f"{status} {field:30s}: {stats['populated']}/{stats['total']} ({pct:5.1f}%)")

        if pct == 100:
            fully_populated.append(field)
        elif pct > 0:
            partially_populated.append(field)
        else:
            not_populated.append(field)

    # Overall stats
    logger.info("\n" + "=" * 80)
    logger.info("Overall Results:")
    logger.info("=" * 80)
    logger.info(f"✅ Fully populated (100%):     {len(fully_populated)}/18 fields")
    logger.info(f"⚠️  Partially populated (1-99%): {len(partially_populated)}/18 fields")
    logger.info(f"❌ Not populated (0%):          {len(not_populated)}/18 fields")

    if fully_populated:
        logger.info(f"\nFully populated fields:")
        for field in fully_populated:
            logger.info(f"  ✅ {field}")

    if partially_populated:
        logger.info(f"\nPartially populated fields:")
        for field in partially_populated:
            logger.info(f"  ⚠️  {field}")

    if not_populated:
        logger.info(f"\nNot populated fields:")
        for field in not_populated:
            logger.info(f"  ❌ {field}")

    # Success criteria
    logger.info("\n" + "=" * 80)
    logger.info("Success Criteria Check:")
    logger.info("=" * 80)

    # At least 15/18 fields should be populated
    success_threshold = 15
    actual_populated = len(fully_populated) + len(partially_populated)

    if actual_populated >= success_threshold:
        logger.info(f"✅ PASS: {actual_populated}/18 fields populated (threshold: {success_threshold})")
    else:
        logger.error(f"❌ FAIL: Only {actual_populated}/18 fields populated (threshold: {success_threshold})")

    # Critical fields should be populated
    critical_fields = [
        'draw', 'prize_money_won', 'racing_post_rating',
        'silk_url', 'weight_stones_lbs', 'jockey_silk_url'
    ]

    logger.info(f"\nCritical fields check:")
    all_critical_ok = True
    for field in critical_fields:
        pct = field_stats[field]['percentage']
        if pct > 0:
            logger.info(f"  ✅ {field}: {pct:.1f}%")
        else:
            logger.error(f"  ❌ {field}: 0% (CRITICAL FIELD MISSING!)")
            all_critical_ok = False

    if all_critical_ok:
        logger.info("\n✅ All critical fields are populated")
    else:
        logger.error("\n❌ Some critical fields are missing data")

    return {
        'field_stats': field_stats,
        'fully_populated': fully_populated,
        'partially_populated': partially_populated,
        'not_populated': not_populated,
        'success': actual_populated >= success_threshold and all_critical_ok
    }


def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("RUNNER FIELD CAPTURE VALIDATION TEST")
    logger.info("=" * 80)
    logger.info(f"Testing {len(FIELDS_TO_CHECK)} fields with real API data")
    logger.info("This test will:")
    logger.info("  1. Fetch recent racecards (2 days)")
    logger.info("  2. Store runners in database")
    logger.info("  3. Validate field population")
    logger.info("  4. Generate detailed report")
    logger.info("=" * 80 + "\n")

    try:
        # Step 1: Fetch test data
        fetch_result = fetch_test_data()

        if not fetch_result.get('success'):
            logger.error("❌ Failed to fetch test data")
            return 1

        if fetch_result.get('runners_inserted', 0) == 0:
            logger.error("❌ No runners were inserted into database")
            return 1

        # Step 2: Validate runners
        validation_results = validate_runners()

        if not validation_results:
            logger.error("❌ Validation failed - no runners to analyze")
            return 1

        # Step 3: Generate summary
        summary = generate_summary(validation_results)

        # Final verdict
        logger.info("\n" + "=" * 80)
        logger.info("FINAL VERDICT")
        logger.info("=" * 80)

        if summary['success']:
            logger.info("✅ TEST PASSED - All critical field mappings are correct")
            logger.info(f"   {len(summary['fully_populated'])}/18 fields fully populated")
            logger.info(f"   {len(summary['partially_populated'])}/18 fields partially populated")
            return 0
        else:
            logger.error("❌ TEST FAILED - Some critical mappings are incorrect")
            logger.error(f"   Fix required for fields: {', '.join(summary['not_populated'])}")
            return 1

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
