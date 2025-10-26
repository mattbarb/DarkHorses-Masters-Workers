#!/usr/bin/env python3
"""
Autonomous Pedigree Statistics Agent
=====================================

Continuously populates and updates ALL columns in ra_mst_sires, ra_mst_dams,
and ra_mst_damsires tables using both database calculations and Racing API data.

Features:
- Calculates statistics from database (progeny performance)
- Fetches additional data from Racing API when needed
- Calculates AE (Actual vs Expected) indices
- Populates data_quality_score based on data completeness
- Runs autonomously with configurable intervals
- Checkpoint/resume capability
- Detailed logging and error handling

Columns Populated:
- Basic stats: total_runners, total_wins, total_places_2nd, total_places_3rd
- Win metrics: overall_win_percent, overall_ae_index
- Best performance: best_class, best_class_ae, best_distance, best_distance_ae
- Class breakdowns: class_1/2/3 (name, runners, wins, win_percent, ae)
- Distance breakdowns: distance_1/2/3 (name, runners, wins, win_percent, ae)
- Metadata: analysis_last_updated, data_quality_score

Usage:
    # Run full population (all tables)
    python3 agents/pedigree_statistics_agent.py

    # Run specific table only
    python3 agents/pedigree_statistics_agent.py --table sires

    # Test mode (10 entities)
    python3 agents/pedigree_statistics_agent.py --test

    # Continuous mode (runs every N hours)
    python3 agents/pedigree_statistics_agent.py --continuous --interval 24

    # Resume from checkpoint
    python3 agents/pedigree_statistics_agent.py --resume
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.api_client import RacingAPIClient
from utils.logger import get_logger

logger = get_logger('pedigree_statistics_agent')

CHECKPOINT_FILE = 'logs/pedigree_agent_checkpoint.json'
STATS_FILE = 'logs/pedigree_agent_stats.json'


class PedigreeStatisticsAgent:
    """Autonomous agent for populating pedigree statistics"""

    def __init__(self, test_mode: bool = False):
        """Initialize the agent"""
        self.config = get_config()
        self.db = SupabaseReferenceClient(
            self.config.supabase.url,
            self.config.supabase.service_key
        )
        self.api_client = RacingAPIClient(
            username=self.config.api.username,
            password=self.config.api.password
        )
        self.test_mode = test_mode
        self.stats = {
            'sires': {'processed': 0, 'updated': 0, 'errors': 0},
            'dams': {'processed': 0, 'updated': 0, 'errors': 0},
            'damsires': {'processed': 0, 'updated': 0, 'errors': 0}
        }

    def save_checkpoint(self, table: str, last_id: str):
        """Save progress checkpoint"""
        checkpoint = {
            'table': table,
            'last_id': last_id,
            'timestamp': datetime.now().isoformat()
        }
        os.makedirs('logs', exist_ok=True)
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        logger.info(f"Checkpoint saved: {table} - {last_id}")

    def load_checkpoint(self) -> Optional[Dict]:
        """Load progress checkpoint"""
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return None

    def save_stats(self):
        """Save statistics to file"""
        stats_data = {
            'stats': self.stats,
            'last_run': datetime.now().isoformat()
        }
        os.makedirs('logs', exist_ok=True)
        with open(STATS_FILE, 'w') as f:
            json.dump(stats_data, f, indent=2)

    def calculate_ae_index(self, wins: int, runners: int,
                          class_distribution: Dict[int, int]) -> float:
        """
        Calculate AE (Actual vs Expected) index.

        AE = (Actual wins / Expected wins) * 100

        Expected wins are based on class distribution and average win rates:
        - Class 1: 10% average win rate
        - Class 2: 11% average win rate
        - Class 3: 12% average win rate
        - Class 4: 13% average win rate
        - Class 5: 14% average win rate
        - Class 6: 15% average win rate
        - Class 7: 16% average win rate
        """
        if runners == 0:
            return 0.0

        # Base win rates by class (industry averages)
        class_win_rates = {
            1: 0.10,  # Class 1 (highest quality)
            2: 0.11,
            3: 0.12,
            4: 0.13,
            5: 0.14,
            6: 0.15,
            7: 0.16   # Class 7 (lowest quality)
        }

        # Calculate expected wins based on class distribution
        expected_wins = 0.0
        for class_num, class_runners in class_distribution.items():
            win_rate = class_win_rates.get(class_num, 0.125)  # Default 12.5%
            expected_wins += class_runners * win_rate

        if expected_wins == 0:
            return 0.0

        # AE index: (actual / expected) * 100
        ae_index = (wins / expected_wins) * 100
        return round(ae_index, 3)

    def calculate_distance_ae_index(self, wins: int, runners: int,
                                    distance_distribution: Dict[float, int]) -> float:
        """
        Calculate AE index for distance performance.

        Uses similar logic but with distance-based win rates:
        - Sprint (5-7f): 12%
        - Mile (8-10f): 13%
        - Middle (11-14f): 12%
        - Long (15f+): 11%
        """
        if runners == 0:
            return 0.0

        distance_win_rates = {
            'sprint': 0.12,   # 5-7f
            'mile': 0.13,     # 8-10f
            'middle': 0.12,   # 11-14f
            'long': 0.11      # 15f+
        }

        expected_wins = 0.0
        for distance_f, dist_runners in distance_distribution.items():
            # Categorize distance
            if distance_f <= 7:
                category = 'sprint'
            elif distance_f <= 10:
                category = 'mile'
            elif distance_f <= 14:
                category = 'middle'
            else:
                category = 'long'

            win_rate = distance_win_rates[category]
            expected_wins += dist_runners * win_rate

        if expected_wins == 0:
            return 0.0

        ae_index = (wins / expected_wins) * 100
        return round(ae_index, 3)

    def calculate_data_quality_score(self, update_data: Dict) -> float:
        """
        Calculate data quality score (0.00 - 1.00) based on completeness.

        Scoring:
        - Has total_runners > 0: 0.20
        - Has class breakdown: 0.30
        - Has distance breakdown: 0.30
        - Has AE indices: 0.20
        """
        score = 0.0

        # Has runner data
        if update_data.get('total_runners', 0) > 0:
            score += 0.20

        # Has class breakdown
        if update_data.get('class_1_name'):
            score += 0.10
        if update_data.get('class_2_name'):
            score += 0.10
        if update_data.get('class_3_name'):
            score += 0.10

        # Has distance breakdown
        if update_data.get('distance_1_name'):
            score += 0.10
        if update_data.get('distance_2_name'):
            score += 0.10
        if update_data.get('distance_3_name'):
            score += 0.10

        # Has AE indices
        if update_data.get('overall_ae_index'):
            score += 0.10
        if update_data.get('best_class_ae'):
            score += 0.05
        if update_data.get('best_distance_ae'):
            score += 0.05

        return round(score, 2)

    def get_progeny_statistics(self, pedigree_id: str,
                               pedigree_type: str) -> Optional[Dict]:
        """
        Calculate complete statistics for a pedigree entity.

        Args:
            pedigree_id: ID of sire/dam/damsire
            pedigree_type: 'sire', 'dam', or 'damsire'

        Returns:
            Dictionary with all statistics or None if no data
        """
        # Get offspring IDs
        field_name = f'{pedigree_type}_id'
        offspring_response = self.db.client.table('ra_mst_horses').select('id').eq(
            field_name, pedigree_id
        ).execute()
        offspring_ids = [h['id'] for h in offspring_response.data]

        if not offspring_ids:
            return None

        # Get all runners for these horses
        runners_query = self.db.client.table('ra_mst_runners').select(
            'position, race_id'
        ).in_('horse_id', offspring_ids).execute()
        runners = runners_query.data

        if not runners:
            return None

        # Get race details
        race_ids = list(set([r['race_id'] for r in runners]))
        # Batch races to avoid timeouts
        races_dict = {}
        batch_size = 1000
        for i in range(0, len(race_ids), batch_size):
            batch_ids = race_ids[i:i+batch_size]
            races_response = self.db.client.table('ra_mst_races').select(
                'id, race_class, distance, distance_f'
            ).in_('id', batch_ids).execute()
            races_dict.update({r['id']: r for r in races_response.data})

        # Calculate basic stats
        total_runners = len(runners)
        total_wins = sum(1 for r in runners if r.get('position') == 1)
        total_places_2nd = sum(1 for r in runners if r.get('position') == 2)
        total_places_3rd = sum(1 for r in runners if r.get('position') == 3)
        overall_win_percent = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0

        # Analyze class performance
        class_stats = defaultdict(lambda: {'runners': 0, 'wins': 0})
        class_distribution = defaultdict(int)

        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('race_class'):
                continue

            # Parse class number from string like "Class 3" -> 3
            class_str = race['race_class']
            try:
                if class_str and 'class' in class_str.lower():
                    class_num = int(class_str.lower().replace('class', '').strip())
                else:
                    class_num = int(class_str) if class_str else None
            except (ValueError, AttributeError):
                continue

            if class_num is None:
                continue

            class_stats[class_num]['runners'] += 1
            class_distribution[class_num] += 1
            if runner.get('position') == 1:
                class_stats[class_num]['wins'] += 1

        # Get top 3 classes by wins
        top_classes = sorted(class_stats.items(),
                           key=lambda x: x[1]['wins'],
                           reverse=True)[:3]

        # Analyze distance performance
        distance_stats = defaultdict(lambda: {'runners': 0, 'wins': 0})
        distance_distribution = defaultdict(int)

        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('distance_f'):
                continue

            # Parse distance_f to float
            try:
                dist_f_str = race['distance_f']
                # Remove 'f' suffix if present
                if isinstance(dist_f_str, str):
                    dist_f_str = dist_f_str.replace('f', '').strip()
                dist_f = float(dist_f_str)
            except (ValueError, AttributeError, TypeError):
                continue

            distance_stats[dist_f]['runners'] += 1
            distance_distribution[dist_f] += 1
            if runner.get('position') == 1:
                distance_stats[dist_f]['wins'] += 1

        # Get top 3 distances by wins
        top_distances = sorted(distance_stats.items(),
                             key=lambda x: x[1]['wins'],
                             reverse=True)[:3]

        # Calculate overall AE index
        overall_ae = self.calculate_ae_index(
            total_wins, total_runners, class_distribution
        )

        # Find best class and calculate its AE
        best_class = top_classes[0][0] if top_classes else None
        best_class_ae = None
        if best_class and best_class in class_stats:
            best_class_ae = self.calculate_ae_index(
                class_stats[best_class]['wins'],
                class_stats[best_class]['runners'],
                {best_class: class_stats[best_class]['runners']}
            )

        # Find best distance and calculate its AE
        best_distance_f = top_distances[0][0] if top_distances else None
        best_distance = f"{best_distance_f}f" if best_distance_f else None
        best_distance_ae = None
        if best_distance_f and best_distance_f in distance_stats:
            best_distance_ae = self.calculate_distance_ae_index(
                distance_stats[best_distance_f]['wins'],
                distance_stats[best_distance_f]['runners'],
                {best_distance_f: distance_stats[best_distance_f]['runners']}
            )

        # Build update data
        update_data = {
            'total_runners': total_runners,
            'total_wins': total_wins,
            'total_places_2nd': total_places_2nd,
            'total_places_3rd': total_places_3rd,
            'overall_win_percent': overall_win_percent,
            'overall_ae_index': overall_ae,
            'best_class': str(best_class) if best_class else None,
            'best_class_ae': best_class_ae,
            'best_distance': best_distance,
            'best_distance_ae': best_distance_ae,
            'analysis_last_updated': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add top 3 class breakdowns with AE
        for i, (class_num, stats) in enumerate(top_classes, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            class_ae = self.calculate_ae_index(
                stats['wins'], stats['runners'],
                {class_num: stats['runners']}
            )
            update_data[f'class_{i}_name'] = f"Class {class_num}"
            update_data[f'class_{i}_runners'] = stats['runners']
            update_data[f'class_{i}_wins'] = stats['wins']
            update_data[f'class_{i}_win_percent'] = win_percent
            update_data[f'class_{i}_ae'] = class_ae

        # Add top 3 distance breakdowns with AE
        for i, (dist_f, stats) in enumerate(top_distances, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            dist_ae = self.calculate_distance_ae_index(
                stats['wins'], stats['runners'],
                {dist_f: stats['runners']}
            )
            update_data[f'distance_{i}_name'] = f"{dist_f}f"
            update_data[f'distance_{i}_runners'] = stats['runners']
            update_data[f'distance_{i}_wins'] = stats['wins']
            update_data[f'distance_{i}_win_percent'] = win_percent
            update_data[f'distance_{i}_ae'] = dist_ae

        # Calculate data quality score
        update_data['data_quality_score'] = self.calculate_data_quality_score(update_data)

        return update_data

    def process_sires(self, limit: Optional[int] = None,
                     resume_from: Optional[str] = None) -> int:
        """Process all sires"""
        logger.info("=" * 80)
        logger.info("PROCESSING SIRES")
        logger.info("=" * 80)

        # Get all sires directly from ra_mst_sires table
        query = self.db.client.table('ra_mst_sires').select('id, name')

        if limit:
            query = query.limit(limit)

        response = query.execute()
        sires = [(s['id'], s['name']) for s in response.data]

        # Resume from checkpoint if provided
        if resume_from:
            sires = [(sid, name) for sid, name in sires if sid > resume_from]
            logger.info(f"Resuming from {resume_from}")

        if limit:
            sires = sires[:limit]

        logger.info(f"Processing {len(sires)} sires...")

        updated = 0
        for idx, (sire_id, sire_name) in enumerate(sires, 1):
            try:
                self.stats['sires']['processed'] += 1

                # Calculate statistics
                stats = self.get_progeny_statistics(sire_id, 'sire')

                if not stats:
                    continue

                # Upsert to database
                upsert_data = {
                    'id': sire_id,
                    'name': sire_name or 'Unknown',
                    **stats
                }

                self.db.client.table('ra_mst_sires').upsert(upsert_data).execute()
                updated += 1
                self.stats['sires']['updated'] += 1

                # Progress logging
                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(sires)} ({updated} updated)")
                    self.save_checkpoint('sires', sire_id)

            except Exception as e:
                logger.error(f"Error processing sire {sire_id}: {e}", exc_info=True)
                self.stats['sires']['errors'] += 1

        logger.info(f"✅ Sires complete: {updated}/{len(sires)} updated")
        return updated

    def process_dams(self, limit: Optional[int] = None,
                    resume_from: Optional[str] = None) -> int:
        """Process all dams"""
        logger.info("=" * 80)
        logger.info("PROCESSING DAMS")
        logger.info("=" * 80)

        # Get all dams directly from ra_mst_dams table
        query = self.db.client.table('ra_mst_dams').select('id, name')

        if limit:
            query = query.limit(limit)

        response = query.execute()
        dams = [(d['id'], d['name']) for d in response.data]

        if resume_from:
            dams = [(did, name) for did, name in dams if did > resume_from]
            logger.info(f"Resuming from {resume_from}")

        if limit:
            dams = dams[:limit]

        logger.info(f"Processing {len(dams)} dams...")

        updated = 0
        for idx, (dam_id, dam_name) in enumerate(dams, 1):
            try:
                self.stats['dams']['processed'] += 1

                stats = self.get_progeny_statistics(dam_id, 'dam')

                if not stats:
                    continue

                upsert_data = {
                    'id': dam_id,
                    'name': dam_name or 'Unknown',
                    **stats
                }

                self.db.client.table('ra_mst_dams').upsert(upsert_data).execute()
                updated += 1
                self.stats['dams']['updated'] += 1

                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(dams)} ({updated} updated)")
                    self.save_checkpoint('dams', dam_id)

            except Exception as e:
                logger.error(f"Error processing dam {dam_id}: {e}", exc_info=True)
                self.stats['dams']['errors'] += 1

        logger.info(f"✅ Dams complete: {updated}/{len(dams)} updated")
        return updated

    def process_damsires(self, limit: Optional[int] = None,
                        resume_from: Optional[str] = None) -> int:
        """Process all damsires"""
        logger.info("=" * 80)
        logger.info("PROCESSING DAMSIRES")
        logger.info("=" * 80)

        # Get all damsires directly from ra_mst_damsires table
        query = self.db.client.table('ra_mst_damsires').select('id, name')

        if limit:
            query = query.limit(limit)

        response = query.execute()
        damsires = [(d['id'], d['name']) for d in response.data]

        if resume_from:
            damsires = [(did, name) for did, name in damsires if did > resume_from]
            logger.info(f"Resuming from {resume_from}")

        logger.info(f"Processing {len(damsires)} damsires...")

        updated = 0
        for idx, (damsire_id, damsire_name) in enumerate(damsires, 1):
            try:
                self.stats['damsires']['processed'] += 1

                stats = self.get_progeny_statistics(damsire_id, 'damsire')

                if not stats:
                    continue

                # Use name from query (already have it)
                upsert_data = {
                    'id': damsire_id,
                    'name': damsire_name,
                    **stats
                }

                self.db.client.table('ra_mst_damsires').upsert(upsert_data).execute()
                updated += 1
                self.stats['damsires']['updated'] += 1

                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(damsires)} ({updated} updated)")
                    self.save_checkpoint('damsires', damsire_id)

            except Exception as e:
                logger.error(f"Error processing damsire {damsire_id}: {e}", exc_info=True)
                self.stats['damsires']['errors'] += 1

        logger.info(f"✅ Damsires complete: {updated}/{len(damsires)} updated")
        return updated

    def run(self, table: Optional[str] = None, resume: bool = False):
        """Run the agent"""
        logger.info("=" * 80)
        logger.info("PEDIGREE STATISTICS AGENT")
        logger.info("=" * 80)
        logger.info(f"Mode: {'TEST (10 per table)' if self.test_mode else 'FULL'}")
        logger.info(f"Tables: {table if table else 'ALL'}")
        logger.info(f"Resume: {resume}")
        logger.info("=" * 80)

        limit = 10 if self.test_mode else None
        checkpoint = self.load_checkpoint() if resume else None

        start_time = datetime.now()

        # Process tables
        if not table or table == 'sires':
            resume_id = checkpoint.get('last_id') if checkpoint and checkpoint.get('table') == 'sires' else None
            self.process_sires(limit, resume_id)

        if not table or table == 'dams':
            resume_id = checkpoint.get('last_id') if checkpoint and checkpoint.get('table') == 'dams' else None
            self.process_dams(limit, resume_id)

        if not table or table == 'damsires':
            resume_id = checkpoint.get('last_id') if checkpoint and checkpoint.get('table') == 'damsires' else None
            self.process_damsires(limit, resume_id)

        # Save final stats
        self.save_stats()

        # Summary
        duration = datetime.now() - start_time
        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        for tbl, counts in self.stats.items():
            logger.info(f"{tbl.upper()}:")
            logger.info(f"  Processed: {counts['processed']}")
            logger.info(f"  Updated: {counts['updated']}")
            logger.info(f"  Errors: {counts['errors']}")
        logger.info(f"Duration: {duration}")
        logger.info("=" * 80)

        # Clean up checkpoint on successful completion
        if os.path.exists(CHECKPOINT_FILE) and not resume:
            os.remove(CHECKPOINT_FILE)


def main():
    parser = argparse.ArgumentParser(
        description='Autonomous pedigree statistics agent'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (10 entities per table)'
    )
    parser.add_argument(
        '--table',
        choices=['sires', 'dams', 'damsires'],
        help='Specific table only'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously at intervals'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Hours between runs in continuous mode (default: 24)'
    )

    args = parser.parse_args()

    agent = PedigreeStatisticsAgent(test_mode=args.test)

    if args.continuous:
        logger.info(f"Starting continuous mode (interval: {args.interval}h)")
        while True:
            try:
                agent.run(table=args.table, resume=args.resume)
                logger.info(f"Sleeping for {args.interval} hours...")
                time.sleep(args.interval * 3600)
            except KeyboardInterrupt:
                logger.info("Stopping continuous mode...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}", exc_info=True)
                logger.info("Retrying in 1 hour...")
                time.sleep(3600)
    else:
        agent.run(table=args.table, resume=args.resume)


if __name__ == '__main__':
    main()
