"""VM configuration dataclass."""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VmConfigs:
    resource_group: str
    name: str
    nsg_name: str
    region: str = "eastus"  # Azure region or GCP zone
    size: str = "Standard_EC4es_v5"
    api_port: int = 7878
    client_proxy_port: int = 8080

    @staticmethod
    def from_args(args: argparse.Namespace) -> "VmConfigs":
        if not args.resource_group:
            raise ValueError(
                "If passing in --deploy, you must specify a --resource-group"
            )
        return VmConfigs(
            resource_group=args.resource_group,
            name=args.resource_group,
            nsg_name=args.resource_group,
            region=args.region,
            size=args.vm_size,
        )

    def to_dict(self):
        return {
            "resourceGroup": self.resource_group,
            "name": self.name,
            "nsgName": self.nsg_name,
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
