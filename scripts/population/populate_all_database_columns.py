#!/usr/bin/env python3
"""
Comprehensive Database Population Script
=========================================

Populates ALL database tables and columns systematically based on the detailed
column inventory. Processes one table at a time, skips already-populated columns,
and updates missing/outdated values.

Usage:
    python3 scripts/populate_all_database_columns.py [OPTIONS]

Options:
    --dry-run          Show what would be done without making changes
    --table TABLE_NAME Process only specific table
    --phase PHASE      Run specific phase only (calculated|simple_migrations)
    --verbose          Show detailed progress

Author: Claude Code
Date: 2025-10-21
"""

import psycopg2
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ====================================================================================
# CONFIGURATION
# ====================================================================================

DB_CONFIG = {
    'host': 'aws-0-eu-west-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.amsjvmlaknnvppxsgpfk',
    'password': 'R0pMr1L58WH3hUkpVtPcwYnw'
}

INVENTORY_PATH = 'docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json'
CHECKPOINT_PATH = 'logs/populate_all_checkpoint.json'
LOG_PATH = f'logs/populate_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# ====================================================================================
# LOGGING SETUP
# ====================================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ====================================================================================
# COLUMN INVENTORY LOADER
# ====================================================================================

class ColumnInventory:
    """Loads and manages the comprehensive column inventory"""

    def __init__(self, inventory_path: str):
        self.inventory_path = inventory_path
        self.columns = []
        self.tables = {}
        self.load()

    def load(self):
        """Load inventory from JSON file"""
        logger.info(f"Loading column inventory from {self.inventory_path}")

        with open(self.inventory_path, 'r') as f:
            data = json.load(f)

        self.columns = data.get('columns', [])

        # Group by table
        for col in self.columns:
            table = col['table']
            if table not in self.tables:
                self.tables[table] = []
            self.tables[table].append(col)

        logger.info(f"Loaded {len(self.columns)} columns across {len(self.tables)} tables")

    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get all columns for a specific table"""
        return self.tables.get(table_name, [])

    def get_columns_by_source(self, data_source: str) -> List[Dict]:
        """Get all columns from a specific data source"""
        return [col for col in self.columns if col['data_source'] == data_source]

    def get_populate_targets(self) -> List[Dict]:
        """Get columns that can be auto-populated (not 100% filled)"""
        return [col for col in self.columns if col['pct_populated'] < 100]

# ====================================================================================
# POPULATION HANDLERS
# ====================================================================================

class DatabasePopulator:
    """Main class to handle database population"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.conn = None
        self.cur = None
        self.stats = {
            'tables_processed': 0,
            'columns_updated': 0,
            'records_updated': 0,
            'errors': 0
        }

    def connect(self):
        """Establish database connection"""
        logger.info("Connecting to database...")
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        logger.info("Database connection established")

    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List]:
        """Execute a query with optional dry-run mode"""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {query[:200]}...")
            return None

        try:
            self.cur.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return self.cur.fetchall()
            else:
                self.conn.commit()
                return None
        except Exception as e:
            logger.error(f"Query failed: {e}")
            logger.error(f"Query: {query[:200]}")
            self.stats['errors'] += 1
            self.conn.rollback()
            raise

    # ====================================================================================
    # PHASE 1: SIMPLE CALCULATED FIELDS
    # ====================================================================================

    def populate_horse_age(self) -> int:
        """Calculate age from date of birth"""
        logger.info("Populating ra_mst_horses.age from dob...")

        query = """
            UPDATE ra_mst_horses
            SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob))::INTEGER,
                updated_at = NOW()
            WHERE dob IS NOT NULL
              AND (age IS NULL OR age != EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob))::INTEGER);
        """

        if self.dry_run:
            # Count what would be updated
            count_query = """
                SELECT COUNT(*)
                FROM ra_mst_horses
                WHERE dob IS NOT NULL
                  AND (age IS NULL OR age != EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob))::INTEGER);
            """
            self.cur.execute(count_query)
            count = self.cur.fetchone()[0]
            logger.info(f"[DRY-RUN] Would update {count:,} horse ages")
            return count

        self.cur.execute(query)
        updated = self.cur.rowcount
        self.conn.commit()
        logger.info(f"Updated {updated:,} horse ages")
        return updated

    def populate_horse_breeder(self) -> int:
        """Migrate breeder from ra_horse_pedigree table"""
        logger.info("Populating ra_mst_horses.breeder from ra_horse_pedigree...")

        query = """
            UPDATE ra_mst_horses h
            SET breeder = p.breeder,
                updated_at = NOW()
            FROM ra_horse_pedigree p
            WHERE h.id = p.horse_id
              AND p.breeder IS NOT NULL
              AND p.breeder != ''
              AND (h.breeder IS NULL OR h.breeder = '');
        """

        if self.dry_run:
            count_query = """
                SELECT COUNT(*)
                FROM ra_mst_horses h
                JOIN ra_horse_pedigree p ON h.id = p.horse_id
                WHERE p.breeder IS NOT NULL
                  AND p.breeder != ''
                  AND (h.breeder IS NULL OR h.breeder = '');
            """
            self.cur.execute(count_query)
            count = self.cur.fetchone()[0]
            logger.info(f"[DRY-RUN] Would update {count:,} horse breeders")
            return count

        self.cur.execute(query)
        updated = self.cur.rowcount
        self.conn.commit()
        logger.info(f"Updated {updated:,} horse breeders")
        return updated

    # ====================================================================================
    # PHASE 2: STATISTICS POPULATION
    # ====================================================================================

    def populate_statistics(self, table_name: str) -> int:
        """
        Populate statistics for entity tables using existing statistics workers

        Args:
            table_name: Table to populate (ra_mst_jockeys, ra_mst_trainers, ra_mst_owners,
                       ra_mst_sires, ra_mst_dams, ra_mst_damsires)
        """
        entity_type = table_name.replace('ra_mst_', '')

        if entity_type in ['jockeys', 'trainers', 'owners']:
            script_path = f'scripts/statistics_workers/calculate_{entity_type}_statistics.py'
        elif entity_type in ['sires', 'dams', 'damsires']:
            script_path = 'scripts/populate_pedigree_statistics.py'
        else:
            logger.warning(f"No statistics script available for {table_name}")
            return 0

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would run statistics script: {script_path}")
            return 0

        # Check if script exists
        if not os.path.exists(script_path):
            logger.warning(f"Statistics script not found: {script_path}")
            return 0

        # Import and run the appropriate script
        logger.info(f"Running statistics calculation for {table_name}...")

        if entity_type in ['sires', 'dams', 'damsires']:
            # For pedigree statistics, run the unified script
            import subprocess
            result = subprocess.run(
                ['python3', script_path, '--table', entity_type],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"Successfully populated {table_name} statistics")
                return 1
            else:
                logger.error(f"Error populating {table_name} statistics: {result.stderr}")
                return 0
        else:
            # For people statistics, the scripts are already available
            logger.info(f"Statistics for {table_name} should be run via existing workers")
            logger.info(f"Use: python3 {script_path}")
            return 0

    # ====================================================================================
    # PHASE 3: TABLE PROCESSING
    # ====================================================================================

    def process_table(self, table_name: str, columns: List[Dict]) -> Dict:
        """
        Process a single table and populate missing data

        Args:
            table_name: Name of the table to process
            columns: List of column definitions from inventory

        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"Processing table: {table_name}")
        logger.info(f"{'='*100}")

        table_stats = {
            'table': table_name,
            'columns_processed': 0,
            'records_updated': 0,
            'errors': 0
        }

        # Group columns by data source
        by_source = {}
        for col in columns:
            source = col['data_source']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(col)

        logger.info(f"Found {len(columns)} columns from {len(by_source)} data sources")

        # Process each data source type
        for source, cols in by_source.items():
            logger.info(f"\n  Processing {len(cols)} columns from: {source}")

            # Skip system-generated and already-populated columns
            if source in ['System Generated - Auto-increment', 'System Timestamp',
                         'System Generated - Composite']:
                logger.info(f"    Skipping system-generated columns")
                continue

            # Skip external/API sources (will be handled by existing fetchers)
            if any(keyword in source for keyword in ['Racing API', 'Odds Worker', 'External']):
                logger.info(f"    Skipping API/external source (handled by fetchers)")
                continue

            # Skip not implemented features
            if 'Not Implemented' in source or 'Future Feature' in source:
                logger.info(f"    Skipping not-implemented features")
                continue

            # Process calculated fields
            if 'Calculated' in source:
                for col in cols:
                    if col['pct_populated'] == 100:
                        logger.info(f"    ✓ {col['column']}: Already 100% populated")
                        continue

                    # Handle specific calculated fields
                    if table_name == 'ra_mst_horses' and col['column'] == 'age':
                        updated = self.populate_horse_age()
                        table_stats['records_updated'] += updated
                        table_stats['columns_processed'] += 1

                    elif table_name.startswith('ra_mst_') and 'total_' in col['column']:
                        # Statistics fields - will be handled by statistics scripts
                        logger.info(f"    • {col['column']}: Statistics field (use populate_pedigree_statistics.py)")

                    else:
                        logger.info(f"    • {col['column']}: Calculated field (implementation needed)")

            # Process database migrations
            elif 'Database Migration' in source or 'Database - Pedigree Extraction' in source:
                for col in cols:
                    if col['pct_populated'] == 100:
                        logger.info(f"    ✓ {col['column']}: Already 100% populated")
                        continue

                    if table_name == 'ra_mst_horses' and col['column'] == 'breeder':
                        updated = self.populate_horse_breeder()
                        table_stats['records_updated'] += updated
                        table_stats['columns_processed'] += 1
                    else:
                        logger.info(f"    • {col['column']}: Database migration (check migrations/ folder)")

        self.stats['tables_processed'] += 1
        return table_stats

    # ====================================================================================
    # MAIN EXECUTION
    # ====================================================================================

    def run(self, inventory: ColumnInventory, target_table: Optional[str] = None,
            phase: Optional[str] = None):
        """
        Main execution method

        Args:
            inventory: Loaded column inventory
            target_table: Optional specific table to process
            phase: Optional specific phase to run
        """
        logger.info("\n" + "="*100)
        logger.info("COMPREHENSIVE DATABASE POPULATION")
        logger.info("="*100)
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*100 + "\n")

        self.connect()

        try:
            # Determine which tables to process
            if target_table:
                if target_table not in inventory.tables:
                    logger.error(f"Table '{target_table}' not found in inventory")
                    return
                tables_to_process = {target_table: inventory.tables[target_table]}
            else:
                tables_to_process = inventory.tables

            # PHASE 1: Simple calculated fields (if not restricted to other phase)
            if phase is None or phase == 'calculated':
                logger.info("\n" + "="*100)
                logger.info("PHASE 1: SIMPLE CALCULATED FIELDS")
                logger.info("="*100 + "\n")

                # Horse age
                if target_table is None or target_table == 'ra_mst_horses':
                    updated = self.populate_horse_age()
                    self.stats['records_updated'] += updated
                    if updated > 0:
                        self.stats['columns_updated'] += 1

            # PHASE 2: Simple migrations (if not restricted to other phase)
            if phase is None or phase == 'simple_migrations':
                logger.info("\n" + "="*100)
                logger.info("PHASE 2: SIMPLE DATABASE MIGRATIONS")
                logger.info("="*100 + "\n")

                # Horse breeder
                if target_table is None or target_table == 'ra_mst_horses':
                    updated = self.populate_horse_breeder()
                    self.stats['records_updated'] += updated
                    if updated > 0:
                        self.stats['columns_updated'] += 1

            # PHASE 3: Table-by-table processing
            if phase is None:
                logger.info("\n" + "="*100)
                logger.info("PHASE 3: TABLE-BY-TABLE PROCESSING")
                logger.info("="*100 + "\n")

                for table_name in sorted(tables_to_process.keys()):
                    columns = tables_to_process[table_name]
                    table_stats = self.process_table(table_name, columns)
                    self.stats['columns_updated'] += table_stats['columns_processed']
                    self.stats['records_updated'] += table_stats['records_updated']
                    self.stats['errors'] += table_stats['errors']

            # Print final summary
            self.print_summary()

        except Exception as e:
            logger.error(f"Fatal error during population: {e}", exc_info=True)
            self.stats['errors'] += 1
        finally:
            self.close()

    def print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "="*100)
        logger.info("EXECUTION SUMMARY")
        logger.info("="*100)
        logger.info(f"Tables processed: {self.stats['tables_processed']}")
        logger.info(f"Columns updated: {self.stats['columns_updated']}")
        logger.info(f"Records updated: {self.stats['records_updated']:,}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*100 + "\n")

# ====================================================================================
# MAIN ENTRY POINT
# ====================================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Comprehensive database population script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run to see what would be done
  python3 scripts/populate_all_database_columns.py --dry-run

  # Process only ra_mst_horses table
  python3 scripts/populate_all_database_columns.py --table ra_mst_horses

  # Run only calculated fields phase
  python3 scripts/populate_all_database_columns.py --phase calculated

  # Run live (make actual changes)
  python3 scripts/populate_all_database_columns.py
        """
    )

    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--table', type=str,
                       help='Process only specific table')
    parser.add_argument('--phase', type=str,
                       choices=['calculated', 'simple_migrations'],
                       help='Run specific phase only')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed progress')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load inventory
    try:
        inventory = ColumnInventory(INVENTORY_PATH)
    except FileNotFoundError:
        logger.error(f"Column inventory not found: {INVENTORY_PATH}")
        logger.error("Please run the column inventory generation script first")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load column inventory: {e}")
        sys.exit(1)

    # Create populator and run
    populator = DatabasePopulator(dry_run=args.dry_run)
    populator.run(inventory, target_table=args.table, phase=args.phase)

    # Exit with error code if there were errors
    sys.exit(1 if populator.stats['errors'] > 0 else 0)

if __name__ == '__main__':
    main()
