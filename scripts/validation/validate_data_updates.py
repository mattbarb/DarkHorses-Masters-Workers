"""
Validation Script: Data Updates
Validates all fixes were applied successfully
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('validation')


def validate_pedigree_population():
    """Validate pedigree table was populated"""
    logger.info("Validating pedigree population...")

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Count pedigrees
    pedigree_result = db_client.client.table('ra_horse_pedigree')\
        .select('*', count='exact')\
        .execute()
    pedigree_count = pedigree_result.count if hasattr(pedigree_result, 'count') else 0

    # Count total horses
    horses_result = db_client.client.table('ra_horses')\
        .select('*', count='exact')\
        .execute()
    horses_count = horses_result.count if hasattr(horses_result, 'count') else 0

    coverage_pct = (pedigree_count / horses_count * 100) if horses_count > 0 else 0

    # Check target
    target_min = 90000
    target_pct = 80.0

    passed = pedigree_count >= target_min and coverage_pct >= target_pct

    result = {
        'test': 'Pedigree Population',
        'passed': passed,
        'pedigree_count': pedigree_count,
        'horses_count': horses_count,
        'coverage_pct': round(coverage_pct, 2),
        'target_min': target_min,
        'target_pct': target_pct
    }

    if passed:
        logger.info(f"✓ PASS: {pedigree_count} pedigrees ({coverage_pct:.1f}% coverage)")
    else:
        logger.error(f"✗ FAIL: {pedigree_count} pedigrees ({coverage_pct:.1f}% coverage)")
        logger.error(f"  Target: ≥{target_min} pedigrees, ≥{target_pct}% coverage")

    return result


def validate_horse_data_completeness():
    """Validate horses have dob, sex_code, colour, region populated"""
    logger.info("Validating horse data completeness...")

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Get sample of horses
    horses_result = db_client.client.table('ra_horses')\
        .select('horse_id, dob, sex_code, colour, region')\
        .limit(1000)\
        .execute()

    horses = horses_result.data if hasattr(horses_result, 'data') else []

    if not horses:
        return {'test': 'Horse Data Completeness', 'passed': False, 'error': 'No horses found'}

    # Count populated fields
    total = len(horses)
    dob_count = sum(1 for h in horses if h.get('dob'))
    sex_code_count = sum(1 for h in horses if h.get('sex_code'))
    colour_count = sum(1 for h in horses if h.get('colour'))
    region_count = sum(1 for h in horses if h.get('region'))

    dob_pct = (dob_count / total * 100)
    sex_code_pct = (sex_code_count / total * 100)
    colour_pct = (colour_count / total * 100)
    region_pct = (region_count / total * 100)

    # Target: >95% populated
    target_pct = 95.0
    passed = all([
        dob_pct >= target_pct,
        sex_code_pct >= target_pct,
        colour_pct >= target_pct,
        region_pct >= target_pct
    ])

    result = {
        'test': 'Horse Data Completeness',
        'passed': passed,
        'sample_size': total,
        'dob_pct': round(dob_pct, 2),
        'sex_code_pct': round(sex_code_pct, 2),
        'colour_pct': round(colour_pct, 2),
        'region_pct': round(region_pct, 2),
        'target_pct': target_pct
    }

    if passed:
        logger.info(f"✓ PASS: Horse fields populated (dob:{dob_pct:.1f}%, sex_code:{sex_code_pct:.1f}%, colour:{colour_pct:.1f}%, region:{region_pct:.1f}%)")
    else:
        logger.error(f"✗ FAIL: Some horse fields under {target_pct}%")
        logger.error(f"  dob: {dob_pct:.1f}%, sex_code: {sex_code_pct:.1f}%, colour: {colour_pct:.1f}%, region: {region_pct:.1f}%")

    return result


def validate_runner_count():
    """Validate average runners per race improved"""
    logger.info("Validating runner count...")

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Query: Average runners per race
    # This is complex, so we'll do it via raw SQL query if possible
    # For now, let's sample and calculate

    # Get sample races
    races_result = db_client.client.table('ra_mst_races')\
        .select('race_id')\
        .limit(1000)\
        .execute()

    races = races_result.data if hasattr(races_result, 'data') else []

    if not races:
        return {'test': 'Runner Count', 'passed': False, 'error': 'No races found'}

    # Count runners for each race
    total_runners = 0
    races_with_runners = 0

    for race in races:
        race_id = race.get('race_id')
        runners_result = db_client.client.table('ra_mst_runners')\
            .select('runner_id', count='exact')\
            .eq('race_id', race_id)\
            .execute()

        runner_count = runners_result.count if hasattr(runners_result, 'count') else 0
        total_runners += runner_count
        if runner_count > 0:
            races_with_runners += 1

    avg_runners = (total_runners / len(races)) if len(races) > 0 else 0

    # Target: 8-12 avg runners per race
    target_min = 8.0
    target_max = 12.0
    passed = avg_runners >= target_min

    result = {
        'test': 'Runner Count',
        'passed': passed,
        'sample_size': len(races),
        'avg_runners_per_race': round(avg_runners, 2),
        'races_with_runners': races_with_runners,
        'races_with_runners_pct': round(races_with_runners / len(races) * 100, 2),
        'target_min': target_min,
        'target_max': target_max
    }

    if passed:
        logger.info(f"✓ PASS: {avg_runners:.2f} avg runners per race")
    else:
        logger.error(f"✗ FAIL: {avg_runners:.2f} avg runners per race (target: {target_min}-{target_max})")

    return result


def validate_new_runner_fields():
    """Validate new runner fields are being populated"""
    logger.info("Validating new runner fields...")

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Get recent runners (last 7 days)
    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=7)).date().isoformat()

    # First get recent races
    races_result = db_client.client.table('ra_mst_races')\
        .select('race_id')\
        .gte('race_date', cutoff_date)\
        .limit(10)\
        .execute()

    if not races_result.data:
        logger.warning("No recent races found - cannot validate new fields")
        return {'test': 'New Runner Fields', 'passed': None, 'warning': 'No recent data'}

    race_ids = [r['race_id'] for r in races_result.data]

    # Get runners from these races
    runners_result = db_client.client.table('ra_mst_runners')\
        .select('runner_id, dob, colour, trainer_location, spotlight, breeder')\
        .in_('race_id', race_ids)\
        .limit(100)\
        .execute()

    runners = runners_result.data if hasattr(runners_result, 'data') else []

    if not runners:
        logger.warning("No recent runners found - cannot validate new fields")
        return {'test': 'New Runner Fields', 'passed': None, 'warning': 'No recent runners'}

    # Count populated fields
    total = len(runners)
    dob_count = sum(1 for r in runners if r.get('dob'))
    colour_count = sum(1 for r in runners if r.get('colour'))
    trainer_loc_count = sum(1 for r in runners if r.get('trainer_location'))
    spotlight_count = sum(1 for r in runners if r.get('spotlight'))
    breeder_count = sum(1 for r in runners if r.get('breeder'))

    dob_pct = (dob_count / total * 100) if total > 0 else 0
    colour_pct = (colour_count / total * 100) if total > 0 else 0
    trainer_loc_pct = (trainer_loc_count / total * 100) if total > 0 else 0
    spotlight_pct = (spotlight_count / total * 100) if total > 0 else 0
    breeder_pct = (breeder_count / total * 100) if total > 0 else 0

    # Target: >50% for most fields (some fields may not always be in API)
    target_pct = 50.0
    passed = any([
        dob_pct >= target_pct,
        colour_pct >= target_pct,
        trainer_loc_pct >= target_pct
    ])

    result = {
        'test': 'New Runner Fields',
        'passed': passed,
        'sample_size': total,
        'dob_pct': round(dob_pct, 2),
        'colour_pct': round(colour_pct, 2),
        'trainer_location_pct': round(trainer_loc_pct, 2),
        'spotlight_pct': round(spotlight_pct, 2),
        'breeder_pct': round(breeder_pct, 2),
        'target_pct': target_pct
    }

    if passed:
        logger.info(f"✓ PASS: New runner fields populating (dob:{dob_pct:.1f}%, colour:{colour_pct:.1f}%, trainer_loc:{trainer_loc_pct:.1f}%)")
    else:
        logger.error(f"✗ FAIL: New runner fields not populating sufficiently")

    return result


def validate_new_race_fields():
    """Validate new race fields are being populated"""
    logger.info("Validating new race fields...")

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Get recent races (last 7 days)
    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=7)).date().isoformat()

    races_result = db_client.client.table('ra_mst_races')\
        .select('race_id, pattern, sex_restriction, rating_band, verdict, tip')\
        .gte('race_date', cutoff_date)\
        .limit(100)\
        .execute()

    races = races_result.data if hasattr(races_result, 'data') else []

    if not races:
        logger.warning("No recent races found - cannot validate new fields")
        return {'test': 'New Race Fields', 'passed': None, 'warning': 'No recent data'}

    # Count populated fields
    total = len(races)
    pattern_count = sum(1 for r in races if r.get('pattern'))
    sex_restriction_count = sum(1 for r in races if r.get('sex_restriction'))
    rating_band_count = sum(1 for r in races if r.get('rating_band'))
    verdict_count = sum(1 for r in races if r.get('verdict'))
    tip_count = sum(1 for r in races if r.get('tip'))

    pattern_pct = (pattern_count / total * 100) if total > 0 else 0
    sex_restriction_pct = (sex_restriction_count / total * 100) if total > 0 else 0
    rating_band_pct = (rating_band_count / total * 100) if total > 0 else 0
    verdict_pct = (verdict_count / total * 100) if total > 0 else 0
    tip_pct = (tip_count / total * 100) if total > 0 else 0

    # Target: >30% for most fields
    target_pct = 30.0
    passed = any([
        pattern_pct >= target_pct,
        sex_restriction_pct >= target_pct,
        rating_band_pct >= target_pct
    ])

    result = {
        'test': 'New Race Fields',
        'passed': passed,
        'sample_size': total,
        'pattern_pct': round(pattern_pct, 2),
        'sex_restriction_pct': round(sex_restriction_pct, 2),
        'rating_band_pct': round(rating_band_pct, 2),
        'verdict_pct': round(verdict_pct, 2),
        'tip_pct': round(tip_pct, 2),
        'target_pct': target_pct
    }

    if passed:
        logger.info(f"✓ PASS: New race fields populating (pattern:{pattern_pct:.1f}%, sex_restriction:{sex_restriction_pct:.1f}%, rating_band:{rating_band_pct:.1f}%)")
    else:
        logger.error(f"✗ FAIL: New race fields not populating sufficiently")

    return result


def run_all_validations():
    """Run all validation tests"""

    logger.info("=" * 70)
    logger.info("DATA UPDATE VALIDATION SUITE")
    logger.info("=" * 70)
    logger.info(f"Started: {datetime.now()}")
    logger.info("")

    results = []

    # Run all tests
    results.append(validate_pedigree_population())
    results.append(validate_horse_data_completeness())
    results.append(validate_runner_count())
    results.append(validate_new_runner_fields())
    results.append(validate_new_race_fields())

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 70)

    passed_count = sum(1 for r in results if r.get('passed') is True)
    failed_count = sum(1 for r in results if r.get('passed') is False)
    skipped_count = sum(1 for r in results if r.get('passed') is None)

    for result in results:
        status = "✓ PASS" if result.get('passed') is True else "✗ FAIL" if result.get('passed') is False else "⊘ SKIP"
        logger.info(f"{status}: {result['test']}")

    logger.info("")
    logger.info(f"Passed: {passed_count}/{len(results)}")
    logger.info(f"Failed: {failed_count}/{len(results)}")
    logger.info(f"Skipped: {skipped_count}/{len(results)}")

    overall_passed = failed_count == 0

    if overall_passed:
        logger.info("")
        logger.info("✓✓✓ ALL VALIDATIONS PASSED ✓✓✓")
    else:
        logger.error("")
        logger.error("✗✗✗ SOME VALIDATIONS FAILED ✗✗✗")

    # Save report
    report_path = Path(__file__).parent.parent / 'logs' / f'validation_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("DATA UPDATE VALIDATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")

        for result in results:
            f.write(f"\n{result['test']}\n")
            f.write("-" * 70 + "\n")
            for key, value in result.items():
                if key != 'test':
                    f.write(f"{key}: {value}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write(f"Overall: {'PASSED' if overall_passed else 'FAILED'}\n")
        f.write(f"Passed: {passed_count}/{len(results)}\n")
        f.write(f"Failed: {failed_count}/{len(results)}\n")

    logger.info(f"\nReport saved to: {report_path}")

    return {
        'overall_passed': overall_passed,
        'results': results,
        'report_path': str(report_path)
    }


if __name__ == '__main__':
    result = run_all_validations()

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Status: {'PASSED' if result['overall_passed'] else 'FAILED'}")
    print(f"Report: {result['report_path']}")

    # Exit code for CI/CD
    sys.exit(0 if result['overall_passed'] else 1)
