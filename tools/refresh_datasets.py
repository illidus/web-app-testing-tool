#!/usr/bin/env python3
"""
Dataset Refresh Utility - SoilOptix Testing Framework

Intelligently refreshes datasets from network drives:
- Checks if network files have changed since last download
- Only downloads changed files (smart refresh)
- Can force full refresh
- Maintains download history

Usage:
    # Smart refresh (only changed files)
    python tools/refresh_datasets.py --provider hutchinson

    # Force full refresh
    python tools/refresh_datasets.py --provider hutchinson --force

    # Refresh all providers
    python tools/refresh_datasets.py --all-providers
"""

import argparse
import hashlib
import json
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Set UTF-8 encoding for Windows console to support special characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Re-use functions from other tools
import importlib.util

def load_module(module_name, file_path):
    """Dynamically load a Python module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_file_hash(file_path: Path) -> str:
    """
    Calculate MD5 hash of file.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (PermissionError, OSError):
        return ""


def get_file_stats(file_path: Path) -> Dict:
    """
    Get file statistics (size, modified time, hash).

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file stats
    """
    try:
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "hash": get_file_hash(file_path),
        }
    except (PermissionError, OSError):
        return {}


def file_has_changed(network_file: Path, local_file: Path) -> bool:
    """
    Check if network file has changed compared to local file.

    Args:
        network_file: Path to network file
        local_file: Path to local file

    Returns:
        True if file has changed or doesn't exist locally
    """
    if not local_file.exists():
        return True  # New file

    network_stats = get_file_stats(network_file)
    local_stats = get_file_stats(local_file)

    # Compare by hash (most reliable)
    if network_stats.get('hash') and local_stats.get('hash'):
        return network_stats['hash'] != local_stats['hash']

    # Fallback to size and modified time
    if network_stats.get('size') != local_stats.get('size'):
        return True

    if network_stats.get('modified', 0) > local_stats.get('modified', 0):
        return True

    return False


def load_download_history(history_file: Path) -> Dict:
    """
    Load download history from JSON file.

    Args:
        history_file: Path to history file

    Returns:
        Download history dictionary
    """
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"downloads": []}


def save_download_history(history_file: Path, history: Dict) -> None:
    """
    Save download history to JSON file.

    Args:
        history_file: Path to history file
        history: Download history dictionary
    """
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def refresh_datasets(
    provider: str,
    datasets_dir: Path,
    force: bool = False,
    verbose: bool = False
) -> Dict:
    """
    Refresh datasets for a provider.

    Args:
        provider: Provider name
        datasets_dir: Base datasets directory
        force: Force full refresh (ignore change detection)
        verbose: Print detailed progress

    Returns:
        Dictionary with refresh statistics
    """
    provider_dir = datasets_dir / provider

    if not provider_dir.exists():
        raise FileNotFoundError(f"Provider directory not found: {provider_dir}")

    print(f"🔄 Refreshing datasets for provider: {provider}")
    print(f"   Mode: {'Force (full refresh)' if force else 'Smart (changed files only)'}")
    print()

    stats = {
        "total_datasets": 0,
        "total_files": 0,
        "changed_files": 0,
        "skipped_files": 0,
        "errors": 0,
    }

    # Find all datasets
    dataset_dirs = [d for d in provider_dir.iterdir() if d.is_dir() and (d / 'metadata.json').exists()]
    stats["total_datasets"] = len(dataset_dirs)

    for dataset_dir in dataset_dirs:
        print(f"📦 Dataset: {dataset_dir.name}")

        # Load metadata
        with open(dataset_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        source_path = Path(metadata['source_path'])

        if not source_path.exists():
            print(f"   ⚠️  Source path not found: {source_path}")
            stats["errors"] += 1
            continue

        # Check each file type
        for file_type in ['labs', 'surveys', 'boundaries']:
            if not metadata['files'].get(file_type):
                continue

            file_dir = dataset_dir / file_type.rstrip('s')  # labs -> lab, surveys -> survey
            if not file_dir.exists():
                continue

            for local_file in file_dir.glob('*'):
                if not local_file.is_file():
                    continue

                stats["total_files"] += 1

                # Find corresponding network file
                # Match by filename
                network_file = source_path / file_type.capitalize() / local_file.name

                if not network_file.exists():
                    print(f"   ⚠️  Network file not found: {network_file}")
                    stats["errors"] += 1
                    continue

                # Check if file has changed
                if force or file_has_changed(network_file, local_file):
                    # Re-download
                    try:
                        import shutil
                        shutil.copy2(network_file, local_file)
                        stats["changed_files"] += 1

                        if verbose:
                            print(f"   ✅ Updated: {local_file.name}")
                        else:
                            print(f"   ✅ Updated {stats['changed_files']} file(s)", end='\r')
                    except Exception as e:
                        print(f"   ❌ Failed to update {local_file.name}: {e}")
                        stats["errors"] += 1
                else:
                    stats["skipped_files"] += 1
                    if verbose:
                        print(f"   ⏭️  Skipped: {local_file.name} (unchanged)")

        print()  # New line after dataset

    return stats


def main():
    """Main entry point for dataset refresh utility."""
    parser = argparse.ArgumentParser(
        description="Intelligently refresh datasets from network drives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--provider",
        help="Provider name to refresh (e.g., 'hutchinson')",
    )

    parser.add_argument(
        "--all-providers",
        action="store_true",
        help="Refresh all providers in datasets/",
    )

    parser.add_argument(
        "--datasets-dir",
        default="datasets",
        help="Path to datasets directory (default: datasets)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full refresh (ignore change detection)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    args = parser.parse_args()

    try:
        datasets_dir = Path(args.datasets_dir)

        if not datasets_dir.exists():
            raise FileNotFoundError(f"Datasets directory not found: {datasets_dir}")

        if not args.provider and not args.all_providers:
            raise ValueError("Must specify --provider or --all-providers")

        # Determine providers to refresh
        if args.all_providers:
            providers = [d.name for d in datasets_dir.iterdir() if d.is_dir()]
        else:
            providers = [args.provider]

        # Refresh each provider
        total_stats = {
            "total_datasets": 0,
            "total_files": 0,
            "changed_files": 0,
            "skipped_files": 0,
            "errors": 0,
        }

        for provider in providers:
            stats = refresh_datasets(
                provider=provider,
                datasets_dir=datasets_dir,
                force=args.force,
                verbose=args.verbose,
            )

            # Aggregate stats
            for key in total_stats:
                total_stats[key] += stats[key]

        # Print summary
        print("=" * 70)
        print("📊 Refresh Summary")
        print("=" * 70)
        print(f"Providers refreshed: {len(providers)}")
        print(f"Total datasets: {total_stats['total_datasets']}")
        print(f"Total files checked: {total_stats['total_files']}")
        print(f"✅ Updated: {total_stats['changed_files']}")
        print(f"⏭️  Skipped (unchanged): {total_stats['skipped_files']}")
        print(f"❌ Errors: {total_stats['errors']}")
        print()

        if total_stats['changed_files'] > 0:
            print("Next steps:")
            print("   1. Run tests: python -m pytest -n auto")
            print("   2. Compare results with previous runs")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
