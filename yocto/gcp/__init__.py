"""
GCP deployment utilities.

This package contains all GCP-specific functionality including:
- defaults: Default constants for GCP deployments
- api: GCP API wrapper and deployment functions
"""

from yocto.gcp.api import GcpApi, confirm, create_base_parser, get_disk_size
from yocto.gcp.defaults import (
    CONSENSUS_PORT,
    DEFAULT_CERTBOT_EMAIL,
    DEFAULT_DISK_SIZE_GB,
    DEFAULT_DISK_TYPE,
    DEFAULT_DOMAIN_NAME,
    DEFAULT_DOMAIN_RESOURCE_GROUP,
    DEFAULT_NETWORK_TIER,
    DEFAULT_NIC_TYPE,
    DEFAULT_PROJECT,
    DEFAULT_PROVISIONING_MODEL,
    DEFAULT_REGION,
    DEFAULT_VM_TYPE,
    DEFAULT_ZONE,
)

__all__ = [
    # API functions and classes
    "GcpApi",
    "confirm",
    "create_base_parser",
    "get_disk_size",
    # Default constants
    "CONSENSUS_PORT",
    "DEFAULT_CERTBOT_EMAIL",
    "DEFAULT_DISK_SIZE_GB",
    "DEFAULT_DISK_TYPE",
    "DEFAULT_DOMAIN_NAME",
    "DEFAULT_DOMAIN_RESOURCE_GROUP",
    "DEFAULT_NIC_TYPE",
    "DEFAULT_NETWORK_TIER",
    "DEFAULT_PROJECT",
    "DEFAULT_PROVISIONING_MODEL",
    "DEFAULT_REGION",
    "DEFAULT_VM_TYPE",
    "DEFAULT_ZONE",
]
