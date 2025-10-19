#!/usr/bin/env python3
"""
Analyze null columns in dh_weather_history table
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict
import json

# Load environment variables
load_dotenv('.env.local')
if not os.getenv('SUPABASE_URL'):
    load_dotenv('../.env.local')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

if not url or not key:
    print('ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY')
    sys.exit(1)

# Create client
from supabase.lib.client_options import ClientOptions
options = ClientOptions()
client = create_client(url, key, options)

print("=== ANALYZING dh_weather_history NULL COLUMNS ===\n")

# Get total count (estimate based on sample)
print("Estimating total record count...")
# Use a simple query to get the count - may timeout but we'll use sample size instead
try:
    result = client.table('dh_weather_history').select('id', count='exact').limit(1).execute()
    total_records = result.count if hasattr(result, 'count') else 0
except Exception as e:
    print(f"  Could not get exact count (timeout expected): {e}")
    # We'll estimate based on sample
    total_records = None

if total_records:
    print(f"Total records: {total_records:,}\n")
else:
    print("Total records: Unknown (will use sample for analysis)\n")

# Define all columns from schema
columns = [
    'id', 'race_id', 'race_datetime', 'course_name', 'latitude', 'longitude',
    'update_number', 'total_updates', 'update_display', 'update_phase',
    'fetch_datetime', 'api_source', 'hours_before_race',
    'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'apparent_temperature',
    'precipitation', 'rain', 'snowfall', 'snow_depth', 'weather_code',
    'pressure_msl', 'surface_pressure', 'cloud_cover', 'cloud_cover_low',
    'cloud_cover_mid', 'cloud_cover_high', 'wind_speed_10m', 'wind_speed_100m',
    'wind_direction_10m', 'wind_direction_100m', 'wind_gusts_10m',
    'temperature_80m', 'temperature_120m', 'temperature_180m',
    'soil_temperature_0_to_7cm', 'soil_temperature_7_to_28cm',
    'soil_temperature_28_to_100cm', 'soil_temperature_100_to_255cm',
    'soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm',
    'soil_moisture_28_to_100cm', 'soil_moisture_100_to_255cm',
    'shortwave_radiation', 'direct_radiation', 'diffuse_radiation',
    'direct_normal_irradiance', 'global_tilted_irradiance', 'terrestrial_radiation',
    'shortwave_radiation_instant', 'direct_radiation_instant',
    'diffuse_radiation_instant', 'direct_normal_irradiance_instant',
    'global_tilted_irradiance_instant', 'terrestrial_radiation_instant',
    'is_day', 'sunshine_duration', 'et0_fao_evapotranspiration',
    'vapour_pressure_deficit', 'temperature_2m_max_daily',
    'temperature_2m_min_daily', 'apparent_temperature_max_daily',
    'apparent_temperature_min_daily', 'precipitation_sum_daily',
    'rain_sum_daily', 'snowfall_sum_daily', 'precipitation_hours_daily',
    'wind_speed_10m_max_daily', 'wind_gusts_10m_max_daily',
    'wind_direction_10m_dominant_daily', 'shortwave_radiation_sum_daily',
    'raw_data', 'created_at', 'updated_at'
]

# Sample-based analysis (fetch sample records to check for nulls)
print("Fetching sample records for null analysis...")
SAMPLE_SIZE = 1000
result = client.table('dh_weather_history').select('*').limit(SAMPLE_SIZE).execute()
sample_records = result.data

null_counts = defaultdict(int)
for record in sample_records:
    for col in columns:
        if record.get(col) is None:
            null_counts[col] += 1

# Calculate percentages
print(f"\n=== NULL ANALYSIS (based on {len(sample_records)} sample records) ===\n")
print(f"{'Column':<45} {'Null Count':>12} {'Null %':>10}")
print("=" * 70)

# Sort by null percentage (descending)
null_stats = []
for col in columns:
    null_count = null_counts[col]
    null_pct = (null_count / len(sample_records)) * 100
    null_stats.append((col, null_count, null_pct))

null_stats.sort(key=lambda x: x[2], reverse=True)

# Categories
high_null = []  # >50%
medium_null = []  # 10-50%
low_null = []  # 1-10%
no_null = []  # 0%

for col, null_count, null_pct in null_stats:
    print(f"{col:<45} {null_count:>12,} {null_pct:>9.2f}%")

    if null_pct > 50:
        high_null.append((col, null_pct))
    elif null_pct > 10:
        medium_null.append((col, null_pct))
    elif null_pct > 0:
        low_null.append((col, null_pct))
    else:
        no_null.append(col)

# Summary
print("\n" + "=" * 70)
print(f"\n=== SUMMARY ===\n")
print(f"Columns with >50% nulls:  {len(high_null)}")
for col, pct in high_null:
    print(f"  - {col}: {pct:.2f}%")

print(f"\nColumns with 10-50% nulls: {len(medium_null)}")
for col, pct in medium_null:
    print(f"  - {col}: {pct:.2f}%")

print(f"\nColumns with 1-10% nulls:  {len(low_null)}")
for col, pct in low_null:
    print(f"  - {col}: {pct:.2f}%")

print(f"\nColumns with 0% nulls:    {len(no_null)}")

# Check specific column types
print(f"\n=== COLUMN TYPE ANALYSIS ===\n")

# Check if sample records have array data
array_columns = [
    'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'apparent_temperature',
    'precipitation', 'rain', 'snowfall', 'snow_depth', 'weather_code',
    'pressure_msl', 'surface_pressure', 'cloud_cover'
]

print("Checking if array columns are properly populated...")
for record in sample_records[:5]:
    print(f"\nRecord ID: {record.get('id')}")
    print(f"  Race ID: {record.get('race_id')}")
    print(f"  Course: {record.get('course_name')}")
    for col in array_columns[:6]:  # Check first 6 array columns
        val = record.get(col)
        if val is None:
            print(f"  {col}: NULL")
        elif isinstance(val, list):
            print(f"  {col}: Array with {len(val)} elements")
        else:
            print(f"  {col}: {type(val).__name__}")

# Save detailed report
report = {
    'total_records': total_records,
    'sample_size': len(sample_records),
    'high_null_columns': [{'column': col, 'null_pct': pct} for col, pct in high_null],
    'medium_null_columns': [{'column': col, 'null_pct': pct} for col, pct in medium_null],
    'low_null_columns': [{'column': col, 'null_pct': pct} for col, pct in low_null],
    'no_null_columns': no_null,
    'summary': {
        'high_null_count': len(high_null),
        'medium_null_count': len(medium_null),
        'low_null_count': len(low_null),
        'no_null_count': len(no_null)
    }
}

report_path = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/logs/weather_null_analysis.json'
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n\nDetailed report saved to: {report_path}")
