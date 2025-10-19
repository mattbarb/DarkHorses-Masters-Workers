"""
Horses Reference Data Fetcher
Fetches horse profiles from Racing API

HYBRID APPROACH:
- Bulk search for discovery (fast)
- Pro endpoint for new horses (complete data)
- This ensures new horses have pedigree data immediately
"""

import time
from datetime import datetime
from typing import Dict, List, Set
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.regional_filter import RegionalFilter
from utils.region_extractor import extract_region_from_name

logger = get_logger('horses_fetcher')


class HorsesFetcher:
    """Fetcher for horse reference data"""

    def __init__(self):
        """Initialize fetcher"""
        self.config = get_config()
        self.api_client = RacingAPIClient(
            username=self.config.api.username,
            password=self.config.api.password,
            base_url=self.config.api.base_url,
            timeout=self.config.api.timeout,
            max_retries=self.config.api.max_retries
        )
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

    def _get_existing_horse_ids(self) -> Set[str]:
        """
        Get set of existing horse IDs from database

        Returns:
            Set of horse IDs already in database
        """
        try:
            result = self.db_client.client.table('ra_horses').select('id').execute()
            existing_ids = {row['id'] for row in result.data}
            logger.info(f"Found {len(existing_ids)} existing horses in database")
            return existing_ids
        except Exception as e:
            logger.error(f"Error fetching existing horse IDs: {e}")
            return set()

    def _fetch_horse_pro(self, horse_id: str) -> Dict:
        """
        Fetch complete horse data from Pro endpoint

        Args:
            horse_id: Horse ID to fetch

        Returns:
            Complete horse data dict or None if fetch fails
        """
        try:
            response = self.api_client.get_horse_details(horse_id, tier='pro')
            if response:
                logger.debug(f"Successfully fetched Pro data for {horse_id}")
                return response
            else:
                logger.warning(f"No data returned from Pro endpoint for {horse_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching Pro data for {horse_id}: {e}")
            return None

    def fetch_and_store(self, limit_per_page: int = 500, max_pages: int = None,
                        filter_uk_ireland: bool = True) -> Dict:
        """
        Fetch horses from API and store in database

        Args:
            limit_per_page: Number of horses per page
            max_pages: Maximum pages to fetch (None = all)
            filter_uk_ireland: Filter to UK and Ireland horses only (default: True)

        Returns:
            Statistics dictionary
        """
        logger.info("Starting horses fetch")
        logger.info(f"UK/Ireland filtering: {'ENABLED' if filter_uk_ireland else 'DISABLED'}")

        all_horses = []
        page = 0
        skip = 0

        while True:
            if max_pages and page >= max_pages:
                logger.info(f"Reached max pages limit ({max_pages})")
                break

            # Fetch page
            logger.info(f"Fetching page {page + 1} (skip={skip})")
            api_response = self.api_client.search_horses(limit=limit_per_page, skip=skip)

            if not api_response or 'horses' not in api_response:
                logger.warning(f"No horses returned for page {page + 1}")
                break

            horses_page = api_response.get('horses', [])
            if not horses_page:
                logger.info("No more horses to fetch")
                break

            all_horses.extend(horses_page)
            logger.info(f"Fetched {len(horses_page)} horses (total: {len(all_horses)})")

            # Check if there are more pages
            if len(horses_page) < limit_per_page:
                logger.info("Reached last page")
                break

            page += 1
            skip += limit_per_page

        logger.info(f"Total horses fetched from API: {len(all_horses)}")

        # Filter to UK/Ireland only if requested
        if filter_uk_ireland:
            all_horses = RegionalFilter.filter_horses_by_region(all_horses)
            logger.info(f"After UK/Ireland filtering: {len(all_horses)} horses")

        # Get existing horse IDs from database
        existing_ids = self._get_existing_horse_ids()

        # Separate new vs existing horses
        new_horses = [h for h in all_horses if h.get('id') not in existing_ids]
        existing_horses = [h for h in all_horses if h.get('id') in existing_ids]

        logger.info(f"New horses: {len(new_horses)}, Existing horses: {len(existing_horses)}")

        # Process horses
        horses_transformed = []
        pro_enrichment_stats = {'success': 0, 'failed': 0, 'pedigrees_captured': 0}

        # Process EXISTING horses (basic update only)
        for horse in existing_horses:
            horse_record = {
                'id': horse.get('id'),  # RENAMED: horse_id → id
                'name': horse.get('name'),
                'sex': horse.get('sex'),
                'updated_at': datetime.utcnow().isoformat()
            }
            horses_transformed.append(horse_record)

        # Process NEW horses (Pro enrichment for complete data)
        if new_horses:
            logger.info(f"Enriching {len(new_horses)} new horses with Pro endpoint...")

        for idx, horse in enumerate(new_horses):
            horse_id = horse.get('id')
            logger.info(f"[{idx+1}/{len(new_horses)}] New horse: {horse_id} - Fetching complete data...")

            # Fetch complete data from Pro endpoint
            horse_pro = self._fetch_horse_pro(horse_id)

            if horse_pro:
                # Extract region from horse name (breeding origin)
                horse_name = horse_pro.get('name', '')
                region = extract_region_from_name(horse_name)

                # Success - insert complete horse data (including pedigree foreign keys)
                horse_record = {
                    'id': horse_pro.get('id'),  # API: 'id' → DB: 'id'
                    'name': horse_name,  # API: 'name' → DB: 'name'
                    'sire_id': horse_pro.get('sire_id'),  # API: 'sire_id' → DB: 'sire_id' (FK)
                    'dam_id': horse_pro.get('dam_id'),  # API: 'dam_id' → DB: 'dam_id' (FK)
                    'damsire_id': horse_pro.get('damsire_id'),  # API: 'damsire_id' → DB: 'damsire_id' (FK)
                    'sex': horse_pro.get('sex'),  # API: 'sex' → DB: 'sex'
                    'dob': horse_pro.get('dob'),  # API: 'dob' → DB: 'dob'
                    'sex_code': horse_pro.get('sex_code'),  # API: 'sex_code' → DB: 'sex_code'
                    'colour': horse_pro.get('colour'),  # API: 'colour' → DB: 'colour'
                    'colour_code': horse_pro.get('colour_code'),  # API: 'colour_code' → DB: 'colour_code'
                    'breeder': horse_pro.get('breeder'),  # API: 'breeder' → DB: 'breeder'
                    'region': region,  # Extracted from name → DB: 'region'
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                horses_transformed.append(horse_record)

                # Track pedigree capture statistics
                if any([horse_pro.get('sire_id'), horse_pro.get('dam_id'), horse_pro.get('damsire_id')]):
                    pro_enrichment_stats['pedigrees_captured'] += 1
                    logger.info(f"  ✓ Pedigree IDs captured for {horse_id}")

                pro_enrichment_stats['success'] += 1

                # Rate limiting: 2 requests/second
                time.sleep(0.5)

            else:
                # Fallback - insert basic data if Pro fetch fails
                logger.warning(f"  ✗ Pro fetch failed for {horse_id}, using basic data")
                horse_record = {
                    'id': horse.get('id'),  # RENAMED: horse_id → id
                    'name': horse.get('name'),
                    'sex': horse.get('sex'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                horses_transformed.append(horse_record)
                pro_enrichment_stats['failed'] += 1

        # Store in database
        results = {}
        if horses_transformed:
            horse_stats = self.db_client.insert_horses(horses_transformed)
            results['horses'] = horse_stats
            logger.info(f"Horses inserted/updated: {horse_stats}")

        # Log Pro enrichment statistics
        if new_horses:
            logger.info("=" * 60)
            logger.info("PRO ENRICHMENT STATISTICS")
            logger.info(f"New horses found: {len(new_horses)}")
            logger.info(f"Successfully enriched: {pro_enrichment_stats['success']}")
            logger.info(f"Failed enrichments: {pro_enrichment_stats['failed']}")
            logger.info(f"Pedigrees captured: {pro_enrichment_stats['pedigrees_captured']}")
            success_rate = (pro_enrichment_stats['success'] / len(new_horses) * 100) if new_horses else 0
            logger.info(f"Success rate: {success_rate:.1f}%")
            logger.info("=" * 60)

        # Calculate statistics
        total_inserted = results.get('horses', {}).get('inserted', 0)

        return {
            'success': True,
            'fetched': len(all_horses),
            'new_horses': len(new_horses),
            'existing_horses': len(existing_horses),
            'inserted': total_inserted,
            'horses_inserted': total_inserted,
            'pedigrees_captured': pro_enrichment_stats['pedigrees_captured'],
            'pro_enrichment': pro_enrichment_stats,
            'api_stats': self.api_client.get_stats(),
            'db_stats': results
        }


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("HORSES REFERENCE DATA FETCHER (HYBRID MODE)")
    logger.info("=" * 60)

    fetcher = HorsesFetcher()

    # Fetch first 10 pages as a test (5000 horses)
    result = fetcher.fetch_and_store(limit_per_page=500, max_pages=10)

    logger.info("\n" + "=" * 60)
    logger.info("FETCH COMPLETE")
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Total fetched: {result.get('fetched', 0)} horses")
    logger.info(f"New horses: {result.get('new_horses', 0)}")
    logger.info(f"Existing horses: {result.get('existing_horses', 0)}")
    logger.info(f"Horses inserted/updated: {result.get('horses_inserted', 0)}")
    logger.info(f"Pedigrees captured: {result.get('pedigrees_captured', 0)}")

    pro_stats = result.get('pro_enrichment', {})
    if pro_stats.get('success', 0) > 0 or pro_stats.get('failed', 0) > 0:
        logger.info("\nPro Enrichment:")
        logger.info(f"  Enriched: {pro_stats.get('success', 0)}/{result.get('new_horses', 0)}")
        logger.info(f"  Pedigrees: {pro_stats.get('pedigrees_captured', 0)}")

    logger.info("=" * 60)

    return result


if __name__ == '__main__':
    main()
