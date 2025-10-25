#!/usr/bin/env python3
"""
Populate Entity Statistics from Database (Optimized)
====================================================

** IMPORTANT: This script requires position data to be populated first! **

Before running this script, you must:
1. Run migration 005_add_position_fields_to_runners.sql (if not already run)
2. Populate results data using: python3 main.py --entities results
3. Verify position data exists in ra_race_results OR ra_runners

This script calculates statistics DIRECTLY from database tables instead of making API calls.

Performance Expectations (once data is available):
- Jockeys (3,483): ~30 seconds vs ~7 hours with API
- Trainers (2,781): ~25 seconds vs ~6 hours with API
- Owners (48,165): ~5 minutes vs ~4 days with API
- Total: ~6 minutes vs ~4.5 days (1000x faster!)

Data Source Options:
1. ra_race_results table (preferred if populated)
2. ra_runners table (if position fields added via migration 005)

Usage:
    # Check database status first
    python3 scripts/populate_statistics_from_database.py --check

    # Process all entity types
    python3 scripts/populate_statistics_from_database.py --all

    # Process specific types
    python3 scripts/populate_statistics_from_database.py --entities jockeys trainers

    # Dry run (show stats without updating)
    python3 scripts/populate_statistics_from_database.py --all --dry-run

Author: Claude Code
Date: 2025-10-19
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import time

sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('populate_statistics_from_database')

# Position handling constants
WIN_POSITIONS = ['1', 'WON', '1st', 1]  # Support both string and integer
PLACE_POSITIONS = ['1', 'WON', '1st', '2', '2nd', '3', '3rd', 1, 2, 3]


class DatabaseStatisticsCalculator:
    """Calculate entity statistics directly from database"""

    def __init__(self, dry_run: bool = False):
        """Initialize calculator"""
        config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=config.supabase.url,
            service_key=config.supabase.service_key,
            batch_size=1000  # Larger batches for statistics
        )
        self.dry_run = dry_run
        self.data_source = None  # Will be determined by check_data_availability
        self.stats = {
            'jockeys': {'processed': 0, 'updated': 0, 'errors': 0},
            'trainers': {'processed': 0, 'updated': 0, 'errors': 0},
            'owners': {'processed': 0, 'updated': 0, 'errors': 0}
        }

    def check_data_availability(self) -> Tuple[bool, str]:
        """
        Check which table has position data

        Returns:
            (has_data: bool, source: str)
        """
        logger.info("Checking database for position data...")

        # Check ra_race_results first (preferred source)
        try:
            result = self.db_client.client.table('ra_race_results')\
                .select('position', count='exact')\
                .limit(1)\
                .execute()

            if result.count and result.count > 0:
                logger.info(f"✓ Found {result.count:,} records in ra_race_results")
                self.data_source = 'ra_race_results'
                return True, 'ra_race_results'
        except Exception as e:
            logger.warning(f"Could not query ra_race_results: {e}")

        # Check ra_runners for position column
        try:
            # Try to select position column
            result = self.db_client.client.table('ra_runners')\
                .select('id, position')\
                .not_.is_('position', 'null')\
                .limit(1)\
                .execute()

            if result.data and len(result.data) > 0:
                # Count how many runners have position data
                count_result = self.db_client.client.table('ra_runners')\
                    .select('*', count='exact')\
                    .not_.is_('position', 'null')\
                    .limit(1)\
                    .execute()

                logger.info(f"✓ Found {count_result.count:,} runners with position data in ra_runners")
                self.data_source = 'ra_runners'
                return True, 'ra_runners'
            else:
                logger.warning("ra_runners.position column exists but has no data")

        except Exception as e:
            logger.error(f"✗ ra_runners.position column does not exist: {e}")

        # No data found
        logger.error("\n" + "=" * 80)
        logger.error("ERROR: No position data found in database!")
        logger.error("=" * 80)
        logger.error("\nBefore using this script, you must populate results data:")
        logger.error("\n1. Check if migration 005 has been run:")
        logger.error("   Run: migrations/005_add_position_fields_to_runners.sql")
        logger.error("\n2. Populate results data:")
        logger.error("   python3 main.py --entities results --days-back 365")
        logger.error("\n3. Verify data:")
        logger.error("   python3 scripts/populate_statistics_from_database.py --check")
        logger.error("\nOr use the API-based calculation method:")
        logger.error("   python3 scripts/calculate_entity_statistics_optimized.py")
        logger.error("=" * 80)

        return False, None

    def calculate_win_rate(self, wins: int, total: int) -> Optional[float]:
        """Calculate win rate with proper NULL handling"""
        if total == 0:
            return None  # NULL in database, not 0.00
        return round((wins / total) * 100, 2)

    def normalize_position(self, pos) -> Optional[str]:
        """Normalize position to standard format"""
        if pos is None:
            return None
        if isinstance(pos, int):
            return str(pos)
        return str(pos).strip().upper()

    def is_win(self, position) -> bool:
        """Check if position is a win"""
        if position is None:
            return False
        norm_pos = self.normalize_position(position)
        return norm_pos in [str(p) for p in WIN_POSITIONS]

    def is_place(self, position) -> bool:
        """Check if position is a place (top 3)"""
        if position is None:
            return False
        norm_pos = self.normalize_position(position)
        return norm_pos in [str(p) for p in PLACE_POSITIONS]

    def get_position_string(self, position) -> Optional[str]:
        """Convert position to display string"""
        if position is None:
            return None
        if isinstance(position, int):
            return str(position)
        return str(position)

    def fetch_jockey_race_data(self, jockey_ids: List[str]) -> Dict:
        """Fetch all race data for jockeys from appropriate source"""
        if self.data_source == 'ra_race_results':
            # Use ra_race_results table
            results = self.db_client.client.table('ra_race_results')\
                .select('jockey_id, position, race_date')\
                .in_('jockey_id', jockey_ids)\
                .not_.is_('position', 'null')\
                .execute()

            jockey_data = {}
            for result in results.data:
                jockey_id = result['jockey_id']
                if jockey_id not in jockey_data:
                    jockey_data[jockey_id] = []

                race_date_str = result['race_date']
                race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str

                jockey_data[jockey_id].append({
                    'position': result['position'],
                    'date': race_date
                })

            return jockey_data

        else:  # ra_runners
            # Get runners with position data
            runners = self.db_client.client.table('ra_runners')\
                .select('jockey_id, position, race_id')\
                .in_('jockey_id', jockey_ids)\
                .not_.is_('position', 'null')\
                .execute()

            # Get race dates
            race_ids = list(set([r['race_id'] for r in runners.data if r['race_id']]))
            if not race_ids:
                return {}

            races = self.db_client.client.table('ra_races')\
                .select('id, date')\
                .in_('id', race_ids)\
                .execute()

            race_dates = {r['id']: r['date'] for r in races.data}

            # Organize by jockey
            jockey_data = {}
            for runner in runners.data:
                jockey_id = runner['jockey_id']
                if jockey_id not in jockey_data:
                    jockey_data[jockey_id] = []

                race_date_str = race_dates.get(runner['race_id'])
                if race_date_str:
                    race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str
                    jockey_data[jockey_id].append({
                        'position': runner['position'],
                        'date': race_date
                    })

            return jockey_data

    def calculate_jockey_statistics(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Calculate all jockey statistics from database

        Statistics calculated:
        - last_ride_date: Date of most recent ride
        - last_win_date: Date of most recent win
        - days_since_last_ride: Days since last ride
        - days_since_last_win: Days since last win
        - recent_14d_rides: Rides in last 14 days
        - recent_14d_wins: Wins in last 14 days
        - recent_14d_win_rate: Win rate in last 14 days
        - recent_30d_rides: Rides in last 30 days
        - recent_30d_wins: Wins in last 30 days
        - recent_30d_win_rate: Win rate in last 30 days
        - total_rides: Career rides
        - total_wins: Career wins
        - total_places: Career top 3 finishes
        - win_rate: Career win percentage
        - place_rate: Career top 3 percentage
        """
        logger.info(f"Calculating jockey statistics from {self.data_source}...")

        # Get all jockeys
        jockeys_query = self.db_client.client.table('ra_jockeys').select('id')
        if limit:
            jockeys_query = jockeys_query.limit(limit)
        jockeys = jockeys_query.execute()

        jockey_ids = [j['id'] for j in jockeys.data]
        logger.info(f"Processing {len(jockey_ids)} jockeys...")

        # Fetch race data for all jockeys
        jockey_race_data = self.fetch_jockey_race_data(jockey_ids)

        # Calculate statistics
        today = date.today()
        cutoff_14d = today - timedelta(days=14)
        cutoff_30d = today - timedelta(days=30)

        results = []
        for jockey_id in jockey_ids:
            race_data = jockey_race_data.get(jockey_id, [])

            if not race_data:
                # No data - set all to NULL/0
                results.append({
                    'id': jockey_id,
                    'last_ride_date': None,
                    'last_win_date': None,
                    'days_since_last_ride': None,
                    'days_since_last_win': None,
                    'recent_14d_rides': 0,
                    'recent_14d_wins': 0,
                    'recent_14d_win_rate': None,
                    'recent_30d_rides': 0,
                    'recent_30d_wins': 0,
                    'recent_30d_win_rate': None,
                    'total_rides': 0,
                    'total_wins': 0,
                    'total_places': 0,
                    'total_seconds': 0,
                    'total_thirds': 0,
                    'win_rate': None,
                    'place_rate': None,
                    'stats_updated_at': datetime.utcnow().isoformat()
                })
                continue

            # Find dates
            all_dates = [r['date'] for r in race_data]
            win_dates = [r['date'] for r in race_data if self.is_win(r['position'])]

            last_ride_date = max(all_dates) if all_dates else None
            last_win_date = max(win_dates) if win_dates else None

            # Days since
            days_since_last_ride = (today - last_ride_date).days if last_ride_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            # 14-day stats
            recent_14d = [r for r in race_data if r['date'] >= cutoff_14d]
            recent_14d_rides = len(recent_14d)
            recent_14d_wins = len([r for r in recent_14d if self.is_win(r['position'])])
            recent_14d_win_rate = self.calculate_win_rate(recent_14d_wins, recent_14d_rides)

            # 30-day stats
            recent_30d = [r for r in race_data if r['date'] >= cutoff_30d]
            recent_30d_rides = len(recent_30d)
            recent_30d_wins = len([r for r in recent_30d if self.is_win(r['position'])])
            recent_30d_win_rate = self.calculate_win_rate(recent_30d_wins, recent_30d_rides)

            # Career stats
            total_rides = len(race_data)
            total_wins = len([r for r in race_data if self.is_win(r['position'])])
            total_places = len([r for r in race_data if self.is_place(r['position'])])

            # Count seconds and thirds
            positions = [self.normalize_position(r['position']) for r in race_data]
            total_seconds = len([p for p in positions if p in ['2', '2ND']])
            total_thirds = len([p for p in positions if p in ['3', '3RD']])

            win_rate = self.calculate_win_rate(total_wins, total_rides)
            place_rate = self.calculate_win_rate(total_places, total_rides)

            results.append({
                'id': jockey_id,
                'last_ride_date': last_ride_date.isoformat() if last_ride_date else None,
                'last_win_date': last_win_date.isoformat() if last_win_date else None,
                'days_since_last_ride': days_since_last_ride,
                'days_since_last_win': days_since_last_win,
                'recent_14d_rides': recent_14d_rides,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_rides': recent_30d_rides,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'total_rides': total_rides,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': total_seconds,
                'total_thirds': total_thirds,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'stats_updated_at': datetime.utcnow().isoformat()
            })

        logger.info(f"Calculated statistics for {len(results)} jockeys")
        return results

    def fetch_trainer_race_data(self, trainer_ids: List[str]) -> Dict:
        """Fetch all race data for trainers from appropriate source"""
        if self.data_source == 'ra_race_results':
            results = self.db_client.client.table('ra_race_results')\
                .select('trainer_id, position, race_date')\
                .in_('trainer_id', trainer_ids)\
                .not_.is_('position', 'null')\
                .execute()

            trainer_data = {}
            for result in results.data:
                trainer_id = result['trainer_id']
                if trainer_id not in trainer_data:
                    trainer_data[trainer_id] = []

                race_date_str = result['race_date']
                race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str

                trainer_data[trainer_id].append({
                    'position': result['position'],
                    'date': race_date
                })

            return trainer_data

        else:  # ra_runners
            runners = self.db_client.client.table('ra_runners')\
                .select('trainer_id, position, race_id')\
                .in_('trainer_id', trainer_ids)\
                .not_.is_('position', 'null')\
                .execute()

            race_ids = list(set([r['race_id'] for r in runners.data if r['race_id']]))
            if not race_ids:
                return {}

            races = self.db_client.client.table('ra_races')\
                .select('id, date')\
                .in_('id', race_ids)\
                .execute()

            race_dates = {r['id']: r['date'] for r in races.data}

            trainer_data = {}
            for runner in runners.data:
                trainer_id = runner['trainer_id']
                if trainer_id not in trainer_data:
                    trainer_data[trainer_id] = []

                race_date_str = race_dates.get(runner['race_id'])
                if race_date_str:
                    race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str
                    trainer_data[trainer_id].append({
                        'position': runner['position'],
                        'date': race_date
                    })

            return trainer_data

    def calculate_trainer_statistics(self, limit: Optional[int] = None) -> List[Dict]:
        """Calculate all trainer statistics from database"""
        logger.info(f"Calculating trainer statistics from {self.data_source}...")

        # Get all trainers
        trainers_query = self.db_client.client.table('ra_trainers').select('id')
        if limit:
            trainers_query = trainers_query.limit(limit)
        trainers = trainers_query.execute()

        trainer_ids = [t['id'] for t in trainers.data]
        logger.info(f"Processing {len(trainer_ids)} trainers...")

        # Fetch race data
        trainer_race_data = self.fetch_trainer_race_data(trainer_ids)

        # Calculate statistics
        today = date.today()
        cutoff_14d = today - timedelta(days=14)
        cutoff_30d = today - timedelta(days=30)

        results = []
        for trainer_id in trainer_ids:
            race_data = trainer_race_data.get(trainer_id, [])

            if not race_data:
                results.append({
                    'id': trainer_id,
                    'last_runner_date': None,
                    'last_win_date': None,
                    'days_since_last_runner': None,
                    'days_since_last_win': None,
                    'recent_14d_runs': 0,
                    'recent_14d_wins': 0,
                    'recent_14d_win_rate': None,
                    'recent_30d_runs': 0,
                    'recent_30d_wins': 0,
                    'recent_30d_win_rate': None,
                    'total_runners': 0,
                    'total_wins': 0,
                    'total_places': 0,
                    'total_seconds': 0,
                    'total_thirds': 0,
                    'win_rate': None,
                    'place_rate': None,
                    'stats_updated_at': datetime.utcnow().isoformat()
                })
                continue

            # Calculate stats
            all_dates = [r['date'] for r in race_data]
            win_dates = [r['date'] for r in race_data if self.is_win(r['position'])]

            last_runner_date = max(all_dates) if all_dates else None
            last_win_date = max(win_dates) if win_dates else None

            days_since_last_runner = (today - last_runner_date).days if last_runner_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            recent_14d = [r for r in race_data if r['date'] >= cutoff_14d]
            recent_14d_runs = len(recent_14d)
            recent_14d_wins = len([r for r in recent_14d if self.is_win(r['position'])])
            recent_14d_win_rate = self.calculate_win_rate(recent_14d_wins, recent_14d_runs)

            recent_30d = [r for r in race_data if r['date'] >= cutoff_30d]
            recent_30d_runs = len(recent_30d)
            recent_30d_wins = len([r for r in recent_30d if self.is_win(r['position'])])
            recent_30d_win_rate = self.calculate_win_rate(recent_30d_wins, recent_30d_runs)

            total_runners = len(race_data)
            total_wins = len([r for r in race_data if self.is_win(r['position'])])
            total_places = len([r for r in race_data if self.is_place(r['position'])])

            positions = [self.normalize_position(r['position']) for r in race_data]
            total_seconds = len([p for p in positions if p in ['2', '2ND']])
            total_thirds = len([p for p in positions if p in ['3', '3RD']])

            win_rate = self.calculate_win_rate(total_wins, total_runners)
            place_rate = self.calculate_win_rate(total_places, total_runners)

            results.append({
                'id': trainer_id,
                'last_runner_date': last_runner_date.isoformat() if last_runner_date else None,
                'last_win_date': last_win_date.isoformat() if last_win_date else None,
                'days_since_last_runner': days_since_last_runner,
                'days_since_last_win': days_since_last_win,
                'recent_14d_runs': recent_14d_runs,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_runs': recent_30d_runs,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'total_runners': total_runners,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': total_seconds,
                'total_thirds': total_thirds,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'stats_updated_at': datetime.utcnow().isoformat()
            })

        logger.info(f"Calculated statistics for {len(results)} trainers")
        return results

    def fetch_owner_race_data(self, owner_ids: List[str]) -> Tuple[Dict, Dict]:
        """Fetch all race data for owners from appropriate source"""
        if self.data_source == 'ra_race_results':
            results = self.db_client.client.table('ra_race_results')\
                .select('owner_id, position, race_date, horse_id')\
                .in_('owner_id', owner_ids)\
                .not_.is_('position', 'null')\
                .execute()

            owner_data = {}
            owner_horses = {}
            for result in results.data:
                owner_id = result['owner_id']
                if owner_id not in owner_data:
                    owner_data[owner_id] = []
                    owner_horses[owner_id] = set()

                race_date_str = result['race_date']
                race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str

                owner_data[owner_id].append({
                    'position': result['position'],
                    'date': race_date
                })

                if result['horse_id']:
                    owner_horses[owner_id].add(result['horse_id'])

            return owner_data, owner_horses

        else:  # ra_runners
            runners = self.db_client.client.table('ra_runners')\
                .select('owner_id, position, race_id, horse_id')\
                .in_('owner_id', owner_ids)\
                .not_.is_('position', 'null')\
                .execute()

            race_ids = list(set([r['race_id'] for r in runners.data if r['race_id']]))
            if not race_ids:
                return {}, {}

            races = self.db_client.client.table('ra_races')\
                .select('id, date')\
                .in_('id', race_ids)\
                .execute()

            race_dates = {r['id']: r['date'] for r in races.data}

            owner_data = {}
            owner_horses = {}
            for runner in runners.data:
                owner_id = runner['owner_id']
                if owner_id not in owner_data:
                    owner_data[owner_id] = []
                    owner_horses[owner_id] = set()

                race_date_str = race_dates.get(runner['race_id'])
                if race_date_str:
                    race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date() if isinstance(race_date_str, str) else race_date_str
                    owner_data[owner_id].append({
                        'position': runner['position'],
                        'date': race_date
                    })

                if runner['horse_id']:
                    owner_horses[owner_id].add(runner['horse_id'])

            return owner_data, owner_horses

    def calculate_owner_statistics(self, limit: Optional[int] = None) -> List[Dict]:
        """Calculate all owner statistics from database"""
        logger.info(f"Calculating owner statistics from {self.data_source}...")

        # Get all owners
        owners_query = self.db_client.client.table('ra_owners').select('id')
        if limit:
            owners_query = owners_query.limit(limit)
        owners = owners_query.execute()

        owner_ids = [o['id'] for o in owners.data]
        logger.info(f"Processing {len(owner_ids)} owners...")

        # Fetch race data
        owner_race_data, owner_horses = self.fetch_owner_race_data(owner_ids)

        # Calculate statistics
        today = date.today()
        cutoff_14d = today - timedelta(days=14)
        cutoff_30d = today - timedelta(days=30)

        results = []
        for owner_id in owner_ids:
            race_data = owner_race_data.get(owner_id, [])
            horses = owner_horses.get(owner_id, set())

            if not race_data:
                results.append({
                    'id': owner_id,
                    'last_runner_date': None,
                    'last_win_date': None,
                    'days_since_last_runner': None,
                    'days_since_last_win': None,
                    'recent_14d_runs': 0,
                    'recent_14d_wins': 0,
                    'recent_14d_win_rate': None,
                    'recent_30d_runs': 0,
                    'recent_30d_wins': 0,
                    'recent_30d_win_rate': None,
                    'total_horses': 0,
                    'total_runners': 0,
                    'total_wins': 0,
                    'total_places': 0,
                    'total_seconds': 0,
                    'total_thirds': 0,
                    'win_rate': None,
                    'place_rate': None,
                    'stats_updated_at': datetime.utcnow().isoformat()
                })
                continue

            # Calculate stats
            all_dates = [r['date'] for r in race_data]
            win_dates = [r['date'] for r in race_data if self.is_win(r['position'])]

            last_runner_date = max(all_dates) if all_dates else None
            last_win_date = max(win_dates) if win_dates else None

            days_since_last_runner = (today - last_runner_date).days if last_runner_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            recent_14d = [r for r in race_data if r['date'] >= cutoff_14d]
            recent_14d_runs = len(recent_14d)
            recent_14d_wins = len([r for r in recent_14d if self.is_win(r['position'])])
            recent_14d_win_rate = self.calculate_win_rate(recent_14d_wins, recent_14d_runs)

            recent_30d = [r for r in race_data if r['date'] >= cutoff_30d]
            recent_30d_runs = len(recent_30d)
            recent_30d_wins = len([r for r in recent_30d if self.is_win(r['position'])])
            recent_30d_win_rate = self.calculate_win_rate(recent_30d_wins, recent_30d_runs)

            total_horses = len(horses)
            total_runners = len(race_data)
            total_wins = len([r for r in race_data if self.is_win(r['position'])])
            total_places = len([r for r in race_data if self.is_place(r['position'])])

            positions = [self.normalize_position(r['position']) for r in race_data]
            total_seconds = len([p for p in positions if p in ['2', '2ND']])
            total_thirds = len([p for p in positions if p in ['3', '3RD']])

            win_rate = self.calculate_win_rate(total_wins, total_runners)
            place_rate = self.calculate_win_rate(total_places, total_runners)

            results.append({
                'id': owner_id,
                'last_runner_date': last_runner_date.isoformat() if last_runner_date else None,
                'last_win_date': last_win_date.isoformat() if last_win_date else None,
                'days_since_last_runner': days_since_last_runner,
                'days_since_last_win': days_since_last_win,
                'recent_14d_runs': recent_14d_runs,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_runs': recent_30d_runs,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'total_horses': total_horses,
                'total_runners': total_runners,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': total_seconds,
                'total_thirds': total_thirds,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'stats_updated_at': datetime.utcnow().isoformat()
            })

        logger.info(f"Calculated statistics for {len(results)} owners")
        return results

    def update_jockeys(self, limit: Optional[int] = None) -> Dict:
        """Calculate and update jockey statistics"""
        start_time = time.time()

        try:
            # Calculate statistics
            stats_list = self.calculate_jockey_statistics(limit)
            self.stats['jockeys']['processed'] = len(stats_list)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would update {len(stats_list)} jockeys")
                if stats_list:
                    logger.info(f"Sample: {stats_list[0]}")
                return {'updated': 0, 'time': time.time() - start_time}

            # Update in batches
            batch_size = 1000
            total_updated = 0

            for i in range(0, len(stats_list), batch_size):
                batch = stats_list[i:i + batch_size]
                try:
                    self.db_client.client.table('ra_jockeys').upsert(batch).execute()
                    total_updated += len(batch)
                    logger.info(f"Updated {total_updated}/{len(stats_list)} jockeys...")
                except Exception as e:
                    logger.error(f"Error updating batch: {e}")
                    self.stats['jockeys']['errors'] += len(batch)

            self.stats['jockeys']['updated'] = total_updated
            elapsed = time.time() - start_time

            logger.info(f"Updated {total_updated} jockeys in {elapsed:.2f}s ({total_updated/elapsed:.1f} entities/sec)")

            return {'updated': total_updated, 'time': elapsed}

        except Exception as e:
            logger.error(f"Error calculating jockey statistics: {e}", exc_info=True)
            raise

    def update_trainers(self, limit: Optional[int] = None) -> Dict:
        """Calculate and update trainer statistics"""
        start_time = time.time()

        try:
            stats_list = self.calculate_trainer_statistics(limit)
            self.stats['trainers']['processed'] = len(stats_list)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would update {len(stats_list)} trainers")
                if stats_list:
                    logger.info(f"Sample: {stats_list[0]}")
                return {'updated': 0, 'time': time.time() - start_time}

            # Update in batches
            batch_size = 1000
            total_updated = 0

            for i in range(0, len(stats_list), batch_size):
                batch = stats_list[i:i + batch_size]
                try:
                    self.db_client.client.table('ra_trainers').upsert(batch).execute()
                    total_updated += len(batch)
                    logger.info(f"Updated {total_updated}/{len(stats_list)} trainers...")
                except Exception as e:
                    logger.error(f"Error updating batch: {e}")
                    self.stats['trainers']['errors'] += len(batch)

            self.stats['trainers']['updated'] = total_updated
            elapsed = time.time() - start_time

            logger.info(f"Updated {total_updated} trainers in {elapsed:.2f}s ({total_updated/elapsed:.1f} entities/sec)")

            return {'updated': total_updated, 'time': elapsed}

        except Exception as e:
            logger.error(f"Error calculating trainer statistics: {e}", exc_info=True)
            raise

    def update_owners(self, limit: Optional[int] = None) -> Dict:
        """Calculate and update owner statistics"""
        start_time = time.time()

        try:
            stats_list = self.calculate_owner_statistics(limit)
            self.stats['owners']['processed'] = len(stats_list)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would update {len(stats_list)} owners")
                if stats_list:
                    logger.info(f"Sample: {stats_list[0]}")
                return {'updated': 0, 'time': time.time() - start_time}

            # Update in batches
            batch_size = 1000
            total_updated = 0

            for i in range(0, len(stats_list), batch_size):
                batch = stats_list[i:i + batch_size]
                try:
                    self.db_client.client.table('ra_owners').upsert(batch).execute()
                    total_updated += len(batch)
                    logger.info(f"Updated {total_updated}/{len(stats_list)} owners...")
                except Exception as e:
                    logger.error(f"Error updating batch: {e}")
                    self.stats['owners']['errors'] += len(batch)

            self.stats['owners']['updated'] = total_updated
            elapsed = time.time() - start_time

            logger.info(f"Updated {total_updated} owners in {elapsed:.2f}s ({total_updated/elapsed:.1f} entities/sec)")

            return {'updated': total_updated, 'time': elapsed}

        except Exception as e:
            logger.error(f"Error calculating owner statistics: {e}", exc_info=True)
            raise

    def get_summary(self) -> Dict:
        """Get execution summary"""
        return self.stats


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate entity statistics from database (optimized)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if position data is available
  python3 scripts/populate_statistics_from_database.py --check

  # Process all entity types
  python3 scripts/populate_statistics_from_database.py --all

  # Process specific types
  python3 scripts/populate_statistics_from_database.py --entities jockeys trainers

  # Dry run (show stats without updating)
  python3 scripts/populate_statistics_from_database.py --all --dry-run

  # Process limited set for testing
  python3 scripts/populate_statistics_from_database.py --entities jockeys --limit 10
        """
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if position data is available in database'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all entity types (jockeys, trainers, owners)'
    )

    parser.add_argument(
        '--entities',
        nargs='+',
        choices=['jockeys', 'trainers', 'owners'],
        help='Specific entity types to process'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of entities to process (for testing)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate statistics but do not update database'
    )

    args = parser.parse_args()

    # Initialize calculator
    calculator = DatabaseStatisticsCalculator(dry_run=args.dry_run)

    # Handle --check mode
    if args.check:
        logger.info("=" * 80)
        logger.info("DATABASE POSITION DATA CHECK")
        logger.info("=" * 80)
        has_data, source = calculator.check_data_availability()
        if has_data:
            logger.info(f"\n✓ Position data available in: {source}")
            logger.info("You can now run statistics population.")
            return 0
        else:
            logger.error("\n✗ No position data available")
            logger.error("See error message above for next steps.")
            return 1

    # Validate arguments for normal mode
    if not args.all and not args.entities:
        parser.error("Must specify either --all, --entities, or --check")

    # Check data availability before processing
    has_data, source = calculator.check_data_availability()
    if not has_data:
        return 1

    # Determine which entities to process
    if args.all:
        entities = ['jockeys', 'trainers', 'owners']
    else:
        entities = args.entities

    # Print execution info
    logger.info("=" * 80)
    logger.info("POPULATE ENTITY STATISTICS FROM DATABASE (OPTIMIZED)")
    logger.info("=" * 80)
    logger.info(f"Data source: {source}")
    logger.info(f"Entities: {', '.join(entities)}")
    logger.info(f"Limit: {args.limit if args.limit else 'None (all)'}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 80)

    total_start = time.time()
    results = {}

    # Process each entity type
    if 'jockeys' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING JOCKEYS")
        logger.info("=" * 80)
        results['jockeys'] = calculator.update_jockeys(limit=args.limit)

    if 'trainers' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING TRAINERS")
        logger.info("=" * 80)
        results['trainers'] = calculator.update_trainers(limit=args.limit)

    if 'owners' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING OWNERS")
        logger.info("=" * 80)
        results['owners'] = calculator.update_owners(limit=args.limit)

    total_elapsed = time.time() - total_start

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 80)

    summary = calculator.get_summary()
    total_processed = sum(s['processed'] for s in summary.values())
    total_updated = sum(s['updated'] for s in summary.values())
    total_errors = sum(s['errors'] for s in summary.values())

    for entity_type in entities:
        if entity_type in results:
            stats = summary[entity_type]
            result = results[entity_type]
            logger.info(f"\n{entity_type.upper()}:")
            logger.info(f"  Processed: {stats['processed']:,}")
            logger.info(f"  Updated: {stats['updated']:,}")
            logger.info(f"  Errors: {stats['errors']:,}")
            logger.info(f"  Time: {result['time']:.2f}s")
            if result['time'] > 0 and stats['updated'] > 0:
                logger.info(f"  Rate: {stats['updated']/result['time']:.1f} entities/sec")

    logger.info(f"\nTOTAL:")
    logger.info(f"  Processed: {total_processed:,}")
    logger.info(f"  Updated: {total_updated:,}")
    logger.info(f"  Errors: {total_errors:,}")
    logger.info(f"  Total time: {total_elapsed:.2f}s")
    if total_elapsed > 0 and total_updated > 0:
        logger.info(f"  Overall rate: {total_updated/total_elapsed:.1f} entities/sec")

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE")
    logger.info("=" * 80)

    return 0 if total_errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
