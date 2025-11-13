#!/usr/bin/env python3
"""
Network Dataset Explorer - SoilOptix Testing Framework

Safely explores network drives to find valid test datasets.
READ-ONLY operations only - no writes to network drives.

Usage:
    python tools/explore_network_datasets.py \\
        --provider hutchinson \\
        --business-id 7635 \\
        --network-path "\\\\172.16.1.12\\SoilData\\2025\\Hutchinson_UK\\Hutchinson_UK" \\
        --output inventory_hutchinson.json \\
        --limit 10
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

# Safety banner
SAFETY_BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  NETWORK DRIVE EXPLORER - READ-ONLY MODE  ⚠️                ║
║                                                                  ║
║  This script will ONLY READ from network drives.                ║
║  NO writes, modifications, or deletions will occur.             ║
║                                                                  ║
║  Approved network paths:                                        ║
║  - \\\\172.16.1.12\\SoilData\\                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Approved network paths for read access
APPROVED_NETWORK_PATHS = [
    r"\\172.16.1.12\SoilData",
]

# Expected folder structure at field level
EXPECTED_FOLDERS = {
    "lab": ["Labs", "Lab"],
    "survey": ["Surveys", "Survey"],
    "boundary": ["Boundaries", "Boundary"],
}

# Folders to ignore (processed data)
IGNORE_FOLDERS = [
    "ProcessedActivities",
    "ProcessedLab",
    "ProcessedSurvey",
    "Processed",
]


def validate_network_path(path: str) -> bool:
    """
    Validate that path is on approved network drives.

    Args:
        path: Network path to validate

    Returns:
        True if path is approved, False otherwise
    """
    return any(path.startswith(approved) for approved in APPROVED_NETWORK_PATHS)


def anonymize_name(name: str, salt: str = "soiloptix") -> str:
    """
    Anonymize customer/farm/field names using hash.

    Args:
        name: Original name to anonymize
        salt: Salt for hashing

    Returns:
        Anonymized hash string (first 8 characters)
    """
    full_hash = hashlib.sha256(f"{salt}:{name}".encode()).hexdigest()
    return full_hash[:8]


def get_folder_size_mb(folder_path: Path) -> float:
    """
    Calculate total size of folder in MB.

    Args:
        folder_path: Path to folder

    Returns:
        Size in megabytes
    """
    total_size = 0
    try:
        for entry in folder_path.rglob('*'):
            if entry.is_file():
                total_size += entry.stat().st_size
    except (PermissionError, OSError):
        pass
    return round(total_size / (1024 * 1024), 2)


def find_numbered_folders(base_path: Path) -> List[Path]:
    """
    Find numbered folders (raw upload directories) within the base path.

    These folders are auto-created by the old system and contain raw upload data.

    Args:
        base_path: Base path to search within

    Returns:
        List of Path objects for numbered folders
    """
    numbered_folders = []

    try:
        for item in base_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                numbered_folders.append(item)
    except (PermissionError, OSError) as e:
        print(f"⚠️  Cannot access {base_path}: {e}", file=sys.stderr)

    return numbered_folders


def validate_dataset_folder(folder_path: Path) -> Optional[Dict]:
    """
    Validate that a numbered folder contains required datasets.

    Args:
        folder_path: Path to numbered folder

    Returns:
        Dictionary with file information if valid, None otherwise
    """
    dataset_info = {
        "labs": [],
        "surveys": [],
        "boundaries": [],
    }

    try:
        subfolders = [f.name for f in folder_path.iterdir() if f.is_dir()]

        # Check for processed folders (we don't want these)
        has_processed = any(ignore in subfolders for ignore in IGNORE_FOLDERS)
        if has_processed:
            # This might be a processed folder, but we can still use raw data
            pass

        # Find Labs folder
        for lab_name in EXPECTED_FOLDERS["lab"]:
            lab_path = folder_path / lab_name
            if lab_path.exists() and lab_path.is_dir():
                # Find CSV/XLSX files
                for ext in ['*.csv', '*.xlsx']:
                    for file in lab_path.glob(ext):
                        if file.is_file() and file.stat().st_size > 0:
                            dataset_info["labs"].append(str(file.relative_to(folder_path)))
                break

        # Find Surveys folder
        for survey_name in EXPECTED_FOLDERS["survey"]:
            survey_path = folder_path / survey_name
            if survey_path.exists() and survey_path.is_dir():
                # Find ZIP files
                for file in survey_path.glob('*.zip'):
                    if file.is_file() and file.stat().st_size > 0:
                        dataset_info["surveys"].append(str(file.relative_to(folder_path)))
                break

        # Find Boundaries folder (optional)
        for boundary_name in EXPECTED_FOLDERS["boundary"]:
            boundary_path = folder_path / boundary_name
            if boundary_path.exists() and boundary_path.is_dir():
                # Find ZIP files
                for file in boundary_path.glob('*.zip'):
                    if file.is_file() and file.stat().st_size > 0:
                        dataset_info["boundaries"].append(str(file.relative_to(folder_path)))
                break

        # Validate: Must have at least Labs and Surveys
        if dataset_info["labs"] and dataset_info["surveys"]:
            return dataset_info
        else:
            return None

    except (PermissionError, OSError) as e:
        print(f"⚠️  Cannot access {folder_path}: {e}", file=sys.stderr)
        return None


def explore_provider_structure(
    network_path: str,
    provider: str,
    business_id: int,
    limit: Optional[int] = None,
    verbose: bool = False
) -> Dict:
    """
    Explore provider network structure to find valid datasets.

    Args:
        network_path: Root network path for provider
        provider: Provider name (e.g., 'hutchinson')
        business_id: Business ID for this provider
        limit: Maximum number of datasets to collect (None = all)
        verbose: Print detailed progress

    Returns:
        Dictionary containing inventory of datasets
    """
    # Validate network path
    if not validate_network_path(network_path):
        raise ValueError(f"Network path not approved: {network_path}")

    base_path = Path(network_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Network path not found: {network_path}")

    print(f"🔍 Exploring: {network_path}")
    print(f"📊 Provider: {provider}")
    print(f"🏢 Business ID: {business_id}")
    if limit:
        print(f"🎯 Limit: {limit} datasets")
    print()

    inventory = {
        "provider": provider,
        "business_id": business_id,
        "network_path": network_path,
        "scanned_at": datetime.now().isoformat(),
        "datasets": [],
    }

    dataset_count = 0

    # Walk through directory structure
    # Structure: Customer -> Farm -> Field -> NumberedFolder
    try:
        for customer_dir in base_path.iterdir():
            if not customer_dir.is_dir():
                continue

            customer_hash = anonymize_name(customer_dir.name)

            if verbose:
                print(f"  📁 Customer: {customer_dir.name} -> {customer_hash}")

            # Look for farm or field folders
            for farm_or_field_dir in customer_dir.iterdir():
                if not farm_or_field_dir.is_dir():
                    continue

                farm_hash = anonymize_name(farm_or_field_dir.name)

                # Check if this is a numbered folder (field level without farm)
                numbered_folders = find_numbered_folders(farm_or_field_dir)

                if numbered_folders:
                    # This is field level
                    for numbered_folder in numbered_folders:
                        if limit and dataset_count >= limit:
                            break

                        dataset_info = validate_dataset_folder(numbered_folder)

                        if dataset_info:
                            dataset_id = f"{provider}_{dataset_count + 1:03d}"

                            dataset_entry = {
                                "id": dataset_id,
                                "path": str(numbered_folder),
                                "customer_hash": customer_hash,
                                "farm_hash": farm_hash,
                                "field_hash": farm_hash,  # Same as farm when no separate farm folder
                                "numbered_folder": numbered_folder.name,
                                "files": dataset_info,
                                "size_mb": get_folder_size_mb(numbered_folder),
                            }

                            inventory["datasets"].append(dataset_entry)
                            dataset_count += 1

                            print(f"  ✅ Found dataset {dataset_id}: {numbered_folder}")
                            if verbose:
                                print(f"     Labs: {len(dataset_info['labs'])}")
                                print(f"     Surveys: {len(dataset_info['surveys'])}")
                                print(f"     Boundaries: {len(dataset_info['boundaries'])}")
                else:
                    # Look for field folders within farm folder
                    for field_dir in farm_or_field_dir.iterdir():
                        if not field_dir.is_dir():
                            continue

                        if limit and dataset_count >= limit:
                            break

                        field_hash = anonymize_name(field_dir.name)

                        # Look for numbered folders
                        numbered_folders = find_numbered_folders(field_dir)

                        for numbered_folder in numbered_folders:
                            if limit and dataset_count >= limit:
                                break

                            dataset_info = validate_dataset_folder(numbered_folder)

                            if dataset_info:
                                dataset_id = f"{provider}_{dataset_count + 1:03d}"

                                dataset_entry = {
                                    "id": dataset_id,
                                    "path": str(numbered_folder),
                                    "customer_hash": customer_hash,
                                    "farm_hash": farm_hash,
                                    "field_hash": field_hash,
                                    "numbered_folder": numbered_folder.name,
                                    "files": dataset_info,
                                    "size_mb": get_folder_size_mb(numbered_folder),
                                }

                                inventory["datasets"].append(dataset_entry)
                                dataset_count += 1

                                print(f"  ✅ Found dataset {dataset_id}: {numbered_folder}")
                                if verbose:
                                    print(f"     Labs: {len(dataset_info['labs'])}")
                                    print(f"     Surveys: {len(dataset_info['surveys'])}")
                                    print(f"     Boundaries: {len(dataset_info['boundaries'])}")

                if limit and dataset_count >= limit:
                    break

            if limit and dataset_count >= limit:
                break

    except (PermissionError, OSError) as e:
        print(f"⚠️  Error exploring directory: {e}", file=sys.stderr)

    print()
    print(f"✅ Found {len(inventory['datasets'])} valid datasets")

    return inventory


def main():
    """Main entry point for network dataset explorer."""
    print(SAFETY_BANNER)

    parser = argparse.ArgumentParser(
        description="Explore network drives for valid SoilOptix test datasets (READ-ONLY)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--provider",
        required=True,
        help="Provider name (e.g., 'hutchinson', 'danish_agro')",
    )

    parser.add_argument(
        "--business-id",
        type=int,
        required=True,
        help="Business ID for this provider (e.g., 7635 for Hutchinson)",
    )

    parser.add_argument(
        "--network-path",
        required=True,
        help="Network path to provider root (e.g., '\\\\172.16.1.12\\SoilData\\2025\\Hutchinson_UK\\Hutchinson_UK')",
    )

    parser.add_argument(
        "--output",
        default="inventory.json",
        help="Output JSON file for inventory (default: inventory.json)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of datasets to collect (default: all)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information",
    )

    args = parser.parse_args()

    try:
        # Explore network structure
        inventory = explore_provider_structure(
            network_path=args.network_path,
            provider=args.provider,
            business_id=args.business_id,
            limit=args.limit,
            verbose=args.verbose,
        )

        # Save inventory to JSON
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved inventory to: {output_path}")
        print()
        print("📊 Summary:")
        print(f"   Provider: {inventory['provider']}")
        print(f"   Business ID: {inventory['business_id']}")
        print(f"   Datasets found: {len(inventory['datasets'])}")

        total_size = sum(d['size_mb'] for d in inventory['datasets'])
        print(f"   Total size: {total_size:.2f} MB")

        print()
        print("Next steps:")
        print(f"   1. Review: {output_path}")
        print(f"   2. Download: python tools/download_datasets.py --inventory {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
