#!/usr/bin/env python3
"""
ML Data Quality Monitor
=======================
Monitors the health and quality of ML runner history data.

Checks:
1. Data freshness (compilation timestamp)
2. Coverage (runners with history vs without)
3. Data quality (non-null critical fields)
4. Historical depth (races per horse)
5. Form completeness (recent form data)
6. Context coverage (course/distance experience)

Can be run:
- On-demand: python monitors/ml_data_monitor.py
- As health check: python monitors/ml_data_monitor.py --health-check
- As alert trigger: python monitors/ml_data_monitor.py --alert-on-issues
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('ml_data_monitor')


class MLDataMonitor:
    """Monitor ML runner history data quality and completeness"""

    def __init__(self):
        """Initialize monitor"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.issues = []
        self.warnings = []
        self.metrics = {}

    def run_health_check(self, verbose: bool = False) -> Tuple[bool, Dict]:
        """
        Run comprehensive health check on ML data

        Args:
            verbose: Log detailed information

        Returns:
            Tuple of (is_healthy, metrics_dict)
        """
        logger.info("=" * 80)
        logger.info("ML DATA HEALTH CHECK - Starting")
        logger.info(f"Time: {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)

        try:
            # Check 1: Data freshness
            self._check_data_freshness()

            # Check 2: Coverage
            self._check_coverage()

            # Check 3: Data quality
            self._check_data_quality()

            # Check 4: Historical depth
            self._check_historical_depth()

            # Check 5: Form completeness
            self._check_form_completeness()

            # Check 6: Context coverage
            self._check_context_coverage()

            # Determine overall health
            is_healthy = len(self.issues) == 0

            # Print summary
            self._print_summary(verbose)

            return is_healthy, self.metrics

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            self.issues.append(f"Health check error: {str(e)}")
            return False, self.metrics

    def _check_data_freshness(self):
        """Check if ML data is recent (compiled within last 24 hours)"""
        logger.info("Checking data freshness...")

        try:
            # Get latest compilation timestamp
            response = self.db_client.client.table('dh_ml_runner_history').select(
                'compilation_date'
            ).order('compilation_date', desc=True).limit(1).execute()

            if not response.data:
                self.issues.append("CRITICAL: No ML data found in database")
                self.metrics['data_freshness'] = 'EMPTY'
                return

            last_compilation = response.data[0]['compilation_date']
            last_compilation_dt = datetime.fromisoformat(last_compilation.replace('Z', '+00:00'))
            age_hours = (datetime.utcnow() - last_compilation_dt.replace(tzinfo=None)).total_seconds() / 3600

            self.metrics['last_compilation'] = last_compilation
            self.metrics['compilation_age_hours'] = round(age_hours, 2)

            # Alert if data is stale (>24 hours)
            if age_hours > 24:
                self.issues.append(
                    f"WARNING: ML data is stale ({round(age_hours, 1)} hours old). "
                    f"Last compilation: {last_compilation}"
                )
                self.metrics['data_freshness'] = 'STALE'
            elif age_hours > 12:
                self.warnings.append(
                    f"ML data is aging ({round(age_hours, 1)} hours old)"
                )
                self.metrics['data_freshness'] = 'AGING'
            else:
                self.metrics['data_freshness'] = 'FRESH'
                logger.info(f"✓ Data is fresh ({round(age_hours, 1)} hours old)")

        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            self.issues.append(f"Freshness check failed: {str(e)}")

    def _check_coverage(self):
        """Check what percentage of upcoming runners have ML data"""
        logger.info("Checking ML data coverage...")

        try:
            # Get count of upcoming runners (next 7 days)
            today = datetime.utcnow().date()
            week_ahead = today + timedelta(days=7)

            # Count upcoming runners in ra_runners
            upcoming_response = self.db_client.client.table('ra_runners').select(
                'runner_id, ra_races!inner(race_date)'
            ).gte('ra_races.race_date', today.isoformat()).lte(
                'ra_races.race_date', week_ahead.isoformat()
            ).execute()

            upcoming_count = len(upcoming_response.data) if upcoming_response.data else 0

            # Count runners with ML data
            ml_response = self.db_client.client.table('dh_ml_runner_history').select(
                'runner_id', count='exact'
            ).gte('race_date', today.isoformat()).lte(
                'race_date', week_ahead.isoformat()
            ).execute()

            ml_count = ml_response.count if ml_response.count else 0

            # Calculate coverage
            coverage_pct = (ml_count / upcoming_count * 100) if upcoming_count > 0 else 0

            self.metrics['upcoming_runners'] = upcoming_count
            self.metrics['ml_compiled_runners'] = ml_count
            self.metrics['coverage_percentage'] = round(coverage_pct, 2)

            # Alert if coverage is low
            if coverage_pct < 50:
                self.issues.append(
                    f"CRITICAL: Low ML coverage ({round(coverage_pct, 1)}%). "
                    f"Only {ml_count}/{upcoming_count} runners compiled."
                )
            elif coverage_pct < 80:
                self.warnings.append(
                    f"ML coverage is below target ({round(coverage_pct, 1)}%). "
                    f"Target: 90%+. Current: {ml_count}/{upcoming_count}"
                )
            else:
                logger.info(
                    f"✓ Good coverage: {round(coverage_pct, 1)}% ({ml_count}/{upcoming_count})"
                )

        except Exception as e:
            logger.error(f"Error checking coverage: {e}")
            self.issues.append(f"Coverage check failed: {str(e)}")

    def _check_data_quality(self):
        """Check for missing critical fields"""
        logger.info("Checking data quality...")

        try:
            # Get upcoming ML records
            today = datetime.utcnow().date()

            response = self.db_client.client.table('dh_ml_runner_history').select(
                'race_id, runner_id, horse_id, total_races, has_form'
            ).gte('race_date', today.isoformat()).execute()

            if not response.data:
                self.warnings.append("No upcoming ML data to check quality")
                return

            total = len(response.data)
            missing_horse_id = sum(1 for r in response.data if not r.get('horse_id'))
            missing_total_races = sum(1 for r in response.data if r.get('total_races') is None)
            no_form = sum(1 for r in response.data if not r.get('has_form'))

            self.metrics['quality_total_records'] = total
            self.metrics['quality_missing_horse_id'] = missing_horse_id
            self.metrics['quality_missing_total_races'] = missing_total_races
            self.metrics['quality_no_form'] = no_form

            # Alert on data quality issues
            if missing_horse_id > 0:
                self.issues.append(
                    f"WARNING: {missing_horse_id}/{total} ML records missing horse_id"
                )

            if missing_total_races > total * 0.1:
                self.warnings.append(
                    f"{missing_total_races}/{total} records missing total_races field"
                )

            no_form_pct = (no_form / total * 100) if total > 0 else 0
            self.metrics['no_form_percentage'] = round(no_form_pct, 2)

            if no_form_pct > 30:
                self.warnings.append(
                    f"{round(no_form_pct, 1)}% of runners have no racing history (expected for some)"
                )

            logger.info(f"✓ Quality check: {total} records, {round(no_form_pct, 1)}% first-time runners")

        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            self.issues.append(f"Quality check failed: {str(e)}")

    def _check_historical_depth(self):
        """Check average historical races per horse"""
        logger.info("Checking historical depth...")

        try:
            today = datetime.utcnow().date()

            response = self.db_client.client.table('dh_ml_runner_history').select(
                'historical_races_count'
            ).gte('race_date', today.isoformat()).execute()

            if not response.data:
                return

            race_counts = [r['historical_races_count'] for r in response.data if r.get('historical_races_count')]

            if not race_counts:
                self.warnings.append("No historical race counts found")
                return

            avg_races = sum(race_counts) / len(race_counts)
            max_races = max(race_counts)
            min_races = min(race_counts)
            with_5plus = sum(1 for c in race_counts if c >= 5)
            with_10plus = sum(1 for c in race_counts if c >= 10)

            self.metrics['avg_historical_races'] = round(avg_races, 2)
            self.metrics['max_historical_races'] = max_races
            self.metrics['min_historical_races'] = min_races
            self.metrics['runners_with_5plus_races'] = with_5plus
            self.metrics['runners_with_10plus_races'] = with_10plus

            pct_5plus = (with_5plus / len(race_counts) * 100)
            self.metrics['pct_with_5plus_races'] = round(pct_5plus, 2)

            if avg_races < 3:
                self.warnings.append(
                    f"Low average historical depth ({round(avg_races, 1)} races per horse)"
                )
            else:
                logger.info(
                    f"✓ Historical depth: avg={round(avg_races, 1)}, "
                    f"{round(pct_5plus, 1)}% with 5+ races"
                )

        except Exception as e:
            logger.error(f"Error checking historical depth: {e}")
            self.issues.append(f"Historical depth check failed: {str(e)}")

    def _check_form_completeness(self):
        """Check completeness of recent form data"""
        logger.info("Checking form completeness...")

        try:
            today = datetime.utcnow().date()

            response = self.db_client.client.table('dh_ml_runner_history').select(
                'last_5_positions, recent_form_score, has_form'
            ).gte('race_date', today.isoformat()).eq('has_form', True).execute()

            if not response.data:
                self.warnings.append("No runners with form to check")
                return

            total_with_form = len(response.data)
            with_last5 = sum(
                1 for r in response.data
                if r.get('last_5_positions') and len(r['last_5_positions']) > 0
            )
            with_form_score = sum(1 for r in response.data if r.get('recent_form_score') is not None)

            self.metrics['runners_with_form'] = total_with_form
            self.metrics['with_last_5_positions'] = with_last5
            self.metrics['with_form_score'] = with_form_score

            pct_last5 = (with_last5 / total_with_form * 100) if total_with_form > 0 else 0
            pct_score = (with_form_score / total_with_form * 100) if total_with_form > 0 else 0

            self.metrics['pct_with_last5'] = round(pct_last5, 2)
            self.metrics['pct_with_form_score'] = round(pct_score, 2)

            if pct_last5 < 80:
                self.warnings.append(
                    f"Only {round(pct_last5, 1)}% of runners have last_5_positions data"
                )
            if pct_score < 80:
                self.warnings.append(
                    f"Only {round(pct_score, 1)}% of runners have form_score calculated"
                )

            if pct_last5 >= 80 and pct_score >= 80:
                logger.info(f"✓ Form data: {round(pct_last5, 1)}% complete")

        except Exception as e:
            logger.error(f"Error checking form completeness: {e}")
            self.issues.append(f"Form completeness check failed: {str(e)}")

    def _check_context_coverage(self):
        """Check context-specific performance coverage"""
        logger.info("Checking context coverage...")

        try:
            today = datetime.utcnow().date()

            response = self.db_client.client.table('dh_ml_runner_history').select(
                'course_runs, distance_runs, surface_runs, has_form'
            ).gte('race_date', today.isoformat()).eq('has_form', True).execute()

            if not response.data:
                self.warnings.append("No runners with form to check context")
                return

            total_with_form = len(response.data)
            with_course_exp = sum(1 for r in response.data if r.get('course_runs', 0) > 0)
            with_distance_exp = sum(1 for r in response.data if r.get('distance_runs', 0) > 0)
            with_surface_exp = sum(1 for r in response.data if r.get('surface_runs', 0) > 0)

            pct_course = (with_course_exp / total_with_form * 100) if total_with_form > 0 else 0
            pct_distance = (with_distance_exp / total_with_form * 100) if total_with_form > 0 else 0
            pct_surface = (with_surface_exp / total_with_form * 100) if total_with_form > 0 else 0

            self.metrics['pct_with_course_experience'] = round(pct_course, 2)
            self.metrics['pct_with_distance_experience'] = round(pct_distance, 2)
            self.metrics['pct_with_surface_experience'] = round(pct_surface, 2)

            logger.info(
                f"✓ Context coverage: course={round(pct_course, 1)}%, "
                f"distance={round(pct_distance, 1)}%, surface={round(pct_surface, 1)}%"
            )

        except Exception as e:
            logger.error(f"Error checking context coverage: {e}")
            self.issues.append(f"Context coverage check failed: {str(e)}")

    def _print_summary(self, verbose: bool = False):
        """Print health check summary"""
        logger.info("\n" + "=" * 80)
        logger.info("ML DATA HEALTH CHECK SUMMARY")
        logger.info("=" * 80)

        # Overall status
        if not self.issues:
            logger.info("✓ HEALTHY - All checks passed")
        else:
            logger.error(f"✗ UNHEALTHY - {len(self.issues)} issues found")

        # Issues
        if self.issues:
            logger.info("\nISSUES:")
            for issue in self.issues:
                logger.error(f"  • {issue}")

        # Warnings
        if self.warnings:
            logger.info("\nWARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")

        # Key metrics
        logger.info("\nKEY METRICS:")
        logger.info(f"  Data freshness: {self.metrics.get('data_freshness', 'UNKNOWN')}")
        logger.info(f"  Compilation age: {self.metrics.get('compilation_age_hours', 'N/A')} hours")
        logger.info(f"  Coverage: {self.metrics.get('coverage_percentage', 0)}%")
        logger.info(f"  Avg historical races: {self.metrics.get('avg_historical_races', 'N/A')}")
        logger.info(f"  Runners with 5+ races: {self.metrics.get('pct_with_5plus_races', 'N/A')}%")
        logger.info(f"  Form completeness: {self.metrics.get('pct_with_last5', 'N/A')}%")

        if verbose:
            logger.info("\nALL METRICS:")
            for key, value in sorted(self.metrics.items()):
                logger.info(f"  {key}: {value}")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Monitor ML runner history data quality'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed metrics'
    )
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Run health check and exit with status code'
    )
    parser.add_argument(
        '--alert-on-issues',
        action='store_true',
        help='Trigger alerts if issues found'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output metrics as JSON'
    )

    args = parser.parse_args()

    try:
        monitor = MLDataMonitor()
        is_healthy, metrics = monitor.run_health_check(verbose=args.verbose)

        # Output JSON if requested
        if args.json:
            output = {
                'is_healthy': is_healthy,
                'issues': monitor.issues,
                'warnings': monitor.warnings,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            print(json.dumps(output, indent=2))

        # Exit with appropriate code
        if args.health_check:
            sys.exit(0 if is_healthy else 1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
