#!/usr/bin/env python3
"""
Base Cloud API abstraction.
Defines the interface that cloud providers (Azure, GCP) must implement.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yocto.config.deploy_config import DeployConfigs


class CloudApi(ABC):
    """Abstract base class for cloud provider APIs."""

    @staticmethod
    @abstractmethod
    def run_command(
        cmd: list[str],
        show_logs: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute a cloud CLI command."""
        pass

    @staticmethod
    @abstractmethod
    def check_dependencies():
        """Check if required tools are installed."""
        pass

    @classmethod
    @abstractmethod
    def resource_group_exists(cls, name: str) -> bool:
        """Check if resource group exists."""
        pass

    @classmethod
    @abstractmethod
    def create_resource_group(cls, name: str, location: str) -> None:
        """Create a resource group."""
        pass

    @classmethod
    @abstractmethod
    def ensure_created_resource_group(cls, name: str, location: str):
        """Ensure resource group exists."""
        pass

    @classmethod
    @abstractmethod
    def create_public_ip(cls, name: str, resource_group: str) -> str:
        """Create a static public IP address and return it."""
        pass

    @classmethod
    @abstractmethod
    def get_existing_public_ip(
        cls,
        name: str,
        resource_group: str,
    ) -> str | None:
        """Get existing IP address if it exists."""
        pass

    @classmethod
    @abstractmethod
    def get_existing_dns_ips(cls, config: "DeployConfigs") -> list[str]:
        """Get existing DNS A record IPs."""
        pass

    @classmethod
    @abstractmethod
    def remove_dns_ip(cls, config: "DeployConfigs", ip_address: str) -> None:
        """Remove IP from DNS A record."""
        pass

    @classmethod
    @abstractmethod
    def add_dns_ip(cls, config: "DeployConfigs", ip_address: str) -> None:
        """Add IP to DNS A record."""
        pass

    @classmethod
    @abstractmethod
    def update_dns_record(
        cls,
        config: "DeployConfigs",
        ip_address: str,
        remove_old: bool = True,
    ) -> None:
        """Update DNS A record with new IP address."""
        pass

    @classmethod
    @abstractmethod
    def disk_exists(cls, config: "DeployConfigs", image_path: Path) -> bool:
        """Check if disk exists."""
        pass

    @classmethod
    @abstractmethod
    def create_disk(cls, config: "DeployConfigs", image_path: Path) -> None:
        """Create a managed disk for upload."""
        pass

    @classmethod
    @abstractmethod
    def grant_disk_access(cls, config: "DeployConfigs", image_path: Path) -> str:
        """Grant access to disk and return access URI."""
        pass

    @classmethod
    @abstractmethod
    def delete_disk(cls, resource_group: str, vm_name: str, artifact: str, zone: str):
        """Delete a disk."""
        pass

    @classmethod
    @abstractmethod
    def copy_disk(
        cls,
        image_path: Path,
        access_uri: str,
        show_logs: bool = False,
    ) -> None:
        """Copy disk to cloud storage."""
        pass

    @classmethod
    @abstractmethod
    def revoke_disk_access(cls, config: "DeployConfigs", image_path: Path) -> None:
        """Revoke access to disk."""
        pass

    @classmethod
    @abstractmethod
    def upload_disk(cls, config: "DeployConfigs", image_path: Path) -> None:
        """Upload disk image to cloud."""
        pass

    @classmethod
    @abstractmethod
    def create_nsg(cls, config: "DeployConfigs") -> None:
        """Create network security group / firewall rules."""
        pass

    @classmethod
    @abstractmethod
    def add_nsg_rule(
        cls,
        config: "DeployConfigs",
        name: str,
        priority: str,
        port: str,
        protocol: str,
        source: str,
    ) -> None:
        """Add a single network security rule."""
        pass

    @classmethod
    @abstractmethod
    def create_standard_nsg_rules(cls, config: "DeployConfigs") -> None:
        """Add all standard security rules."""
        pass

    @classmethod
    @abstractmethod
    def create_data_disk(
        cls,
        resource_group: str,
        disk_name: str,
        location: str,
        size_gb: int,
        sku: str = "Premium_LRS",
        show_logs: bool = False,
    ) -> None:
        """Create a data disk for persistent storage."""
        pass

    @classmethod
    @abstractmethod
    def attach_data_disk(
        cls,
        resource_group: str,
        vm_name: str,
        disk_name: str,
        zone: str,
        lun: int = 10,
        show_logs: bool = False,
    ) -> None:
        """Attach a data disk to a VM."""
        pass

    @classmethod
    @abstractmethod
    def create_user_data_file(cls, config: "DeployConfigs") -> str:
        """Create temporary user data file."""
        pass

    @classmethod
    @abstractmethod
    def create_vm_simple(
        cls,
        vm_name: str,
        vm_size: str,
        resource_group: str,
        location: str,
        os_disk_name: str,
        nsg_name: str,
        ip_name: str,
        show_logs: bool = False,
    ) -> None:
        """Create a confidential VM without user-data."""
        pass

    @classmethod
    @abstractmethod
    def create_vm(cls, config: "DeployConfigs", image_path: Path, ip_name: str) -> None:
        """Create the virtual machine with user-data."""
        pass
