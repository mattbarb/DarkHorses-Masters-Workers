"""
API Data Validation Script
Tests Racing API to see what fields are actually available and being captured
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from datetime import datetime, timedelta
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient

logger = get_logger('api_validator')


def validate_racecards_endpoint():
    """Test racecards endpoint and show what fields are available"""
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries
    )

    # Fetch yesterday's racecards (more likely to have data)
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

    logger.info(f"Fetching racecards for {yesterday}...")
    response = api_client.get_racecards_pro(date=yesterday, region_codes=['gb', 'ire'])

    if not response or 'racecards' not in response:
        logger.error("No racecards data returned")
        return None

    racecards = response.get('racecards', [])
    if not racecards:
        logger.error("Empty racecards list")
        return None

    # Analyze first racecard
    sample_race = racecards[0]
    logger.info(f"\n{'='*80}")
    logger.info(f"RACECARD SAMPLE - Race: {sample_race.get('race_name', 'Unknown')}")
    logger.info(f"{'='*80}")

    # Race-level fields
    logger.info("\nRACE-LEVEL FIELDS:")
    race_fields = {
        'race_id': sample_race.get('race_id'),
        'course': sample_race.get('course'),
        'course_id': sample_race.get('course_id'),
        'date': sample_race.get('date'),
        'off_time': sample_race.get('off_time'),
        'off_dt': sample_race.get('off_dt'),
        'race_name': sample_race.get('race_name'),
        'distance': sample_race.get('distance'),
        'distance_f': sample_race.get('distance_f'),
        'distance_round': sample_race.get('distance_round'),
        'dist_m': sample_race.get('dist_m'),
        'region': sample_race.get('region'),
        'type': sample_race.get('type'),
        'race_class': sample_race.get('race_class'),
        'age_band': sample_race.get('age_band'),
        'surface': sample_race.get('surface'),
        'going': sample_race.get('going'),
        'going_detailed': sample_race.get('going_detailed'),
        'prize': sample_race.get('prize'),
        'currency': sample_race.get('currency'),
        'weather': sample_race.get('weather'),
        'rail_movements': sample_race.get('rail_movements'),
        'stalls_position': sample_race.get('stalls_position'),
        'big_race': sample_race.get('big_race'),
        'is_abandoned': sample_race.get('is_abandoned'),
    }

    for field, value in race_fields.items():
        status = "✓" if value else "✗"
        logger.info(f"  {status} {field:20s} = {repr(value)[:60]}")

    # Runner-level fields
    runners = sample_race.get('runners', [])
    if runners:
        sample_runner = runners[0]
        logger.info(f"\nRUNNER-LEVEL FIELDS (Sample: {sample_runner.get('horse', 'Unknown')}):")
        runner_fields = {
            'horse_id': sample_runner.get('horse_id'),
            'horse': sample_runner.get('horse'),
            'age': sample_runner.get('age'),
            'sex': sample_runner.get('sex'),
            'colour': sample_runner.get('colour'),
            'region': sample_runner.get('region'),
            'breeder': sample_runner.get('breeder'),
            'sire': sample_runner.get('sire'),
            'sire_id': sample_runner.get('sire_id'),
            'dam': sample_runner.get('dam'),
            'dam_id': sample_runner.get('dam_id'),
            'damsire': sample_runner.get('damsire'),
            'damsire_id': sample_runner.get('damsire_id'),
            'jockey': sample_runner.get('jockey'),
            'jockey_id': sample_runner.get('jockey_id'),
            'trainer': sample_runner.get('trainer'),
            'trainer_id': sample_runner.get('trainer_id'),
            'trainer_location': sample_runner.get('trainer_location'),
            'owner': sample_runner.get('owner'),
            'owner_id': sample_runner.get('owner_id'),
            'number': sample_runner.get('number'),
            'draw': sample_runner.get('draw'),
            'lbs': sample_runner.get('lbs'),
            'headgear': sample_runner.get('headgear'),
            'headgear_run': sample_runner.get('headgear_run'),
            'ofr': sample_runner.get('ofr'),
            'rpr': sample_runner.get('rpr'),
            'ts': sample_runner.get('ts'),
            'tfr': sample_runner.get('tfr'),
            'form': sample_runner.get('form'),
            'comment': sample_runner.get('comment'),
            'silk_url': sample_runner.get('silk_url'),
        }

        for field, value in runner_fields.items():
            status = "✓" if value else "✗"
            logger.info(f"  {status} {field:20s} = {repr(value)[:60]}")

    return racecards


def validate_results_endpoint():
    """Test results endpoint and show what fields are available"""
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries
    )

    # Fetch results from 3 days ago (more likely to have results)
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')

    logger.info(f"\nFetching results for {three_days_ago}...")
    response = api_client.get_results(date=three_days_ago, region_codes=['gb', 'ire'])

    if not response or 'results' not in response:
        logger.error("No results data returned")
        return None

    results = response.get('results', [])
    if not results:
        logger.error("Empty results list")
        return None

    # Analyze first result
    sample_result = results[0]
    logger.info(f"\n{'='*80}")
    logger.info(f"RESULT SAMPLE - Race: {sample_result.get('race_name', 'Unknown')}")
    logger.info(f"{'='*80}")

    # Race-level fields
    logger.info("\nRESULT RACE-LEVEL FIELDS:")
    race_fields = {
        'race_id': sample_result.get('race_id'),
        'course': sample_result.get('course'),
        'course_id': sample_result.get('course_id'),
        'date': sample_result.get('date'),
        'off': sample_result.get('off'),
        'off_dt': sample_result.get('off_dt'),
        'race_name': sample_result.get('race_name'),
        'dist_f': sample_result.get('dist_f'),
        'dist_m': sample_result.get('dist_m'),
        'type': sample_result.get('type'),
        'class': sample_result.get('class'),
        'surface': sample_result.get('surface'),
        'going': sample_result.get('going'),
        'prize': sample_result.get('prize'),
        'currency': sample_result.get('currency'),
        'region': sample_result.get('region'),
        'results_status': sample_result.get('results_status'),
        'is_abandoned': sample_result.get('is_abandoned'),
    }

    for field, value in race_fields.items():
        status = "✓" if value else "✗"
        logger.info(f"  {status} {field:20s} = {repr(value)[:60]}")

    # Runner results fields
    runners = sample_result.get('runners', [])
    if runners:
        sample_runner = runners[0]
        logger.info(f"\nRESULT RUNNER-LEVEL FIELDS (Sample: {sample_runner.get('horse', 'Unknown')}):")
        runner_fields = {
            'horse_id': sample_runner.get('horse_id'),
            'horse': sample_runner.get('horse'),
            'position': sample_runner.get('position'),  # CRITICAL
            'btn': sample_runner.get('btn'),  # Distance beaten
            'sp': sample_runner.get('sp'),  # Starting price
            'prize': sample_runner.get('prize'),  # Prize won
            'number': sample_runner.get('number'),
            'draw': sample_runner.get('draw'),
            'age': sample_runner.get('age'),
            'sex': sample_runner.get('sex'),
            'weight_lbs': sample_runner.get('weight_lbs'),
            'headgear': sample_runner.get('headgear'),
            'time': sample_runner.get('time'),
            'or': sample_runner.get('or'),  # Official rating
            'rpr': sample_runner.get('rpr'),  # Racing Post Rating
            'tsr': sample_runner.get('tsr'),  # Top Speed Rating
            'jockey': sample_runner.get('jockey'),
            'jockey_id': sample_runner.get('jockey_id'),
            'trainer': sample_runner.get('trainer'),
            'trainer_id': sample_runner.get('trainer_id'),
            'owner': sample_runner.get('owner'),
            'owner_id': sample_runner.get('owner_id'),
            'sire': sample_runner.get('sire'),
            'sire_id': sample_runner.get('sire_id'),
            'dam': sample_runner.get('dam'),
            'dam_id': sample_runner.get('dam_id'),
            'damsire': sample_runner.get('damsire'),
            'damsire_id': sample_runner.get('damsire_id'),
        }

        for field, value in runner_fields.items():
            status = "✓" if value else "✗"
            logger.info(f"  {status} {field:20s} = {repr(value)[:60]}")

    return results


def main():
    """Run validation"""
    logger.info("="*80)
    logger.info("RACING API DATA VALIDATION")
    logger.info("="*80)

    # Test racecards
    racecards = validate_racecards_endpoint()

    # Test results
    results = validate_results_endpoint()

    logger.info("\n" + "="*80)
    logger.info("VALIDATION COMPLETE")
    logger.info("="*80)
    logger.info("\nNext steps:")
    logger.info("1. Review the fields marked with ✗ (not available)")
    logger.info("2. Check if any important fields are missing from our tables")
    logger.info("3. Update migrations if needed")
    logger.info("4. Update fetchers to capture any missing fields")


if __name__ == '__main__':
    main()
