-- Migration 030: Add region columns to pedigree statistics tables
-- Date: 2025-10-23
-- Purpose: Capture region data for sires/dams/damsires to enable more accurate horse_id matching
-- Source: Racing API provides sire_region, dam_region, damsire_region in racecard runners

-- Add region column to ra_mst_sires
ALTER TABLE ra_mst_sires
ADD COLUMN IF NOT EXISTS region VARCHAR(10);

-- Add region column to ra_mst_dams
ALTER TABLE ra_mst_dams
ADD COLUMN IF NOT EXISTS region VARCHAR(10);

-- Add region column to ra_mst_damsires
ALTER TABLE ra_mst_damsires
ADD COLUMN IF NOT EXISTS region VARCHAR(10);

-- Add comments
COMMENT ON COLUMN ra_mst_sires.region IS 'Region code for sire (e.g., GB, IRE, FR) - from Racing API sire_region field';
COMMENT ON COLUMN ra_mst_dams.region IS 'Region code for dam (e.g., GB, IRE, FR) - from Racing API dam_region field';
COMMENT ON COLUMN ra_mst_damsires.region IS 'Region code for damsire (e.g., GB, IRE, FR) - from Racing API damsire_region field';

-- Create indexes for efficient matching queries
CREATE INDEX IF NOT EXISTS idx_sires_name_region ON ra_mst_sires(name, region);
CREATE INDEX IF NOT EXISTS idx_dams_name_region ON ra_mst_dams(name, region);
CREATE INDEX IF NOT EXISTS idx_damsires_name_region ON ra_mst_damsires(name, region);

-- Note: Region enables more accurate matching to ra_mst_horses
-- Example: "Masked Marvel (GB)" with region="GB" is more specific than name-only match
