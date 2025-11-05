#!/usr/bin/env python3
"""
Unified cloud argument parser.
"""

import argparse
import sys

from yocto.cloud.cloud_config import (
    AZURE_REGIONS,
    GCP_ZONES,
    CloudProvider,
    get_default_region,
    get_default_resource_group,
    get_default_vm_size,
    validate_region,
)


def create_cloud_parser(description: str) -> argparse.ArgumentParser:
    """Create unified argument parser that works across cloud providers.

    Args:
        description: Description for the parser

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Cloud provider selection (required)
    parser.add_argument(
        "--cloud",
        type=str,
        choices=["azure", "gcp"],
        required=True,
        help="Cloud provider to use (azure or gcp)",
    )

    # Region/Zone (optional, defaults based on cloud)
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        help=(
            "Cloud region/zone. Defaults based on --cloud:\n"
            f"  Azure: {get_default_region(CloudProvider.AZURE)} "
            f"(valid: {', '.join(sorted(AZURE_REGIONS))})\n"
            f"  GCP: {get_default_region(CloudProvider.GCP)} "
            f"(valid: {', '.join(sorted(GCP_ZONES)[:5])}...)"
        ),
    )

    # Resource group / Project (optional, defaults based on cloud)
    parser.add_argument(
        "--resource-group",
        type=str,
        help=(
            "Resource group (Azure) or project (GCP). "
            "Defaults based on --cloud:\n"
            f"  Azure: {get_default_resource_group(CloudProvider.AZURE)}\n"
            f"  GCP: {get_default_resource_group(CloudProvider.GCP)}"
        ),
    )

    # VM size / machine type (optional, defaults based on cloud)
    parser.add_argument(
        "--vm-size",
        type=str,
        help=(
            "VM size (Azure) or machine type (GCP). "
            "Defaults based on --cloud:\n"
            f"  Azure: {get_default_vm_size(CloudProvider.AZURE)}\n"
            f"  GCP: {get_default_vm_size(CloudProvider.GCP)}"
        ),
    )

    # Domain configuration
    parser.add_argument(
        "--domain-resource-group",
        type=str,
        default="yocto-testnet",
        help="Domain resource group (default: yocto-testnet)",
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        default="seismictest.net",
        help="Domain name (default: seismictest.net)",
    )

    # SSL configuration
    parser.add_argument(
        "--certbot-email",
        type=str,
        default="c@seismic.systems",
        help="Certbot email (default: c@seismic.systems)",
    )

    # Network configuration
    parser.add_argument(
        "--source-ip",
        type=str,
        help="Source IP address for SSH access. Defaults to this machine's IP",
    )

    # Logging
    parser.add_argument(
        "-v",
        "--logs",
        action="store_true",
        help="If flagged, print build and/or deploy logs as they run",
        default=False,
    )

    # Code path
    parser.add_argument(
        "--code-path",
        default="",
        type=str,
        help="Path to code relative to $HOME",
    )

    # Deployment options (mutually exclusive)
    deploy_parser = parser.add_mutually_exclusive_group(required=True)
    deploy_parser.add_argument(
        "-a",
        "--artifact",
        type=str,
        help=(
            "Artifact to deploy (e.g., "
            "'cvm-image-azure-tdx.rootfs-20241203182636.wic.vhd')"
        ),
    )
    deploy_parser.add_argument(
        "--ip-only",
        action="store_true",
        help="Only deploy genesis IPs",
    )

    return parser


def validate_and_apply_defaults(args: argparse.Namespace) -> argparse.Namespace:
    """Validate arguments and apply cloud-specific defaults.

    Args:
        args: Parsed arguments

    Returns:
        Args with defaults applied and validated

    Raises:
        ValueError: If validation fails
    """
    # Convert cloud string to enum
    cloud = CloudProvider(args.cloud)

    # Apply defaults based on cloud provider
    if args.region is None:
        args.region = get_default_region(cloud)
    if args.resource_group is None:
        args.resource_group = get_default_resource_group(cloud)
    if args.vm_size is None:
        args.vm_size = get_default_vm_size(cloud)

    # Validate region for the selected cloud
    try:
        validate_region(cloud, args.region)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Store cloud enum for later use
    args.cloud_provider = cloud

    return args


def parse_cloud_args(description: str) -> argparse.Namespace:
    """Parse and validate cloud deployment arguments.

    Args:
        description: Description for the parser

    Returns:
        Validated arguments with cloud-specific defaults applied
    """
    parser = create_cloud_parser(description)
    args = parser.parse_args()
    return validate_and_apply_defaults(args)


def confirm(what: str) -> bool:
    """Ask user for confirmation.

    Args:
        what: Description of the action

    Returns:
        True if user confirms, raises ValueError otherwise
    """
    inp = input(f"Are you sure you want to {what}? [y/N]\n")
    if not inp.strip().lower() == "y":
        raise ValueError(f"Aborting; will not {what}")
    return True
