#!/usr/bin/env python3
"""
Metadata Tracker - Track data collection updates and statistics

Maintains a metadata table with:
- Last update timestamp for each table
- Number of records created/updated
- Success/failure status
- Update history
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from supabase import Client

logger = logging.getLogger(__name__)


class MetadataTracker:
    """Track and manage data collection metadata"""

    # Metadata table name
    METADATA_TABLE = 'ra_collection_metadata'

    def __init__(self, supabase_client: Client):
        """
        Initialize metadata tracker

        Args:
            supabase_client: Supabase client instance
        """
        self.client = supabase_client

    def record_update(
        self,
        table_name: str,
        operation: str,
        records_processed: int,
        records_inserted: int = 0,
        records_updated: int = 0,
        records_skipped: int = 0,
        status: str = 'success',
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Record an update operation to metadata table

        Args:
            table_name: Name of the table that was updated
            operation: Type of operation (e.g., 'initialization', 'daily_update', 'live_update')
            records_processed: Total number of records processed
            records_inserted: Number of new records inserted
            records_updated: Number of existing records updated
            records_skipped: Number of records skipped
            status: Status of the operation ('success', 'partial', 'failed')
            error_message: Error message if operation failed
            metadata: Additional metadata (e.g., date range, chunk info)

        Returns:
            True if metadata was recorded successfully
        """
        try:
            record = {
                'table_name': table_name,
                'operation': operation,
                'records_processed': records_processed,
                'records_inserted': records_inserted,
                'records_updated': records_updated,
                'records_skipped': records_skipped,
                'status': status,
                'error_message': error_message,
                'metadata': metadata or {},
                'updated_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }

            self.client.table(self.METADATA_TABLE).insert(record).execute()
            logger.info(f"Recorded metadata for {table_name}: {operation} - {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to record metadata: {e}")
            return False

    def get_last_update(self, table_name: str) -> Optional[Dict]:
        """
        Get the last update record for a table

        Args:
            table_name: Name of the table

        Returns:
            Latest update record or None
        """
        try:
            result = self.client.table(self.METADATA_TABLE).select('*').eq(
                'table_name', table_name
            ).order('created_at', desc=True).limit(1).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Failed to get last update for {table_name}: {e}")
            return None

    def get_update_history(
        self,
        table_name: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get update history with optional filters

        Args:
            table_name: Filter by table name
            operation: Filter by operation type
            limit: Maximum number of records to return

        Returns:
            List of update records
        """
        try:
            query = self.client.table(self.METADATA_TABLE).select('*')

            if table_name:
                query = query.eq('table_name', table_name)
            if operation:
                query = query.eq('operation', operation)

            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get update history: {e}")
            return []

    def get_table_summary(self) -> Dict[str, Dict]:
        """
        Get summary of last updates for all tables

        Returns:
            Dictionary mapping table names to their last update info
        """
        tables = [
            'ra_courses', 'ra_bookmakers', 'ra_mst_races',
            'ra_mst_runners', 'ra_horses', 'ra_jockeys', 'ra_trainers', 'ra_owners'
        ]

        summary = {}
        for table in tables:
            last_update = self.get_last_update(table)
            if last_update:
                summary[table] = {
                    'last_updated': last_update.get('updated_at'),
                    'operation': last_update.get('operation'),
                    'records_inserted': last_update.get('records_inserted', 0),
                    'records_updated': last_update.get('records_updated', 0),
                    'status': last_update.get('status'),
                    'error_message': last_update.get('error_message')
                }
            else:
                summary[table] = {
                    'last_updated': None,
                    'operation': None,
                    'records_inserted': 0,
                    'records_updated': 0,
                    'status': 'never_updated',
                    'error_message': None
                }

        return summary

    def get_statistics(self, table_name: str, days: int = 30) -> Dict:
        """
        Get statistics for a table over a period

        Args:
            table_name: Name of the table
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        try:
            # Get records from last N days
            from_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            result = self.client.table(self.METADATA_TABLE).select('*').eq(
                'table_name', table_name
            ).gte('created_at', from_date).execute()

            if not result.data:
                return {
                    'total_updates': 0,
                    'total_inserted': 0,
                    'total_updated': 0,
                    'success_rate': 0.0
                }

            records = result.data
            total_updates = len(records)
            total_inserted = sum(r.get('records_inserted', 0) for r in records)
            total_updated = sum(r.get('records_updated', 0) for r in records)
            successful = sum(1 for r in records if r.get('status') == 'success')
            success_rate = (successful / total_updates * 100) if total_updates > 0 else 0

            return {
                'total_updates': total_updates,
                'total_inserted': total_inserted,
                'total_updated': total_updated,
                'success_rate': success_rate,
                'period_days': days
            }

        except Exception as e:
            logger.error(f"Failed to get statistics for {table_name}: {e}")
            return {
                'total_updates': 0,
                'total_inserted': 0,
                'total_updated': 0,
                'success_rate': 0.0
            }

    def ensure_metadata_table(self) -> bool:
        """
        Ensure metadata table exists (create if not)
        Note: This should be run manually or via migration, not automatically

        Returns:
            True if table exists or was created
        """
        # This is informational - actual table creation should be done via Supabase migration
        logger.info(f"Metadata table name: {self.METADATA_TABLE}")
        logger.info("To create, run SQL migration in Supabase:")
        logger.info("""
        CREATE TABLE IF NOT EXISTS ra_collection_metadata (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            records_processed INTEGER DEFAULT 0,
            records_inserted INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            records_skipped INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error_message TEXT,
            metadata JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX idx_metadata_table_name ON ra_collection_metadata(table_name);
        CREATE INDEX idx_metadata_created_at ON ra_collection_metadata(created_at);
        CREATE INDEX idx_metadata_status ON ra_collection_metadata(status);
        """)
        return True
