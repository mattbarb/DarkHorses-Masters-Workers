"""
Seed ra_regions Table
Seeds the ra_regions reference table with standard region codes
"""

from datetime import datetime
from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('seed_regions')


def seed_regions():
    """Seed ra_regions table with standard region codes"""

    logger.info("Starting ra_regions seeding...")

    # Initialize database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    # Define region data
    # Based on Racing API documentation and common racing regions
    regions = [
        {'code': 'gb', 'name': 'Great Britain'},
        {'code': 'ire', 'name': 'Ireland'},
        {'code': 'fr', 'name': 'France'},
        {'code': 'uae', 'name': 'United Arab Emirates'},
        {'code': 'aus', 'name': 'Australia'},
        {'code': 'usa', 'name': 'United States'},
        {'code': 'can', 'name': 'Canada'},
        {'code': 'nz', 'name': 'New Zealand'},
        {'code': 'sa', 'name': 'South Africa'},
        {'code': 'hk', 'name': 'Hong Kong'},
        {'code': 'jpn', 'name': 'Japan'},
        {'code': 'ger', 'name': 'Germany'},
        {'code': 'ita', 'name': 'Italy'},
        {'code': 'spa', 'name': 'Spain'},
    ]

    # Add timestamps
    timestamp = datetime.utcnow().isoformat()
    for region in regions:
        region['created_at'] = timestamp

    logger.info(f"Seeding {len(regions)} regions...")

    try:
        # Insert using upsert_batch with 'code' as unique key
        result = db_client.upsert_batch('ra_regions', regions, unique_key='code')

        logger.info(f"✓ Seeded {result.get('inserted', 0)} regions")
        logger.info(f"  Regions: {', '.join([r['code'] for r in regions])}")

        return {
            'success': True,
            'inserted': result.get('inserted', 0),
            'regions': regions
        }

    except Exception as e:
        logger.error(f"Failed to seed regions: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Seed ra_regions table')
    args = parser.parse_args()

    result = seed_regions()

    if result['success']:
        print(f"\n✓ Successfully seeded {result['inserted']} regions")
    else:
        print(f"\n✗ Failed to seed regions: {result.get('error')}")
        exit(1)
