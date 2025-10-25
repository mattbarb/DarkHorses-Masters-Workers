#!/usr/bin/env python3
"""
Populate ra_mst_regions Table

Extracts unique region codes and names from ra_mst_courses
and populates the ra_mst_regions reference table.

Phase 1 - Quick Win (No external API calls needed)

Usage:
    python3 scripts/populate_regions.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_regions')


def populate_regions():
    """
    Extract unique regions from courses table and populate regions table

    Returns:
        Dict with operation statistics
    """
    config = get_config()

    # Initialize database client
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    logger.info("=" * 80)
    logger.info("POPULATING ra_mst_regions TABLE")
    logger.info("=" * 80)

    try:
        # Step 1: Extract unique regions from courses
        logger.info("Step 1: Extracting unique regions from ra_mst_courses...")

        response = db_client.client.table('ra_mst_courses')\
            .select('region_code, region')\
            .execute()

        if not response.data:
            logger.error("No courses found in database")
            return {'success': False, 'error': 'No courses data'}

        # Get unique region combinations
        unique_regions = {}
        for course in response.data:
            region_code = course.get('region_code')
            region_name = course.get('region')

            if region_code and region_name:
                # Use region_code as key to deduplicate
                unique_regions[region_code] = {
                    'code': region_code,  # Use 'code' not 'region_code'
                    'name': region_name    # Use 'name' not 'region_name'
                }

        logger.info(f"Found {len(unique_regions)} unique regions")
        for region_code, region_data in sorted(unique_regions.items()):
            logger.info(f"  {region_code}: {region_data['name']}")

        # Step 2: Prepare region records
        logger.info("\nStep 2: Preparing region records...")

        region_records = []
        for region_code, region_data in sorted(unique_regions.items()):
            record = {
                'code': region_data['code'],  # Primary key is 'code'
                'name': region_data['name']
            }
            region_records.append(record)

        logger.info(f"Prepared {len(region_records)} region records")

        # Step 3: Upsert to database
        logger.info("\nStep 3: Upserting regions to database...")

        stats = db_client.upsert_batch(
            table='ra_mst_regions',
            records=region_records,
            unique_key='code'  # Primary key is 'code' not 'id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Updated: {stats.get('updated', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Step 4: Verify results
        logger.info("\nStep 4: Verifying results...")

        verify_response = db_client.client.table('ra_mst_regions')\
            .select('*')\
            .execute()

        logger.info(f"Total regions in database: {len(verify_response.data)}")

        # Show sample
        logger.info("\nSample regions in database:")
        for region in verify_response.data[:10]:
            logger.info(f"  {region['code']}: {region['name']}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ REGIONS TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'regions_found': len(unique_regions),
            'records_created': len(region_records),
            'database_stats': stats,
            'total_in_db': len(verify_response.data)
        }

    except Exception as e:
        logger.error(f"Failed to populate regions: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution"""
    logger.info("Starting regions table population...")

    result = populate_regions()

    if result['success']:
        logger.info("\n✅ SUCCESS")
        logger.info(f"Regions extracted: {result['regions_found']}")
        logger.info(f"Records created: {result['records_created']}")
        logger.info(f"Total in database: {result['total_in_db']}")
    else:
        logger.error(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
