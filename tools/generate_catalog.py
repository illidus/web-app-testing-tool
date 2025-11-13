#!/usr/bin/env python3
"""
Catalog Generator - SoilOptix Testing Framework

Generates catalog.yml entries from downloaded datasets.

Usage:
    # Generate for single provider
    python tools/generate_catalog.py --provider hutchinson

    # Generate for all providers
    python tools/generate_catalog.py --all-providers

    # Append to existing catalog.yml
    python tools/generate_catalog.py --provider hutchinson --append
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List

# Provider to Business ID mapping
BUSINESS_MAPPING = {
    "hutchinson": {
        "id": 7635,
        "name": "Hutchinson_UK",
        "code": "hlh",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7635",
    },
    "danish_agro": {
        "id": 7619,
        "name": "Danish_Agro",
        "code": "danish_agro",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7619",
    },
    "syngenta": {
        "id": 7650,
        "name": "Syngenta_Europe",
        "code": "syngenta",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7650",
    },
    "croptech": {
        "id": 7616,
        "name": "CropTech",
        "code": "croptech",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7616",
    },
    "glimax": {
        "id": 7623,
        "name": "Glimax_AgroIdeas",
        "code": "glimax",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7623",
    },
    "moose_ag": {
        "id": 7641,
        "name": "Moose_Ag",
        "code": "moose_ag",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7641",
    },
    "mosburger": {
        "id": 7637,
        "name": "Mosburger_Ag",
        "code": "mosburger",
        "url": "https://analystportalstaging.local.soiloptix.com/Businesses/7637",
    },
}


def find_dataset_directories(datasets_dir: Path, provider: str = None) -> List[Path]:
    """
    Find all dataset directories in the datasets folder.

    Args:
        datasets_dir: Path to datasets directory
        provider: Optional provider name to filter by

    Returns:
        List of dataset directory paths
    """
    dataset_dirs = []

    if provider:
        # Look for specific provider
        provider_dir = datasets_dir / provider
        if provider_dir.exists():
            for dataset_dir in provider_dir.iterdir():
                if dataset_dir.is_dir() and (dataset_dir / 'metadata.json').exists():
                    dataset_dirs.append(dataset_dir)
    else:
        # Look for all providers
        for provider_dir in datasets_dir.iterdir():
            if provider_dir.is_dir():
                for dataset_dir in provider_dir.iterdir():
                    if dataset_dir.is_dir() and (dataset_dir / 'metadata.json').exists():
                        dataset_dirs.append(dataset_dir)

    return sorted(dataset_dirs)


def load_metadata(dataset_dir: Path) -> Dict:
    """
    Load metadata.json from dataset directory.

    Args:
        dataset_dir: Path to dataset directory

    Returns:
        Metadata dictionary
    """
    metadata_file = dataset_dir / 'metadata.json'
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_dataset_entry(dataset_dir: Path, metadata: Dict) -> Dict:
    """
    Generate catalog.yml entry for a dataset.

    Args:
        dataset_dir: Path to dataset directory
        metadata: Metadata dictionary

    Returns:
        Dataset entry dictionary
    """
    provider = metadata['provider']
    dataset_id = metadata['id']

    # Find files in dataset
    lab_files = list((dataset_dir / 'lab').glob('*')) if (dataset_dir / 'lab').exists() else []
    survey_files = list((dataset_dir / 'survey').glob('*')) if (dataset_dir / 'survey').exists() else []
    boundary_files = list((dataset_dir / 'boundary').glob('*')) if (dataset_dir / 'boundary').exists() else []

    # Build entry
    entry = {
        "id": dataset_id,
        "business_id": BUSINESS_MAPPING[provider]["id"],
        "provider": provider,
        "classification": "sanitized",  # Real data, anonymized
        "expected": "success",
    }

    # Add file paths (relative to repository root)
    if lab_files:
        entry["lab"] = str(lab_files[0].relative_to(Path.cwd()))
    if survey_files:
        entry["survey"] = str(survey_files[0].relative_to(Path.cwd()))
    if boundary_files:
        entry["boundary"] = str(boundary_files[0].relative_to(Path.cwd()))
    else:
        entry["boundary"] = None

    return entry


def generate_catalog_yaml(datasets_dir: Path, provider: str = None) -> str:
    """
    Generate catalog.yml content for datasets.

    Args:
        datasets_dir: Path to datasets directory
        provider: Optional provider name to filter by

    Returns:
        YAML string for catalog entries
    """
    # Find dataset directories
    dataset_dirs = find_dataset_directories(datasets_dir, provider)

    if not dataset_dirs:
        print(f"⚠️  No datasets found in {datasets_dir}")
        return ""

    print(f"📦 Found {len(dataset_dirs)} datasets")

    # Group datasets by provider
    datasets_by_provider = {}
    for dataset_dir in dataset_dirs:
        metadata = load_metadata(dataset_dir)
        provider_name = metadata['provider']

        if provider_name not in datasets_by_provider:
            datasets_by_provider[provider_name] = []

        entry = generate_dataset_entry(dataset_dir, metadata)
        datasets_by_provider[provider_name].append(entry)

    # Build YAML content
    yaml_lines = []

    # Business definitions
    yaml_lines.append("# Business/Provider Definitions")
    yaml_lines.append("businesses:")
    for provider_name in sorted(datasets_by_provider.keys()):
        biz = BUSINESS_MAPPING[provider_name]
        yaml_lines.append(f"  - id: {biz['id']}")
        yaml_lines.append(f"    name: {biz['name']}")
        yaml_lines.append(f"    code: {biz['code']}")
        yaml_lines.append("")

    yaml_lines.append("")

    # Dataset entries
    yaml_lines.append("# Dataset Definitions")
    yaml_lines.append("# Generated by tools/generate_catalog.py")
    yaml_lines.append("datasets:")

    for provider_name in sorted(datasets_by_provider.keys()):
        yaml_lines.append(f"  # {provider_name.upper()} datasets")

        for entry in datasets_by_provider[provider_name]:
            yaml_lines.append(f"  - id: {entry['id']}")
            yaml_lines.append(f"    business_id: {entry['business_id']}")
            yaml_lines.append(f"    provider: {entry['provider']}")

            if 'lab' in entry:
                yaml_lines.append(f"    lab: {entry['lab']}")
            if 'survey' in entry:
                yaml_lines.append(f"    survey: {entry['survey']}")
            if 'boundary' in entry:
                yaml_lines.append(f"    boundary: {entry['boundary']}")

            yaml_lines.append(f"    classification: {entry['classification']}")
            yaml_lines.append(f"    expected: {entry['expected']}")
            yaml_lines.append("")

    return "\n".join(yaml_lines)


def append_to_catalog(new_content: str, catalog_file: Path) -> None:
    """
    Append new content to existing catalog.yml file.

    Args:
        new_content: New YAML content to append
        catalog_file: Path to catalog.yml file
    """
    # Read existing catalog
    with open(catalog_file, 'r', encoding='utf-8') as f:
        existing_content = f.read()

    # Backup existing catalog
    backup_file = catalog_file.parent / f"{catalog_file.stem}.backup.yml"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(existing_content)

    print(f"💾 Backed up existing catalog to: {backup_file}")

    # Append new content
    with open(catalog_file, 'a', encoding='utf-8') as f:
        f.write("\n\n")
        f.write("# " + "=" * 70 + "\n")
        f.write("# Generated Dataset Entries\n")
        f.write("# " + "=" * 70 + "\n\n")
        f.write(new_content)

    print(f"✅ Appended to: {catalog_file}")


def main():
    """Main entry point for catalog generator."""
    parser = argparse.ArgumentParser(
        description="Generate catalog.yml entries from downloaded datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--provider",
        help="Provider name to generate catalog for (e.g., 'hutchinson')",
    )

    parser.add_argument(
        "--all-providers",
        action="store_true",
        help="Generate catalog for all providers in datasets/",
    )

    parser.add_argument(
        "--datasets-dir",
        default="datasets",
        help="Path to datasets directory (default: datasets)",
    )

    parser.add_argument(
        "--output",
        default="catalog_generated.yml",
        help="Output file for generated catalog (default: catalog_generated.yml)",
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing catalog.yml instead of creating new file",
    )

    args = parser.parse_args()

    try:
        datasets_dir = Path(args.datasets_dir)

        if not datasets_dir.exists():
            raise FileNotFoundError(f"Datasets directory not found: {datasets_dir}")

        if not args.provider and not args.all_providers:
            raise ValueError("Must specify --provider or --all-providers")

        # Generate catalog content
        provider = args.provider if not args.all_providers else None
        yaml_content = generate_catalog_yaml(datasets_dir, provider)

        if not yaml_content:
            print("❌ No catalog entries generated")
            sys.exit(1)

        # Save or append
        if args.append:
            catalog_file = Path("catalog.yml")
            if not catalog_file.exists():
                raise FileNotFoundError(f"catalog.yml not found. Use without --append to create new file.")

            append_to_catalog(yaml_content, catalog_file)
        else:
            output_file = Path(args.output)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            print(f"✅ Generated catalog: {output_file}")
            print()
            print("Next steps:")
            print(f"   1. Review: cat {output_file}")
            print(f"   2. Merge to catalog.yml manually or use --append flag")
            print(f"   3. Update conftest.py to support business_id parameter")
            print(f"   4. Run tests: python -m pytest -n auto")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
