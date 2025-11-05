"""
Azure deployment utilities.

This package contains all Azure-specific functionality including:
- defaults: Default constants for Azure deployments
- api: Azure API wrapper and deployment functions
- parser: Azure-specific argument parser
"""

from yocto.cloud.azure.api import AzureApi
from yocto.cloud.azure.defaults import (
    CONSENSUS_PORT,
    DEFAULT_CERTBOT_EMAIL,
    DEFAULT_DOMAIN_NAME,
    DEFAULT_DOMAIN_RESOURCE_GROUP,
    DEFAULT_REGION,
    DEFAULT_RESOURCE_GROUP,
    DEFAULT_VM_SIZE,
)
from yocto.cloud.azure.parser import create_base_parser

__all__ = [
    # API functions and classes
    "AzureApi",
    # Default constants
    "CONSENSUS_PORT",
    "DEFAULT_CERTBOT_EMAIL",
    "DEFAULT_DOMAIN_NAME",
    "DEFAULT_DOMAIN_RESOURCE_GROUP",
    "DEFAULT_REGION",
    "DEFAULT_RESOURCE_GROUP",
    "DEFAULT_VM_SIZE",
    # Parser functions
    "create_base_parser",
]
