#!/usr/bin/env python3
"""
Update Column Inventory with Population Sources
================================================

Updates /docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json with:
- Pedigree statistics agent column mappings
- Population script references
- Current population status from database

Run this after:
- Adding new tables/columns
- Creating new population scripts
- Running population operations
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('update_inventory')

# Pedigree statistics column mappings (ra_mst_sires, ra_mst_dams, ra_mst_damsires)
PEDIGREE_COLUMNS = {
    # Basic statistics
    "total_runners": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "COUNT(ra_runners) WHERE horse_id IN (SELECT id FROM ra_mst_horses WHERE sire_id/dam_id/damsire_id = entity.id)",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Total number of race starts by all progeny",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "total_wins": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "COUNT(ra_runners) WHERE position = 1 AND horse_id IN progeny",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Total wins by all progeny",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "total_places_2nd": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "COUNT(ra_runners) WHERE position = 2 AND horse_id IN progeny",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Total 2nd place finishes by all progeny",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "total_places_3rd": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "COUNT(ra_runners) WHERE position = 3 AND horse_id IN progeny",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Total 3rd place finishes by all progeny",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "overall_win_percent": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "(total_wins / total_runners * 100)",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Win percentage across all progeny",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "overall_ae_index": {
        "data_source": "Database Calculation - Pedigree Agent (AE Index)",
        "api_endpoint": "N/A - Advanced calculation",
        "field_path": "(actual_wins / expected_wins * 100) based on class distribution",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Actual vs Expected index comparing performance to baseline win rates by class",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "best_class": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "Class with most wins from progeny",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Race class where progeny perform best",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "best_class_ae": {
        "data_source": "Database Calculation - Pedigree Agent (AE Index)",
        "api_endpoint": "N/A - Advanced calculation",
        "field_path": "AE index for best_class",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - AE index for the best performing class",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "best_distance": {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": "Distance (furlongs) with most wins from progeny",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Race distance where progeny perform best",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "best_distance_ae": {
        "data_source": "Database Calculation - Pedigree Agent (AE Index)",
        "api_endpoint": "N/A - Advanced calculation",
        "field_path": "AE index for best_distance",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - AE index for the best performing distance",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "analysis_last_updated": {
        "data_source": "System Timestamp - Pedigree Agent",
        "api_endpoint": "N/A - Set by script",
        "field_path": "datetime.now() when calculation runs",
        "implementation_notes": "Set by pedigree_statistics_agent.py - Timestamp of last statistics calculation",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    },
    "data_quality_score": {
        "data_source": "Database Calculation - Pedigree Agent (Quality Score)",
        "api_endpoint": "N/A - Calculated score 0.00-1.00",
        "field_path": "Weighted score based on data completeness: runners(0.20) + class_breakdown(0.30) + distance_breakdown(0.30) + ae_indices(0.20)",
        "implementation_notes": "Calculated by pedigree_statistics_agent.py - Data quality/completeness score",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
}

# Add class breakdown columns (1-3)
for i in range(1, 4):
    PEDIGREE_COLUMNS[f"class_{i}_name"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"Top {i} class by wins (e.g., 'Class 3')",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - {i}{'st' if i==1 else 'nd' if i==2 else 'rd'} best performing class name",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"class_{i}_runners"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"COUNT(ra_runners) WHERE race.class = class_{i}_name",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Total runners in class_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"class_{i}_wins"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"COUNT(ra_runners) WHERE position = 1 AND race.class = class_{i}_name",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Total wins in class_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"class_{i}_win_percent"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"(class_{i}_wins / class_{i}_runners * 100)",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Win percentage in class_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"class_{i}_ae"] = {
        "data_source": "Database Calculation - Pedigree Agent (AE Index)",
        "api_endpoint": "N/A - Advanced calculation",
        "field_path": f"(actual_wins / expected_wins * 100) for class_{i}",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - AE index for class_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }

# Add distance breakdown columns (1-3)
for i in range(1, 4):
    PEDIGREE_COLUMNS[f"distance_{i}_name"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"Top {i} distance by wins (e.g., '7.0f')",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - {i}{'st' if i==1 else 'nd' if i==2 else 'rd'} best performing distance",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"distance_{i}_runners"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"COUNT(ra_runners) WHERE race.distance_f = distance_{i}_name",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Total runners at distance_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"distance_{i}_wins"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"COUNT(ra_runners) WHERE position = 1 AND race.distance_f = distance_{i}_name",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Total wins at distance_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"distance_{i}_win_percent"] = {
        "data_source": "Database Calculation - Pedigree Agent",
        "api_endpoint": "N/A - Calculated from database",
        "field_path": f"(distance_{i}_wins / distance_{i}_runners * 100)",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - Win percentage at distance_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }
    PEDIGREE_COLUMNS[f"distance_{i}_ae"] = {
        "data_source": "Database Calculation - Pedigree Agent (AE Index)",
        "api_endpoint": "N/A - Advanced calculation",
        "field_path": f"(actual_wins / expected_wins * 100) for distance_{i}",
        "implementation_notes": f"Calculated by pedigree_statistics_agent.py - AE index for distance_{i}",
        "script": "scripts/population_workers/pedigree_statistics_agent.py"
    }


def update_inventory():
    """Update the column inventory JSON with current data"""
    inventory_path = "/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json"

    logger.info("Loading column inventory...")
    with open(inventory_path, 'r') as f:
        data = json.load(f)

    columns = data['columns']
    updated_count = 0

    # Update pedigree table columns
    pedigree_tables = ['ra_mst_sires', 'ra_mst_dams', 'ra_mst_damsires']

    for column_entry in columns:
        table = column_entry['table']
        column = column_entry['column']

        # Update pedigree statistics columns
        if table in pedigree_tables and column in PEDIGREE_COLUMNS:
            mapping = PEDIGREE_COLUMNS[column]
            column_entry['data_source'] = mapping['data_source']
            column_entry['api_endpoint'] = mapping['api_endpoint']
            column_entry['field_path'] = mapping['field_path']
            column_entry['implementation_notes'] = mapping['implementation_notes']
            if 'script' in mapping:
                column_entry['population_script'] = mapping['script']
            updated_count += 1
            logger.info(f"Updated: {table}.{column}")

    # Update metadata
    data['last_updated'] = datetime.now().isoformat()
    data['total_pedigree_columns_updated'] = updated_count

    # Save
    logger.info(f"Saving updated inventory ({updated_count} columns updated)...")
    with open(inventory_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"✅ Inventory updated successfully")
    logger.info(f"   Updated columns: {updated_count}")
    logger.info(f"   File: {inventory_path}")


def verify_coverage():
    """Verify that all pedigree columns are documented"""
    inventory_path = "/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json"

    with open(inventory_path, 'r') as f:
        data = json.load(f)

    columns = data['columns']
    pedigree_tables = ['ra_mst_sires', 'ra_mst_dams', 'ra_mst_damsires']

    logger.info("\n" + "=" * 80)
    logger.info("PEDIGREE COLUMN COVERAGE VERIFICATION")
    logger.info("=" * 80)

    for table in pedigree_tables:
        table_columns = [c for c in columns if c['table'] == table]
        pedigree_cols = [c for c in table_columns if c['column'] in PEDIGREE_COLUMNS]

        logger.info(f"\n{table}:")
        logger.info(f"  Total columns: {len(table_columns)}")
        logger.info(f"  Pedigree stats columns: {len(pedigree_cols)}")
        logger.info(f"  Coverage: {len(pedigree_cols)}/{len(PEDIGREE_COLUMNS)} ({len(pedigree_cols)/len(PEDIGREE_COLUMNS)*100:.1f}%)")

        # Check for missing
        missing = [c['column'] for c in table_columns if c['column'] in PEDIGREE_COLUMNS and c.get('data_source', '').startswith('Not Implemented')]
        if missing:
            logger.warning(f"  Missing mappings: {missing}")


def main():
    logger.info("=" * 80)
    logger.info("UPDATING COLUMN INVENTORY")
    logger.info("=" * 80)

    update_inventory()
    verify_coverage()

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
