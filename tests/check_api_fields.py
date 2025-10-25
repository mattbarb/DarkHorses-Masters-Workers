"""Check what fields the API actually returns"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.api_client import RacingAPIClient
import json

config = get_config()
client = RacingAPIClient(
    username=config.api.username,
    password=config.api.password
)

# Fetch a single racecard
response = client.get_racecards_pro(date='2025-10-23', region_codes=['gb', 'ire'])

if response and 'racecards' in response and len(response['racecards']) > 0:
    race = response['racecards'][0]

    print('='*80)
    print('RACE FIELDS FROM API:')
    print('='*80)
    for key, value in race.items():
        if key != 'runners':
            print(f"{key}: {value}")

    print('\n' + '='*80)
    print('RUNNER FIELDS FROM API (first runner):')
    print('='*80)
    if race.get('runners') and len(race['runners']) > 0:
        runner = race['runners'][0]
        for key, value in runner.items():
            print(f"{key}: {value}")
