-- Migration: Create Metadata Tracking Table
-- Purpose: Track data collection operations, update history, and success rates
-- Date: 2025-10-06

-- Create metadata tracking table
CREATE TABLE IF NOT EXISTS ra_collection_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    error_message TEXT,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_metadata_table_name
    ON ra_collection_metadata(table_name);

CREATE INDEX IF NOT EXISTS idx_metadata_created_at
    ON ra_collection_metadata(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_metadata_status
    ON ra_collection_metadata(status);

CREATE INDEX IF NOT EXISTS idx_metadata_operation
    ON ra_collection_metadata(operation);

CREATE INDEX IF NOT EXISTS idx_metadata_table_created
    ON ra_collection_metadata(table_name, created_at DESC);

-- Add table comment
COMMENT ON TABLE ra_collection_metadata IS
'Tracks data collection operations: when tables were updated, how many records, success/failure status';

-- Add column comments
COMMENT ON COLUMN ra_collection_metadata.table_name IS
'Name of the table that was updated (e.g., ra_results, ra_races)';

COMMENT ON COLUMN ra_collection_metadata.operation IS
'Type of operation (e.g., initialization, daily_update, live_update, reference_update)';

COMMENT ON COLUMN ra_collection_metadata.records_processed IS
'Total number of records processed in this operation';

COMMENT ON COLUMN ra_collection_metadata.records_inserted IS
'Number of new records inserted';

COMMENT ON COLUMN ra_collection_metadata.records_updated IS
'Number of existing records updated';

COMMENT ON COLUMN ra_collection_metadata.records_skipped IS
'Number of records skipped (duplicates, errors, etc.)';

COMMENT ON COLUMN ra_collection_metadata.status IS
'Status of the operation: success, partial, or failed';

COMMENT ON COLUMN ra_collection_metadata.error_message IS
'Error message if the operation failed';

COMMENT ON COLUMN ra_collection_metadata.metadata IS
'Additional metadata (JSON): date ranges, chunks, API parameters, etc.';

-- Create a view for easy querying
CREATE OR REPLACE VIEW v_latest_table_updates AS
SELECT DISTINCT ON (table_name)
    table_name,
    operation,
    records_inserted,
    records_updated,
    status,
    created_at as last_updated
FROM ra_collection_metadata
ORDER BY table_name, created_at DESC;

COMMENT ON VIEW v_latest_table_updates IS
'View showing the most recent update for each table';

-- Grant permissions (adjust as needed for your setup)
-- Uncomment if using RLS or specific roles
-- GRANT SELECT, INSERT ON ra_collection_metadata TO authenticated;
-- GRANT SELECT ON v_latest_table_updates TO authenticated;

-- Example: Insert a test record
INSERT INTO ra_collection_metadata (
    table_name,
    operation,
    records_processed,
    records_inserted,
    records_updated,
    records_skipped,
    status,
    metadata
) VALUES (
    'ra_courses',
    'migration_test',
    101,
    101,
    0,
    0,
    'success',
    '{"note": "Migration test record", "version": "1.0"}'::jsonb
);

-- Verify the table was created
SELECT
    'Metadata table created successfully' as message,
    COUNT(*) as test_records
FROM ra_collection_metadata;
