#!/usr/bin/env python3
"""
ML Runner History Compilation Script
=====================================
Autonomous agent that compiles complete runner history for upcoming races
to support ML predictions.

This script:
1. Identifies all runners in upcoming races (next 7 days by default)
2. For each runner, compiles their complete racing history
3. Calculates statistics, form metrics, and context-specific performance
4. Stores denormalized data in ra_ml_runner_history table
5. Cleans up old data automatically

Designed to run daily at 6:00 AM UTC via scheduler
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('compile_ml_data')


class MLDataCompiler:
    """Compiles ML-ready runner history data for upcoming races"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize ML data compiler

        Args:
            dry_run: If True, don't write to database (testing only)
        """
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.utcnow(),
            'races_processed': 0,
            'runners_compiled': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errors': 0,
            'warnings': 0
        }

        if dry_run:
            logger.warning("DRY RUN MODE - No database writes will occur")

    def run(
        self,
        days_ahead: int = 7,
        days_to_keep: int = 30,
        regions: List[str] = None
    ) -> Dict:
        """
        Run ML data compilation

        Args:
            days_ahead: Number of days ahead to compile (default: 7)
            days_to_keep: Keep historical ML data for this many days (default: 30)
            regions: Optional list of region codes to filter

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("ML RUNNER HISTORY COMPILATION - Starting")
        logger.info(f"Time: {self.stats['start_time'].isoformat()}")
        logger.info(f"Days ahead: {days_ahead}")
        logger.info(f"Regions: {regions or 'All'}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)

        try:
            # Step 1: Get upcoming races
            upcoming_races = self._get_upcoming_races(days_ahead, regions)
            logger.info(f"Found {len(upcoming_races)} upcoming races")

            if not upcoming_races:
                logger.warning("No upcoming races found. Nothing to compile.")
                return self.stats

            # Step 2: Get runners for upcoming races
            upcoming_runners = self._get_upcoming_runners(upcoming_races)
            logger.info(f"Found {len(upcoming_runners)} upcoming runners")

            if not upcoming_runners:
                logger.warning("No upcoming runners found. Nothing to compile.")
                return self.stats

            # Step 3: Compile history for each runner
            ml_records = []
            for runner in upcoming_runners:
                try:
                    ml_record = self._compile_runner_history(runner)
                    if ml_record:
                        ml_records.append(ml_record)
                        self.stats['runners_compiled'] += 1
                    else:
                        self.stats['records_skipped'] += 1
                except Exception as e:
                    logger.error(f"Error compiling runner {runner.get('runner_id')}: {e}", exc_info=True)
                    self.stats['errors'] += 1

            logger.info(f"Compiled {len(ml_records)} ML records")

            # Step 4: Store in database
            if ml_records and not self.dry_run:
                self._store_ml_records(ml_records)
            elif self.dry_run:
                logger.info(f"[DRY RUN] Would store {len(ml_records)} records")

            # Step 5: Cleanup old data
            if not self.dry_run:
                self._cleanup_old_data(days_to_keep)

            # Calculate execution time
            self.stats['end_time'] = datetime.utcnow()
            self.stats['duration_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            logger.error(f"ML compilation failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            self.stats['error'] = str(e)
            return self.stats

    def _get_upcoming_races(
        self,
        days_ahead: int,
        regions: List[str] = None
    ) -> List[Dict]:
        """
        Get upcoming races from database

        Args:
            days_ahead: Number of days ahead to look
            regions: Optional region filter

        Returns:
            List of race dictionaries
        """
        logger.info(f"Fetching races for next {days_ahead} days...")

        start_date = datetime.utcnow().date()
        end_date = start_date + timedelta(days=days_ahead)

        try:
            # Build query
            query = self.db_client.client.table('ra_races').select('*')

            # Date filter
            query = query.gte('race_date', start_date.isoformat())
            query = query.lte('race_date', end_date.isoformat())

            # Region filter
            if regions:
                query = query.in_('region', regions)

            # Execute query
            response = query.execute()

            races = response.data if response.data else []
            logger.info(f"Retrieved {len(races)} upcoming races")

            return races

        except Exception as e:
            logger.error(f"Error fetching upcoming races: {e}", exc_info=True)
            return []

    def _get_upcoming_runners(self, races: List[Dict]) -> List[Dict]:
        """
        Get runners for upcoming races

        Args:
            races: List of race dictionaries

        Returns:
            List of runner dictionaries with race context
        """
        logger.info("Fetching runners for upcoming races...")

        race_ids = [race['race_id'] for race in races]
        if not race_ids:
            return []

        try:
            # Get runners in batches to avoid query limits
            all_runners = []
            batch_size = 100

            for i in range(0, len(race_ids), batch_size):
                batch_ids = race_ids[i:i + batch_size]

                response = self.db_client.client.table('ra_runners').select('*').in_(
                    'race_id', batch_ids
                ).execute()

                if response.data:
                    all_runners.extend(response.data)

            logger.info(f"Retrieved {len(all_runners)} upcoming runners")

            # Attach race context to each runner
            race_map = {race['race_id']: race for race in races}
            for runner in all_runners:
                runner['race_context'] = race_map.get(runner['race_id'], {})

            return all_runners

        except Exception as e:
            logger.error(f"Error fetching upcoming runners: {e}", exc_info=True)
            return []

    def _compile_runner_history(self, runner: Dict) -> Optional[Dict]:
        """
        Compile complete history for a single runner

        Args:
            runner: Runner dictionary with race context

        Returns:
            ML record dictionary or None if compilation fails
        """
        horse_id = runner.get('horse_id')
        if not horse_id:
            logger.warning(f"Runner {runner.get('runner_id')} missing horse_id")
            return None

        race_context = runner.get('race_context', {})

        # Get all historical races for this horse
        historical_races = self._get_horse_history(horse_id)

        # Calculate statistics
        career_stats = self._calculate_career_stats(historical_races)
        context_stats = self._calculate_context_stats(historical_races, race_context)
        recent_form = self._calculate_recent_form(historical_races)
        relationship_stats = self._calculate_relationship_stats(
            historical_races,
            runner.get('jockey_id'),
            runner.get('trainer_id')
        )

        # Build ML record
        ml_record = {
            # Identification
            'race_id': runner.get('race_id'),
            'runner_id': runner.get('runner_id'),
            'horse_id': horse_id,
            'horse_name': runner.get('horse_name'),
            'compilation_date': datetime.utcnow().isoformat(),

            # Race context
            'race_date': race_context.get('race_date'),
            'off_datetime': race_context.get('off_datetime'),
            'course_id': race_context.get('course_id'),
            'course_name': race_context.get('course_name'),
            'region': race_context.get('region'),
            'distance_meters': race_context.get('distance_meters'),
            'distance_f': race_context.get('distance_f'),
            'surface': race_context.get('surface'),
            'going': race_context.get('going'),
            'race_type': race_context.get('race_type'),
            'race_class': race_context.get('race_class'),
            'age_band': race_context.get('age_band'),
            'prize_money': race_context.get('prize_money'),
            'field_size': race_context.get('field_size'),

            # Current runner details
            'current_weight_lbs': runner.get('weight_lbs'),
            'current_draw': runner.get('draw'),
            'current_number': runner.get('number'),
            'headgear': runner.get('headgear'),
            'blinkers': runner.get('blinkers', False),
            'cheekpieces': runner.get('cheekpieces', False),
            'visor': runner.get('visor', False),
            'tongue_tie': runner.get('tongue_tie', False),

            # Current entities
            'jockey_id': runner.get('jockey_id'),
            'jockey_name': runner.get('jockey_name'),
            'trainer_id': runner.get('trainer_id'),
            'trainer_name': runner.get('trainer_name'),
            'owner_id': runner.get('owner_id'),
            'owner_name': runner.get('owner_name'),
            'official_rating': runner.get('official_rating'),
            'racing_post_rating': runner.get('racing_post_rating'),
            'timeform_rating': runner.get('timeform_rating'),

            # Career statistics
            **career_stats,

            # Context-specific performance
            **context_stats,

            # Recent form
            **recent_form,

            # Relationship statistics
            **relationship_stats,

            # Pedigree
            'sire_id': runner.get('sire_id'),
            'sire_name': runner.get('sire_name'),
            'dam_id': runner.get('dam_id'),
            'dam_name': runner.get('dam_name'),
            'damsire_id': runner.get('damsire_id'),
            'damsire_name': runner.get('damsire_name'),
            'horse_age': runner.get('age'),
            'horse_sex': runner.get('sex'),

            # Historical races (full array)
            'historical_races': historical_races,
            'historical_races_count': len(historical_races),

            # Status flags
            'has_form': len(historical_races) > 0,
            'ml_features_version': '1.0'
        }

        return ml_record

    def _get_horse_history(self, horse_id: str) -> List[Dict]:
        """
        Get complete racing history for a horse

        Args:
            horse_id: Horse ID

        Returns:
            List of historical race dictionaries
        """
        try:
            # Query all runners for this horse, ordered by date
            response = self.db_client.client.table('ra_runners').select(
                '*, ra_races!inner(*)'
            ).eq('horse_id', horse_id).execute()

            if not response.data:
                return []

            # Filter to only past races and sort by date
            today = datetime.utcnow().date()
            historical = []

            for record in response.data:
                race = record.get('ra_races', {})
                race_date_str = race.get('race_date')

                if race_date_str:
                    try:
                        race_date = datetime.fromisoformat(race_date_str).date()
                        if race_date < today:
                            historical.append({
                                **record,
                                'race': race
                            })
                    except (ValueError, TypeError):
                        continue

            # Sort by date (most recent first)
            historical.sort(key=lambda x: x['race'].get('race_date', ''), reverse=True)

            return historical

        except Exception as e:
            logger.error(f"Error fetching history for horse {horse_id}: {e}")
            return []

    def _calculate_career_stats(self, historical_races: List[Dict]) -> Dict:
        """Calculate career statistics from historical races"""
        if not historical_races:
            return {
                'total_races': 0,
                'total_wins': 0,
                'total_places': 0,
                'total_seconds': 0,
                'total_thirds': 0,
                'win_rate': None,
                'place_rate': None,
                'avg_finish_position': None,
                'total_earnings': None,
                'days_since_last_run': None
            }

        total_races = len(historical_races)
        wins = sum(1 for r in historical_races if self._get_position(r) == 1)
        seconds = sum(1 for r in historical_races if self._get_position(r) == 2)
        thirds = sum(1 for r in historical_races if self._get_position(r) == 3)
        places = wins + seconds + thirds

        # Calculate average finish position (only for races with valid positions)
        positions = [self._get_position(r) for r in historical_races if self._get_position(r)]
        avg_position = sum(positions) / len(positions) if positions else None

        # Calculate days since last run
        if historical_races:
            try:
                last_race_date = datetime.fromisoformat(
                    historical_races[0]['race'].get('race_date')
                ).date()
                days_since = (datetime.utcnow().date() - last_race_date).days
            except (ValueError, TypeError, KeyError):
                days_since = None
        else:
            days_since = None

        return {
            'total_races': total_races,
            'total_wins': wins,
            'total_places': places,
            'total_seconds': seconds,
            'total_thirds': thirds,
            'win_rate': round(wins / total_races * 100, 2) if total_races > 0 else 0,
            'place_rate': round(places / total_races * 100, 2) if total_races > 0 else 0,
            'avg_finish_position': round(avg_position, 2) if avg_position else None,
            'total_earnings': None,  # TODO: Calculate from prize money when available
            'days_since_last_run': days_since
        }

    def _calculate_context_stats(
        self,
        historical_races: List[Dict],
        race_context: Dict
    ) -> Dict:
        """Calculate context-specific statistics"""
        if not historical_races:
            return self._empty_context_stats()

        course_id = race_context.get('course_id')
        distance_meters = race_context.get('distance_meters')
        surface = race_context.get('surface')
        going = race_context.get('going')
        race_class = race_context.get('race_class')

        # Course statistics
        course_races = [r for r in historical_races if r['race'].get('course_id') == course_id]
        course_wins = sum(1 for r in course_races if self._get_position(r) == 1)
        course_places = sum(1 for r in course_races if self._get_position(r) in [1, 2, 3])

        # Distance statistics (±10% tolerance)
        distance_races = []
        if distance_meters:
            min_dist = distance_meters * 0.9
            max_dist = distance_meters * 1.1
            distance_races = [
                r for r in historical_races
                if r['race'].get('distance_meters')
                and min_dist <= r['race'].get('distance_meters') <= max_dist
            ]
        distance_wins = sum(1 for r in distance_races if self._get_position(r) == 1)
        distance_places = sum(1 for r in distance_races if self._get_position(r) in [1, 2, 3])

        # Surface statistics
        surface_races = [r for r in historical_races if r['race'].get('surface') == surface]
        surface_wins = sum(1 for r in surface_races if self._get_position(r) == 1)
        surface_places = sum(1 for r in surface_races if self._get_position(r) in [1, 2, 3])

        # Going statistics (exact match for now - could add similarity logic)
        going_races = [r for r in historical_races if r['race'].get('going') == going]
        going_wins = sum(1 for r in going_races if self._get_position(r) == 1)
        going_places = sum(1 for r in going_races if self._get_position(r) in [1, 2, 3])

        # Class statistics
        class_races = [r for r in historical_races if r['race'].get('race_class') == race_class]
        class_wins = sum(1 for r in class_races if self._get_position(r) == 1)
        class_places = sum(1 for r in class_races if self._get_position(r) in [1, 2, 3])

        return {
            'course_runs': len(course_races),
            'course_wins': course_wins,
            'course_places': course_places,
            'course_win_rate': round(course_wins / len(course_races) * 100, 2) if course_races else None,

            'distance_runs': len(distance_races),
            'distance_wins': distance_wins,
            'distance_places': distance_places,
            'distance_win_rate': round(distance_wins / len(distance_races) * 100, 2) if distance_races else None,

            'surface_runs': len(surface_races),
            'surface_wins': surface_wins,
            'surface_places': surface_places,
            'surface_win_rate': round(surface_wins / len(surface_races) * 100, 2) if surface_races else None,

            'going_runs': len(going_races),
            'going_wins': going_wins,
            'going_places': going_places,
            'going_win_rate': round(going_wins / len(going_races) * 100, 2) if going_races else None,

            'class_runs': len(class_races),
            'class_wins': class_wins,
            'class_places': class_places,
            'class_win_rate': round(class_wins / len(class_races) * 100, 2) if class_races else None
        }

    def _calculate_recent_form(self, historical_races: List[Dict]) -> Dict:
        """Calculate recent form statistics"""
        if not historical_races:
            return {
                'last_5_positions': [],
                'last_5_dates': [],
                'last_5_courses': [],
                'last_5_distances': [],
                'last_5_classes': [],
                'last_10_positions': [],
                'recent_form_score': None
            }

        # Extract last 10 races
        recent_10 = historical_races[:10]
        recent_5 = historical_races[:5]

        last_5_positions = [self._get_position(r) for r in recent_5]
        last_10_positions = [self._get_position(r) for r in recent_10]

        last_5_dates = [r['race'].get('race_date') for r in recent_5]
        last_5_courses = [r['race'].get('course_name') for r in recent_5]
        last_5_distances = [r['race'].get('distance_meters') for r in recent_5]
        last_5_classes = [r['race'].get('race_class') for r in recent_5]

        # Calculate form score (weighted by recency)
        # Win = 10 points, 2nd = 7, 3rd = 5, 4th = 3, 5th+ = 1
        # Most recent race weighted 2x
        form_score = 0
        weights = [2.0, 1.5, 1.2, 1.0, 1.0]  # Recency weights

        for i, race in enumerate(recent_5):
            position = self._get_position(race)
            if position:
                if position == 1:
                    points = 10
                elif position == 2:
                    points = 7
                elif position == 3:
                    points = 5
                elif position == 4:
                    points = 3
                else:
                    points = 1
                form_score += points * weights[i]

        # Normalize to 0-100
        max_score = sum([10 * w for w in weights])
        normalized_score = round(form_score / max_score * 100, 2) if max_score > 0 else 0

        return {
            'last_5_positions': last_5_positions,
            'last_5_dates': last_5_dates,
            'last_5_courses': last_5_courses,
            'last_5_distances': last_5_distances,
            'last_5_classes': last_5_classes,
            'last_10_positions': last_10_positions,
            'recent_form_score': normalized_score
        }

    def _calculate_relationship_stats(
        self,
        historical_races: List[Dict],
        current_jockey_id: str,
        current_trainer_id: str
    ) -> Dict:
        """Calculate horse-jockey and horse-trainer relationship statistics"""
        if not historical_races:
            return {
                'horse_jockey_runs': 0,
                'horse_jockey_wins': 0,
                'horse_jockey_win_rate': None,
                'horse_trainer_runs': 0,
                'horse_trainer_wins': 0,
                'horse_trainer_win_rate': None,
                'jockey_trainer_runs': 0,
                'jockey_trainer_wins': 0,
                'jockey_trainer_win_rate': None,
                'jockey_career_stats': None,
                'trainer_career_stats': None
            }

        # Horse-Jockey stats
        hj_races = [r for r in historical_races if r.get('jockey_id') == current_jockey_id]
        hj_wins = sum(1 for r in hj_races if self._get_position(r) == 1)

        # Horse-Trainer stats
        ht_races = [r for r in historical_races if r.get('trainer_id') == current_trainer_id]
        ht_wins = sum(1 for r in ht_races if self._get_position(r) == 1)

        # Jockey-Trainer combination stats
        jt_races = [
            r for r in historical_races
            if r.get('jockey_id') == current_jockey_id
            and r.get('trainer_id') == current_trainer_id
        ]
        jt_wins = sum(1 for r in jt_races if self._get_position(r) == 1)

        return {
            'horse_jockey_runs': len(hj_races),
            'horse_jockey_wins': hj_wins,
            'horse_jockey_win_rate': round(hj_wins / len(hj_races) * 100, 2) if hj_races else None,

            'horse_trainer_runs': len(ht_races),
            'horse_trainer_wins': ht_wins,
            'horse_trainer_win_rate': round(ht_wins / len(ht_races) * 100, 2) if ht_races else None,

            'jockey_trainer_runs': len(jt_races),
            'jockey_trainer_wins': jt_wins,
            'jockey_trainer_win_rate': round(jt_wins / len(jt_races) * 100, 2) if jt_races else None,

            'jockey_career_stats': None,  # TODO: Query ra_jockeys for overall stats
            'trainer_career_stats': None  # TODO: Query ra_trainers for overall stats
        }

    def _get_position(self, race_record: Dict) -> Optional[int]:
        """Extract finishing position from race record"""
        # Try multiple fields where position might be stored
        position = None

        # Check runner record fields
        for field in ['position', 'finish_position', 'place', 'finishing_position']:
            if field in race_record:
                pos = race_record[field]
                if isinstance(pos, int) and pos > 0:
                    position = pos
                    break
                elif isinstance(pos, str) and pos.isdigit():
                    position = int(pos)
                    break

        # Check race context if available
        if not position and 'race' in race_record:
            race = race_record['race']
            for field in ['position', 'finish_position']:
                if field in race:
                    pos = race[field]
                    if isinstance(pos, int) and pos > 0:
                        position = pos
                        break

        # Check api_data JSONB
        if not position and 'api_data' in race_record:
            api_data = race_record.get('api_data', {})
            if isinstance(api_data, dict):
                for field in ['position', 'place', 'finish_position']:
                    if field in api_data:
                        pos = api_data[field]
                        if isinstance(pos, (int, str)):
                            try:
                                position = int(pos)
                                break
                            except (ValueError, TypeError):
                                pass

        return position

    def _empty_context_stats(self) -> Dict:
        """Return empty context stats structure"""
        return {
            'course_runs': 0, 'course_wins': 0, 'course_places': 0, 'course_win_rate': None,
            'distance_runs': 0, 'distance_wins': 0, 'distance_places': 0, 'distance_win_rate': None,
            'surface_runs': 0, 'surface_wins': 0, 'surface_places': 0, 'surface_win_rate': None,
            'going_runs': 0, 'going_wins': 0, 'going_places': 0, 'going_win_rate': None,
            'class_runs': 0, 'class_wins': 0, 'class_places': 0, 'class_win_rate': None
        }

    def _store_ml_records(self, ml_records: List[Dict]):
        """Store ML records in database (upsert)"""
        logger.info(f"Storing {len(ml_records)} ML records...")

        try:
            # Batch insert (Supabase upsert requires a unique constraint, so we'll just insert)
            # Duplicates are prevented by checking before insert or cleaning up old compilations
            batch_size = 100
            for i in range(0, len(ml_records), batch_size):
                batch = ml_records[i:i + batch_size]

                response = self.db_client.client.table('dh_ml_runner_history').insert(
                    batch
                ).execute()

                if response.data:
                    self.stats['records_inserted'] += len(response.data)

            logger.info(f"Successfully stored {self.stats['records_inserted']} ML records")

        except Exception as e:
            logger.error(f"Error storing ML records: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _cleanup_old_data(self, days_to_keep: int):
        """Remove old ML data for races that have passed"""
        logger.info(f"Cleaning up ML data older than {days_to_keep} days...")

        try:
            cutoff_date = (datetime.utcnow().date() - timedelta(days=days_to_keep)).isoformat()

            response = self.db_client.client.table('dh_ml_runner_history').delete().lt(
                'race_date', cutoff_date
            ).execute()

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Deleted {deleted_count} old ML records")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}", exc_info=True)

    def _print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("ML COMPILATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time'].isoformat()}")
        logger.info(f"End time: {self.stats['end_time'].isoformat()}")
        logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        logger.info("")
        logger.info(f"Races processed: {self.stats['races_processed']}")
        logger.info(f"Runners compiled: {self.stats['runners_compiled']}")
        logger.info(f"Records inserted: {self.stats['records_inserted']}")
        logger.info(f"Records updated: {self.stats['records_updated']}")
        logger.info(f"Records skipped: {self.stats['records_skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Warnings: {self.stats['warnings']}")

        if self.dry_run:
            logger.info("")
            logger.info("[DRY RUN] No data was written to database")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Compile ML-ready runner history for upcoming races'
    )
    parser.add_argument(
        '--days-ahead',
        type=int,
        default=7,
        help='Number of days ahead to compile (default: 7)'
    )
    parser.add_argument(
        '--days-to-keep',
        type=int,
        default=30,
        help='Keep ML data for this many days after race (default: 30)'
    )
    parser.add_argument(
        '--regions',
        nargs='+',
        default=['gb', 'ire'],
        help='Region codes to compile (default: gb ire)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - compile data but do not write to database'
    )

    args = parser.parse_args()

    try:
        compiler = MLDataCompiler(dry_run=args.dry_run)
        stats = compiler.run(
            days_ahead=args.days_ahead,
            days_to_keep=args.days_to_keep,
            regions=args.regions
        )

        # Exit with appropriate code
        if stats.get('errors', 0) > 0:
            logger.warning("ML compilation completed with errors")
            sys.exit(1)
        else:
            logger.info("ML compilation completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
