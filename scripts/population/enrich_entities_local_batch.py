"""
Local Batch Entity Enrichment Script

This script uses a highly optimized approach:
1. Fetch all unique entities that need enrichment from database
2. Enrich locally by fetching from API and storing in memory
3. Batch write all enriched data to database at once

This eliminates per-entity database queries and uses bulk inserts for maximum speed.

USAGE:
    # Enrich all entities locally then bulk insert
    python3 scripts/enrich_entities_local_batch.py

    # Resume from checkpoint
    python3 scripts/enrich_entities_local_batch.py --resume

    # Test mode (100 horses only)
    python3 scripts/enrich_entities_local_batch.py --test
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('enrich_entities_local_batch')


class LocalBatchEnricher:
    """Local batch enrichment for maximum performance"""

    def __init__(self, checkpoint_file: str = None):
        """Initialize local batch enricher"""
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

        # Checkpoint file
        if checkpoint_file:
            self.checkpoint_file = Path(checkpoint_file)
        else:
            self.checkpoint_file = Path(__file__).parent.parent / 'logs' / 'local_batch_enrichment_checkpoint.json'

        # Local cache directory for intermediate results
        self.cache_dir = Path(__file__).parent.parent / 'logs' / 'enrichment_cache'
        self.cache_dir.mkdir(exist_ok=True)

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, stats: Dict):
        """Save checkpoint"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def get_unique_entities_to_enrich(self) -> Dict[str, Set[str]]:
        """
        Get all unique entities from runners that need enrichment

        Returns:
            Dict with sets of unique IDs for each entity type
        """
        logger.info("Fetching unique entities from ra_mst_runners...")

        entities = {
            'horses': set(),
            'jockeys': set(),
            'trainers': set(),
            'owners': set()
        }

        # Fetch all runners in batches
        offset = 0
        limit = 1000  # Supabase default limit
        total_processed = 0

        try:
            while True:
                result = self.db_client.client.table('ra_mst_runners')\
                    .select('horse_id,jockey_id,trainer_id,owner_id')\
                    .limit(limit)\
                    .offset(offset)\
                    .execute()

                if not result.data or len(result.data) == 0:
                    break

                for runner in result.data:
                    if runner.get('horse_id'):
                        entities['horses'].add(runner['horse_id'])
                    if runner.get('jockey_id'):
                        entities['jockeys'].add(runner['jockey_id'])
                    if runner.get('trainer_id'):
                        entities['trainers'].add(runner['trainer_id'])
                    if runner.get('owner_id'):
                        entities['owners'].add(runner['owner_id'])

                total_processed += len(result.data)

                # Log progress every 100k runners
                if total_processed % 100000 == 0:
                    logger.info(f"Processed {total_processed:,} runners...")

                offset += len(result.data)

                if len(result.data) < limit:
                    break

            logger.info(f"Processed {total_processed:,} runners total")
            logger.info(f"Found unique entities:")
            logger.info(f"  Horses: {len(entities['horses']):,}")
            logger.info(f"  Jockeys: {len(entities['jockeys']):,}")
            logger.info(f"  Trainers: {len(entities['trainers']):,}")
            logger.info(f"  Owners: {len(entities['owners']):,}")

            return entities

        except Exception as e:
            logger.error(f"Error fetching unique entities: {e}")
            return entities

    def get_existing_entities(self) -> Dict[str, Set[str]]:
        """Get IDs of entities already in database"""
        logger.info("Fetching existing entities from database...")

        existing = {
            'horses': set(),
            'jockeys': set(),
            'trainers': set(),
            'owners': set()
        }

        # Get existing horses
        try:
            offset = 0
            limit = 10000
            while True:
                result = self.db_client.client.table('ra_horses')\
                    .select('horse_id')\
                    .range(offset, offset + limit - 1)\
                    .execute()

                if not result.data:
                    break

                for row in result.data:
                    existing['horses'].add(row['horse_id'])

                offset += limit
                if len(result.data) < limit:
                    break

            logger.info(f"  Existing horses: {len(existing['horses']):,}")
        except Exception as e:
            logger.error(f"Error fetching existing horses: {e}")

        # Get existing jockeys
        try:
            offset = 0
            while True:
                result = self.db_client.client.table('ra_jockeys')\
                    .select('jockey_id')\
                    .range(offset, offset + limit - 1)\
                    .execute()

                if not result.data:
                    break

                for row in result.data:
                    existing['jockeys'].add(row['jockey_id'])

                offset += limit
                if len(result.data) < limit:
                    break

            logger.info(f"  Existing jockeys: {len(existing['jockeys']):,}")
        except Exception as e:
            logger.error(f"Error fetching existing jockeys: {e}")

        # Get existing trainers
        try:
            offset = 0
            while True:
                result = self.db_client.client.table('ra_trainers')\
                    .select('trainer_id')\
                    .range(offset, offset + limit - 1)\
                    .execute()

                if not result.data:
                    break

                for row in result.data:
                    existing['trainers'].add(row['trainer_id'])

                offset += limit
                if len(result.data) < limit:
                    break

            logger.info(f"  Existing trainers: {len(existing['trainers']):,}")
        except Exception as e:
            logger.error(f"Error fetching existing trainers: {e}")

        # Get existing owners
        try:
            offset = 0
            while True:
                result = self.db_client.client.table('ra_owners')\
                    .select('owner_id')\
                    .range(offset, offset + limit - 1)\
                    .execute()

                if not result.data:
                    break

                for row in result.data:
                    existing['owners'].add(row['owner_id'])

                offset += limit
                if len(result.data) < limit:
                    break

            logger.info(f"  Existing owners: {len(existing['owners']):,}")
        except Exception as e:
            logger.error(f"Error fetching existing owners: {e}")

        return existing

    def enrich_horses_locally(
        self,
        horse_ids: List[str],
        resume_from: Optional[str] = None
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Enrich horses by fetching from API and building local lists

        Args:
            horse_ids: List of horse IDs to enrich
            resume_from: Horse ID to resume from

        Returns:
            Tuple of (horses_list, pedigrees_list)
        """
        horses = []
        pedigrees = []

        start_index = 0
        if resume_from:
            try:
                start_index = horse_ids.index(resume_from) + 1
                logger.info(f"Resuming from horse index {start_index}")
            except ValueError:
                pass

        total = len(horse_ids)
        for idx, horse_id in enumerate(horse_ids[start_index:], start=start_index):
            try:
                # Fetch horse details from Pro endpoint
                logger.debug(f"[{idx+1}/{total}] Fetching horse {horse_id}...")
                horse_data = self.api_client.get_horse_details(horse_id, tier='pro')

                if not horse_data:
                    continue

                # Build horse record (matching EntityExtractor format)
                horse_record = {
                    'horse_id': horse_id,
                    'name': horse_data.get('name'),
                    'sex': horse_data.get('sex'),
                    'dob': horse_data.get('dob'),
                    'sex_code': horse_data.get('sex_code'),
                    'colour': horse_data.get('colour'),
                    'colour_code': horse_data.get('colour_code'),
                    'region': horse_data.get('region'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                horses.append(horse_record)

                # Build pedigree record if we have pedigree data (matching EntityExtractor format)
                if horse_data.get('sire_id') or horse_data.get('dam_id') or horse_data.get('damsire_id'):
                    pedigree_record = {
                        'horse_id': horse_id,
                        'sire_id': horse_data.get('sire_id'),
                        'sire': horse_data.get('sire'),
                        'dam_id': horse_data.get('dam_id'),
                        'dam': horse_data.get('dam'),
                        'damsire_id': horse_data.get('damsire_id'),
                        'damsire': horse_data.get('damsire'),
                        'breeder': horse_data.get('breeder'),
                        'region': horse_data.get('region'),
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    pedigrees.append(pedigree_record)

                # Rate limiting: 2 requests/second
                time.sleep(0.5)

                # Save progress every 100 horses
                if (idx + 1) % 100 == 0:
                    logger.info(f"Progress: {idx+1}/{total} horses enriched ({(idx+1)/total*100:.1f}%)")
                    # Save intermediate results
                    self._save_intermediate_results(horses, pedigrees, horse_id)

            except Exception as e:
                logger.error(f"Error enriching horse {horse_id}: {e}")
                continue

        return horses, pedigrees

    def _save_intermediate_results(self, horses: List[Dict], pedigrees: List[Dict], last_horse_id: str):
        """Save intermediate results to cache files"""
        try:
            horses_file = self.cache_dir / 'horses_cache.json'
            pedigrees_file = self.cache_dir / 'pedigrees_cache.json'
            progress_file = self.cache_dir / 'progress.json'

            with open(horses_file, 'w') as f:
                json.dump(horses, f)

            with open(pedigrees_file, 'w') as f:
                json.dump(pedigrees, f)

            with open(progress_file, 'w') as f:
                json.dump({'last_horse_id': last_horse_id, 'count': len(horses)}, f)

        except Exception as e:
            logger.error(f"Error saving intermediate results: {e}")

    def load_intermediate_results(self) -> tuple[List[Dict], List[Dict], Optional[str]]:
        """Load intermediate results from cache"""
        horses_file = self.cache_dir / 'horses_cache.json'
        pedigrees_file = self.cache_dir / 'pedigrees_cache.json'
        progress_file = self.cache_dir / 'progress.json'

        horses = []
        pedigrees = []
        last_horse_id = None

        try:
            if horses_file.exists():
                with open(horses_file, 'r') as f:
                    horses = json.load(f)

            if pedigrees_file.exists():
                with open(pedigrees_file, 'r') as f:
                    pedigrees = json.load(f)

            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
                    last_horse_id = progress.get('last_horse_id')

            if horses:
                logger.info(f"Loaded {len(horses)} horses from cache, resume from {last_horse_id}")

        except Exception as e:
            logger.error(f"Error loading intermediate results: {e}")

        return horses, pedigrees, last_horse_id

    def enrich_all(self, test_mode: bool = False, resume: bool = False):
        """
        Main enrichment process

        Args:
            test_mode: Only process 100 horses for testing
            resume: Resume from cached progress
        """
        logger.info("=" * 80)
        logger.info("LOCAL BATCH ENTITY ENRICHMENT")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        # Step 1: Get all unique entities from runners
        all_entities = self.get_unique_entities_to_enrich()

        # Step 2: Get existing entities to skip
        existing_entities = self.get_existing_entities()

        # Step 3: Calculate what needs to be enriched
        horses_to_enrich = list(all_entities['horses'] - existing_entities['horses'])
        jockeys_to_add = list(all_entities['jockeys'] - existing_entities['jockeys'])
        trainers_to_add = list(all_entities['trainers'] - existing_entities['trainers'])
        owners_to_add = list(all_entities['owners'] - existing_entities['owners'])

        logger.info(f"\nEntities needing enrichment:")
        logger.info(f"  New horses: {len(horses_to_enrich):,}")
        logger.info(f"  New jockeys: {len(jockeys_to_add):,}")
        logger.info(f"  New trainers: {len(trainers_to_add):,}")
        logger.info(f"  New owners: {len(owners_to_add):,}")

        # Test mode: limit to 100 horses
        if test_mode:
            horses_to_enrich = horses_to_enrich[:100]
            logger.info(f"\nTest mode: limiting to {len(horses_to_enrich)} horses")

        # Check for cached results
        horses_enriched = []
        pedigrees_enriched = []
        resume_from = None

        if resume:
            horses_enriched, pedigrees_enriched, resume_from = self.load_intermediate_results()

        # Step 4: Enrich horses locally (fetch from API, build lists)
        if horses_to_enrich:
            logger.info(f"\nEnriching {len(horses_to_enrich)} horses from Racing API...")
            estimated_time = len(horses_to_enrich) * 0.5 / 60  # 0.5s per horse in minutes

            logger.info(f"Estimated time: {estimated_time:.1f} minutes ({estimated_time/60:.1f} hours)")

            new_horses, new_pedigrees = self.enrich_horses_locally(
                horses_to_enrich,
                resume_from=resume_from
            )

            horses_enriched.extend(new_horses)
            pedigrees_enriched.extend(new_pedigrees)

            logger.info(f"Enrichment complete: {len(horses_enriched)} horses, {len(pedigrees_enriched)} pedigrees")

        # Step 5: Bulk insert everything to database
        logger.info("\n" + "=" * 80)
        logger.info("BULK INSERTING TO DATABASE")
        logger.info("=" * 80)

        stats = {
            'horses_inserted': 0,
            'pedigrees_inserted': 0,
            'jockeys_inserted': 0,
            'trainers_inserted': 0,
            'owners_inserted': 0
        }

        # Insert horses
        if horses_enriched:
            logger.info(f"\nInserting {len(horses_enriched)} horses...")
            result = self.db_client.insert_horses(horses_enriched)
            stats['horses_inserted'] = result.get('inserted', 0)
            logger.info(f"Horses inserted: {stats['horses_inserted']}")

        # Insert pedigrees
        if pedigrees_enriched:
            logger.info(f"\nInserting {len(pedigrees_enriched)} pedigrees...")
            result = self.db_client.insert_pedigree(pedigrees_enriched)
            stats['pedigrees_inserted'] = result.get('inserted', 0)
            logger.info(f"Pedigrees inserted: {stats['pedigrees_inserted']}")

        # Build basic records for jockeys/trainers/owners from runner data
        # (we already have their IDs and names from runners, no API enrichment needed)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("\n" + "=" * 80)
        logger.info("ENRICHMENT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration/60:.1f} minutes ({duration/3600:.1f} hours)")
        logger.info(f"Horses enriched: {stats['horses_inserted']:,}")
        logger.info(f"Pedigrees captured: {stats['pedigrees_inserted']:,}")
        logger.info("=" * 80)

        # Clear cache on successful completion
        if not test_mode:
            self._clear_cache()

        return stats

    def _clear_cache(self):
        """Clear intermediate cache files"""
        try:
            for file in self.cache_dir.glob('*.json'):
                file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Local batch entity enrichment with bulk inserts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich all entities
  python3 scripts/enrich_entities_local_batch.py

  # Resume from cache
  python3 scripts/enrich_entities_local_batch.py --resume

  # Test mode (100 horses only)
  python3 scripts/enrich_entities_local_batch.py --test
        """
    )

    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only 100 horses')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from cached progress')
    parser.add_argument('--checkpoint-file', type=str,
                       help='Custom checkpoint file path')

    args = parser.parse_args()

    enricher = LocalBatchEnricher(checkpoint_file=args.checkpoint_file)

    # Run enrichment
    result = enricher.enrich_all(
        test_mode=args.test,
        resume=args.resume
    )

    return result


if __name__ == '__main__':
    main()
