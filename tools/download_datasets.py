#!/usr/bin/env python3
"""
Dataset Downloader - SoilOptix Testing Framework

Downloads datasets from network drives to local storage based on inventory JSON.
READ-ONLY operations on network drives - only writes to local datasets/ directory.

Usage:
    python tools/download_datasets.py \\
        --inventory inventory_hutchinson.json \\
        --output-dir datasets/hutchinson \\
        --limit 10
"""

import argparse
import json
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Set UTF-8 encoding for Windows console to support special characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Safety banner
SAFETY_BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║  📥  DATASET DOWNLOADER - NETWORK READ-ONLY MODE  📥            ║
║                                                                  ║
║  This script will:                                              ║
║  - READ from network drives (read-only)                         ║
║  - WRITE to local datasets/ directory only                      ║
║                                                                  ║
║  NO modifications to network drives will occur.                 ║
╚══════════════════════════════════════════════════════════════════╝
"""


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path to create
    """
    path.mkdir(parents=True, exist_ok=True)


def copy_file_safe(source: Path, destination: Path, verbose: bool = False) -> bool:
    """
    Safely copy file from network to local storage.

    Args:
        source: Source file path (network)
        destination: Destination file path (local)
        verbose: Print detailed progress

    Returns:
        True if successful, False otherwise
    """
    try:
        if not source.exists():
            print(f"⚠️  Source file not found: {source}", file=sys.stderr)
            return False

        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source, destination)

        if verbose:
            size_mb = destination.stat().st_size / (1024 * 1024)
            print(f"     Copied: {source.name} ({size_mb:.2f} MB)")

        return True

    except (PermissionError, OSError) as e:
        print(f"⚠️  Cannot copy {source}: {e}", file=sys.stderr)
        return False


def download_dataset(
    dataset: Dict,
    output_dir: Path,
    provider: str,
    verbose: bool = False
) -> bool:
    """
    Download a single dataset from network to local storage.

    Args:
        dataset: Dataset dictionary from inventory
        output_dir: Output directory for this provider
        provider: Provider name
        verbose: Print detailed progress

    Returns:
        True if successful, False otherwise
    """
    dataset_id = dataset['id']
    source_path = Path(dataset['path'])

    # Create dataset directory
    dataset_dir = output_dir / dataset_id
    ensure_directory(dataset_dir)

    print(f"📦 Downloading: {dataset_id}")

    success = True
    file_count = 0

    # Download Lab files
    if dataset['files']['labs']:
        lab_dir = dataset_dir / 'lab'
        ensure_directory(lab_dir)

        for lab_file in dataset['files']['labs']:
            source_file = source_path / lab_file
            dest_file = lab_dir / Path(lab_file).name

            if copy_file_safe(source_file, dest_file, verbose):
                file_count += 1
            else:
                success = False

    # Download Survey files
    if dataset['files']['surveys']:
        survey_dir = dataset_dir / 'survey'
        ensure_directory(survey_dir)

        for survey_file in dataset['files']['surveys']:
            source_file = source_path / survey_file
            dest_file = survey_dir / Path(survey_file).name

            if copy_file_safe(source_file, dest_file, verbose):
                file_count += 1
            else:
                success = False

    # Download Boundary files (optional)
    if dataset['files']['boundaries']:
        boundary_dir = dataset_dir / 'boundary'
        ensure_directory(boundary_dir)

        for boundary_file in dataset['files']['boundaries']:
            source_file = source_path / boundary_file
            dest_file = boundary_dir / Path(boundary_file).name

            if copy_file_safe(source_file, dest_file, verbose):
                file_count += 1
            else:
                success = False

    # Create metadata file
    metadata = {
        "id": dataset_id,
        "provider": provider,
        "source_path": str(source_path),
        "customer_hash": dataset.get('customer_hash'),
        "farm_hash": dataset.get('farm_hash'),
        "field_hash": dataset.get('field_hash'),
        "numbered_folder": dataset.get('numbered_folder'),
        "files": dataset['files'],
        "size_mb": dataset.get('size_mb', 0),
        "downloaded_at": datetime.now().isoformat(),
    }

    metadata_file = dataset_dir / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    if success:
        print(f"   ✅ Success: {file_count} files downloaded")
    else:
        print(f"   ⚠️  Partial: {file_count} files downloaded (some failed)")

    return success


def download_all_datasets(
    inventory_file: Path,
    output_dir: Path,
    limit: int = None,
    skip: int = 0,
    verbose: bool = False
) -> Dict:
    """
    Download all datasets from inventory to local storage.

    Args:
        inventory_file: Path to inventory JSON file
        output_dir: Output directory for datasets
        limit: Maximum number of datasets to download
        skip: Number of datasets to skip
        verbose: Print detailed progress

    Returns:
        Dictionary with download statistics
    """
    # Load inventory
    with open(inventory_file, 'r', encoding='utf-8') as f:
        inventory = json.load(f)

    provider = inventory['provider']
    business_id = inventory['business_id']
    datasets = inventory['datasets']

    print(f"📋 Inventory: {inventory_file}")
    print(f"📊 Provider: {provider} (Business ID: {business_id})")
    print(f"📦 Total datasets: {len(datasets)}")

    if skip > 0:
        print(f"⏭️  Skipping first {skip} datasets")
        datasets = datasets[skip:]

    if limit:
        print(f"🎯 Downloading: {limit} datasets")
        datasets = datasets[:limit]
    else:
        print(f"🎯 Downloading: All {len(datasets)} datasets")

    print()

    # Create output directory
    ensure_directory(output_dir)

    # Download datasets
    stats = {
        "total": len(datasets),
        "successful": 0,
        "failed": 0,
        "start_time": datetime.now().isoformat(),
    }

    for idx, dataset in enumerate(datasets, 1):
        print(f"[{idx}/{len(datasets)}] ", end="")

        if download_dataset(dataset, output_dir, provider, verbose):
            stats["successful"] += 1
        else:
            stats["failed"] += 1

        print()

    stats["end_time"] = datetime.now().isoformat()

    return stats


def main():
    """Main entry point for dataset downloader."""
    print(SAFETY_BANNER)

    parser = argparse.ArgumentParser(
        description="Download datasets from network drives to local storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--inventory",
        required=True,
        help="Inventory JSON file from explore_network_datasets.py",
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for datasets (default: datasets/<provider>)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of datasets to download (default: all)",
    )

    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of datasets to skip from start (default: 0)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    args = parser.parse_args()

    try:
        inventory_file = Path(args.inventory)

        if not inventory_file.exists():
            raise FileNotFoundError(f"Inventory file not found: {inventory_file}")

        # Load inventory to get provider name
        with open(inventory_file, 'r', encoding='utf-8') as f:
            inventory = json.load(f)

        provider = inventory['provider']

        # Determine output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = Path('datasets') / provider

        # Download datasets
        stats = download_all_datasets(
            inventory_file=inventory_file,
            output_dir=output_dir,
            limit=args.limit,
            skip=args.skip,
            verbose=args.verbose,
        )

        # Print summary
        print("=" * 70)
        print("📊 Download Summary")
        print("=" * 70)
        print(f"Total datasets: {stats['total']}")
        print(f"✅ Successful: {stats['successful']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📁 Output directory: {output_dir}")
        print()

        if stats['successful'] > 0:
            print("Next steps:")
            print(f"   1. Review downloaded datasets: ls -R {output_dir}")
            print(f"   2. Generate catalog: python tools/generate_catalog.py --provider {provider}")
            print(f"   3. Run tests: python -m pytest -n auto")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
