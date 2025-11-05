#!/usr/bin/env python3
"""
Cloud provider configuration and validation.
"""

from enum import Enum


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AZURE = "azure"
    GCP = "gcp"


# Valid regions/zones for each cloud provider
AZURE_REGIONS = {
    "eastus",
    "westus3",
    "westeurope",
}

GCP_ZONES = {
    "us-central1-a",
    "asia-northeast1-b",
}


def _get_azure_defaults():
    """Import Azure defaults lazily to avoid circular imports."""
    from yocto.azure.defaults import (
        DEFAULT_REGION,
        DEFAULT_RESOURCE_GROUP,
        DEFAULT_VM_SIZE,
    )

    return DEFAULT_REGION, DEFAULT_RESOURCE_GROUP, DEFAULT_VM_SIZE


def _get_gcp_defaults():
    """Import GCP defaults lazily to avoid circular imports."""
    from yocto.gcp.defaults import DEFAULT_PROJECT, DEFAULT_VM_TYPE, DEFAULT_ZONE

    return DEFAULT_ZONE, DEFAULT_PROJECT, DEFAULT_VM_TYPE


def validate_region(cloud: CloudProvider, region: str) -> None:
    """Validate that the region is valid for the specified cloud provider.

    Args:
        cloud: The cloud provider
        region: The region/zone to validate

    Raises:
        ValueError: If the region is not valid for the cloud provider
    """
    if cloud == CloudProvider.AZURE:
        if region not in AZURE_REGIONS:
            valid_regions = ", ".join(sorted(AZURE_REGIONS))
            raise ValueError(
                f"Invalid Azure region: {region}. "
                f"Valid Azure regions are: {valid_regions}"
            )
    elif cloud == CloudProvider.GCP:
        if region not in GCP_ZONES:
            valid_zones = ", ".join(sorted(GCP_ZONES))
            raise ValueError(
                f"Invalid GCP zone: {region}. Valid GCP zones are: {valid_zones}"
            )


def get_default_region(cloud: CloudProvider) -> str:
    """Get the default region for a cloud provider.

    Args:
        cloud: The cloud provider

    Returns:
        The default region/zone for that provider
    """
    if cloud == CloudProvider.AZURE:
        region, _, _ = _get_azure_defaults()
        return region
    elif cloud == CloudProvider.GCP:
        zone, _, _ = _get_gcp_defaults()
        return zone
    else:
        raise ValueError(f"Unknown cloud provider: {cloud}")


def get_default_resource_group(cloud: CloudProvider) -> str:
    """Get the default resource group/project for a cloud provider.

    Args:
        cloud: The cloud provider

    Returns:
        The default resource group/project name
    """
    if cloud == CloudProvider.AZURE:
        _, resource_group, _ = _get_azure_defaults()
        return resource_group
    elif cloud == CloudProvider.GCP:
        _, project, _ = _get_gcp_defaults()
        return project
    else:
        raise ValueError(f"Unknown cloud provider: {cloud}")


def get_default_vm_size(cloud: CloudProvider) -> str:
    """Get the default VM size/type for a cloud provider.

    Args:
        cloud: The cloud provider

    Returns:
        The default VM size/machine type
    """
    if cloud == CloudProvider.AZURE:
        _, _, vm_size = _get_azure_defaults()
        return vm_size
    elif cloud == CloudProvider.GCP:
        _, _, vm_type = _get_gcp_defaults()
        return vm_type
    else:
        raise ValueError(f"Unknown cloud provider: {cloud}")


def get_cloud_api(cloud: CloudProvider):
    """Get the appropriate CloudApi implementation for a cloud provider.

    Args:
        cloud: The cloud provider

    Returns:
        The CloudApi class for that provider
    """
    if cloud == CloudProvider.AZURE:
        from yocto.azure import AzureApi

        return AzureApi
    elif cloud == CloudProvider.GCP:
        from yocto.gcp import GcpApi

        return GcpApi
    else:
        raise ValueError(f"Unknown cloud provider: {cloud}")
