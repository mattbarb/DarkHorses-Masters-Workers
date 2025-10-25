#!/usr/bin/env python3
"""
Cleanup Non-UK/IRE Courses

This script removes all courses from ra_mst_courses that are not UK (GB) or Ireland (IRE).

The system is designed to work exclusively with UK and Ireland racing data,
so courses from other countries should not be in the database.

Usage:
    python3 scripts/cleanup_non_uk_ire_courses.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without making changes
"""

import sys
from pathlib import Path
from typing import Dict, List
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger(__name__)


def get_course_distribution(db_client: SupabaseReferenceClient) -> Dict:
    """
    Get distribution of courses by region.

    Returns:
        Dict with course data and statistics
    """
    logger.info("Fetching all courses from database...")

    response = db_client.client.table('ra_mst_courses').select(
        'id, name, region_code, region'
    ).execute()

    all_courses = response.data
    logger.info(f"Found {len(all_courses)} total courses")

    # Count by region
    region_counts = Counter(
        c.get('region_code', 'unknown').upper()
        for c in all_courses
    )

    # Separate UK/IRE from others
    uk_ire_courses = [
        c for c in all_courses
        if c.get('region_code', '').upper() in ['GB', 'IRE']
    ]

    other_courses = [
        c for c in all_courses
        if c.get('region_code', '').upper() not in ['GB', 'IRE']
    ]

    return {
        'all_courses': all_courses,
        'uk_ire_courses': uk_ire_courses,
        'other_courses': other_courses,
        'region_counts': region_counts,
        'total': len(all_courses),
        'uk_ire_count': len(uk_ire_courses),
        'other_count': len(other_courses)
    }


def show_distribution(stats: Dict):
    """Display course distribution."""
    logger.info("\nCurrent Course Distribution by Region:")
    logger.info("=" * 60)

    for region, count in sorted(
        stats['region_counts'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        marker = "✓" if region in ['GB', 'IRE'] else "✗"
        logger.info(f"{marker} {region:20} {count:4} courses")

    logger.info("=" * 60)
    logger.info(f"Total: {stats['total']} courses")
    logger.info("")
    logger.info(f"✓ Keep (UK/IRE): {stats['uk_ire_count']} courses")
    logger.info(f"✗ Delete (Other): {stats['other_count']} courses")


def delete_non_uk_ire_courses(
    db_client: SupabaseReferenceClient,
    courses_to_delete: List[Dict],
    dry_run: bool = False
) -> Dict:
    """
    Delete non-UK/IRE courses from database.

    Args:
        db_client: Supabase client
        courses_to_delete: List of course records to delete
        dry_run: If True, only show what would be deleted

    Returns:
        Dict with deletion statistics
    """
    if dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN - No changes will be made")
        logger.info("=" * 60)
        logger.info(f"\nWould delete {len(courses_to_delete)} courses:")

        # Show sample by region
        sample_by_region = {}
        for course in courses_to_delete:
            region = course.get('region_code', 'unknown').upper()
            if region not in sample_by_region:
                sample_by_region[region] = []
            if len(sample_by_region[region]) < 3:  # Show 3 per region
                sample_by_region[region].append(course.get('name', 'Unknown'))

        for region in sorted(sample_by_region.keys()):
            names = ', '.join(sample_by_region[region])
            total = sum(1 for c in courses_to_delete if c.get('region_code', '').upper() == region)
            logger.info(f"  {region}: {names} (+ {total - len(sample_by_region[region])} more)")

        return {'dry_run': True, 'would_delete': len(courses_to_delete)}

    logger.info("\n" + "=" * 60)
    logger.info(f"DELETING {len(courses_to_delete)} non-UK/IRE courses")
    logger.info("=" * 60)

    # Delete in batches
    batch_size = 100
    deleted_count = 0
    error_count = 0

    course_ids = [c['id'] for c in courses_to_delete]

    # Process in batches
    for i in range(0, len(course_ids), batch_size):
        batch_ids = course_ids[i:i + batch_size]

        try:
            # Delete batch using IN clause
            response = db_client.client.table('ra_mst_courses').delete().in_(
                'id', batch_ids
            ).execute()

            # Count deletions (Supabase returns deleted rows)
            batch_deleted = len(response.data) if response.data else len(batch_ids)
            deleted_count += batch_deleted

            logger.info(f"Deleted batch {i // batch_size + 1}/{(len(course_ids) + batch_size - 1) // batch_size}: "
                       f"{batch_deleted} courses")

        except Exception as e:
            error_count += len(batch_ids)
            logger.error(f"Error deleting batch: {e}")

    logger.info(f"\n✅ Successfully deleted {deleted_count} courses")
    if error_count > 0:
        logger.warning(f"⚠️  Failed to delete {error_count} courses")

    return {
        'success': True,
        'deleted': deleted_count,
        'errors': error_count,
        'total': len(courses_to_delete)
    }


def verify_cleanup(db_client: SupabaseReferenceClient) -> Dict:
    """Verify that only UK/IRE courses remain."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying cleanup...")
    logger.info("=" * 60)

    stats = get_course_distribution(db_client)

    logger.info(f"\nFinal course count: {stats['total']}")
    logger.info(f"  UK (GB): {stats['region_counts'].get('GB', 0)} courses")
    logger.info(f"  Ireland (IRE): {stats['region_counts'].get('IRE', 0)} courses")

    if stats['other_count'] == 0:
        logger.info("\n✅ SUCCESS: Only UK and Ireland courses remain!")
    else:
        logger.warning(f"\n⚠️  WARNING: {stats['other_count']} non-UK/IRE courses still present")

        # Show what's left
        for region, count in stats['region_counts'].items():
            if region not in ['GB', 'IRE']:
                logger.warning(f"  Remaining {region}: {count} courses")

    return stats


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove non-UK/IRE courses from ra_mst_courses'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without making changes'
    )
    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("CLEANUP NON-UK/IRE COURSES")
        logger.info("=" * 60)

        # Initialize
        config = get_config()
        db_client = SupabaseReferenceClient(
            url=config.supabase.url,
            service_key=config.supabase.service_key,
            batch_size=100
        )

        # Get current distribution
        stats = get_course_distribution(db_client)
        show_distribution(stats)

        if stats['other_count'] == 0:
            logger.info("\n✅ No cleanup needed - only UK/IRE courses present!")
            return

        # Confirm deletion (unless dry-run)
        if not args.dry_run:
            logger.info("\n" + "!" * 60)
            logger.info(f"⚠️  WARNING: About to delete {stats['other_count']} courses!")
            logger.info("!" * 60)
            response = input("\nProceed with deletion? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Cancelled by user")
                return

        # Delete courses
        result = delete_non_uk_ire_courses(
            db_client,
            stats['other_courses'],
            dry_run=args.dry_run
        )

        if not args.dry_run:
            # Verify cleanup
            verify_cleanup(db_client)

            logger.info("\n" + "=" * 60)
            logger.info("CLEANUP COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Deleted: {result['deleted']} courses")
            logger.info(f"Errors: {result['errors']}")
        else:
            logger.info("\n" + "=" * 60)
            logger.info("DRY RUN COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Would delete: {result['would_delete']} courses")
            logger.info("\nRun without --dry-run to execute deletion")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
