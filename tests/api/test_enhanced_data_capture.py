"""
Test Enhanced Data Capture - Validate New Runner Fields
Tests that all 6 new fields from Migration 011 are properly captured and stored
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from fetchers.results_fetcher import ResultsFetcher
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('test_enhanced_capture')


def test_enhanced_data_capture():
    """Test that new fields are captured and stored correctly"""

    logger.info("=" * 80)
    logger.info("TESTING ENHANCED DATA CAPTURE - NEW RUNNER FIELDS")
    logger.info("=" * 80)

    # Initialize config and clients
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    # Test 1: Fetch recent results with enhanced capture
    logger.info("\nTest 1: Fetching recent results (last 2 days)...")
    logger.info("-" * 80)

    yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    day_before = (datetime.utcnow().date() - timedelta(days=2)).strftime('%Y-%m-%d')

    fetcher = ResultsFetcher()
    result = fetcher.fetch_and_store(
        start_date=day_before,
        end_date=yesterday,
        region_codes=['gb', 'ire']
    )

    if not result.get('success'):
        logger.error("Failed to fetch results")
        return False

    logger.info(f"✓ Fetched {result.get('fetched', 0)} results")
    logger.info(f"✓ Inserted {result.get('db_stats', {}).get('runners', {}).get('inserted', 0)} runners")

    # Test 2: Query database for new fields
    logger.info("\nTest 2: Querying database for new field population...")
    logger.info("-" * 80)

    try:
        # Query recent runners to check new fields
        runners_result = db_client.client.table('ra_mst_runners')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(100)\
            .execute()

        if not runners_result.data:
            logger.error("No runners found in database")
            return False

        runners = runners_result.data
        logger.info(f"✓ Found {len(runners)} recent runners")

        # Analyze field population
        logger.info("\nTest 3: Analyzing field population rates...")
        logger.info("-" * 80)

        # Define the 6 new fields from Migration 011
        new_fields = {
            'finishing_time': 'Finishing time',
            'starting_price_decimal': 'SP (decimal format)',
            'overall_beaten_distance': 'Overall beaten distance',
            'jockey_claim_lbs': 'Jockey claim (lbs)',
            'weight_stones_lbs': 'Weight (stones-lbs)',
            'race_comment': 'Race commentary',
            'jockey_silk_url': 'Jockey silk URL'
        }

        field_stats = {}

        for field, description in new_fields.items():
            populated_count = 0
            example_value = None

            for runner in runners:
                value = runner.get(field)
                if value is not None and value != '':
                    populated_count += 1
                    if example_value is None:
                        example_value = value

            percentage = (populated_count / len(runners) * 100) if runners else 0
            field_stats[field] = {
                'populated': populated_count,
                'total': len(runners),
                'percentage': percentage,
                'example': example_value
            }

            # Format example
            example_str = str(example_value) if example_value is not None else 'N/A'
            if len(example_str) > 50:
                example_str = example_str[:50] + "..."

            logger.info(f"{description:30} | {populated_count:3}/{len(runners):3} ({percentage:5.1f}%) | Example: {example_str}")

        # Test 4: Validate data quality
        logger.info("\nTest 4: Validating data quality...")
        logger.info("-" * 80)

        # Check critical fields have high population
        critical_fields = {
            'finishing_time': 80.0,  # Should be >80% for finished races
            'starting_price_decimal': 80.0,  # Should be >80%
            'jockey_silk_url': 80.0,  # Should be >80%
        }

        validation_passed = True
        for field, min_percentage in critical_fields.items():
            actual_percentage = field_stats[field]['percentage']
            status = "✓" if actual_percentage >= min_percentage else "✗"
            logger.info(f"{status} {field}: {actual_percentage:.1f}% (expected >{min_percentage}%)")

            if actual_percentage < min_percentage:
                validation_passed = False
                logger.warning(f"  Warning: {field} population below threshold!")

        # Test 5: Verify data types
        logger.info("\nTest 5: Verifying data types...")
        logger.info("-" * 80)

        type_checks = {
            'finishing_time': str,
            'starting_price_decimal': (float, int, type(None)),
            'overall_beaten_distance': (float, int, type(None)),
            'jockey_claim_lbs': (int, type(None)),
            'weight_stones_lbs': (str, type(None)),
            'race_comment': (str, type(None)),
            'jockey_silk_url': (str, type(None))
        }

        type_errors = []
        for runner in runners[:10]:  # Check first 10 runners
            for field, expected_types in type_checks.items():
                value = runner.get(field)
                if value is not None:
                    if not isinstance(value, expected_types):
                        type_errors.append(f"Field {field} has wrong type: {type(value)} (expected {expected_types})")

        if type_errors:
            validation_passed = False
            logger.error("Type validation errors:")
            for error in type_errors:
                logger.error(f"  ✗ {error}")
        else:
            logger.info("✓ All data types correct")

        # Test 6: Sample data display
        logger.info("\nTest 6: Sample runner data (first runner with all new fields)...")
        logger.info("-" * 80)

        # Find a runner with all fields populated
        sample_runner = None
        for runner in runners:
            has_all_fields = True
            for field in new_fields.keys():
                if runner.get(field) is None or runner.get(field) == '':
                    has_all_fields = False
                    break
            if has_all_fields:
                sample_runner = runner
                break

        if sample_runner:
            logger.info(f"Horse: {sample_runner.get('horse_name')}")
            logger.info(f"Race ID: {sample_runner.get('race_id')}")
            for field, description in new_fields.items():
                value = sample_runner.get(field)
                if isinstance(value, str) and len(str(value)) > 60:
                    value = str(value)[:60] + "..."
                logger.info(f"  {description:30} : {value}")
        else:
            logger.warning("No runner found with all new fields populated")

        # Test 7: Database schema validation
        logger.info("\nTest 7: Validating database schema...")
        logger.info("-" * 80)

        # Check that all new fields exist in schema
        if runners:
            runner_keys = set(runners[0].keys())
            missing_fields = []

            for field in new_fields.keys():
                if field not in runner_keys:
                    missing_fields.append(field)
                    validation_passed = False

            if missing_fields:
                logger.error(f"✗ Missing fields in database schema: {missing_fields}")
            else:
                logger.info("✓ All new fields exist in database schema")

        # Test 8: Save detailed report
        logger.info("\nTest 8: Saving detailed test report...")
        logger.info("-" * 80)

        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)

        report_file = logs_dir / f'enhanced_data_capture_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        report = {
            'test_date': datetime.utcnow().isoformat(),
            'test_date_range': f"{day_before} to {yesterday}",
            'total_runners_analyzed': len(runners),
            'field_statistics': field_stats,
            'validation_passed': validation_passed,
            'type_errors': type_errors if type_errors else None,
            'sample_runner': {
                'horse_name': sample_runner.get('horse_name') if sample_runner else None,
                'race_id': sample_runner.get('race_id') if sample_runner else None,
                'new_fields': {field: sample_runner.get(field) for field in new_fields.keys()} if sample_runner else None
            },
            'fetch_stats': result
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Report saved to: {report_file}")

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)

        if validation_passed:
            logger.info("✓✓✓ ALL TESTS PASSED ✓✓✓")
            logger.info("\nNew fields are being captured and stored correctly:")
            for field, description in new_fields.items():
                percentage = field_stats[field]['percentage']
                logger.info(f"  • {description}: {percentage:.1f}%")
        else:
            logger.warning("⚠ SOME TESTS FAILED ⚠")
            logger.warning("\nReview the warnings above and the detailed report.")

        logger.info("\nNext steps:")
        logger.info("  1. Run database migration: migrations/011_add_missing_runner_fields.sql")
        logger.info("  2. Backfill historical data if needed")
        logger.info("  3. Update ML models to use new fields (especially starting_price_decimal)")

        logger.info("=" * 80)

        return validation_passed

    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        return False


def main():
    """Main execution"""
    try:
        success = test_enhanced_data_capture()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
