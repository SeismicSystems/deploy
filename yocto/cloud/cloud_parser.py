#!/usr/bin/env python3
"""
Unified cloud argument parser.
"""

import argparse

from yocto.cloud.cloud_config import (
    AZURE_REGIONS,
    GCP_ZONES,
    CloudProvider,
    get_default_region,
    get_default_resource_group,
    get_default_vm_size,
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


def parse_cloud_args(description: str) -> argparse.Namespace:
    """Parse cloud deployment arguments.

    Args:
        description: Description for the parser

    Returns:
        Parsed arguments (defaults will be applied in config.from_args())
    """
    parser = create_cloud_parser(description)
    args = parser.parse_args()
    return args


def create_base_parser(description: str) -> argparse.ArgumentParser:
    """Create base argument parser without cloud selection (for cloud-specific tools).

    This parser is for tools that are cloud-agnostic or work with a single cloud provider.
    It includes all common deployment arguments with defaults shown for both Azure and GCP.

    Args:
        description: Description for the parser

    Returns:
        Configured ArgumentParser
    """
    # Import defaults here to avoid circular imports
    from yocto.cloud.azure.defaults import (
        DEFAULT_CERTBOT_EMAIL as AZURE_CERTBOT_EMAIL,
        DEFAULT_DOMAIN_NAME as AZURE_DOMAIN_NAME,
        DEFAULT_DOMAIN_RESOURCE_GROUP as AZURE_DOMAIN_RG,
        DEFAULT_REGION as AZURE_REGION,
        DEFAULT_RESOURCE_GROUP as AZURE_RESOURCE_GROUP,
        DEFAULT_VM_SIZE as AZURE_VM_SIZE,
        VALID_REGIONS as AZURE_REGIONS,
    )
    from yocto.cloud.gcp.defaults import (
        DEFAULT_CERTBOT_EMAIL as GCP_CERTBOT_EMAIL,
        DEFAULT_DOMAIN_NAME as GCP_DOMAIN_NAME,
        DEFAULT_DOMAIN_RESOURCE_GROUP as GCP_DOMAIN_RG,
        DEFAULT_PROJECT as GCP_PROJECT,
        DEFAULT_VM_TYPE as GCP_VM_TYPE,
        DEFAULT_ZONE as GCP_ZONE,
        VALID_ZONES as GCP_ZONES,
    )

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Region/Zone
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        default=None,
        help=(
            "Cloud region/zone. Defaults:\n"
            f"  Azure: {AZURE_REGION} (valid: {', '.join(sorted(AZURE_REGIONS))})\n"
            f"  GCP: {GCP_ZONE} (valid: {', '.join(sorted(GCP_ZONES))}...)"
        ),
    )

    # Resource group / Project
    parser.add_argument(
        "--resource-group",
        type=str,
        default=None,
        help=(
            "Resource group (Azure) or project (GCP). Defaults:\n"
            f"  Azure: {AZURE_RESOURCE_GROUP}\n"
            f"  GCP: {GCP_PROJECT}"
        ),
    )

    # VM size / machine type
    parser.add_argument(
        "--vm-size",
        type=str,
        default=None,
        help=(
            "VM size (Azure) or machine type (GCP). Defaults:\n"
            f"  Azure: {AZURE_VM_SIZE}\n"
            f"  GCP: {GCP_VM_TYPE}"
        ),
    )

    # Domain configuration
    parser.add_argument(
        "--domain-resource-group",
        type=str,
        default=None,
        help=(
            f"Domain resource group. Defaults:\n"
            f"  Azure: {AZURE_DOMAIN_RG}\n"
            f"  GCP: {GCP_DOMAIN_RG}"
        ),
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        default=None,
        help=(
            f"Domain name. Defaults:\n"
            f"  Azure: {AZURE_DOMAIN_NAME}\n"
            f"  GCP: {GCP_DOMAIN_NAME}"
        ),
    )

    # SSL configuration
    parser.add_argument(
        "--certbot-email",
        type=str,
        default=None,
        help=(
            f"Certbot email. Defaults:\n"
            f"  Azure: {AZURE_CERTBOT_EMAIL}\n"
            f"  GCP: {GCP_CERTBOT_EMAIL}"
        ),
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
