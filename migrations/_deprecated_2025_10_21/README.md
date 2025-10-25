# Deprecated Migrations - 2025-10-21

**Date Deprecated:** 2025-10-21
**Reason:** Migration cleanup - old/superseded migrations moved
**Files Moved:** 38 migration files

---

## Why These Migrations Were Deprecated

These migrations were either:
1. **Superseded** by later migrations that consolidated multiple changes
2. **Experimental** backfill attempts that didn't work or were replaced
3. **Staged migrations** that were combined into simpler migrations
4. **Duplicate** migrations with different approaches to the same problem
5. **Manual fixes** that are no longer needed

---

## Current Active Migrations

**Location:** `/migrations/` (parent directory)

**Active Migrations (11 files):**
1. `001_create_metadata_tracking.sql` - Initial metadata tracking system
2. `019_create_ra_lineage_table.sql` - Lineage table (may be superseded by 025)
3. `020_create_ancestor_stats_tables.sql` - Sires/dams/damsires statistics tables
4. `021_add_course_coordinates.sql` - Course latitude/longitude coordinates
5. `022_rename_tables_to_mst.sql` - Rename tables to mst_ prefix (CANONICAL)
6. `023_add_missing_columns.sql` - Add missing columns to various tables
7. `024_fix_off_time_nullable.sql` - Fix off_time field to be nullable
8. `025_denormalize_pedigree_ids.sql` - Add sire_id, dam_id, damsire_id to ra_mst_horses
9. `026_populate_pedigree_names.sql` - Populate pedigree names from IDs
10. `add_enhanced_statistics_columns.sql` - Add enhanced statistics columns
11. `remove_redundant_active_last_30d.sql` - Remove redundant active_last_30d columns

---

## Deprecated Migrations by Category

### Early Schema Fixes (002-009) - 9 files

**Superseded by:** Later consolidated migrations (018, 022, 023)

- `002_database_fixes.sql` - Early database fixes
- `003_add_missing_fields.sql` - Early field additions
- `005_add_position_fields_to_runners.sql` - Position fields (replaced by 011)
- `006_add_finishing_time_field.sql` - Finishing time (replaced by 011)
- `007_add_entity_table_enhancements.sql` - Entity enhancements
- `007_drop_unused_tables.sql` - Cleanup attempt
- `007_entity_statistics_RUNME.sql` - Early statistics
- `008_add_pedigree_and_horse_fields.sql` - Pedigree fields (replaced by 025)
- `009_remove_unused_columns.sql` - Column removal

### Region and Runner Field Additions (010-011) - 3 files

**Superseded by:** 023_add_missing_columns.sql and 025_denormalize_pedigree_ids.sql

- `010_add_region_to_pedigree.sql` - Region addition
- `010_add_region_to_pedigree_simple.sql` - Duplicate/simpler version
- `011_add_missing_runner_fields.sql` - Runner fields

### Backfill Attempts (012-015) - 6 files

**Status:** Experimental backfill migrations that didn't work or were replaced

**Note:** Backfills are now handled by Python scripts in `/scripts/`, not SQL migrations

- `012_backfill_runners_BATCHED.sql` - Batched backfill attempt
- `012_backfill_runners_from_api_data.sql` - API data backfill attempt
- `013_backfill_SMALLEST_BATCH.sql` - Small batch backfill
- `013_backfill_SMALLEST_BATCH_FIXED.sql` - Fixed version
- `014_backfill_ALL_EXTENDED_TIMEOUT.sql` - Extended timeout attempt
- `015_backfill_using_functions.sql` - Function-based backfill

### Schema Cleanup (016-017) - 4 files

**Superseded by:** 018 series and later migrations

- `016_drop_duplicate_columns.sql` - Duplicate column cleanup
- `016a_drop_racing_api_columns.sql` - Racing API column cleanup
- `017_create_ra_results_table.sql` - Results table creation
- `017a_fix_ra_results_dist_f_type.sql` - Distance field type fix

### Migration 018 Series (13 files)

**Superseded by:** 022_rename_tables_to_mst.sql and 023_add_missing_columns.sql

**Note:** Migration 018 was attempted in multiple forms (consolidated, staged, safe) but was ultimately replaced by simpler migrations

**Consolidated Attempts:**
- `018_FINAL_consolidate_and_complete.sql` - Final consolidation attempt
- `018_REVISED_standardize_and_complete_schema.sql` - Revised version
- `018_SAFE_complete_schema.sql` - Safe version
- `018_add_all_missing_runner_fields.sql` - Runner fields addition

**Staged Attempts:**
- `018_STAGE_1A_drop_first.sql` - Drop stage 1A
- `018_STAGE_1B_drop_second.sql` - Drop stage 1B
- `018_STAGE_1C_drop_third.sql` - Drop stage 1C
- `018_STAGE_1D_drop_fourth.sql` - Drop stage 1D
- `018_STAGE_1E_drop_fifth.sql` - Drop stage 1E
- `018_STAGE_1_drop_duplicates.sql` - Drop duplicates
- `018_STAGE_2_rename_columns.sql` - Rename columns
- `018_STAGE_3_add_new_columns.sql` - Add new columns
- `018_STAGE_4_add_indexes.sql` - Add indexes

### Manual Fixes and Utilities (5 files)

**Status:** One-time fixes or utilities no longer needed

- `022_rename_master_tables.sql` - Duplicate of 022_rename_tables_to_mst.sql
- `APPLY_FIXES_NOW.sql` - Manual fix script
- `RUN_STATISTICS_UPDATE.sql` - Manual statistics update
- `SETUP_SUPABASE_CRON.sql` - Cron setup (now handled differently)
- `drop_ml_runner_history.sql` - ML runner history cleanup

---

## Migration History Timeline

```
001 → Initial metadata tracking
002-009 → Early schema fixes and enhancements
010-011 → Region and runner field additions
012-015 → Backfill attempts (experimental)
016-017 → Schema cleanup
018 series → Consolidation attempts (staged and all-in-one)
019 → Lineage table creation
020 → Ancestor statistics tables (sires, dams, damsires)
021 → Course coordinates
022 → Table renaming to mst_ prefix ✅ CANONICAL
023 → Missing columns addition ✅ CURRENT
024 → Off time nullable fix ✅ CURRENT
025 → Denormalize pedigree IDs ✅ CURRENT
026 → Populate pedigree names ✅ CURRENT
```

---

## Migration Strategy Going Forward

**Lessons Learned:**

1. **Avoid large consolidation migrations** - Break changes into smaller, focused migrations
2. **Don't use SQL for backfills** - Use Python scripts with proper error handling and resume capability
3. **Test migrations thoroughly** - Use staged rollout with SAFE versions first
4. **Number migrations sequentially** - Avoid multiple versions with same number
5. **Document superseded migrations** - Move to deprecated directory with explanation

**Current Best Practices:**

- One migration per logical change
- Clear naming convention: `NNN_description.sql`
- Test in development before production
- Keep migrations idempotent where possible
- Use Python scripts for data backfills

---

## Statistics

**Before Cleanup:** 49 migration files
**After Cleanup:** 11 migration files (78% reduction)

**Deprecated:** 38 migration files
**Active:** 11 migration files

---

## Migration Guide

**If you need to:**

- **Apply current migrations:** See `/migrations/` parent directory
- **Understand migration history:** Review this directory for context
- **Create new migrations:** Follow current best practices (see above)
- **Backfill data:** Use Python scripts in `/scripts/`, not SQL migrations

**If you find useful SQL in deprecated migrations:**
- Extract the specific SQL needed
- Create a new properly-numbered migration
- Test thoroughly before applying

---

**Deprecation Date:** 2025-10-21
**Deprecated By:** Migration cleanup and organization
**Status:** Preserved for historical reference only
**Use:** Reference only - DO NOT apply these migrations
