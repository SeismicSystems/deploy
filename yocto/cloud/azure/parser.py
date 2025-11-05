#!/usr/bin/env python3
"""
Azure-specific argument parser.
"""

import argparse

from yocto.cloud.azure.defaults import (
    DEFAULT_CERTBOT_EMAIL,
    DEFAULT_DOMAIN_NAME,
    DEFAULT_DOMAIN_RESOURCE_GROUP,
    DEFAULT_REGION,
    DEFAULT_RESOURCE_GROUP,
    DEFAULT_VM_SIZE,
    VALID_REGIONS,
)


def create_base_parser(description: str) -> argparse.ArgumentParser:
    """Create Azure-specific argument parser.

    Args:
        description: Description for the parser

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Region (Azure-specific)
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        default=None,
        help=(
            f"Azure region (default: {DEFAULT_REGION}). "
            f"Valid regions: {', '.join(sorted(VALID_REGIONS))}"
        ),
    )

    # Resource group
    parser.add_argument(
        "--resource-group",
        type=str,
        default=None,
        help=f"Azure resource group (default: {DEFAULT_RESOURCE_GROUP})",
    )

    # VM size
    parser.add_argument(
        "--vm-size",
        type=str,
        default=None,
        help=f"Azure VM size (default: {DEFAULT_VM_SIZE})",
    )

    # Domain configuration
    parser.add_argument(
        "--domain-resource-group",
        type=str,
        default=None,
        help=f"Domain resource group (default: {DEFAULT_DOMAIN_RESOURCE_GROUP})",
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        default=None,
        help=f"Domain name (default: {DEFAULT_DOMAIN_NAME})",
    )

    # SSL configuration
    parser.add_argument(
        "--certbot-email",
        type=str,
        default=None,
        help=f"Certbot email (default: {DEFAULT_CERTBOT_EMAIL})",
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
