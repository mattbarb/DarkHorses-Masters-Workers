"""
Entity Extractor
Extracts unique entities (jockeys, trainers, owners, horses) from race/runner data

HYBRID APPROACH:
- Extracts basic horse data from racecard runners
- Enriches NEW horses with Pro endpoint for complete pedigree data
- 2 requests/second rate limit
"""

import logging
import time
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from utils.region_extractor import extract_region_from_name

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract and store unique entities from race data"""

    def __init__(self, db_client, api_client=None):
        """
        Initialize entity extractor

        Args:
            db_client: SupabaseReferenceClient instance
            api_client: RacingAPIClient instance (optional, for Pro enrichment)
        """
        self.db_client = db_client
        self.api_client = api_client
        self.stats = {
            'jockeys': 0,
            'trainers': 0,
            'owners': 0,
            'horses': 0,
            'horses_enriched': 0,
            'pedigrees_captured': 0
        }

    def extract_from_runners(self, runner_records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract unique entities from runner records

        Args:
            runner_records: List of runner dictionaries

        Returns:
            Dictionary with entity types as keys and lists of entity records as values
        """
        jockeys = {}
        trainers = {}
        owners = {}
        horses = {}

        for runner in runner_records:
            # Extract jockey
            jockey_id = runner.get('jockey_id') or runner.get('racing_api_jockey_id')
            jockey_name = runner.get('jockey_name')
            if jockey_id and jockey_name and jockey_id not in jockeys:
                jockeys[jockey_id] = {
                    'id': jockey_id,
                    'name': jockey_name,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

            # Extract trainer
            trainer_id = runner.get('trainer_id') or runner.get('racing_api_trainer_id')
            trainer_name = runner.get('trainer_name')
            if trainer_id and trainer_name and trainer_id not in trainers:
                trainers[trainer_id] = {
                    'id': trainer_id,
                    'name': trainer_name,
                    'location': runner.get('trainer_location'),  # Capture trainer location from API
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

            # Extract owner
            owner_id = runner.get('owner_id') or runner.get('racing_api_owner_id')
            owner_name = runner.get('owner_name')
            if owner_id and owner_name and owner_id not in owners:
                owners[owner_id] = {
                    'id': owner_id,
                    'name': owner_name,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

            # Extract horse
            horse_id = runner.get('horse_id') or runner.get('racing_api_horse_id')
            horse_name = runner.get('horse_name')
            if horse_id and horse_name and horse_id not in horses:
                horse_record = {
                    'id': horse_id,
                    'name': horse_name,
                    'sex': runner.get('sex'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

                # Note: sire/dam fields are stored in ra_mst_runners table, not ra_horses
                # The ra_horses table only has basic horse identification

                horses[horse_id] = horse_record

        return {
            'jockeys': list(jockeys.values()),
            'trainers': list(trainers.values()),
            'owners': list(owners.values()),
            'horses': list(horses.values())
        }

    def _lookup_horse_id_by_name(self, name: str, region: str = None) -> Optional[str]:
        """
        Look up horse_id in database by horse name and optional region
        Uses intelligent matching strategy:
        1. Try name + region match (most accurate)
        2. Fallback to name-only match if region not provided or no match found

        Args:
            name: Horse name (e.g., "Masked Marvel (GB)")
            region: Region code (e.g., "GB", "IRE") - optional for better matching

        Returns:
            horse_id if found, None otherwise
        """
        if not name:
            return None

        try:
            # Normalize name for matching (remove extra whitespace, lowercase)
            normalized_name = ' '.join(name.split()).lower()

            # Strategy 1: Try name + region match (if region provided)
            if region:
                result = self.db_client.client.table('ra_mst_horses')\
                    .select('id, name, region')\
                    .execute()

                # Filter in Python for case-insensitive name and region match
                for horse in result.data:
                    horse_name_normalized = ' '.join(horse.get('name', '').split()).lower()
                    horse_region = horse.get('region', '').upper() if horse.get('region') else None

                    if horse_name_normalized == normalized_name and horse_region == region.upper():
                        horse_id = horse.get('id')
                        logger.debug(f"✓ Found horse_id '{horse_id}' for '{name}' (region: {region}) via name+region match")
                        return horse_id

            # Strategy 2: Fallback to name-only match
            result = self.db_client.client.table('ra_mst_horses')\
                .select('id, name')\
                .execute()

            # Filter in Python for case-insensitive exact name match
            matches = []
            for horse in result.data:
                horse_name_normalized = ' '.join(horse.get('name', '').split()).lower()
                if horse_name_normalized == normalized_name:
                    matches.append(horse)

            if len(matches) == 1:
                # Single match - safe to use
                horse_id = matches[0].get('id')
                match_type = "name-only (no region)" if not region else "name-only (region mismatch)"
                logger.debug(f"✓ Found horse_id '{horse_id}' for '{name}' via {match_type}")
                return horse_id
            elif len(matches) > 1:
                # Multiple matches - ambiguous, skip for safety
                logger.debug(f"⚠ Multiple horses found for '{name}' ({len(matches)} matches), skipping for safety")
                return None
            else:
                logger.debug(f"No horse_id found for '{name}'" + (f" (region: {region})" if region else ""))
                return None

        except Exception as e:
            logger.warning(f"Error looking up horse_id for '{name}': {e}")
            return None

    def extract_breeding_from_runners(self, runner_records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract unique breeding entities from runner records
        NOW WITH HORSE_ID LOOKUP!

        Args:
            runner_records: List of runner dictionaries

        Returns:
            Dictionary with breeding entity types (sires, dams, damsires) and lists of records
        """
        sires = {}
        dams = {}
        damsires = {}

        for runner in runner_records:
            # Extract sire with horse_id lookup (using region-aware matching)
            sire_id = runner.get('sire_id')
            sire_name = runner.get('sire_name')
            sire_region = runner.get('sire_region')
            if sire_id and sire_name and sire_id not in sires:
                sire_horse_id = self._lookup_horse_id_by_name(sire_name, sire_region)
                sires[sire_id] = {
                    'id': sire_id,
                    'name': sire_name,
                    'horse_id': sire_horse_id,  # Link to horse record
                    'region': sire_region,  # Region for better matching
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                if sire_horse_id:
                    logger.debug(f"  ✓ Linked sire '{sire_name}' to horse_id '{sire_horse_id}'")

            # Extract dam with horse_id lookup (using region-aware matching)
            dam_id = runner.get('dam_id')
            dam_name = runner.get('dam_name')
            dam_region = runner.get('dam_region')
            if dam_id and dam_name and dam_id not in dams:
                dam_horse_id = self._lookup_horse_id_by_name(dam_name, dam_region)
                dams[dam_id] = {
                    'id': dam_id,
                    'name': dam_name,
                    'horse_id': dam_horse_id,  # Link to horse record
                    'region': dam_region,  # Region for better matching
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                if dam_horse_id:
                    logger.debug(f"  ✓ Linked dam '{dam_name}' to horse_id '{dam_horse_id}'")

            # Extract damsire with horse_id lookup (using region-aware matching)
            damsire_id = runner.get('damsire_id')
            damsire_name = runner.get('damsire_name')
            damsire_region = runner.get('damsire_region')
            if damsire_id and damsire_name and damsire_id not in damsires:
                damsire_horse_id = self._lookup_horse_id_by_name(damsire_name, damsire_region)
                damsires[damsire_id] = {
                    'id': damsire_id,
                    'name': damsire_name,
                    'horse_id': damsire_horse_id,  # Link to horse record
                    'region': damsire_region,  # Region for better matching
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                if damsire_horse_id:
                    logger.debug(f"  ✓ Linked damsire '{damsire_name}' to horse_id '{damsire_horse_id}'")

        return {
            'sires': list(sires.values()),
            'dams': list(dams.values()),
            'damsires': list(damsires.values())
        }

    def store_entities(self, entities: Dict[str, List[Dict]]) -> Dict:
        """
        Store extracted entities in database

        Args:
            entities: Dictionary with entity types and records

        Returns:
            Statistics dictionary
        """
        results = {}

        # Store jockeys
        jockeys = entities.get('jockeys', [])
        if jockeys:
            try:
                db_result = self.db_client.insert_jockeys(jockeys)
                results['jockeys'] = db_result
                self.stats['jockeys'] += db_result.get('inserted', 0)
                logger.info(f"Stored {db_result.get('inserted', 0)} jockeys")
            except Exception as e:
                logger.error(f"Failed to store jockeys: {e}")
                results['jockeys'] = {'error': str(e)}

        # Store trainers
        trainers = entities.get('trainers', [])
        if trainers:
            try:
                db_result = self.db_client.insert_trainers(trainers)
                results['trainers'] = db_result
                self.stats['trainers'] += db_result.get('inserted', 0)
                logger.info(f"Stored {db_result.get('inserted', 0)} trainers")
            except Exception as e:
                logger.error(f"Failed to store trainers: {e}")
                results['trainers'] = {'error': str(e)}

        # Store owners
        owners = entities.get('owners', [])
        if owners:
            try:
                db_result = self.db_client.insert_owners(owners)
                results['owners'] = db_result
                self.stats['owners'] += db_result.get('inserted', 0)
                logger.info(f"Stored {db_result.get('inserted', 0)} owners")
            except Exception as e:
                logger.error(f"Failed to store owners: {e}")
                results['owners'] = {'error': str(e)}

        # Store sires
        sires = entities.get('sires', [])
        if sires:
            try:
                db_result = self.db_client.insert_sires(sires)
                results['sires'] = db_result
                logger.info(f"Stored {db_result.get('inserted', 0)} sires")
            except Exception as e:
                logger.error(f"Failed to store sires: {e}")

        # Store dams
        dams = entities.get('dams', [])
        if dams:
            try:
                db_result = self.db_client.insert_dams(dams)
                results['dams'] = db_result
                logger.info(f"Stored {db_result.get('inserted', 0)} dams")
            except Exception as e:
                logger.error(f"Failed to store dams: {e}")

        # Store damsires
        damsires = entities.get('damsires', [])
        if damsires:
            try:
                db_result = self.db_client.insert_damsires(damsires)
                results['damsires'] = db_result
                logger.info(f"Stored {db_result.get('inserted', 0)} damsires")
            except Exception as e:
                logger.error(f"Failed to store damsires: {e}")

        # Store horses with Pro enrichment for new horses
        horses = entities.get('horses', [])
        if horses:
            try:
                # Enrich new horses with Pro endpoint data
                enriched_horses, pedigree_records = self._enrich_new_horses(horses)

                # Store enriched horses
                db_result = self.db_client.insert_horses(enriched_horses)
                results['horses'] = db_result
                self.stats['horses'] += db_result.get('inserted', 0)
                logger.info(f"Stored {db_result.get('inserted', 0)} horses")

                # Store pedigree records
                if pedigree_records:
                    try:
                        pedigree_result = self.db_client.insert_pedigree(pedigree_records)
                        results['pedigrees'] = pedigree_result
                        logger.info(f"Stored {pedigree_result.get('inserted', 0)} pedigree records")
                    except Exception as e:
                        logger.error(f"Failed to store pedigree records: {e}")
                        results['pedigrees'] = {'error': str(e)}

            except Exception as e:
                logger.error(f"Failed to store horses: {e}")
                results['horses'] = {'error': str(e)}

        return results

    def _get_existing_horse_ids(self) -> Set[str]:
        """
        Get set of existing horse IDs from database

        Returns:
            Set of horse IDs already in database
        """
        try:
            result = self.db_client.client.table('ra_mst_horses').select('id').execute()
            return {row['id'] for row in result.data}
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
        if not self.api_client:
            return None

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

    def _enrich_new_horses(self, horse_records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Enrich new horses with Pro endpoint data

        Args:
            horse_records: List of basic horse records

        Returns:
            Tuple of (enriched_horses, pedigree_records)
        """
        if not self.api_client:
            logger.info("No API client provided - skipping horse enrichment")
            return horse_records, []

        # Get existing horse IDs
        existing_ids = self._get_existing_horse_ids()
        logger.info(f"Found {len(existing_ids)} existing horses in database")

        # Separate new vs existing horses
        new_horses = [h for h in horse_records if h['id'] not in existing_ids]
        existing_horses = [h for h in horse_records if h['id'] in existing_ids]

        logger.info(f"New horses to enrich: {len(new_horses)}, Existing horses: {len(existing_horses)}")

        if not new_horses:
            return horse_records, []

        # Enrich new horses with Pro data
        enriched_horses = []
        pedigree_records = []

        logger.info(f"Enriching {len(new_horses)} new horses with Pro endpoint...")

        for idx, horse in enumerate(new_horses):
            horse_id = horse['id']
            logger.info(f"[{idx+1}/{len(new_horses)}] Enriching {horse_id} ({horse.get('name')})...")

            # Fetch complete data
            horse_pro = self._fetch_horse_pro(horse_id)

            if horse_pro:
                # Extract region from horse name (breeding origin)
                horse_name = horse_pro.get('name', horse.get('name', ''))
                region = extract_region_from_name(horse_name)

                # Update horse record with complete data
                enriched_horse = {
                    **horse,  # Keep basic data
                    'dob': horse_pro.get('dob'),
                    'sex_code': horse_pro.get('sex_code'),
                    'colour': horse_pro.get('colour'),
                    'colour_code': horse_pro.get('colour_code'),
                    'breeder': horse_pro.get('breeder'),
                    'region': region,  # Extracted from horse name
                    'updated_at': datetime.utcnow().isoformat()
                }
                enriched_horses.append(enriched_horse)

                # Create pedigree record if available
                if any([horse_pro.get('sire_id'), horse_pro.get('dam_id'), horse_pro.get('damsire_id')]):
                    pedigree_record = {
                        'horse_id': horse_id,
                        'sire_id': horse_pro.get('sire_id'),
                        'sire': horse_pro.get('sire'),
                        'dam_id': horse_pro.get('dam_id'),
                        'dam': horse_pro.get('dam'),
                        'damsire_id': horse_pro.get('damsire_id'),
                        'damsire': horse_pro.get('damsire'),
                        'breeder': horse_pro.get('breeder'),
                        'region': region,  # Extracted from horse name
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    pedigree_records.append(pedigree_record)
                    self.stats['pedigrees_captured'] += 1
                    logger.info(f"  ✓ Pedigree captured for {horse_id}")

                self.stats['horses_enriched'] += 1

                # Rate limiting: 2 requests/second
                time.sleep(0.5)

            else:
                # Fallback - keep basic data
                logger.warning(f"  ✗ Pro fetch failed for {horse_id}, using basic data")
                enriched_horses.append(horse)

        # Combine enriched new horses with existing horses
        all_horses = existing_horses + enriched_horses

        return all_horses, pedigree_records

    def extract_and_store_from_runners(self, runner_records: List[Dict]) -> Dict:
        """
        Extract entities from runners and store them in database

        Args:
            runner_records: List of runner dictionaries

        Returns:
            Statistics dictionary
        """
        entities = self.extract_from_runners(runner_records)

        # Extract breeding entities (sires, dams, damsires)
        breeding_entities = self.extract_breeding_from_runners(runner_records)
        entities.update(breeding_entities)

        # Log summary
        logger.info(f"Extracted {len(entities['jockeys'])} unique jockeys")
        logger.info(f"Extracted {len(entities['trainers'])} unique trainers")
        logger.info(f"Extracted {len(entities['owners'])} unique owners")
        logger.info(f"Extracted {len(entities['horses'])} unique horses")
        logger.info(f"Extracted {len(entities.get('sires', []))} unique sires")
        logger.info(f"Extracted {len(entities.get('dams', []))} unique dams")
        logger.info(f"Extracted {len(entities.get('damsires', []))} unique damsires")

        # Store in database
        results = self.store_entities(entities)

        return results

    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return self.stats.copy()
