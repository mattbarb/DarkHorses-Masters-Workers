-- Migration 019: Create ra_lineage table for comprehensive lineage tracking
-- Date: 2025-10-18
-- Purpose: Link pedigree data to runner_id with unlimited generations support

-- =============================================================================
-- STAGE 1: Create ra_lineage table
-- =============================================================================

CREATE TABLE IF NOT EXISTS ra_lineage (
    -- Primary key
    lineage_id VARCHAR PRIMARY KEY,  -- Generated: runner_id_generation_type

    -- Foreign keys
    runner_id VARCHAR NOT NULL,      -- FK to ra_runners
    horse_id VARCHAR NOT NULL,       -- The horse in this race

    -- Lineage details
    generation INT NOT NULL,         -- 1=parent, 2=grandparent, 3=great-grand, etc.
    lineage_path VARCHAR NOT NULL,   -- 'sire' | 'dam' | 'sire.sire' | 'sire.dam' | 'dam.sire' | 'dam.dam', etc.
    relation_type VARCHAR NOT NULL,  -- 'sire' | 'dam' | 'grandsire_paternal' | 'granddam_paternal' | 'grandsire_maternal' | 'granddam_maternal', etc.

    -- Ancestor details
    ancestor_horse_id VARCHAR,       -- ID of the ancestor horse (can link to ra_horses)
    ancestor_name VARCHAR,           -- Name (e.g., "Galileo (IRE)")
    ancestor_region VARCHAR,         -- Breeding region
    ancestor_dob DATE,               -- Date of birth if known

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE (runner_id, lineage_path)  -- One record per ancestor per runner
);

-- Add comment
COMMENT ON TABLE ra_lineage IS 'Comprehensive lineage/pedigree tracking linked to runner_id. Supports unlimited generations with flexible querying via lineage_path and relation_type.';

-- =============================================================================
-- STAGE 2: Create indexes for performance
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_lineage_runner_id ON ra_lineage(runner_id);
CREATE INDEX IF NOT EXISTS idx_lineage_horse_id ON ra_lineage(horse_id);
CREATE INDEX IF NOT EXISTS idx_lineage_ancestor_id ON ra_lineage(ancestor_horse_id);
CREATE INDEX IF NOT EXISTS idx_lineage_generation ON ra_lineage(generation);
CREATE INDEX IF NOT EXISTS idx_lineage_relation ON ra_lineage(relation_type);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_lineage_runner_generation ON ra_lineage(runner_id, generation);
CREATE INDEX IF NOT EXISTS idx_lineage_ancestor_relation ON ra_lineage(ancestor_horse_id, relation_type);

-- =============================================================================
-- NOTES
-- =============================================================================
--
-- Design decisions:
-- 1. lineage_id format: {runner_id}_{generation}_{lineage_path}
--    Example: "rac_123_hrs_456_1_sire", "rac_123_hrs_456_2_sire.sire"
--
-- 2. lineage_path examples:
--    - Generation 1: "sire", "dam"
--    - Generation 2: "sire.sire", "sire.dam", "dam.sire", "dam.dam"
--    - Generation 3: "sire.sire.sire", "sire.sire.dam", etc.
--
-- 3. relation_type examples:
--    - Generation 1: "sire", "dam"
--    - Generation 2: "grandsire_paternal", "granddam_paternal", "grandsire_maternal", "granddam_maternal"
--    - Generation 3: "great_grandsire_paternal_paternal", etc.
--
-- 4. Current API data provides 3 generations:
--    - Horse → sire/dam → damsire (maternal grandsire)
--    - Note: API provides damsire but not full 2nd generation (4 grandparents)
--    - This design supports extending to more generations if API provides it
--
-- 5. Data sources:
--    - /v1/racecards/pro: provides sire_id, dam_id, damsire_id for each runner
--    - /v1/results: provides same pedigree data
--    - /v1/horses/{id}/pro: provides complete pedigree for individual horses
--    - ra_horse_pedigree: existing canonical pedigree data
--
-- 6. Backfill strategy:
--    - Populate from existing ra_runners + ra_horse_pedigree
--    - For each runner, extract lineage path and create records
--    - Update fetchers to populate ra_lineage on new runners
--
-- =============================================================================
