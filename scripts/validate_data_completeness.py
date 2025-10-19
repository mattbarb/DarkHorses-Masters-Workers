"""
Data Completeness Validation Script
Validates that workers are capturing 100% of available data from Racing API
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('validate_data_completeness')


class DataCompletenessValidator:
    """Validate data completeness across all tables"""

    def __init__(self):
        """Initialize validator"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

    def check_table_counts(self):
        """Check record counts for all tables"""
        logger.info("=" * 80)
        logger.info("TABLE RECORD COUNTS")
        logger.info("=" * 80)

        tables = [
            'ra_courses',
            'ra_bookmakers',
            'ra_horses',
            'ra_jockeys',
            'ra_trainers',
            'ra_owners',
            'ra_races',
            'ra_runners',
            'ra_horse_pedigree'
        ]

        counts = {}
        for table in tables:
            try:
                result = self.db_client.client.table(table).select('*', count='exact').limit(0).execute()
                counts[table] = result.count
                status = "✅" if result.count > 0 else "❌"
                logger.info(f"{status} {table:<25} {result.count:>10,} records")
            except Exception as e:
                logger.error(f"❌ {table:<25} ERROR: {e}")
                counts[table] = None

        return counts

    def check_horse_pedigree_coverage(self):
        """Check pedigree data coverage"""
        logger.info("\n" + "=" * 80)
        logger.info("HORSE PEDIGREE COVERAGE")
        logger.info("=" * 80)

        try:
            # Total horses
            total_horses = self.db_client.client.table('ra_horses').select('*', count='exact').limit(0).execute().count

            # Horses with pedigree
            total_pedigree = self.db_client.client.table('ra_horse_pedigree').select('*', count='exact').limit(0).execute().count

            # Horses with DOB
            horses_with_dob = self.db_client.client.table('ra_horses').select('dob', count='exact').not_.is_('dob', 'null').limit(0).execute().count

            # Horses with colour
            horses_with_colour = self.db_client.client.table('ra_horses').select('colour', count='exact').not_.is_('colour', 'null').limit(0).execute().count

            # Horses with colour_code
            horses_with_colour_code = self.db_client.client.table('ra_horses').select('colour_code', count='exact').not_.is_('colour_code', 'null').limit(0).execute().count

            # Pedigree records with breeder
            pedigree_with_breeder = self.db_client.client.table('ra_horse_pedigree').select('breeder', count='exact').not_.is_('breeder', 'null').limit(0).execute().count

            # Calculate percentages
            pedigree_pct = (total_pedigree / total_horses * 100) if total_horses > 0 else 0
            dob_pct = (horses_with_dob / total_horses * 100) if total_horses > 0 else 0
            colour_pct = (horses_with_colour / total_horses * 100) if total_horses > 0 else 0
            colour_code_pct = (horses_with_colour_code / total_horses * 100) if total_horses > 0 else 0
            breeder_pct = (pedigree_with_breeder / total_pedigree * 100) if total_pedigree > 0 else 0

            logger.info(f"Total horses: {total_horses:,}")
            logger.info(f"Horses with pedigree: {total_pedigree:,} ({pedigree_pct:.1f}%)")
            logger.info(f"Horses with DOB: {horses_with_dob:,} ({dob_pct:.1f}%)")
            logger.info(f"Horses with colour: {horses_with_colour:,} ({colour_pct:.1f}%)")
            logger.info(f"Horses with colour_code: {horses_with_colour_code:,} ({colour_code_pct:.1f}%)")
            logger.info(f"Pedigree with breeder: {pedigree_with_breeder:,} ({breeder_pct:.1f}%)")

            # Status checks
            if pedigree_pct < 80:
                logger.warning("⚠️  Pedigree coverage below 80%")
            else:
                logger.info("✅ Pedigree coverage OK")

            if dob_pct < 90:
                logger.warning("⚠️  DOB coverage below 90%")
            else:
                logger.info("✅ DOB coverage OK")

            return {
                'total_horses': total_horses,
                'pedigree_coverage': pedigree_pct,
                'dob_coverage': dob_pct,
                'colour_coverage': colour_pct,
                'colour_code_coverage': colour_code_pct,
                'breeder_coverage': breeder_pct
            }

        except Exception as e:
            logger.error(f"Error checking pedigree coverage: {e}")
            return None

    def check_position_data_coverage(self):
        """Check position data coverage in runners"""
        logger.info("\n" + "=" * 80)
        logger.info("POSITION DATA COVERAGE")
        logger.info("=" * 80)

        try:
            # Total runners
            total_runners = self.db_client.client.table('ra_runners').select('*', count='exact').limit(0).execute().count

            # Runners with position
            runners_with_position = self.db_client.client.table('ra_runners').select('position', count='exact').not_.is_('position', 'null').limit(0).execute().count

            # Runners with distance_beaten
            runners_with_distance = self.db_client.client.table('ra_runners').select('distance_beaten', count='exact').not_.is_('distance_beaten', 'null').limit(0).execute().count

            # Runners with prize_won
            runners_with_prize = self.db_client.client.table('ra_runners').select('prize_won', count='exact').not_.is_('prize_won', 'null').limit(0).execute().count

            # Runners with starting_price
            runners_with_sp = self.db_client.client.table('ra_runners').select('starting_price', count='exact').not_.is_('starting_price', 'null').limit(0).execute().count

            # Calculate percentages
            position_pct = (runners_with_position / total_runners * 100) if total_runners > 0 else 0
            distance_pct = (runners_with_distance / total_runners * 100) if total_runners > 0 else 0
            prize_pct = (runners_with_prize / total_runners * 100) if total_runners > 0 else 0
            sp_pct = (runners_with_sp / total_runners * 100) if total_runners > 0 else 0

            logger.info(f"Total runners: {total_runners:,}")
            logger.info(f"Runners with position: {runners_with_position:,} ({position_pct:.1f}%)")
            logger.info(f"Runners with distance_beaten: {runners_with_distance:,} ({distance_pct:.1f}%)")
            logger.info(f"Runners with prize_won: {runners_with_prize:,} ({prize_pct:.1f}%)")
            logger.info(f"Runners with starting_price: {runners_with_sp:,} ({sp_pct:.1f}%)")

            # Status checks (position data only available from results, not racecards)
            # So we expect lower coverage if we have more racecards than results
            if position_pct < 30:
                logger.warning("⚠️  Position data coverage very low (< 30%)")
            elif position_pct < 60:
                logger.warning("⚠️  Position data coverage moderate (30-60%)")
            else:
                logger.info("✅ Position data coverage good (> 60%)")

            return {
                'total_runners': total_runners,
                'position_coverage': position_pct,
                'distance_coverage': distance_pct,
                'prize_coverage': prize_pct,
                'sp_coverage': sp_pct
            }

        except Exception as e:
            logger.error(f"Error checking position data coverage: {e}")
            return None

    def check_ratings_coverage(self):
        """Check ratings data coverage in runners"""
        logger.info("\n" + "=" * 80)
        logger.info("RATINGS DATA COVERAGE")
        logger.info("=" * 80)

        try:
            # Total runners
            total_runners = self.db_client.client.table('ra_runners').select('*', count='exact').limit(0).execute().count

            # Runners with ratings
            runners_with_or = self.db_client.client.table('ra_runners').select('official_rating', count='exact').not_.is_('official_rating', 'null').limit(0).execute().count

            runners_with_rpr = self.db_client.client.table('ra_runners').select('rpr', count='exact').not_.is_('rpr', 'null').limit(0).execute().count

            runners_with_tsr = self.db_client.client.table('ra_runners').select('tsr', count='exact').not_.is_('tsr', 'null').limit(0).execute().count

            # Calculate percentages
            or_pct = (runners_with_or / total_runners * 100) if total_runners > 0 else 0
            rpr_pct = (runners_with_rpr / total_runners * 100) if total_runners > 0 else 0
            tsr_pct = (runners_with_tsr / total_runners * 100) if total_runners > 0 else 0

            logger.info(f"Total runners: {total_runners:,}")
            logger.info(f"Runners with official_rating: {runners_with_or:,} ({or_pct:.1f}%)")
            logger.info(f"Runners with RPR: {runners_with_rpr:,} ({rpr_pct:.1f}%)")
            logger.info(f"Runners with TSR: {runners_with_tsr:,} ({tsr_pct:.1f}%)")

            # Ratings are not always available (depends on race type, region, etc.)
            # So we expect 60-85% coverage
            if or_pct < 40:
                logger.warning("⚠️  Official rating coverage low (< 40%)")
            else:
                logger.info("✅ Official rating coverage OK")

            return {
                'total_runners': total_runners,
                'or_coverage': or_pct,
                'rpr_coverage': rpr_pct,
                'tsr_coverage': tsr_pct
            }

        except Exception as e:
            logger.error(f"Error checking ratings coverage: {e}")
            return None

    def run_validation(self):
        """Run all validation checks"""
        logger.info("=" * 80)
        logger.info("DATA COMPLETENESS VALIDATION")
        logger.info(f"Started: {datetime.now()}")
        logger.info("=" * 80)

        results = {}

        # 1. Table counts
        results['table_counts'] = self.check_table_counts()

        # 2. Pedigree coverage
        results['pedigree'] = self.check_horse_pedigree_coverage()

        # 3. Position data coverage
        results['position_data'] = self.check_position_data_coverage()

        # 4. Ratings coverage
        results['ratings'] = self.check_ratings_coverage()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)

        # Check critical metrics
        issues = []

        if results.get('table_counts', {}).get('ra_horse_pedigree', 0) == 0:
            issues.append("❌ ra_horse_pedigree table is empty")

        if results.get('pedigree', {}).get('pedigree_coverage', 0) < 80:
            issues.append(f"⚠️  Pedigree coverage at {results['pedigree']['pedigree_coverage']:.1f}% (target: 80%+)")

        if results.get('position_data', {}).get('position_coverage', 0) < 30:
            issues.append(f"⚠️  Position data coverage at {results['position_data']['position_coverage']:.1f}% (target: 30%+)")

        if issues:
            logger.warning("Issues found:")
            for issue in issues:
                logger.warning(f"  {issue}")
        else:
            logger.info("✅ All validation checks passed!")

        logger.info("=" * 80)

        return results


def main():
    """Main execution"""
    validator = DataCompletenessValidator()
    results = validator.run_validation()
    return results


if __name__ == '__main__':
    main()
