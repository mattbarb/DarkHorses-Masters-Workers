"""
Data Gap Analysis: /v1/jockeys/{jockey_id}/results vs Current Data Capture
Compares runner data from jockey results endpoint with what we're capturing
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('data_gap_analysis')


def analyze_jockey_results_fields():
    """Analyze fields available in jockey results endpoint"""

    # Load sample response
    with open('logs/jockey_results_jky_268488_20251017_183936.json', 'r') as f:
        data = json.load(f)

    logger.info("="*80)
    logger.info("JOCKEY RESULTS ENDPOINT - DATA GAP ANALYSIS")
    logger.info("="*80)

    # Extract all unique fields from runners across all results
    runner_fields = set()
    race_fields = set()

    for result in data.get('results', []):
        # Race-level fields
        for key in result.keys():
            if key != 'runners':
                race_fields.add(key)

        # Runner-level fields
        for runner in result.get('runners', []):
            for key in runner.keys():
                runner_fields.add(key)

    logger.info(f"\n--- RACE-LEVEL FIELDS (from jockey results) ---")
    logger.info(f"Total: {len(race_fields)}")
    for field in sorted(race_fields):
        logger.info(f"  - {field}")

    logger.info(f"\n--- RUNNER-LEVEL FIELDS (from jockey results) ---")
    logger.info(f"Total: {len(runner_fields)}")
    for field in sorted(runner_fields):
        logger.info(f"  - {field}")

    return race_fields, runner_fields


def get_currently_captured_fields():
    """Get fields we're currently capturing in ra_mst_runners table"""

    # These are the fields we currently capture in ra_mst_runners based on the code review
    # Source: fetchers/results_fetcher.py and fetchers/races_fetcher.py

    current_runner_fields = {
        # Identity fields
        'runner_id',
        'race_id',
        'racing_api_race_id',
        'horse_id',
        'racing_api_horse_id',
        'horse_name',
        'jockey_id',
        'racing_api_jockey_id',
        'jockey_name',
        'trainer_id',
        'racing_api_trainer_id',
        'trainer_name',
        'owner_id',
        'racing_api_owner_id',
        'owner_name',

        # Basic runner info
        'age',
        'sex',
        'number',
        'draw',
        'weight',
        'weight_lbs',
        'headgear',

        # Headgear flags (parsed from headgear_run)
        'blinkers',
        'cheekpieces',
        'visor',
        'tongue_tie',

        # Pedigree
        'sire_id',
        'sire_name',
        'dam_id',
        'dam_name',
        'damsire_id',
        'damsire_name',

        # Form data
        'form',
        'form_string',
        'days_since_last_run',
        'last_run_performance',
        'career_runs',
        'career_wins',
        'career_places',
        'prize_money_won',

        # Ratings
        'official_rating',
        'racing_post_rating',
        'rpr',
        'tsr',

        # Jockey info
        'jockey_claim',
        'apprentice_allowance',

        # Results data (from results fetcher)
        'position',
        'distance_beaten',
        'prize_won',
        'starting_price',
        'result_updated_at',

        # Other
        'comment',
        'silk_url',

        # Metadata
        'is_from_api',
        'fetched_at',
        'api_data',
        'created_at',
        'updated_at'
    }

    return current_runner_fields


def compare_fields():
    """Compare fields from jockey results vs what we currently capture"""

    logger.info("\n" + "="*80)
    logger.info("FIELD COMPARISON ANALYSIS")
    logger.info("="*80)

    # Get fields from jockey results endpoint
    race_fields, runner_fields = analyze_jockey_results_fields()

    # Get currently captured fields
    current_fields = get_currently_captured_fields()

    # Map jockey results API fields to our database fields
    # This shows how API fields map to our schema
    field_mapping = {
        # Identity
        'horse_id': 'horse_id',
        'horse': 'horse_name',
        'jockey_id': 'jockey_id',
        'jockey': 'jockey_name',
        'trainer_id': 'trainer_id',
        'trainer': 'trainer_name',
        'owner_id': 'owner_id',
        'owner': 'owner_name',

        # Basic info
        'age': 'age',
        'sex': 'sex',
        'number': 'number',
        'draw': 'draw',
        'weight_lbs': 'weight_lbs',
        'headgear': 'headgear',

        # Pedigree
        'sire_id': 'sire_id',
        'sire': 'sire_name',
        'dam_id': 'dam_id',
        'dam': 'dam_name',
        'damsire_id': 'damsire_id',
        'damsire': 'damsire_name',

        # Ratings
        'or': 'official_rating',
        'rpr': 'rpr',
        'tsr': 'tsr',

        # Results
        'position': 'position',
        'btn': 'distance_beaten',  # "beaten by"
        'prize': 'prize_won',
        'sp': 'starting_price (fractional)',
        'sp_dec': 'starting_price (decimal)',

        # Other
        'comment': 'comment',
        'silk_url': 'silk_url',
        'jockey_claim_lbs': 'jockey_claim',

        # NEW FIELDS NOT CURRENTLY CAPTURED
        'weight': 'NOT CAPTURED (weight in lbs-stones format)',
        'time': 'NOT CAPTURED (individual finishing time)',
        'ovr_btn': 'NOT CAPTURED (overall beaten distance)',
    }

    logger.info("\n--- FIELDS IN JOCKEY RESULTS BUT NOT CAPTURED ---")

    # Fields in jockey results that we don't capture
    unmapped_fields = []
    for field in runner_fields:
        if field not in field_mapping:
            unmapped_fields.append(field)

    if unmapped_fields:
        logger.info(f"Total uncaptured fields: {len(unmapped_fields)}")
        for field in sorted(unmapped_fields):
            logger.info(f"  - {field}")
    else:
        logger.info("All fields are captured!")

    # Fields we capture that aren't in jockey results (likely from racecards)
    logger.info("\n--- FIELDS WE CAPTURE THAT AREN'T IN JOCKEY RESULTS ---")
    logger.info("(These likely come from racecards or other endpoints)")

    our_extra_fields = []
    api_fields_normalized = {field_mapping.get(f, f) for f in runner_fields}

    for field in current_fields:
        if field not in api_fields_normalized and field not in [
            'runner_id', 'racing_api_race_id', 'racing_api_horse_id',
            'racing_api_jockey_id', 'racing_api_trainer_id', 'racing_api_owner_id',
            'is_from_api', 'fetched_at', 'api_data', 'created_at', 'updated_at',
            'result_updated_at'
        ]:
            our_extra_fields.append(field)

    logger.info(f"Total: {len(our_extra_fields)}")
    for field in sorted(our_extra_fields):
        logger.info(f"  - {field}")

    return runner_fields, current_fields, field_mapping


def create_comparison_table():
    """Create detailed comparison table"""

    logger.info("\n" + "="*80)
    logger.info("DETAILED FIELD COMPARISON TABLE")
    logger.info("="*80)

    # Define comprehensive comparison
    # Format: (Field Name, In /v1/results, In /v1/jockeys/{id}/results, Currently Captured, Should Capture, Notes)

    comparison = [
        # Identity fields
        ("horse_id", "Yes", "Yes", "Yes", "Yes", "Primary identifier"),
        ("horse_name", "Yes (horse)", "Yes (horse)", "Yes", "Yes", ""),
        ("jockey_id", "Yes", "Yes", "Yes", "Yes", "Primary identifier"),
        ("jockey_name", "Yes (jockey)", "Yes (jockey)", "Yes", "Yes", ""),
        ("trainer_id", "Yes", "Yes", "Yes", "Yes", "Primary identifier"),
        ("trainer_name", "Yes (trainer)", "Yes (trainer)", "Yes", "Yes", ""),
        ("owner_id", "Yes", "Yes", "Yes", "Yes", "Primary identifier"),
        ("owner_name", "Yes (owner)", "Yes (owner)", "Yes", "Yes", ""),

        # Basic runner information
        ("age", "Yes", "Yes", "Yes", "Yes", "Horse age at time of race"),
        ("sex", "Yes", "Yes", "Yes", "Yes", "Horse sex"),
        ("number", "Yes", "Yes", "Yes", "Yes", "Runner/saddle cloth number"),
        ("draw", "Yes", "Yes", "Yes", "Yes", "Starting stall (flat racing)"),
        ("weight_lbs", "Yes", "Yes", "Yes", "Yes", "Weight carried (pounds)"),
        ("weight", "No", "Yes", "Partial", "Yes", "Weight in stones-pounds format (e.g., '11-7')"),
        ("headgear", "Yes", "Yes", "Yes", "Yes", "Headgear code"),

        # Pedigree
        ("sire_id", "Yes", "Yes", "Yes", "Yes", "Sire identifier"),
        ("sire_name", "Yes (sire)", "Yes (sire)", "Yes", "Yes", ""),
        ("dam_id", "Yes", "Yes", "Yes", "Yes", "Dam identifier"),
        ("dam_name", "Yes (dam)", "Yes (dam)", "Yes", "Yes", ""),
        ("damsire_id", "Yes", "Yes", "Yes", "Yes", "Damsire identifier"),
        ("damsire_name", "Yes (damsire)", "Yes (damsire)", "Yes", "Yes", ""),

        # Ratings
        ("official_rating (or)", "Yes", "Yes", "Yes", "Yes", "Official rating"),
        ("rpr", "Yes", "Yes", "Yes", "Yes", "Racing Post Rating"),
        ("tsr", "Yes", "Yes", "Yes", "Yes", "Top Speed Rating"),

        # Results data
        ("position", "Yes", "Yes", "Yes", "Yes", "Finishing position"),
        ("btn (distance_beaten)", "Yes", "Yes", "Yes", "Yes", "Beaten distance (lengths)"),
        ("ovr_btn", "No", "Yes", "No", "Maybe", "Overall beaten distance - different from btn?"),
        ("prize", "Yes", "Yes", "Yes", "Yes", "Prize money won"),
        ("sp", "Yes", "Yes", "Partial", "Yes", "Starting price (fractional format)"),
        ("sp_dec", "No", "Yes", "No", "Yes", "Starting price (decimal format)"),
        ("time", "No", "Yes", "No", "Yes", "Individual finishing time (very valuable for ML!)"),

        # Jockey information
        ("jockey_claim", "No", "Yes (jockey_claim_lbs)", "Yes", "Yes", "Jockey weight allowance"),

        # Other
        ("comment", "No", "Yes", "Yes", "Yes", "Race comment/analysis"),
        ("silk_url", "No", "Yes", "Yes", "Yes", "Jockey silk image URL"),

        # Form data (from racecards, not in results)
        ("form", "No", "No", "Yes", "Yes", "Recent form string"),
        ("form_string", "No", "No", "Yes", "Yes", "Detailed form"),
        ("days_since_last_run", "No", "No", "Yes", "Yes", ""),
        ("career_runs", "No", "No", "Yes", "Yes", ""),
        ("career_wins", "No", "No", "Yes", "Yes", ""),
        ("career_places", "No", "No", "Yes", "Yes", ""),

        # Headgear flags (we parse these)
        ("blinkers", "No", "No", "Yes (parsed)", "Yes", "Parsed from headgear"),
        ("cheekpieces", "No", "No", "Yes (parsed)", "Yes", "Parsed from headgear"),
        ("visor", "No", "No", "Yes (parsed)", "Yes", "Parsed from headgear"),
        ("tongue_tie", "No", "No", "Yes (parsed)", "Yes", "Parsed from headgear"),
    ]

    # Print table
    logger.info("\n")
    header = f"{'Field':<30} | {'In /v1/results':<15} | {'In Jockey Results':<18} | {'Currently Captured':<18} | {'Should Capture':<15} | {'Notes':<50}"
    logger.info(header)
    logger.info("-" * len(header))

    for field, in_results, in_jockey, captured, should, notes in comparison:
        row = f"{field:<30} | {in_results:<15} | {in_jockey:<18} | {captured:<18} | {should:<15} | {notes:<50}"
        logger.info(row)

    # Highlight key missing fields
    logger.info("\n" + "="*80)
    logger.info("KEY MISSING FIELDS (HIGH VALUE FOR ML)")
    logger.info("="*80)

    missing_high_value = [
        ("time", "Individual finishing time - critical for performance analysis"),
        ("sp_dec", "Starting price in decimal format - easier to use than fractional"),
        ("ovr_btn", "Overall beaten distance - may differ from btn in specific race types"),
        ("weight (stones-lbs)", "Human-readable weight format - currently only have lbs"),
    ]

    for field, description in missing_high_value:
        logger.info(f"\n{field}:")
        logger.info(f"  Description: {description}")
        logger.info(f"  Available in: /v1/jockeys/{{id}}/results")
        logger.info(f"  Currently captured: NO")


def compare_data_sources():
    """Compare /v1/results vs /v1/jockeys/{id}/results"""

    logger.info("\n" + "="*80)
    logger.info("DATA SOURCE COMPARISON")
    logger.info("="*80)

    logger.info("\n--- /v1/results (Current primary source) ---")
    logger.info("Endpoint: /v1/results")
    logger.info("Query: By date range, region, course")
    logger.info("Returns: All races and runners for specified criteria")
    logger.info("Pagination: Yes (limit max 50)")
    logger.info("Pros:")
    logger.info("  + Bulk fetch by date - efficient")
    logger.info("  + Gets all runners in all races")
    logger.info("  + No need to iterate by entity")
    logger.info("Cons:")
    logger.info("  - Missing some fields (time, sp_dec, ovr_btn)")
    logger.info("  - Limited to 12 months history (Standard plan)")

    logger.info("\n--- /v1/jockeys/{jockey_id}/results ---")
    logger.info("Endpoint: /v1/jockeys/{jockey_id}/results")
    logger.info("Query: By jockey_id, optional date range, region")
    logger.info("Returns: All races where this jockey rode")
    logger.info("Pagination: Yes (limit not restricted to 50)")
    logger.info("Pros:")
    logger.info("  + Additional fields: time, sp_dec, ovr_btn, weight (stones-lbs)")
    logger.info("  + Detailed race comments")
    logger.info("  + Complete historical data (not limited to 12 months)")
    logger.info("Cons:")
    logger.info("  - Must iterate by jockey_id")
    logger.info("  - Rate limit impact: 2 req/sec = 120 jockeys/minute")
    logger.info("  - Only gets data for specific jockey (not all runners in race)")

    logger.info("\n--- /v1/trainers/{trainer_id}/results (if exists) ---")
    logger.info("Similar pattern to jockey results")

    logger.info("\n--- /v1/horses/{horse_id}/results (if exists) ---")
    logger.info("Similar pattern to jockey results")


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("JOCKEY RESULTS ENDPOINT - COMPREHENSIVE DATA GAP ANALYSIS")
    logger.info("="*80)

    # Perform analysis
    runner_fields, current_fields, field_mapping = compare_fields()
    create_comparison_table()
    compare_data_sources()

    # Final recommendations
    logger.info("\n" + "="*80)
    logger.info("RECOMMENDATIONS")
    logger.info("="*80)

    logger.info("\n1. PRIMARY RECOMMENDATION: Continue using /v1/results as main source")
    logger.info("   Reason: Most efficient for bulk fetching all races and runners")

    logger.info("\n2. ADD MISSING FIELDS to /v1/results capture:")
    logger.info("   - Verify if 'time' field exists in /v1/results response")
    logger.info("   - Verify if 'sp_dec' field exists in /v1/results response")
    logger.info("   - Add 'weight' (stones-lbs format) alongside weight_lbs")
    logger.info("   - Check for 'ovr_btn' field in /v1/results")

    logger.info("\n3. OPTIONAL: Use /v1/jockeys/{id}/results for historical backfill")
    logger.info("   - Only if you need >12 months of historical data")
    logger.info("   - Rate limit impact: ~4.7 hours to fetch all ~34,000 jockeys")
    logger.info("   - Consider backfilling only active jockeys")

    logger.info("\n4. DO NOT use jockey results endpoint for daily operations")
    logger.info("   - Too slow to iterate all jockeys daily")
    logger.info("   - No advantage over /v1/results for recent data")

    logger.info("\n5. NEXT STEPS:")
    logger.info("   a) Check if /v1/results already includes 'time', 'sp_dec', 'ovr_btn'")
    logger.info("   b) If yes, update results_fetcher.py to capture these fields")
    logger.info("   c) If no, assess value of jockey-specific enrichment pattern")
    logger.info("   d) Test /v1/trainers/{id}/results and /v1/horses/{id}/results")

    logger.info("\n" + "="*80)


if __name__ == '__main__':
    main()
