#!/usr/bin/env python3
"""
Simple Pedigree Statistics Calculator
======================================

Calculates statistics for ra_mst_sires, ra_mst_dams, and ra_mst_damsires tables
using progeny performance data from ra_mst_runners + ra_races.

Matches ACTUAL table schema with columns:
- total_runners, total_wins, total_places_2nd, total_places_3rd
- overall_win_percent, overall_ae_index
- best_class, best_distance
- class breakdowns (class_1/2/3_name, runners, wins, win_percent, ae)
- distance breakdowns (distance_1/2/3_name, runners, wins, win_percent, ae)

Usage:
    # Test mode (10 entities)
    python3 scripts/populate_pedigree_statistics.py --test

    # Full run (all sires, dams, damsires from 2015)
    python3 scripts/populate_pedigree_statistics.py

    # Specific table only
    python3 scripts/populate_pedigree_statistics.py --table sires
"""

import sys
import os
from datetime import datetime
from collections import Counter
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('populate_pedigree_statistics')


def calculate_and_update_sires(db: SupabaseReferenceClient, limit: int = None):
    """Calculate and update sire statistics"""
    logger.info("=" * 80)
    logger.info("CALCULATING SIRE STATISTICS")
    logger.info("=" * 80)

    # Get all sires (from horses that have offspring)
    query = db.client.table('ra_mst_horses').select('sire_id, sire_name').neq('sire_id', 'null')
    if limit:
        query = query.limit(limit * 10)  # Get more to ensure unique sires

    response = query.execute()
    horses = response.data

    # Get unique sires
    sires_dict = {}
    for h in horses:
        sire_id = h.get('sire_id')
        sire_name = h.get('sire_name')
        if sire_id and sire_id not in sires_dict:
            sires_dict[sire_id] = sire_name

    sires = list(sires_dict.items())[:limit] if limit else list(sires_dict.items())
    logger.info(f"Processing {len(sires)} sires...")

    updated = 0
    for idx, (sire_id, sire_name) in enumerate(sires, 1):
        # Get all horses with this sire
        offspring_response = db.client.table('ra_mst_horses').select('id').eq('sire_id', sire_id).execute()
        offspring_ids = [h['id'] for h in offspring_response.data]

        if not offspring_ids:
            continue

        # Get all runners for these horses
        runners_query = db.client.table('ra_mst_runners').select(
            'position, race_id'
        ).in_('horse_id', offspring_ids).execute()
        runners = runners_query.data

        if not runners:
            continue

        # Get race details for class/distance analysis
        race_ids = list(set([r['race_id'] for r in runners]))
        races_response = db.client.table('ra_mst_races').select('id, class, distance, distance_f').in_('id', race_ids[:1000]).execute()  # Limit to avoid timeout
        races_dict = {r['id']: r for r in races_response.data}

        # Calculate basic stats
        total_runners = len(runners)
        total_wins = sum(1 for r in runners if r.get('position') == 1)
        total_places_2nd = sum(1 for r in runners if r.get('position') == 2)
        total_places_3rd = sum(1 for r in runners if r.get('position') == 3)
        overall_win_percent = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0

        # Analyze class performance (top 3 classes by wins)
        class_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('class'):
                continue

            class_num = race['class']
            if class_num not in class_stats:
                class_stats[class_num] = {'runners': 0, 'wins': 0}

            class_stats[class_num]['runners'] += 1
            if runner.get('position') == 1:
                class_stats[class_num]['wins'] += 1

        # Get top 3 classes by wins
        top_classes = sorted(class_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        # Analyze distance performance (group by distance_f - furlongs)
        distance_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('distance_f'):
                continue

            dist_f = race['distance_f']
            if dist_f not in distance_stats:
                distance_stats[dist_f] = {'runners': 0, 'wins': 0}

            distance_stats[dist_f]['runners'] += 1
            if runner.get('position') == 1:
                distance_stats[dist_f]['wins'] += 1

        # Get top 3 distances by wins
        top_distances = sorted(distance_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        # Find best class and distance
        best_class = top_classes[0][0] if top_classes else None
        best_distance_f = top_distances[0][0] if top_distances else None
        best_distance = f"{best_distance_f}f" if best_distance_f else None

        # Prepare update data
        update_data = {
            'total_runners': total_runners,
            'total_wins': total_wins,
            'total_places_2nd': total_places_2nd,
            'total_places_3rd': total_places_3rd,
            'overall_win_percent': overall_win_percent,
            'best_class': str(best_class) if best_class else None,
            'best_distance': best_distance,
            'analysis_last_updated': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add top 3 class breakdowns
        for i, (class_num, stats) in enumerate(top_classes, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'class_{i}_name'] = f"Class {class_num}"
            update_data[f'class_{i}_runners'] = stats['runners']
            update_data[f'class_{i}_wins'] = stats['wins']
            update_data[f'class_{i}_win_percent'] = win_percent

        # Add top 3 distance breakdowns
        for i, (dist_f, stats) in enumerate(top_distances, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'distance_{i}_name'] = f"{dist_f}f"
            update_data[f'distance_{i}_runners'] = stats['runners']
            update_data[f'distance_{i}_wins'] = stats['wins']
            update_data[f'distance_{i}_win_percent'] = win_percent

        # Upsert to ra_mst_sires
        upsert_data = {
            'id': sire_id,
            'name': sire_name or 'Unknown',
            **update_data
        }

        try:
            db.client.table('ra_mst_sires').upsert(upsert_data).execute()
            updated += 1

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(sires)} sires ({updated} updated)")
        except Exception as e:
            logger.error(f"Error updating sire {sire_id}: {e}")

    logger.info(f"✅ Sires complete: {updated}/{len(sires)} updated")
    return updated


def calculate_and_update_dams(db: SupabaseReferenceClient, limit: int = None):
    """Calculate and update dam statistics"""
    logger.info("=" * 80)
    logger.info("CALCULATING DAM STATISTICS")
    logger.info("=" * 80)

    # Get all dams
    query = db.client.table('ra_mst_horses').select('dam_id, dam_name').neq('dam_id', 'null')
    if limit:
        query = query.limit(limit * 10)

    response = query.execute()
    horses = response.data

    dams_dict = {}
    for h in horses:
        dam_id = h.get('dam_id')
        dam_name = h.get('dam_name')
        if dam_id and dam_id not in dams_dict:
            dams_dict[dam_id] = dam_name

    dams = list(dams_dict.items())[:limit] if limit else list(dams_dict.items())
    logger.info(f"Processing {len(dams)} dams...")

    updated = 0
    for idx, (dam_id, dam_name) in enumerate(dams, 1):
        # Same logic as sires but for dam_id
        offspring_response = db.client.table('ra_mst_horses').select('id').eq('dam_id', dam_id).execute()
        offspring_ids = [h['id'] for h in offspring_response.data]

        if not offspring_ids:
            continue

        runners_query = db.client.table('ra_mst_runners').select('position, race_id').in_('horse_id', offspring_ids).execute()
        runners = runners_query.data

        if not runners:
            continue

        race_ids = list(set([r['race_id'] for r in runners]))
        races_response = db.client.table('ra_mst_races').select('id, class, distance, distance_f').in_('id', race_ids[:1000]).execute()
        races_dict = {r['id']: r for r in races_response.data}

        total_runners = len(runners)
        total_wins = sum(1 for r in runners if r.get('position') == 1)
        total_places_2nd = sum(1 for r in runners if r.get('position') == 2)
        total_places_3rd = sum(1 for r in runners if r.get('position') == 3)
        overall_win_percent = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0

        class_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('class'):
                continue
            class_num = race['class']
            if class_num not in class_stats:
                class_stats[class_num] = {'runners': 0, 'wins': 0}
            class_stats[class_num]['runners'] += 1
            if runner.get('position') == 1:
                class_stats[class_num]['wins'] += 1

        top_classes = sorted(class_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        distance_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('distance_f'):
                continue
            dist_f = race['distance_f']
            if dist_f not in distance_stats:
                distance_stats[dist_f] = {'runners': 0, 'wins': 0}
            distance_stats[dist_f]['runners'] += 1
            if runner.get('position') == 1:
                distance_stats[dist_f]['wins'] += 1

        top_distances = sorted(distance_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        best_class = top_classes[0][0] if top_classes else None
        best_distance_f = top_distances[0][0] if top_distances else None
        best_distance = f"{best_distance_f}f" if best_distance_f else None

        update_data = {
            'total_runners': total_runners,
            'total_wins': total_wins,
            'total_places_2nd': total_places_2nd,
            'total_places_3rd': total_places_3rd,
            'overall_win_percent': overall_win_percent,
            'best_class': str(best_class) if best_class else None,
            'best_distance': best_distance,
            'analysis_last_updated': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        for i, (class_num, stats) in enumerate(top_classes, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'class_{i}_name'] = f"Class {class_num}"
            update_data[f'class_{i}_runners'] = stats['runners']
            update_data[f'class_{i}_wins'] = stats['wins']
            update_data[f'class_{i}_win_percent'] = win_percent

        for i, (dist_f, stats) in enumerate(top_distances, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'distance_{i}_name'] = f"{dist_f}f"
            update_data[f'distance_{i}_runners'] = stats['runners']
            update_data[f'distance_{i}_wins'] = stats['wins']
            update_data[f'distance_{i}_win_percent'] = win_percent

        upsert_data = {
            'id': dam_id,
            'name': dam_name or 'Unknown',
            **update_data
        }

        try:
            db.client.table('ra_mst_dams').upsert(upsert_data).execute()
            updated += 1

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(dams)} dams ({updated} updated)")
        except Exception as e:
            logger.error(f"Error updating dam {dam_id}: {e}")

    logger.info(f"✅ Dams complete: {updated}/{len(dams)} updated")
    return updated


def calculate_and_update_damsires(db: SupabaseReferenceClient, limit: int = None):
    """Calculate and update damsire statistics"""
    logger.info("=" * 80)
    logger.info("CALCULATING DAMSIRE STATISTICS")
    logger.info("=" * 80)

    # Get all damsires
    query = db.client.table('ra_mst_horses').select('damsire_id').neq('damsire_id', 'null')
    if limit:
        query = query.limit(limit * 10)

    response = query.execute()
    horses = response.data

    damsires_set = set()
    for h in horses:
        damsire_id = h.get('damsire_id')
        if damsire_id:
            damsires_set.add(damsire_id)

    damsires = sorted(list(damsires_set))[:limit] if limit else sorted(list(damsires_set))
    logger.info(f"Processing {len(damsires)} damsires...")

    updated = 0
    for idx, damsire_id in enumerate(damsires, 1):
        # Same logic but for damsire_id (grandoffspring)
        offspring_response = db.client.table('ra_mst_horses').select('id').eq('damsire_id', damsire_id).execute()
        offspring_ids = [h['id'] for h in offspring_response.data]

        if not offspring_ids:
            continue

        runners_query = db.client.table('ra_mst_runners').select('position, race_id').in_('horse_id', offspring_ids).execute()
        runners = runners_query.data

        if not runners:
            continue

        race_ids = list(set([r['race_id'] for r in runners]))
        races_response = db.client.table('ra_mst_races').select('id, class, distance, distance_f').in_('id', race_ids[:1000]).execute()
        races_dict = {r['id']: r for r in races_response.data}

        total_runners = len(runners)
        total_wins = sum(1 for r in runners if r.get('position') == 1)
        total_places_2nd = sum(1 for r in runners if r.get('position') == 2)
        total_places_3rd = sum(1 for r in runners if r.get('position') == 3)
        overall_win_percent = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0

        class_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('class'):
                continue
            class_num = race['class']
            if class_num not in class_stats:
                class_stats[class_num] = {'runners': 0, 'wins': 0}
            class_stats[class_num]['runners'] += 1
            if runner.get('position') == 1:
                class_stats[class_num]['wins'] += 1

        top_classes = sorted(class_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        distance_stats = {}
        for runner in runners:
            race = races_dict.get(runner['race_id'])
            if not race or not race.get('distance_f'):
                continue
            dist_f = race['distance_f']
            if dist_f not in distance_stats:
                distance_stats[dist_f] = {'runners': 0, 'wins': 0}
            distance_stats[dist_f]['runners'] += 1
            if runner.get('position') == 1:
                distance_stats[dist_f]['wins'] += 1

        top_distances = sorted(distance_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]

        best_class = top_classes[0][0] if top_classes else None
        best_distance_f = top_distances[0][0] if top_distances else None
        best_distance = f"{best_distance_f}f" if best_distance_f else None

        update_data = {
            'total_runners': total_runners,
            'total_wins': total_wins,
            'total_places_2nd': total_places_2nd,
            'total_places_3rd': total_places_3rd,
            'overall_win_percent': overall_win_percent,
            'best_class': str(best_class) if best_class else None,
            'best_distance': best_distance,
            'analysis_last_updated': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        for i, (class_num, stats) in enumerate(top_classes, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'class_{i}_name'] = f"Class {class_num}"
            update_data[f'class_{i}_runners'] = stats['runners']
            update_data[f'class_{i}_wins'] = stats['wins']
            update_data[f'class_{i}_win_percent'] = win_percent

        for i, (dist_f, stats) in enumerate(top_distances, 1):
            win_percent = round((stats['wins'] / stats['runners'] * 100), 2) if stats['runners'] > 0 else 0.0
            update_data[f'distance_{i}_name'] = f"{dist_f}f"
            update_data[f'distance_{i}_runners'] = stats['runners']
            update_data[f'distance_{i}_wins'] = stats['wins']
            update_data[f'distance_{i}_win_percent'] = win_percent

        # Get name from horses if this damsire is also a horse
        name_response = db.client.table('ra_mst_horses').select('name').eq('id', damsire_id).limit(1).execute()
        damsire_name = name_response.data[0]['name'] if name_response.data else 'Unknown'

        upsert_data = {
            'id': damsire_id,
            'name': damsire_name,
            **update_data
        }

        try:
            db.client.table('ra_mst_damsires').upsert(upsert_data).execute()
            updated += 1

            if idx % 10 == 0:
                logger.info(f"  Progress: {idx}/{len(damsires)} damsires ({updated} updated)")
        except Exception as e:
            logger.error(f"Error updating damsire {damsire_id}: {e}")

    logger.info(f"✅ Damsires complete: {updated}/{len(damsires)} updated")
    return updated


def main():
    parser = argparse.ArgumentParser(description='Calculate pedigree statistics from database')
    parser.add_argument('--test', action='store_true', help='Test mode (10 entities per table)')
    parser.add_argument('--table', choices=['sires', 'dams', 'damsires'], help='Specific table only')
    args = parser.parse_args()

    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    limit = 10 if args.test else None

    logger.info("=" * 80)
    logger.info("PEDIGREE STATISTICS CALCULATOR")
    logger.info("=" * 80)
    logger.info(f"Mode: {'TEST (10 per table)' if args.test else 'FULL'}")
    logger.info(f"Tables: {args.table if args.table else 'ALL'}")
    logger.info("=" * 80)

    results = {}

    if not args.table or args.table == 'sires':
        results['sires'] = calculate_and_update_sires(db, limit)

    if not args.table or args.table == 'dams':
        results['dams'] = calculate_and_update_dams(db, limit)

    if not args.table or args.table == 'damsires':
        results['damsires'] = calculate_and_update_damsires(db, limit)

    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    for table, count in results.items():
        logger.info(f"✅ {table}: {count} updated")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
