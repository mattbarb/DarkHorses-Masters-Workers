# Database Management Scripts

This folder contains scripts for managing database state and cleanup operations.

## Scripts

**`cleanup_and_reset.py`**
- Clean up and reset database tables
- Preview mode (dry run) to see what will be deleted
- Confirmation required for actual deletion
- Truncates all data while preserving schemas

## Usage

### Preview Current State (Safe)

```bash
# From project root
python3 cleanup_and_reset.py

# Shows current record counts for all tables
# Does NOT delete anything
```

### Delete All Data (Requires Confirmation)

```bash
# From project root
python3 cleanup_and_reset.py --confirm

# Will prompt you to type 'DELETE' to confirm
# Deletes ALL records from ALL tables
```

### Delete Specific Tables Only

```bash
# From project root
python3 cleanup_and_reset.py --confirm --tables ra_races ra_results

# Deletes only specified tables
```

## Safety Features

1. **Dry Run by Default**: Running without `--confirm` shows what WOULD be deleted
2. **Confirmation Required**: Must type 'DELETE' (exact case) to confirm
3. **Foreign Key Aware**: Deletes tables in correct order to respect relationships
4. **Batch Processing**: Deletes in batches to avoid timeouts
5. **Before/After Counts**: Shows exactly what was deleted

## Use Cases

- **Fresh Start**: Clean database before re-running initialization
- **Development Reset**: Clear test data
- **Partial Cleanup**: Remove data from specific tables only

## ⚠️ Warning

This script permanently deletes data. Always:
1. Run preview mode first
2. Backup important data
3. Verify you're connected to the correct database
4. Double-check before typing 'DELETE'

## Examples

```bash
# Check current state
python3 cleanup_and_reset.py

# Clean everything
python3 cleanup_and_reset.py --confirm

# Clean only results and races
python3 cleanup_and_reset.py --confirm --tables ra_results ra_races
```
