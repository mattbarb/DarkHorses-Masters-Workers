#!/usr/bin/env python3
"""
Analyze dam progeny and damsire grandoffspring results from Pro endpoints
"""

import json
import sys
from pathlib import Path

print("=" * 100)
print("ANALYZING PRO LINEAGE ENDPOINT DATA")
print("=" * 100)
print()

# Load dam progeny response
dam_file = Path(__file__).parent.parent / "test_dam_progeny_response.json"
with open(dam_file, 'r') as f:
    dam_data = json.load(f)

print("DAM PROGENY RESULTS")
print("-" * 100)
print(f"Dam tested: Whazzat (GB) - dam_4206832")
print()

# Analyze dam progeny
dam_id = "dam_4206832"
total_races = len(dam_data['results'])
total_runners_in_races = sum(len(race['runners']) for race in dam_data['results'])

# Find progeny (horses with this dam)
progeny_performances = []
for race in dam_data['results']:
    for runner in race['runners']:
        if runner.get('dam_id') == dam_id:
            progeny_performances.append({
                'horse_id': runner.get('horse_id'),
                'horse_name': runner.get('horse'),
                'race_id': race['race_id'],
                'race_date': race['date'],
                'course': race['course'],
                'position': runner.get('position'),
                'prize': runner.get('prize', 0),
                'sp': runner.get('sp'),
                'sire': runner.get('sire'),
                'sire_id': runner.get('sire_id'),
            })

print(f"Total races returned: {total_races}")
print(f"Total runners in all races: {total_runners_in_races}")
print(f"Progeny (horses with Whazzat as dam): {len(progeny_performances)}")
print()

# Show progeny
print(f"Progeny found:")
print(f"{'Horse':<30} {'Sire':<30} {'Race Date':<12} {'Course':<20} {'Pos':<5} {'Prize':<10}")
print("-" * 100)

unique_progeny = {}
for perf in progeny_performances:
    horse_id = perf['horse_id']
    if horse_id not in unique_progeny:
        unique_progeny[horse_id] = {
            'name': perf['horse_name'],
            'sire': perf['sire'],
            'performances': []
        }
    unique_progeny[horse_id]['performances'].append(perf)

for horse_id, data in unique_progeny.items():
    # Show first performance
    first_perf = data['performances'][0]
    prize = f"£{first_perf['prize']}" if first_perf['prize'] else 'N/A'
    print(f"{data['name']:<30} {data['sire']:<30} {first_perf['race_date']:<12} {first_perf['course']:<20} {first_perf['position']:<5} {prize:<10}")

print()
print(f"Unique progeny horses: {len(unique_progeny)}")
print()

# Statistics
total_wins = sum(1 for p in progeny_performances if p['position'] == '1')
total_places = sum(1 for p in progeny_performances if p['position'] and int(p['position']) <= 3)
total_prize = sum(float(p['prize']) if p['prize'] else 0 for p in progeny_performances)

print("Performance summary:")
print(f"  Total runs: {len(progeny_performances)}")
print(f"  Wins: {total_wins}")
print(f"  Places (1-3): {total_places}")
print(f"  Total prize money: £{total_prize:,.0f}")
if len(progeny_performances) > 0:
    print(f"  Win rate: {total_wins/len(progeny_performances)*100:.1f}%")
    print(f"  Place rate: {total_places/len(progeny_performances)*100:.1f}%")

print()
print()

# Load damsire grandoffspring response
damsire_file = Path(__file__).parent.parent / "test_damsire_grandoffspring_response.json"
with open(damsire_file, 'r') as f:
    damsire_data = json.load(f)

print("=" * 100)
print("DAMSIRE GRANDOFFSPRING RESULTS")
print("-" * 100)
print(f"Damsire tested: Galileo - dsi_3722383")
print()

# Analyze damsire grandoffspring
damsire_id = "dsi_3722383"
total_races = len(damsire_data['results'])
total_runners_in_races = sum(len(race['runners']) for race in damsire_data['results'])

# Find grandoffspring (horses with this damsire)
grandoffspring_performances = []
for race in damsire_data['results']:
    for runner in race['runners']:
        if runner.get('damsire_id') == damsire_id:
            grandoffspring_performances.append({
                'horse_id': runner.get('horse_id'),
                'horse_name': runner.get('horse'),
                'race_id': race['race_id'],
                'race_date': race['date'],
                'course': race['course'],
                'position': runner.get('position'),
                'prize': runner.get('prize', 0),
                'sp': runner.get('sp'),
                'sire': runner.get('sire'),
                'dam': runner.get('dam'),
            })

print(f"Total races returned: {total_races}")
print(f"Total runners in all races: {total_runners_in_races}")
print(f"Grandoffspring (horses with Galileo as damsire): {len(grandoffspring_performances)}")
print()

# Show sample grandoffspring
print(f"Sample grandoffspring (first 10):")
print(f"{'Horse':<30} {'Dam':<30} {'Race Date':<12} {'Course':<20} {'Pos':<5}")
print("-" * 100)

unique_grandoffspring = {}
for perf in grandoffspring_performances:
    horse_id = perf['horse_id']
    if horse_id not in unique_grandoffspring:
        unique_grandoffspring[horse_id] = {
            'name': perf['horse_name'],
            'sire': perf['sire'],
            'dam': perf['dam'],
            'performances': []
        }
    unique_grandoffspring[horse_id]['performances'].append(perf)

count = 0
for horse_id, data in list(unique_grandoffspring.items())[:10]:
    first_perf = data['performances'][0]
    print(f"{data['name']:<30} {data['dam']:<30} {first_perf['race_date']:<12} {first_perf['course']:<20} {first_perf['position']:<5}")
    count += 1

print()
print(f"Unique grandoffspring horses: {len(unique_grandoffspring)}")
print()

# Statistics
total_wins = sum(1 for p in grandoffspring_performances if p['position'] == '1')
total_places = sum(1 for p in grandoffspring_performances if p['position'] and int(p['position']) <= 3)
total_prize = sum(float(p['prize']) if p['prize'] else 0 for p in grandoffspring_performances)

print("Performance summary:")
print(f"  Total runs: {len(grandoffspring_performances)}")
print(f"  Wins: {total_wins}")
print(f"  Places (1-3): {total_places}")
print(f"  Total prize money: £{total_prize:,.0f}")
if len(grandoffspring_performances) > 0:
    print(f"  Win rate: {total_wins/len(grandoffspring_performances)*100:.1f}%")
    print(f"  Place rate: {total_places/len(grandoffspring_performances)*100:.1f}%")

print()
print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)
print()
print("1. The Pro endpoints return COMPLETE race results, not just progeny/grandoffspring")
print("2. We need to FILTER runners by dam_id/damsire_id to find the relevant horses")
print("3. This data structure is identical to /v1/results endpoint")
print("4. The only difference is the API pre-filters races to those containing progeny/grandoffspring")
print()
print("CONCLUSION:")
print("Since we already fetch all results via /v1/results and track lineage in ra_lineage,")
print("we can query this same data locally without these Pro endpoints.")
print()
print("The Pro endpoints are useful for:")
print("- Validation (ensure we have all races)")
print("- Backfill (find historical gaps)")
print("- One-off analysis (without writing SQL)")
print()
