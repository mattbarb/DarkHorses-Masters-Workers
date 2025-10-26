#!/bin/bash
# Auto-loop script to complete distance_m backfill to 100%

echo "=========================================="
echo "Distance_m Backfill Auto-Loop"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/maintenance/backfill_distance_m.py"
LOG_DIR="$PROJECT_ROOT/logs"

# Check how many races are missing
echo "Checking database status..."
MISSING=$(python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
result = db.client.from_('ra_mst_races').select('id', count='exact').is_('distance_m', 'null').execute()
print(result.count)
" 2>/dev/null)

echo "Races missing distance_m: $MISSING"
echo ""

if [ "$MISSING" -eq 0 ]; then
    echo "✓ All races have distance_m! Backfill complete."
    exit 0
fi

# Calculate iterations needed (assuming ~13K per run)
ITERATIONS=$(( ($MISSING + 12999) / 13000 ))
echo "Estimated iterations needed: $ITERATIONS"
echo ""

# Run backfill in loop until complete
ITERATION=1
while [ "$MISSING" -gt 0 ]; do
    echo "=========================================="
    echo "ITERATION $ITERATION"
    echo "Remaining races: $MISSING"
    echo "=========================================="
    
    # Run backfill
    LOG_FILE="$LOG_DIR/backfill_distance_m_loop_iter${ITERATION}_$(date +%Y%m%d_%H%M%S).log"
    echo "Running backfill (log: $LOG_FILE)..."
    python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1
    
    # Check result
    if [ $? -eq 0 ]; then
        echo "✓ Iteration $ITERATION completed successfully"
    else
        echo "✗ Iteration $ITERATION failed (check log)"
    fi
    
    # Wait a bit between runs
    echo "Waiting 5 seconds..."
    sleep 5
    
    # Check remaining
    MISSING=$(python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
result = db.client.from_('ra_mst_races').select('id', count='exact').is_('distance_m', 'null').execute()
print(result.count)
" 2>/dev/null)
    
    echo "After iteration $ITERATION: $MISSING races remaining"
    echo ""
    
    ITERATION=$((ITERATION + 1))
    
    # Safety limit (max 10 iterations)
    if [ "$ITERATION" -gt 10 ]; then
        echo "⚠ Reached safety limit of 10 iterations"
        echo "Still missing: $MISSING races"
        break
    fi
done

echo ""
echo "=========================================="
echo "BACKFILL LOOP COMPLETE"
echo "=========================================="
echo "Final check..."

# Final stats
python3 << 'PYEOF'
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
total = db.client.from_('ra_mst_races').select('id', count='exact').execute().count
with_dist = db.client.from_('ra_mst_races').select('id', count='exact').not_.is_('distance_m', 'null').execute().count
missing = total - with_dist
pct = (with_dist / total * 100) if total > 0 else 0
print(f"Total races: {total:,}")
print(f"With distance_m: {with_dist:,} ({pct:.2f}%)")
print(f"Missing: {missing:,}")
if missing == 0:
    print("\n✓✓✓ 100% COMPLETE! ✓✓✓")
else:
    print(f"\n⚠ {missing:,} races still need distance_m")
PYEOF
