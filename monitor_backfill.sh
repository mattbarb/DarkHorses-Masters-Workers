#!/bin/bash
echo "=== Distance_m Backfill Monitor ==="
echo ""
echo "Process Status:"
ps -p 85747 -o pid,etime,comm 2>/dev/null || echo "Process completed or not running"
echo ""
echo "Latest Log Entries:"
tail -5 logs/backfill_distance_m_continuation.log 2>/dev/null
echo ""
echo "Current Database Status:"
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
result = db.client.from_('ra_races').select('id', count='exact').is_('distance_m', 'null').execute()
missing = result.count
total_result = db.client.from_('ra_races').select('id', count='exact').execute()
total = total_result.count
pct = ((total - missing) / total * 100) if total > 0 else 0
print(f'Total races: {total:,}')
print(f'Races with distance_m: {total - missing:,}')
print(f'Races missing distance_m: {missing:,}')
print(f'Completion: {pct:.2f}%')
" 2>/dev/null
