# Multi-Business Testing Guide

Complete guide for scaling the SoilOptix testing framework to multiple businesses/providers using network drive datasets.

---

## Overview

This guide covers how to:
1. Explore network drives to find datasets
2. Download datasets to local storage
3. Generate catalog entries for multi-business testing
4. Run tests across multiple businesses
5. Keep datasets fresh with smart refresh

---

## Quick Start

```bash
# 1. Explore network drive (find datasets)
python tools/explore_network_datasets.py \
  --provider hutchinson \
  --business-id 7635 \
  --network-path "\\172.16.1.12\SoilData\2025\Hutchinson_UK\Hutchinson_UK" \
  --output inventory_hutchinson.json \
  --limit 10

# 2. Download datasets (copy to local storage)
python tools/download_datasets.py \
  --inventory inventory_hutchinson.json \
  --output-dir datasets/hutchinson

# 3. Generate catalog entries
python tools/generate_catalog.py \
  --provider hutchinson \
  --output catalog_generated.yml

# 4. Merge catalog entries (manual review recommended)
cat catalog_generated.yml >> catalog.yml

# 5. Run tests
python -m pytest -n auto

# 6. Refresh datasets (weekly or as needed)
python tools/refresh_datasets.py --provider hutchinson
```

---

## Provider/Business Mapping

The framework supports 8-10 providers. Each provider maps to a Business ID in the staging portal.

| Provider | Business ID | Network Path |
|----------|-------------|--------------|
| hutchinson | 7635 | `\\172.16.1.12\SoilData\2025\Hutchinson_UK\Hutchinson_UK` |
| danish_agro | 7619 | `\\172.16.1.12\SoilData\2025\FieldSense\Danish_Agro` |
| syngenta | 7650 | `\\172.16.1.12\SoilData\2025\Syngenta_Europe\Syngenta_Europe` |
| croptech | 7616 | `\\172.16.1.12\SoilData\2025\Crop_Tech_Solutions\Crop_Tech_Solutions` |
| glimax | 7623 | `\\172.16.1.12\SoilData\2025\Glimax\Glimax_-_Agroideas` |
| moose_ag | 7641 | `\\172.16.1.12\SoilData\2025\Moose_Ag\Moose_Ag` |
| mosburger | 7637 | `\\172.16.1.12\SoilData\2025\Mosburger_Ag\Mosburger_Ag` |

---

## Tool Reference

### 1. `explore_network_datasets.py`

**Purpose:** Scan network drives to find valid datasets

**What it does:**
- Recursively explores provider directory structure
- Finds numbered folders (raw uploads from customers)
- Validates presence of Labs, Surveys, Boundaries
- Generates JSON inventory with anonymized names
- **READ-ONLY** - No writes to network

**Usage:**
```bash
python tools/explore_network_datasets.py \
  --provider hutchinson \
  --business-id 7635 \
  --network-path "\\172.16.1.12\SoilData\2025\Hutchinson_UK\Hutchinson_UK" \
  --output inventory_hutchinson.json \
  --limit 10 \
  --verbose
```

**Options:**
- `--provider`: Provider name (e.g., 'hutchinson', 'danish_agro')
- `--business-id`: Business ID for this provider
- `--network-path`: Network path to provider root
- `--output`: Output JSON file (default: inventory.json)
- `--limit`: Max datasets to collect (default: all)
- `--verbose`: Print detailed progress

**Output:** JSON inventory file with dataset metadata

---

### 2. `download_datasets.py`

**Purpose:** Copy datasets from network to local storage

**What it does:**
- Reads inventory JSON from explorer
- Creates organized local structure
- **READ-ONLY** network operations
- Logs all downloads with timestamps
- Creates metadata files for each dataset

**Usage:**
```bash
python tools/download_datasets.py \
  --inventory inventory_hutchinson.json \
  --output-dir datasets/hutchinson \
  --limit 10 \
  --skip 0 \
  --verbose
```

**Options:**
- `--inventory`: Inventory JSON file (required)
- `--output-dir`: Output directory (default: datasets/<provider>)
- `--limit`: Max datasets to download
- `--skip`: Number of datasets to skip from start
- `--verbose`: Print detailed progress

**Output:** Local datasets directory structure:
```
datasets/hutchinson/
├── hutchinson_001/
│   ├── lab/
│   │   └── soil_analysis.csv
│   ├── survey/
│   │   └── survey_data.zip
│   ├── boundary/
│   │   └── boundary.zip
│   └── metadata.json
├── hutchinson_002/
└── ...
```

---

### 3. `generate_catalog.py`

**Purpose:** Auto-generate catalog.yml entries from downloaded datasets

**What it does:**
- Scans local datasets/ directory
- Maps providers to business IDs
- Generates YAML catalog entries
- Allows manual review before merging

**Usage:**
```bash
# Generate for single provider
python tools/generate_catalog.py \
  --provider hutchinson \
  --output catalog_generated.yml

# Generate for all providers
python tools/generate_catalog.py \
  --all-providers \
  --output catalog_all_providers.yml

# Append directly to catalog.yml (with backup)
python tools/generate_catalog.py \
  --provider hutchinson \
  --append
```

**Options:**
- `--provider`: Provider name to generate for
- `--all-providers`: Generate for all providers
- `--datasets-dir`: Path to datasets directory (default: datasets)
- `--output`: Output file (default: catalog_generated.yml)
- `--append`: Append to existing catalog.yml (creates backup)

**Output:** YAML catalog entries:
```yaml
businesses:
  - id: 7635
    name: Hutchinson_UK
    code: hlh

datasets:
  # HUTCHINSON datasets
  - id: hutchinson_001
    business_id: 7635
    provider: hutchinson
    lab: datasets/hutchinson/hutchinson_001/lab/soil_analysis.csv
    survey: datasets/hutchinson/hutchinson_001/survey/survey_data.zip
    boundary: null
    classification: sanitized
    expected: success
```

---

### 4. `refresh_datasets.py`

**Purpose:** Intelligently refresh datasets from network drives

**What it does:**
- Checks if network files changed since last download
- Only downloads changed files (smart refresh)
- Can force full refresh
- Maintains download history

**Usage:**
```bash
# Smart refresh (only changed files)
python tools/refresh_datasets.py \
  --provider hutchinson

# Force full refresh
python tools/refresh_datasets.py \
  --provider hutchinson \
  --force

# Refresh all providers
python tools/refresh_datasets.py \
  --all-providers
```

**Options:**
- `--provider`: Provider to refresh
- `--all-providers`: Refresh all providers
- `--datasets-dir`: Path to datasets directory
- `--force`: Force full refresh (ignore change detection)
- `--verbose`: Print detailed progress

---

## Complete Workflow

### Phase 1: Single Provider (Hutchinson)

**Goal:** Get 5-10 Hutchinson datasets working

```bash
# Step 1: Explore network drive
python tools/explore_network_datasets.py \
  --provider hutchinson \
  --business-id 7635 \
  --network-path "\\172.16.1.12\SoilData\2025\Hutchinson_UK\Hutchinson_UK" \
  --output inventory_hutchinson.json \
  --limit 10

# Step 2: Review inventory
cat inventory_hutchinson.json | less

# Step 3: Download datasets
python tools/download_datasets.py \
  --inventory inventory_hutchinson.json \
  --output-dir datasets/hutchinson

# Step 4: Generate catalog
python tools/generate_catalog.py \
  --provider hutchinson \
  --output catalog_hutchinson.yml

# Step 5: Review generated catalog
cat catalog_hutchinson.yml

# Step 6: Merge to main catalog (manual review!)
# Backup first
cp catalog.yml catalog.yml.backup

# Append (or manually merge)
cat catalog_hutchinson.yml >> catalog.yml

# Step 7: Run tests
python -m pytest -n auto

# Step 8: Review results
python tools/summarize.py
cat out/summary.md
```

---

### Phase 2: Add More Providers

**Goal:** Scale to 4-8 providers (20-80 datasets)

```bash
# Repeat for each provider
for PROVIDER in danish_agro syngenta croptech glimax; do
  echo "Processing $PROVIDER..."

  # Get provider info
  case $PROVIDER in
    danish_agro)
      BIZ_ID=7619
      NET_PATH="\\172.16.1.12\SoilData\2025\FieldSense\Danish_Agro"
      ;;
    syngenta)
      BIZ_ID=7650
      NET_PATH="\\172.16.1.12\SoilData\2025\Syngenta_Europe\Syngenta_Europe"
      ;;
    croptech)
      BIZ_ID=7616
      NET_PATH="\\172.16.1.12\SoilData\2025\Crop_Tech_Solutions\Crop_Tech_Solutions"
      ;;
    glimax)
      BIZ_ID=7623
      NET_PATH="\\172.16.1.12\SoilData\2025\Glimax\Glimax_-_Agroideas"
      ;;
  esac

  # Explore
  python tools/explore_network_datasets.py \
    --provider $PROVIDER \
    --business-id $BIZ_ID \
    --network-path "$NET_PATH" \
    --output "inventory_${PROVIDER}.json" \
    --limit 10

  # Download
  python tools/download_datasets.py \
    --inventory "inventory_${PROVIDER}.json" \
    --output-dir "datasets/${PROVIDER}"

  echo "Done with $PROVIDER"
  echo ""
done

# Generate catalog for all providers
python tools/generate_catalog.py \
  --all-providers \
  --output catalog_all_generated.yml

# Review and merge
cat catalog_all_generated.yml >> catalog.yml

# Run full test suite
python -m pytest -n auto

# Generate comprehensive report
python tools/summarize.py
```

---

### Phase 3: Ongoing Maintenance

**Weekly refresh:**
```bash
# Refresh all providers (only downloads changed files)
python tools/refresh_datasets.py --all-providers

# Run tests to detect regressions
python -m pytest -n auto

# Compare results with previous week
python tools/summarize.py
```

**Monthly full refresh:**
```bash
# Force full refresh
python tools/refresh_datasets.py --all-providers --force

# Run comprehensive tests
python -m pytest -n auto --include-sensitive
```

---

## Safety Features

### Network Drive Protection

All tools implement **READ-ONLY** operations on network drives:

```python
# Network paths are validated
APPROVED_NETWORK_PATHS = [
    r"\\172.16.1.12\SoilData",
]

# Only read operations are used
shutil.copy2(network_file, local_file)  # Safe: network is source

# Write operations are to local storage only
with open(local_file, 'w') as f:  # Safe: writing to local
    f.write(data)
```

### Customer Name Anonymization

Customer/farm/field names are hashed:

```python
def anonymize_name(name: str) -> str:
    """Anonymize names using SHA256 hash"""
    return hashlib.sha256(f"soiloptix:{name}".encode()).hexdigest()[:8]

# Example:
# "FarmName" -> "a1b2c3d4"
```

### Error Handling

- Network timeouts: Retry with exponential backoff
- File access errors: Log and continue (don't fail entire batch)
- Missing files: Report but don't crash

---

## Testing Strategy

### Test Matrix

With multiple providers and datasets, the test matrix expands:

```
Test Runs = Providers × Datasets per Provider × Repeats

Example:
- 8 providers
- 10 datasets per provider
- 2 repeats for flake detection
= 160 test runs
```

**Runtime estimate:**
- ~30 seconds per test
- 160 tests × 30s = 4,800s = ~80 minutes
- With parallelism (-n auto): ~20-40 minutes

### Organizing Results

Results are automatically grouped by provider in `out/summary.md`:

```markdown
## Summary by Provider

### Hutchinson (10 datasets, 20 runs)
- Pass rate: 95% (19/20)
- Flaky: 0
- Failed: 1

### Danish Agro (10 datasets, 20 runs)
- Pass rate: 100% (20/20)
- Flaky: 0
- Failed: 0
```

---

## Troubleshooting

### "Network path not found"

**Cause:** Not connected to VPN or incorrect path

**Solution:**
```bash
# Check VPN connection
# Verify path exists
ls "\\172.16.1.12\SoilData\2025\Hutchinson_UK\Hutchinson_UK"
```

### "Permission denied"

**Cause:** Insufficient network drive permissions

**Solution:**
- Verify you have read access to network drive
- Contact IT if permissions are missing

### "No datasets found"

**Cause:** Empty or incorrectly structured network path

**Solution:**
```bash
# Explore manually first
python tools/explore_network_datasets.py --verbose
```

### "Dataset file not found during test"

**Cause:** Dataset path mismatch between catalog.yml and actual files

**Solution:**
```bash
# Verify dataset exists
ls datasets/hutchinson/hutchinson_001/

# Regenerate catalog
python tools/generate_catalog.py --provider hutchinson
```

---

## Best Practices

1. **Start Small:** Begin with 5-10 datasets from one provider
2. **Review Before Merging:** Always review generated catalog before merging to catalog.yml
3. **Backup catalog.yml:** Always backup before modifications
4. **Test Incrementally:** Run tests after each provider addition
5. **Use Smart Refresh:** Weekly refresh with `--smart` to save time
6. **Monitor Disk Space:** Datasets can be large (GB per provider)
7. **Clean Old Data:** Remove outdated datasets periodically
8. **Document Failures:** Use bug packets to track and resolve issues

---

## Advanced Topics

### Custom Dataset Selection

Filter datasets during exploration:

```python
# In explore_network_datasets.py, add filtering logic:
def should_include_dataset(dataset_path):
    # Example: Only datasets from 2025
    return "2025" in str(dataset_path)
```

### Parallel Downloads

Download multiple providers simultaneously:

```bash
# In separate terminals
python tools/download_datasets.py --inventory inventory_hutchinson.json &
python tools/download_datasets.py --inventory inventory_danish_agro.json &
wait
```

### Custom Business Mapping

Add new providers in `tools/generate_catalog.py`:

```python
BUSINESS_MAPPING = {
    "new_provider": {
        "id": 9999,
        "name": "New_Provider",
        "code": "newprov",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/9999",
    },
}
```

---

## Next Steps

1. ✅ Run Phase 1 (single provider)
2. ⏭️  Verify tests pass with Hutchinson datasets
3. ⏭️  Add 2-3 more providers (Phase 2)
4. ⏭️  Set up weekly refresh automation
5. ⏭️  Implement analyst portal verification (Phase 3)

---

**Last Updated:** 2025-11-13
**Maintained By:** QA Engineering
