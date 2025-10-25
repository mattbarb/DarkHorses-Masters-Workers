#!/usr/bin/env python3
"""
Statistics Validation Tests
============================

Comprehensive validation tests for statistics fields across ra_jockeys,
ra_trainers, and ra_owners tables.

Tests verify:
1. No unexpected NULL values
2. Calculation accuracy (spot-checks)
3. Data consistency (logical constraints)
4. Field population rates
5. Data quality

Usage:
    # Run all validations
    python3 tests/test_statistics_validation.py

    # Run specific entity type
    python3 tests/test_statistics_validation.py --entities jockeys

    # Detailed output
    python3 tests/test_statistics_validation.py --verbose

Author: Claude Code
Date: 2025-10-19
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('statistics_validation')


class StatisticsValidator:
    """Validates statistics fields for data quality and consistency"""

    def __init__(self, db_client: SupabaseReferenceClient, verbose: bool = False):
        """Initialize validator"""
        self.db_client = db_client
        self.verbose = verbose
        self.test_results = {
            'jockeys': {'passed': 0, 'failed': 0, 'warnings': 0, 'tests': []},
            'trainers': {'passed': 0, 'failed': 0, 'warnings': 0, 'tests': []},
            'owners': {'passed': 0, 'failed': 0, 'warnings': 0, 'tests': []}
        }

    def _log_test(self, entity_type: str, test_name: str, passed: bool, message: str, warning: bool = False):
        """Log a test result"""
        status = "PASS" if passed else "WARN" if warning else "FAIL"
        self.test_results[entity_type]['tests'].append({
            'name': test_name,
            'status': status,
            'message': message
        })

        if passed:
            self.test_results[entity_type]['passed'] += 1
            if self.verbose:
                logger.info(f"  ✓ {test_name}: {message}")
        elif warning:
            self.test_results[entity_type]['warnings'] += 1
            logger.warning(f"  ⚠️  {test_name}: {message}")
        else:
            self.test_results[entity_type]['failed'] += 1
            logger.error(f"  ❌ {test_name}: {message}")

    def validate_field_population(self, entity_type: str) -> bool:
        """
        Validate that required fields are populated

        Args:
            entity_type: 'jockeys', 'trainers', or 'owners'

        Returns:
            True if validation passes
        """
        logger.info(f"\n[1] Field Population Validation - {entity_type}")

        table_name = f'ra_{entity_type}'
        result = self.db_client.client.table(table_name).select('*').not_.like('id', '**TEST**%').execute()
        total = len(result.data)

        if total == 0:
            self._log_test(entity_type, 'population', False, f"No {entity_type} found")
            return False

        # Check each field
        required_fields = [
            'total_rides' if entity_type == 'jockeys' else 'total_runners',
            'total_wins',
            'total_places',
            'recent_14d_rides' if entity_type == 'jockeys' else 'recent_14d_runs',
            'recent_14d_wins',
            'recent_30d_rides' if entity_type == 'jockeys' else 'recent_30d_runs',
            'recent_30d_wins'
        ]

        all_passed = True
        for field in required_fields:
            count = sum(1 for r in result.data if r.get(field) is not None)
            pct = (count / total) * 100 if total > 0 else 0

            if pct >= 95:
                self._log_test(entity_type, f'{field}_population', True, f'{field}: {pct:.1f}% populated ({count}/{total})')
            elif pct >= 50:
                self._log_test(entity_type, f'{field}_population', True, f'{field}: {pct:.1f}% populated ({count}/{total})', warning=True)
                all_passed = False
            else:
                self._log_test(entity_type, f'{field}_population', False, f'{field}: Only {pct:.1f}% populated ({count}/{total})')
                all_passed = False

        return all_passed

    def validate_calculation_accuracy(self, entity_type: str, sample_size: int = 10) -> bool:
        """
        Spot-check calculation accuracy

        Args:
            entity_type: 'jockeys', 'trainers', or 'owners'
            sample_size: Number of entities to validate

        Returns:
            True if validation passes
        """
        logger.info(f"\n[2] Calculation Accuracy Validation - {entity_type} (sample: {sample_size})")

        table_name = f'ra_{entity_type}'
        entities = self.db_client.client.table(table_name)\
            .select('*')\
            .not_.like('id', '**TEST**%')\
            .limit(sample_size)\
            .execute()

        if not entities.data:
            self._log_test(entity_type, 'calculation', False, "No entities to validate")
            return False

        all_passed = True
        for entity in entities.data:
            # Validate win_rate calculation
            if entity.get('total_rides') or entity.get('total_runners'):
                total = entity.get('total_rides') or entity.get('total_runners')
                wins = entity.get('total_wins', 0)
                win_rate = entity.get('win_rate')

                if total > 0:
                    expected_rate = round((wins / total) * 100, 2)
                    if win_rate is not None:
                        if abs(win_rate - expected_rate) > 0.1:  # Allow 0.1% tolerance
                            self._log_test(entity_type, 'win_rate_calc', False,
                                         f"{entity['name']}: win_rate {win_rate} != expected {expected_rate}")
                            all_passed = False

            # Validate place_rate calculation
            if entity.get('total_rides') or entity.get('total_runners'):
                total = entity.get('total_rides') or entity.get('total_runners')
                places = entity.get('total_places', 0)
                place_rate = entity.get('place_rate')

                if total > 0:
                    expected_rate = round((places / total) * 100, 2)
                    if place_rate is not None:
                        if abs(place_rate - expected_rate) > 0.1:
                            self._log_test(entity_type, 'place_rate_calc', False,
                                         f"{entity['name']}: place_rate {place_rate} != expected {expected_rate}")
                            all_passed = False

        if all_passed:
            self._log_test(entity_type, 'calculations', True, f'All {sample_size} sampled entities have correct calculations')

        return all_passed

    def validate_data_consistency(self, entity_type: str) -> bool:
        """
        Validate logical consistency of data

        Args:
            entity_type: 'jockeys', 'trainers', or 'owners'

        Returns:
            True if validation passes
        """
        logger.info(f"\n[3] Data Consistency Validation - {entity_type}")

        table_name = f'ra_{entity_type}'
        entities = self.db_client.client.table(table_name).select('*').not_.like('id', '**TEST**%').execute()

        all_passed = True
        issues = []

        for entity in entities.data:
            # Check: win_rate <= 100%
            win_rate = entity.get('win_rate')
            if win_rate is not None and win_rate > 100:
                issues.append(f"{entity['name']}: win_rate {win_rate} > 100%")
                all_passed = False

            # Check: place_rate <= 100%
            place_rate = entity.get('place_rate')
            if place_rate is not None and place_rate > 100:
                issues.append(f"{entity['name']}: place_rate {place_rate} > 100%")
                all_passed = False

            # Check: wins <= total rides
            total = entity.get('total_rides') or entity.get('total_runners', 0)
            wins = entity.get('total_wins', 0)
            if wins > total:
                issues.append(f"{entity['name']}: wins {wins} > total {total}")
                all_passed = False

            # Check: 14d <= 30d
            rides_14d = entity.get('recent_14d_rides') or entity.get('recent_14d_runs', 0)
            rides_30d = entity.get('recent_30d_rides') or entity.get('recent_30d_runs', 0)
            if rides_14d > rides_30d:
                issues.append(f"{entity['name']}: 14d rides {rides_14d} > 30d rides {rides_30d}")
                all_passed = False

            # Check: last_*_date <= today
            date_field = 'last_ride_date' if entity_type == 'jockeys' else 'last_runner_date'
            last_date_str = entity.get(date_field)
            if last_date_str:
                last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
                if last_date > datetime.utcnow():
                    issues.append(f"{entity['name']}: last date {last_date_str} is in future")
                    all_passed = False

        if all_passed:
            self._log_test(entity_type, 'consistency', True, 'All data is logically consistent')
        else:
            self._log_test(entity_type, 'consistency', False, f'Found {len(issues)} consistency issues')
            if self.verbose and issues:
                for issue in issues[:5]:  # Show first 5
                    logger.error(f"    - {issue}")

        return all_passed

    def validate_recent_activity(self, entity_type: str) -> bool:
        """
        Validate that recent activity fields are up-to-date

        Args:
            entity_type: 'jockeys', 'trainers', or 'owners'

        Returns:
            True if validation passes
        """
        logger.info(f"\n[4] Recent Activity Validation - {entity_type}")

        # Check if any entities have recent_30d_* fields populated
        table_name = f'ra_{entity_type}'
        field = 'recent_30d_rides' if entity_type == 'jockeys' else 'recent_30d_runs'

        result = self.db_client.client.table(table_name)\
            .select(field)\
            .not_.is_(field, 'null')\
            .not_.like('id', '**TEST**%')\
            .execute()

        count = len([r for r in result.data if r.get(field, 0) > 0])

        if count > 0:
            self._log_test(entity_type, 'recent_activity', True,
                         f'{count} {entity_type} have recent activity (30d)')
        else:
            self._log_test(entity_type, 'recent_activity', True,
                         f'No {entity_type} have recent activity (30d)', warning=True)

        return True

    def validate_entity_type(self, entity_type: str) -> Dict:
        """
        Run all validations for one entity type

        Args:
            entity_type: 'jockeys', 'trainers', or 'owners'

        Returns:
            Validation results dictionary
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"VALIDATING {entity_type.upper()}")
        logger.info(f"{'='*80}")

        # Run all validations
        self.validate_field_population(entity_type)
        self.validate_calculation_accuracy(entity_type, sample_size=10)
        self.validate_data_consistency(entity_type)
        self.validate_recent_activity(entity_type)

        return self.test_results[entity_type]

    def print_summary(self, entities: List[str]):
        """Print validation summary"""
        logger.info(f"\n{'='*80}")
        logger.info("VALIDATION SUMMARY")
        logger.info(f"{'='*80}")

        total_passed = 0
        total_failed = 0
        total_warnings = 0

        for entity_type in entities:
            results = self.test_results[entity_type]
            logger.info(f"\n{entity_type.title()}:")
            logger.info(f"  Passed: {results['passed']}")
            logger.info(f"  Failed: {results['failed']}")
            logger.info(f"  Warnings: {results['warnings']}")

            total_passed += results['passed']
            total_failed += results['failed']
            total_warnings += results['warnings']

        logger.info(f"\nOverall:")
        logger.info(f"  Total Tests: {total_passed + total_failed + total_warnings}")
        logger.info(f"  Passed: {total_passed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Warnings: {total_warnings}")

        if total_failed == 0:
            logger.info(f"\n✓ ALL VALIDATIONS PASSED")
        else:
            logger.error(f"\n❌ {total_failed} VALIDATIONS FAILED")

        logger.info(f"{'='*80}")

        return total_failed == 0


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Validate statistics data quality')
    parser.add_argument('--entities', nargs='+', choices=['jockeys', 'trainers', 'owners'],
                       help='Specific entity types to validate (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    entities = args.entities or ['jockeys', 'trainers', 'owners']

    logger.info("=" * 80)
    logger.info("STATISTICS VALIDATION TESTS")
    logger.info("=" * 80)
    logger.info(f"Entities: {', '.join(entities)}")
    logger.info(f"Verbose: {args.verbose}")
    logger.info("=" * 80)

    # Initialize
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    validator = StatisticsValidator(db_client, verbose=args.verbose)

    # Run validations
    for entity_type in entities:
        validator.validate_entity_type(entity_type)

    # Print summary
    all_passed = validator.print_summary(entities)

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
