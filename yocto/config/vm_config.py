"""VM configuration dataclass."""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VmConfigs:
    resource_group: str
    name: str
    nsg_name: str
    cloud: str  # Cloud provider: "azure" or "gcp"
    region: str = "eastus"  # Azure region or GCP zone
    size: str = "Standard_EC4es_v5"
    api_port: int = 7878
    client_proxy_port: int = 8080

    @staticmethod
    def from_args(args: argparse.Namespace) -> "VmConfigs":
        # Import at runtime to avoid circular import
        from yocto.cloud.cloud_config import (
            CloudProvider,
            get_default_region,
            get_default_resource_group,
            get_default_vm_size,
            validate_region,
        )

        # Get cloud provider (should be set by parser or passed in)
        if not hasattr(args, "cloud"):
            raise ValueError("args must have 'cloud' attribute set")

        cloud = CloudProvider(args.cloud)

        # Apply cloud-specific defaults if not provided
        resource_group = args.resource_group
        if resource_group is None:
            resource_group = get_default_resource_group(cloud)

        region = args.region
        if region is None:
            region = get_default_region(cloud)

        vm_size = args.vm_size
        if vm_size is None:
            vm_size = get_default_vm_size(cloud)

        # Validate region for the selected cloud
        validate_region(cloud, region)

        return VmConfigs(
            resource_group=resource_group,
            name=resource_group,
            nsg_name=resource_group,
            cloud=args.cloud,  # Store the cloud provider
            region=region,
            size=vm_size,
        )

    def to_dict(self):
        return {
            "resourceGroup": self.resource_group,
            "name": self.name,
            "nsgName": self.nsg_name,
            "cloud": self.cloud,
            "region": self.region,
            "size": self.size,
        }

    # For backwards compatibility
    @property
    def location(self) -> str:
        """Alias for region (backwards compatibility)."""
        return self.region

    @staticmethod
    def get_disk_name(vm_name: str, artifact: str) -> str:
        return f"{vm_name}_{artifact}"

    def disk_name(self, image_path: Path) -> str:
        return self.get_disk_name(self.name, image_path.name)
