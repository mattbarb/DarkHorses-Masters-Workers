"""
Diagnostic Script: Missing Runners Investigation
Compares API runner counts to database to identify root cause
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
import random

logger = get_logger('missing_runners_diagnostic')


def diagnose_missing_runners():
    """Run diagnostic to identify why runner count is low"""

    logger.info("=" * 70)
    logger.info("MISSING RUNNERS DIAGNOSTIC")
    logger.info("=" * 70)

    # Initialize clients
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Sample dates to check (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    sample_dates = []
    current = start_date
    while current <= end_date:
        sample_dates.append(current)
        current += timedelta(days=3)  # Sample every 3 days

    logger.info(f"Sampling {len(sample_dates)} dates from {start_date} to {end_date}")

    results = {
        'dates_checked': 0,
        'races_checked': 0,
        'perfect_matches': 0,
        'missing_runners': 0,
        'missing_horses': 0,
        'api_more_runners': 0,
        'db_more_runners': 0,
        'races_with_zero_db_runners': 0,
        'examples': []
    }

    for sample_date in sample_dates:
        date_str = sample_date.strftime('%Y-%m-%d')
        logger.info(f"Checking {date_str}...")

        # Fetch from API
        api_response = api_client.get_racecards_pro(
            date=date_str,
            region_codes=['gb', 'ire']
        )

        if not api_response or 'racecards' not in api_response:
            logger.warning(f"No API data for {date_str}")
            continue

        racecards = api_response.get('racecards', [])
        results['dates_checked'] += 1

        # Sample up to 10 races from this date
        sample_races = random.sample(racecards, min(10, len(racecards)))

        for race in sample_races:
            race_id = race.get('race_id')
            if not race_id:
                continue

            results['races_checked'] += 1

            # Count API runners
            api_runners = race.get('runners', [])
            api_count = len(api_runners)
            api_runners_with_horse_id = sum(1 for r in api_runners if r.get('horse_id'))
            api_runners_without_horse_id = api_count - api_runners_with_horse_id

            # Count database runners
            db_result = db_client.client.table('ra_runners')\
                .select('runner_id', count='exact')\
                .eq('race_id', race_id)\
                .execute()

            db_count = db_result.count if hasattr(db_result, 'count') else 0

            # Analyze
            if api_count == db_count:
                results['perfect_matches'] += 1
            else:
                results['missing_runners'] += abs(api_count - db_count)

                if api_count > db_count:
                    results['api_more_runners'] += 1

                    # Is it because of missing horse_id?
                    if api_runners_without_horse_id > 0:
                        results['missing_horses'] += 1

                    # Store example
                    if len(results['examples']) < 20:
                        results['examples'].append({
                            'date': date_str,
                            'race_id': race_id,
                            'race_name': race.get('race_name', 'Unknown'),
                            'api_runners': api_count,
                            'api_with_horse_id': api_runners_with_horse_id,
                            'api_without_horse_id': api_runners_without_horse_id,
                            'db_runners': db_count,
                            'missing': api_count - db_count
                        })
                else:
                    results['db_more_runners'] += 1

                if db_count == 0:
                    results['races_with_zero_db_runners'] += 1

    # Generate report
    logger.info("=" * 70)
    logger.info("DIAGNOSTIC RESULTS")
    logger.info("=" * 70)

    logger.info(f"Dates checked: {results['dates_checked']}")
    logger.info(f"Races checked: {results['races_checked']}")
    logger.info(f"Perfect matches: {results['perfect_matches']} ({results['perfect_matches']/max(results['races_checked'],1)*100:.1f}%)")
    logger.info(f"Races with API > DB: {results['api_more_runners']} ({results['api_more_runners']/max(results['races_checked'],1)*100:.1f}%)")
    logger.info(f"Races with DB > API: {results['db_more_runners']} ({results['db_more_runners']/max(results['races_checked'],1)*100:.1f}%)")
    logger.info(f"Races with 0 DB runners: {results['races_with_zero_db_runners']} ({results['races_with_zero_db_runners']/max(results['races_checked'],1)*100:.1f}%)")
    logger.info(f"Total missing runners: {results['missing_runners']}")
    logger.info(f"Races with missing horse_id in API: {results['missing_horses']}")

    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE MISMATCHES (first 20)")
    logger.info("=" * 70)

    for ex in results['examples']:
        logger.info(f"\nDate: {ex['date']}")
        logger.info(f"Race: {ex['race_name']} ({ex['race_id']})")
        logger.info(f"API: {ex['api_runners']} runners ({ex['api_with_horse_id']} with horse_id, {ex['api_without_horse_id']} without)")
        logger.info(f"DB: {ex['db_runners']} runners")
        logger.info(f"Missing: {ex['missing']} runners")

    # Determine root cause
    logger.info("\n" + "=" * 70)
    logger.info("ROOT CAUSE ANALYSIS")
    logger.info("=" * 70)

    if results['races_with_zero_db_runners'] > results['races_checked'] * 0.5:
        logger.warning("FINDING: Over 50% of races have 0 DB runners")
        logger.warning("LIKELY CAUSE: Races not being fetched/stored properly")
        logger.warning("RECOMMENDATION: Check races_fetcher.py - may not be calling insert_runners()")

    elif results['missing_horses'] > results['api_more_runners'] * 0.5:
        logger.warning("FINDING: Many API runners missing horse_id")
        logger.warning("LIKELY CAUSE: Skipping runners without horse_id (line 284-286)")
        logger.warning("RECOMMENDATION: Use Option A - create placeholder horse_id")

    elif results['api_more_runners'] > results['races_checked'] * 0.7:
        logger.warning("FINDING: Most races have fewer DB runners than API")
        logger.warning("LIKELY CAUSE: Filtering or data loss during storage")
        logger.warning("RECOMMENDATION: Check races_fetcher.py transform logic")

    else:
        logger.info("FINDING: Inconsistent pattern")
        logger.info("RECOMMENDATION: Manual investigation needed - review examples above")

    # Save report to file
    report_path = Path(__file__).parent.parent / 'logs' / f'missing_runners_diagnostic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("MISSING RUNNERS DIAGNOSTIC REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(f"Dates checked: {results['dates_checked']}\n")
        f.write(f"Races checked: {results['races_checked']}\n")
        f.write(f"Perfect matches: {results['perfect_matches']} ({results['perfect_matches']/max(results['races_checked'],1)*100:.1f}%)\n")
        f.write(f"Races with API > DB: {results['api_more_runners']} ({results['api_more_runners']/max(results['races_checked'],1)*100:.1f}%)\n")
        f.write(f"Races with 0 DB runners: {results['races_with_zero_db_runners']} ({results['races_with_zero_db_runners']/max(results['races_checked'],1)*100:.1f}%)\n")
        f.write(f"Total missing runners: {results['missing_runners']}\n")
        f.write(f"Races with missing horse_id: {results['missing_horses']}\n\n")

        f.write("EXAMPLE MISMATCHES:\n")
        f.write("=" * 70 + "\n\n")
        for ex in results['examples']:
            f.write(f"Date: {ex['date']}\n")
            f.write(f"Race: {ex['race_name']} ({ex['race_id']})\n")
            f.write(f"API: {ex['api_runners']} runners ({ex['api_with_horse_id']} with horse_id)\n")
            f.write(f"DB: {ex['db_runners']} runners\n")
            f.write(f"Missing: {ex['missing']} runners\n\n")

    logger.info(f"\nReport saved to: {report_path}")

    return results


if __name__ == '__main__':
    results = diagnose_missing_runners()

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print(f"Races checked: {results['races_checked']}")
    print(f"Mismatches found: {results['races_checked'] - results['perfect_matches']}")
    print(f"See logs for detailed report")
