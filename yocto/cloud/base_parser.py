#!/usr/bin/env python3
"""
Base argument parser for cloud-agnostic deployments.
"""

import argparse
from typing import Optional

from yocto.cloud.azure.defaults import (
    DEFAULT_CERTBOT_EMAIL as AZURE_CERTBOT_EMAIL,
    DEFAULT_DOMAIN_NAME as AZURE_DOMAIN_NAME,
    DEFAULT_DOMAIN_RESOURCE_GROUP as AZURE_DOMAIN_RG,
    DEFAULT_REGION as AZURE_REGION,
    DEFAULT_RESOURCE_GROUP as AZURE_RESOURCE_GROUP,
    DEFAULT_VM_SIZE as AZURE_VM_SIZE,
    VALID_REGIONS as AZURE_REGIONS,
)
from yocto.cloud.cloud_config import CloudProvider
from yocto.cloud.gcp.defaults import (
    DEFAULT_PROJECT as GCP_PROJECT,
    DEFAULT_VM_TYPE as GCP_VM_TYPE,
    DEFAULT_ZONE as GCP_ZONE,
    VALID_ZONES as GCP_ZONES,
)


def create_base_parser(
    description: str, cloud: Optional[CloudProvider] = None
) -> argparse.ArgumentParser:
    """Create base argument parser without cloud selection (for cloud-specific tools).

    This parser is for tools that are cloud-agnostic or work with a single cloud provider.
    It includes all common deployment arguments with cloud-specific defaults if cloud is provided.

    Args:
        description: Description for the parser
        cloud: Optional cloud provider to use for defaults (Azure or GCP)

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Determine defaults based on cloud provider
    # Note: Domain/DNS config always uses Azure defaults regardless of cloud provider
    if cloud == CloudProvider.AZURE:
        default_region = AZURE_REGION
        default_resource_group = AZURE_RESOURCE_GROUP
        default_vm_size = AZURE_VM_SIZE
        region_help = f"Azure region (default: {AZURE_REGION}, valid: {', '.join(sorted(AZURE_REGIONS))})"
        resource_group_help = f"Azure resource group (default: {AZURE_RESOURCE_GROUP})"
        vm_size_help = f"Azure VM size (default: {AZURE_VM_SIZE})"
    elif cloud == CloudProvider.GCP:
        default_region = GCP_ZONE
        default_resource_group = GCP_PROJECT
        default_vm_size = GCP_VM_TYPE
        region_help = f"GCP zone (default: {GCP_ZONE}, valid: {', '.join(sorted(GCP_ZONES))})"
        resource_group_help = f"GCP project (default: {GCP_PROJECT})"
        vm_size_help = f"GCP machine type (default: {GCP_VM_TYPE})"
    else:
        # No cloud specified - show both defaults
        default_region = None
        default_resource_group = None
        default_vm_size = None
        region_help = (
            "Cloud region/zone. Defaults:\n"
            f"  Azure: {AZURE_REGION} (valid: {', '.join(sorted(AZURE_REGIONS))})\n"
            f"  GCP: {GCP_ZONE} (valid: {', '.join(sorted(GCP_ZONES))})"
        )
        resource_group_help = (
            "Resource group (Azure) or project (GCP). Defaults:\n"
            f"  Azure: {AZURE_RESOURCE_GROUP}\n"
            f"  GCP: {GCP_PROJECT}"
        )
        vm_size_help = (
            "VM size (Azure) or machine type (GCP). Defaults:\n"
            f"  Azure: {AZURE_VM_SIZE}\n"
            f"  GCP: {GCP_VM_TYPE}"
        )

    # Domain/DNS defaults - always use Azure regardless of cloud provider
    default_domain_rg = AZURE_DOMAIN_RG
    default_domain_name = AZURE_DOMAIN_NAME
    default_certbot_email = AZURE_CERTBOT_EMAIL

    # Region/Zone/Location with aliases
    parser.add_argument(
        "-r",
        "--region",
        "-z",
        "--zone",
        "-l",
        "--location",
        type=str,
        default=default_region,
        dest="region",
        help=region_help,
    )

    # Resource group / Project with aliases
    parser.add_argument(
        "--resource-group",
        "-p",
        "--project",
        type=str,
        default=default_resource_group,
        dest="resource_group",
        help=resource_group_help,
    )

    # VM size / machine type with aliases
    parser.add_argument(
        "--vm-size",
        "--machine-type",
        type=str,
        default=default_vm_size,
        dest="vm_size",
        help=vm_size_help,
    )

    # Domain configuration (always uses Azure for DNS)
    parser.add_argument(
        "--domain-resource-group",
        type=str,
        default=default_domain_rg,
        help=f"Domain resource group for Azure DNS (default: {AZURE_DOMAIN_RG})",
    )
    parser.add_argument(
        "--domain-name",
        type=str,
        default=default_domain_name,
        help=f"Domain name for DNS records (default: {AZURE_DOMAIN_NAME})",
    )

    # SSL configuration
    parser.add_argument(
        "--certbot-email",
        type=str,
        default=default_certbot_email,
        help=f"Certbot email for SSL certificates (default: {AZURE_CERTBOT_EMAIL})",
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
