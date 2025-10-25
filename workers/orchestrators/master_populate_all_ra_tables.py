#!/usr/bin/env python3
"""
Master Population Script for ALL ra_ Tables
============================================

This is the MASTER script that coordinates population of ALL columns
across ALL ra_ tables in the database.

It orchestrates:
1. Core data fetchers (from Racing API)
2. Statistics calculators (from database analysis)
3. Pedigree agents (from progeny performance)
4. Derived data calculators (relationships, supplementary)

Tables Populated (23 tables):
- ra_mst_* (10 master tables): bookmakers, courses, dams, damsires, horses, jockeys, owners, regions, sires, trainers
- ra_races (race metadata)
- ra_runners (race entries)
- ra_race_results (historical results)
- ra_horse_pedigree (lineage)
- ra_runner_statistics (runner-level stats)
- ra_runner_supplementary (additional runner data)
- ra_performance_by_distance (distance analysis)
- ra_performance_by_venue (course analysis)
- ra_odds_* (odds data - 3 tables)
- ra_runner_odds (runner odds)
- ra_entity_combinations (entity pair analysis)

Usage:
    # Full population (all tables, all columns)
    python3 scripts/population_workers/master_populate_all_ra_tables.py

    # Specific category
    python3 scripts/population_workers/master_populate_all_ra_tables.py --category core
    python3 scripts/population_workers/master_populate_all_ra_tables.py --category statistics
    python3 scripts/population_workers/master_populate_all_ra_tables.py --category pedigree

    # Specific table
    python3 scripts/population_workers/master_populate_all_ra_tables.py --table ra_mst_sires

    # Test mode
    python3 scripts/population_workers/master_populate_all_ra_tables.py --test

    # Status report only (no execution)
    python3 scripts/population_workers/master_populate_all_ra_tables.py --status
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('master_population')

# Population script mapping
POPULATION_SCRIPTS = {
    # ============================================================================
    # CATEGORY 1: CORE DATA (From Racing API)
    # ============================================================================
    "core": {
        "ra_mst_courses": {
            "script": "main.py --entities courses",
            "description": "Fetch courses from Racing API",
            "source": "/v1/courses",
            "estimated_time": "30s"
        },
        "ra_mst_bookmakers": {
            "script": "main.py --entities bookmakers",
            "description": "Fetch bookmakers from Racing API",
            "source": "/v1/bookmakers",
            "estimated_time": "30s"
        },
        "ra_mst_jockeys": {
            "script": "main.py --entities jockeys",
            "description": "Fetch jockeys from Racing API",
            "source": "/v1/jockeys",
            "estimated_time": "2m"
        },
        "ra_mst_trainers": {
            "script": "main.py --entities trainers",
            "description": "Fetch trainers from Racing API",
            "source": "/v1/trainers",
            "estimated_time": "2m"
        },
        "ra_mst_owners": {
            "script": "main.py --entities owners",
            "description": "Fetch owners from Racing API",
            "source": "/v1/owners",
            "estimated_time": "3m"
        },
        "ra_mst_horses": {
            "script": "main.py --entities races",  # Extracted from racecards
            "description": "Fetch horses from racecards (with enrichment)",
            "source": "/v1/racecards/pro + /v1/horses/{id}/pro",
            "estimated_time": "5m"
        },
        "ra_races": {
            "script": "main.py --entities races",
            "description": "Fetch race metadata",
            "source": "/v1/racecards/pro",
            "estimated_time": "5m"
        },
        "ra_runners": {
            "script": "main.py --entities races",
            "description": "Fetch race runners/entries",
            "source": "/v1/racecards/pro",
            "estimated_time": "5m"
        },
        "ra_race_results": {
            "script": "main.py --entities results",
            "description": "Fetch race results",
            "source": "/v1/results",
            "estimated_time": "10m"
        },
        "ra_horse_pedigree": {
            "script": "main.py --entities races",  # Captured during enrichment
            "description": "Capture pedigree from horse enrichment",
            "source": "/v1/horses/{id}/pro",
            "estimated_time": "Included in horses"
        }
    },

    # ============================================================================
    # CATEGORY 2: PEDIGREE STATISTICS (From Database Analysis)
    # ============================================================================
    "pedigree": {
        "ra_mst_sires": {
            "script": "agents/pedigree_statistics_agent.py --table sires",
            "description": "Calculate sire statistics from progeny performance",
            "source": "Database: ra_mst_horses + ra_runners + ra_races",
            "estimated_time": "10m"
        },
        "ra_mst_dams": {
            "script": "agents/pedigree_statistics_agent.py --table dams",
            "description": "Calculate dam statistics from progeny performance",
            "source": "Database: ra_mst_horses + ra_runners + ra_races",
            "estimated_time": "2-3h"
        },
        "ra_mst_damsires": {
            "script": "agents/pedigree_statistics_agent.py --table damsires",
            "description": "Calculate damsire statistics from progeny performance",
            "source": "Database: ra_mst_horses + ra_runners + ra_races",
            "estimated_time": "10m"
        }
    },

    # ============================================================================
    # CATEGORY 3: ENTITY STATISTICS (From Database Analysis)
    # ============================================================================
    "statistics": {
        "ra_mst_jockeys_stats": {
            "script": "scripts/statistics_workers/calculate_jockey_statistics.py",
            "description": "Calculate jockey statistics",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "5m"
        },
        "ra_mst_trainers_stats": {
            "script": "scripts/statistics_workers/calculate_trainer_statistics.py",
            "description": "Calculate trainer statistics",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "5m"
        },
        "ra_mst_owners_stats": {
            "script": "scripts/statistics_workers/calculate_owner_statistics.py",
            "description": "Calculate owner statistics",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "5m"
        }
    },

    # ============================================================================
    # CATEGORY 4: SUPPLEMENTARY DATA (Derived/Calculated)
    # ============================================================================
    "supplementary": {
        "ra_runner_statistics": {
            "script": "scripts/population_workers/calculate_runner_statistics.py",
            "description": "Calculate per-runner statistics",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "10m"
        },
        "ra_runner_supplementary": {
            "script": "scripts/population_workers/populate_runner_supplementary.py",
            "description": "Populate supplementary runner data",
            "source": "Database: ra_runners + ra_races + entities",
            "estimated_time": "5m"
        },
        "ra_performance_by_distance": {
            "script": "scripts/population_workers/calculate_distance_performance.py",
            "description": "Calculate distance-based performance",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "5m"
        },
        "ra_performance_by_venue": {
            "script": "scripts/population_workers/calculate_venue_performance.py",
            "description": "Calculate venue-based performance",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "5m"
        },
        "ra_entity_combinations": {
            "script": "scripts/population_workers/calculate_entity_combinations.py",
            "description": "Calculate entity pair statistics",
            "source": "Database: ra_runners + ra_races",
            "estimated_time": "10m"
        }
    },

    # ============================================================================
    # CATEGORY 5: ODDS DATA (From Odds Workers - if available)
    # ============================================================================
    "odds": {
        "ra_odds_live": {
            "script": "# External: DarkHorses-Odds-Workers",
            "description": "Live odds (populated by separate system)",
            "source": "External odds workers",
            "estimated_time": "N/A"
        },
        "ra_odds_historical": {
            "script": "# External: DarkHorses-Odds-Workers",
            "description": "Historical odds (populated by separate system)",
            "source": "External odds workers",
            "estimated_time": "N/A"
        },
        "ra_odds_statistics": {
            "script": "# External: DarkHorses-Odds-Workers",
            "description": "Odds statistics (populated by separate system)",
            "source": "External odds workers",
            "estimated_time": "N/A"
        },
        "ra_runner_odds": {
            "script": "# External: DarkHorses-Odds-Workers",
            "description": "Runner-level odds (populated by separate system)",
            "source": "External odds workers",
            "estimated_time": "N/A"
        }
    }
}


class MasterPopulator:
    """Master coordinator for populating all ra_ tables"""

    def __init__(self, test_mode: bool = False):
        self.config = get_config()
        self.db = SupabaseReferenceClient(
            self.config.supabase.url,
            self.config.supabase.service_key
        )
        self.test_mode = test_mode
        self.results = {}

    def get_table_status(self, table: str) -> Dict:
        """Get current population status for a table"""
        try:
            # Get total rows
            count_response = self.db.client.table(table).select('*', count='exact', head=True).execute()
            total = count_response.count if count_response else 0

            # Get column count
            schema_response = self.db.client.rpc('get_table_columns', {'table_name': table}).execute()
            columns = len(schema_response.data) if schema_response and schema_response.data else 0

            return {
                'table': table,
                'total_rows': total,
                'total_columns': columns,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting status for {table}: {e}")
            return {
                'table': table,
                'total_rows': 0,
                'total_columns': 0,
                'exists': False,
                'error': str(e)
            }

    def run_script(self, script: str, description: str) -> Dict:
        """Execute a population script"""
        if script.startswith('#'):
            logger.info(f"Skipping: {description} - {script}")
            return {'success': True, 'skipped': True, 'message': script}

        logger.info(f"Running: {description}")
        logger.info(f"Script: {script}")

        try:
            # Build command
            if script.startswith('python3') or script.endswith('.py'):
                cmd = f"python3 {script}" if not script.startswith('python3') else script
            else:
                cmd = f"python3 {script}"

            if self.test_mode and '--test' not in cmd:
                cmd += ' --test'

            # Execute
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info(f"✅ Success: {description}")
                return {
                    'success': True,
                    'stdout': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,
                    'stderr': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
                }
            else:
                logger.error(f"❌ Failed: {description}")
                logger.error(f"Error: {result.stderr}")
                return {
                    'success': False,
                    'stdout': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,
                    'stderr': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
                    'returncode': result.returncode
                }

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Timeout: {description}")
            return {'success': False, 'error': 'Timeout after 1 hour'}
        except Exception as e:
            logger.error(f"❌ Error: {description} - {e}")
            return {'success': False, 'error': str(e)}

    def populate_category(self, category: str):
        """Populate all tables in a category"""
        if category not in POPULATION_SCRIPTS:
            logger.error(f"Unknown category: {category}")
            return

        scripts = POPULATION_SCRIPTS[category]
        logger.info(f"=" * 80)
        logger.info(f"CATEGORY: {category.upper()}")
        logger.info(f"Tables: {len(scripts)}")
        logger.info(f"=" * 80)

        for table, config in scripts.items():
            logger.info(f"\n{'=' * 80}")
            logger.info(f"TABLE: {table}")
            logger.info(f"Description: {config['description']}")
            logger.info(f"Source: {config['source']}")
            logger.info(f"Estimated Time: {config['estimated_time']}")
            logger.info(f"{'=' * 80}")

            result = self.run_script(config['script'], config['description'])
            self.results[table] = result

    def populate_table(self, table: str):
        """Populate a specific table"""
        # Find table in scripts
        for category, tables in POPULATION_SCRIPTS.items():
            if table in tables:
                config = tables[table]
                logger.info(f"Found {table} in category: {category}")
                result = self.run_script(config['script'], config['description'])
                self.results[table] = result
                return

        logger.error(f"Table {table} not found in population scripts")

    def show_status(self):
        """Show status of all tables"""
        logger.info("=" * 80)
        logger.info("DATABASE POPULATION STATUS")
        logger.info("=" * 80)

        for category, tables in POPULATION_SCRIPTS.items():
            logger.info(f"\n{category.upper()}:")
            for table, config in tables.items():
                status = self.get_table_status(table)
                logger.info(f"  {table}:")
                logger.info(f"    Rows: {status.get('total_rows', 0)}")
                logger.info(f"    Columns: {status.get('total_columns', 0)}")
                logger.info(f"    Script: {config['script']}")

    def run_all(self):
        """Run all population scripts"""
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("MASTER POPULATION - ALL TABLES")
        logger.info("=" * 80)
        logger.info(f"Mode: {'TEST' if self.test_mode else 'FULL'}")
        logger.info(f"Start: {start_time}")
        logger.info("=" * 80)

        # Execute in order
        categories = ['core', 'pedigree', 'statistics', 'supplementary']

        for category in categories:
            self.populate_category(category)

        # Summary
        duration = datetime.now() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)

        success_count = sum(1 for r in self.results.values() if r.get('success'))
        skip_count = sum(1 for r in self.results.values() if r.get('skipped'))
        fail_count = len(self.results) - success_count - skip_count

        logger.info(f"Total: {len(self.results)}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Skipped: {skip_count}")
        logger.info(f"Failed: {fail_count}")
        logger.info(f"Duration: {duration}")
        logger.info("=" * 80)

        # Save results
        results_file = f"logs/master_population_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'start_time': start_time.isoformat(),
                'duration': str(duration),
                'results': self.results
            }, f, indent=2)
        logger.info(f"Results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(description='Master population script for all ra_ tables')
    parser.add_argument('--category', choices=['core', 'pedigree', 'statistics', 'supplementary', 'odds'],
                       help='Populate specific category only')
    parser.add_argument('--table', help='Populate specific table only')
    parser.add_argument('--test', action='store_true', help='Test mode (limited data)')
    parser.add_argument('--status', action='store_true', help='Show status only (no execution)')

    args = parser.parse_args()

    populator = MasterPopulator(test_mode=args.test)

    if args.status:
        populator.show_status()
    elif args.table:
        populator.populate_table(args.table)
    elif args.category:
        populator.populate_category(args.category)
    else:
        populator.run_all()


if __name__ == '__main__':
    main()
