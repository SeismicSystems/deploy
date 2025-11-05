"""
Azure deployment utilities.

This package contains all Azure-specific functionality including:
- defaults: Default constants for Azure deployments
- api: Azure API wrapper and deployment functions
"""

from yocto.azure.api import AzureApi, confirm, create_base_parser, get_disk_size
from yocto.azure.defaults import (
    CONSENSUS_PORT,
    DEFAULT_CERTBOT_EMAIL,
    DEFAULT_DOMAIN_NAME,
    DEFAULT_DOMAIN_RESOURCE_GROUP,
    DEFAULT_REGION,
    DEFAULT_RESOURCE_GROUP,
    DEFAULT_VM_SIZE,
)

__all__ = [
    # API functions and classes
    "AzureApi",
    "confirm",
    "create_base_parser",
    "get_disk_size",
    # Default constants
    "CONSENSUS_PORT",
    "DEFAULT_CERTBOT_EMAIL",
    "DEFAULT_DOMAIN_NAME",
    "DEFAULT_DOMAIN_RESOURCE_GROUP",
    "DEFAULT_REGION",
    "DEFAULT_RESOURCE_GROUP",
    "DEFAULT_VM_SIZE",
]
