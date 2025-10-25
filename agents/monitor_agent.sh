#!/bin/bash
# Monitor the pedigree statistics agent progress

echo "========================================"
echo "Pedigree Statistics Agent Monitor"
echo "========================================"
echo ""

# Check if agent is running
if pgrep -f "pedigree_statistics_agent.py" > /dev/null; then
    echo "✅ Agent is RUNNING"
    echo "Process ID: $(pgrep -f pedigree_statistics_agent.py)"
else
    echo "❌ Agent is NOT running"
fi

echo ""
echo "========================================"
echo "Current Statistics Population"
echo "========================================"

PGPASSWORD='R0pMr1L58WH3hUkpVtPcwYnw' psql -h aws-0-eu-west-2.pooler.supabase.com -p 5432 \
    -U postgres.amsjvmlaknnvppxsgpfk -d postgres -c "
SELECT
    'Sires' as entity_type,
    COUNT(*) as total,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as with_stats,
    ROUND(COUNT(total_runners) FILTER (WHERE total_runners > 0)::numeric / COUNT(*)::numeric * 100, 2) as pct_complete,
    COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL) as with_ae
FROM ra_mst_sires
UNION ALL
SELECT
    'Dams' as entity_type,
    COUNT(*) as total,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as with_stats,
    ROUND(COUNT(total_runners) FILTER (WHERE total_runners > 0)::numeric / COUNT(*)::numeric * 100, 2) as pct_complete,
    COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL) as with_ae
FROM ra_mst_dams
UNION ALL
SELECT
    'Damsires' as entity_type,
    COUNT(*) as total,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as with_stats,
    ROUND(COUNT(total_runners) FILTER (WHERE total_runners > 0)::numeric / COUNT(*)::numeric * 100, 2) as pct_complete,
    COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL) as with_ae
FROM ra_mst_damsires;"

echo ""
echo "========================================"
echo "Recent Log Entries (last 10 lines)"
echo "========================================"
tail -n 10 logs/pedigree_agent_run.log 2>/dev/null || echo "No log file found"

echo ""
echo "========================================"
echo "Last Checkpoint"
echo "========================================"
if [ -f logs/pedigree_agent_checkpoint.json ]; then
    cat logs/pedigree_agent_checkpoint.json
else
    echo "No checkpoint file found"
fi

echo ""
echo "========================================"
echo "Agent Statistics"
echo "========================================"
if [ -f logs/pedigree_agent_stats.json ]; then
    cat logs/pedigree_agent_stats.json
else
    echo "No stats file found"
fi
