"""
Master Execution Script: Data Updates
Orchestrates all database update tasks in correct order
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from utils.logger import get_logger
import subprocess

logger = get_logger('execute_data_updates')


def print_banner(text):
    """Print a formatted banner"""
    logger.info("")
    logger.info("=" * 70)
    logger.info(text)
    logger.info("=" * 70)
    logger.info("")


def run_step(step_num, title, func):
    """Run a step and track success/failure"""
    print_banner(f"STEP {step_num}: {title}")

    try:
        result = func()
        logger.info(f"✓ Step {step_num} completed successfully")
        return True, result
    except Exception as e:
        logger.error(f"✗ Step {step_num} failed: {e}")
        return False, str(e)


def step1_backup_database():
    """Step 1: Backup database tables"""
    logger.info("Creating backup tables...")

    # This would typically use psycopg2 or the Supabase client
    # For now, just log instructions

    logger.warning("IMPORTANT: Manually create backup tables before proceeding:")
    logger.warning("  CREATE TABLE ra_horses_backup_20251008 AS SELECT * FROM ra_horses;")
    logger.warning("  CREATE TABLE ra_runners_backup_20251008 AS SELECT * FROM ra_runners;")
    logger.warning("  CREATE TABLE ra_races_backup_20251008 AS SELECT * FROM ra_races;")
    logger.warning("  CREATE TABLE ra_horse_pedigree_backup_20251008 AS SELECT * FROM ra_horse_pedigree;")

    response = input("\nHave you created the backup tables? (yes/no): ")
    if response.lower() != 'yes':
        raise Exception("Backup not confirmed. Aborting.")

    logger.info("✓ Backup confirmed")
    return {'status': 'confirmed'}


def step2_apply_migrations():
    """Step 2: Apply database migrations"""
    logger.info("Applying database migrations...")

    migration_file = Path(__file__).parent.parent / 'migrations' / '003_add_missing_fields.sql'

    if not migration_file.exists():
        raise Exception(f"Migration file not found: {migration_file}")

    logger.warning(f"IMPORTANT: Apply migration manually:")
    logger.warning(f"  File: {migration_file}")
    logger.warning(f"  Run via Supabase dashboard or psql")

    response = input("\nHave you applied the migration? (yes/no): ")
    if response.lower() != 'yes':
        raise Exception("Migration not confirmed. Aborting.")

    logger.info("✓ Migration confirmed")
    return {'status': 'confirmed'}


def step3_update_fetchers():
    """Step 3: Update fetcher code"""
    logger.info("Checking fetcher updates...")

    horses_fetcher = Path(__file__).parent.parent / 'fetchers' / 'horses_fetcher.py'
    races_fetcher = Path(__file__).parent.parent / 'fetchers' / 'races_fetcher.py'

    logger.warning("IMPORTANT: Update fetcher files with new methods:")
    logger.warning(f"  1. {horses_fetcher}")
    logger.warning(f"     Add fetch_and_store_detailed() method (see DATA_UPDATE_MASTER_PLAN.md Section 1.1)")
    logger.warning(f"  2. {races_fetcher}")
    logger.warning(f"     Add new field extraction (see DATA_UPDATE_MASTER_PLAN.md Sections 1.2 & 1.3)")

    response = input("\nHave you updated the fetchers? (yes/no): ")
    if response.lower() != 'yes':
        raise Exception("Fetcher updates not confirmed. Aborting.")

    logger.info("✓ Fetcher updates confirmed")
    return {'status': 'confirmed'}


def step4_test_updates():
    """Step 4: Test updates with sample data"""
    logger.info("Testing updates with sample data...")

    logger.info("Running validation script...")

    try:
        # Run validation script
        result = subprocess.run(
            ['python3', 'scripts/validate_data_updates.py'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=300
        )

        logger.info(result.stdout)
        if result.returncode != 0:
            logger.error(result.stderr)
            logger.warning("Validation script reported failures")
            logger.warning("This may be expected if pedigree job hasn't run yet")

        return {'status': 'tested', 'output': result.stdout}

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


def step5_start_pedigree_job():
    """Step 5: Start pedigree backfill background job"""
    logger.info("Starting pedigree backfill job...")

    logger.warning("IMPORTANT: Start background job for pedigree population:")
    logger.warning("  This will run for ~15.5 hours")
    logger.warning("  Command: python3 scripts/start_pedigree_backfill.py > logs/pedigree_backfill.log 2>&1 &")

    response = input("\nStart pedigree backfill job now? (yes/no): ")
    if response.lower() != 'yes':
        logger.warning("Pedigree job not started. You can start it manually later.")
        return {'status': 'skipped'}

    try:
        # Start background job
        backfill_script = Path(__file__).parent / 'start_pedigree_backfill.py'
        log_file = Path(__file__).parent.parent / 'logs' / 'pedigree_backfill.log'
        log_file.parent.mkdir(exist_ok=True)

        # This would start the job in background
        # For safety, we'll just log instructions
        logger.info(f"Run this command in a separate terminal:")
        logger.info(f"  nohup python3 {backfill_script} > {log_file} 2>&1 &")

        return {'status': 'instructions_provided'}

    except Exception as e:
        logger.error(f"Failed to start job: {e}")
        raise


def step6_diagnose_runners():
    """Step 6: Diagnose missing runners issue"""
    logger.info("Running runner diagnostic...")

    try:
        # Run diagnostic script
        result = subprocess.run(
            ['python3', 'scripts/diagnose_missing_runners.py'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=600
        )

        logger.info(result.stdout)
        if result.returncode != 0:
            logger.error(result.stderr)

        return {'status': 'completed', 'output': result.stdout}

    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        raise


def main():
    """Main execution flow"""

    print_banner("DATA UPDATE MASTER EXECUTION")
    logger.info(f"Started: {datetime.now()}")
    logger.info("")

    logger.warning("=" * 70)
    logger.warning("IMPORTANT: This script will guide you through the update process")
    logger.warning("Some steps require manual intervention")
    logger.warning("Have DATA_UPDATE_MASTER_PLAN.md and EXECUTION_CHECKLIST.md open")
    logger.warning("=" * 70)

    response = input("\nReady to proceed? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Aborted by user")
        return

    results = {}

    # Step 1: Backup
    success, result = run_step(1, "Backup Database", step1_backup_database)
    results['step1'] = result
    if not success:
        logger.error("Step 1 failed. Aborting.")
        return

    # Step 2: Migrations
    success, result = run_step(2, "Apply Database Migrations", step2_apply_migrations)
    results['step2'] = result
    if not success:
        logger.error("Step 2 failed. Aborting.")
        return

    # Step 3: Update fetchers
    success, result = run_step(3, "Update Fetcher Code", step3_update_fetchers)
    results['step3'] = result
    if not success:
        logger.error("Step 3 failed. Aborting.")
        return

    # Step 4: Test
    success, result = run_step(4, "Test Updates", step4_test_updates)
    results['step4'] = result
    # Don't abort on test failure - validation may fail before pedigree job runs

    # Step 5: Start pedigree job
    success, result = run_step(5, "Start Pedigree Backfill Job", step5_start_pedigree_job)
    results['step5'] = result

    # Step 6: Diagnose runners
    success, result = run_step(6, "Diagnose Missing Runners", step6_diagnose_runners)
    results['step6'] = result

    # Summary
    print_banner("EXECUTION SUMMARY")

    logger.info("Completed Steps:")
    for step, result in results.items():
        status = result.get('status', 'unknown') if isinstance(result, dict) else 'error'
        logger.info(f"  {step}: {status}")

    logger.info("")
    logger.info("Next Steps:")
    logger.info("  1. Monitor pedigree backfill job (tail -f logs/pedigree_backfill.log)")
    logger.info("  2. Review diagnostic results in logs/")
    logger.info("  3. Implement runner fix based on diagnostic findings")
    logger.info("  4. Run validation script again after pedigree job completes")
    logger.info("  5. Follow EXECUTION_CHECKLIST.md for remaining tasks")

    logger.info("")
    logger.info(f"Completed: {datetime.now()}")

    # Save execution log
    log_path = Path(__file__).parent.parent / 'logs' / f'execution_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    log_path.parent.mkdir(exist_ok=True)

    with open(log_path, 'w') as f:
        f.write("DATA UPDATE EXECUTION LOG\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Started: {datetime.now()}\n\n")

        for step, result in results.items():
            f.write(f"\n{step}:\n")
            f.write(f"{result}\n")

    logger.info(f"\nExecution log saved to: {log_path}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nExecution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nExecution failed: {e}")
        sys.exit(1)
