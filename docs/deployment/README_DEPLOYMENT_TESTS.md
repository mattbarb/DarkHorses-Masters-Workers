# Deployment Tests - Quick Reference

## Quick Start

```bash
# 1. Setup environment
cd /path/to/DarkHorses-Masters-Workers
cp .env.local.example .env.local
# Edit .env.local with your credentials

# 2. Run all deployment tests
cd tests
python3 run_deployment_tests.py
```

## Test Files

| File | Purpose | Runtime | Critical |
|------|---------|---------|----------|
| `test_deployment.py` | Environment & connectivity | ~5-10s | ✅ Yes |
| `test_schedule.py` | Scheduler configuration | ~3-5s | ✅ Yes |
| `test_data_freshness.py` | Data age monitoring | ~5-10s | ⚠️ Warning |
| `test_e2e_worker.py` | End-to-end pipeline | ~15-30s | ✅ Yes |
| `run_deployment_tests.py` | **Master orchestrator** | ~2-5min | ✅ Yes |

## Run Individual Tests

```bash
cd tests

# Quick checks
python3 test_deployment.py      # Check environment
python3 test_schedule.py         # Check scheduler
python3 test_data_freshness.py  # Check data age

# Comprehensive test
python3 test_e2e_worker.py       # Full pipeline test

# Complete suite
python3 run_deployment_tests.py  # All tests + report
```

## Exit Codes

- `0` = All critical tests passed (warnings OK)
- `1` = Critical failures detected

## Common Commands

```bash
# Run and save output
python3 run_deployment_tests.py | tee deployment-test-$(date +%Y%m%d).log

# Run quietly (errors only)
python3 run_deployment_tests.py 2>&1 | grep -E "(FAIL|CRITICAL)"

# Check specific phase
python3 test_deployment.py && echo "Environment OK"
```

## What Gets Tested

✅ Environment variables loaded
✅ API & database connectivity
✅ Scheduler configuration
✅ Data freshness (8 tables)
✅ Complete fetch→store pipeline
✅ Data quality validation
✅ Error handling
✅ Regional filtering (UK/Ireland)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Missing env vars | Copy `.env.local.example` to `.env.local` |
| API connection failed | Check Racing API credentials |
| DB connection failed | Check Supabase credentials |
| Tables missing | Run database migrations |
| Stale data | Check Render.com logs |
| Import errors | `pip install -r requirements.txt` |

## Full Documentation

See `DEPLOYMENT_TESTING.md` for complete documentation.

## Monitoring Recommendations

- **Daily:** Run `run_deployment_tests.py`
- **Weekly:** Review data freshness trends
- **Monthly:** Update freshness thresholds if needed
- **Always:** After deployment or configuration changes

---

**Last Updated:** 2025-10-06
