#!/usr/bin/env python3
"""
GCP API functionality using Google Cloud Python SDKs.
"""

import logging
import os
import tempfile
import time
from pathlib import Path

from google.cloud import compute_v1, resourcemanager_v3, storage

from yocto.cloud.azure.api import AzureApi
from yocto.cloud.cloud_api import CloudApi
from yocto.cloud.gcp.defaults import (
    CONSENSUS_PORT,
    DEFAULT_DISK_TYPE,
    DEFAULT_NETWORK_TIER,
    DEFAULT_NIC_TYPE,
    DEFAULT_PROVISIONING_MODEL,
    DEFAULT_REGION,
)
from yocto.config import DeployConfigs, VmConfigs

logger = logging.getLogger(__name__)


# Disk Operations
def wait_for_extended_operation(
    operation: compute_v1.Operation,
    operation_name: str,
    timeout: int = 600,
) -> None:
    """
    Wait for a Compute Engine operation to complete.

    Args:
        operation: The operation object to wait for
        operation_name: Human-readable name for logging
        timeout: Maximum time to wait in seconds
    """
    start_time = time.time()

    while not operation.done():
        if time.time() - start_time > timeout:
            raise TimeoutError(f"{operation_name} timed out after {timeout} seconds")

        time.sleep(5)
        logger.info(f"Waiting for {operation_name}...")

    if operation.error:
        raise RuntimeError(f"{operation_name} failed: {operation.error}")


class GcpApi(CloudApi):
    """GCP implementation of CloudApi."""

    @staticmethod
    def _upload_to_gcs(
        image_path: Path,
        project: str,
        bucket_name: str,
        blob_name: str,
    ) -> None:
        """Upload image file to Google Cloud Storage."""
        storage_client = storage.Client(project=project)

        # Create bucket if it doesn't exist
        try:
            bucket = storage_client.get_bucket(bucket_name)
            logger.info(f"Using existing bucket: {bucket_name}")
        except Exception:
            logger.info(f"Creating new bucket: {bucket_name}")
            bucket = storage_client.create_bucket(bucket_name, location=DEFAULT_REGION)

        # Upload the file
        blob = bucket.blob(blob_name)

        # Get file size for progress reporting
        file_size = image_path.stat().st_size
        file_size_gb = file_size / (1024**3)
        logger.info(f"Uploading {file_size_gb:.2f} GB to Cloud Storage...")

        blob.upload_from_filename(str(image_path), timeout=3600)

        logger.info(f"Upload complete: gs://{bucket_name}/{blob_name}")

    @staticmethod
    def _create_image_from_gcs(
        project: str,
        image_name: str,
        bucket_name: str,
        blob_name: str,
    ) -> None:
        """Create a GCP image from a Cloud Storage object."""
        image_client = compute_v1.ImagesClient()

        # Check if image already exists
        try:
            image_client.get(project=project, image=image_name)
            logger.info(f"Image {image_name} already exists, skipping creation")
            return
        except Exception:
            pass

        # Create image from Cloud Storage
        image = compute_v1.Image()
        image.name = image_name
        image.source_type = "RAW"
        image.raw_disk = compute_v1.RawDisk()
        image.raw_disk.source = (
            f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
        )

        # Add TDX guest OS feature
        guest_os_feature = compute_v1.GuestOsFeature()
        guest_os_feature.type_ = "TDX"
        image.guest_os_features = [guest_os_feature]

        operation = image_client.insert(project=project, image_resource=image)

        # Wait for operation to complete
        logger.info(f"Waiting for image {image_name} to be created...")
        wait_for_extended_operation(operation, "image creation")
        logger.info(f"Image {image_name} created successfully")

    @staticmethod
    def _create_disk_from_image(
        project: str,
        zone: str,
        disk_name: str,
        image_name: str,
        disk_type: str,
    ) -> None:
        """Create a disk from an image."""
        disk_client = compute_v1.DisksClient()

        disk = compute_v1.Disk()
        disk.name = disk_name
        disk.source_image = f"projects/{project}/global/images/{image_name}"
        disk.type_ = f"projects/{project}/zones/{zone}/diskTypes/{disk_type}"

        operation = disk_client.insert(
            project=project,
            zone=zone,
            disk_resource=disk,
        )

        # Wait for operation to complete
        logger.info(f"Waiting for disk {disk_name} to be created...")
        wait_for_extended_operation(operation, "disk creation")
        logger.info(f"Disk {disk_name} created successfully")

    @staticmethod
    def check_dependencies():
        """Check if required dependencies are available.

        For GCP, all dependencies are Python packages that are imported at
        module load time, so this is a no-op.
        """
        pass

    @classmethod
    def resource_group_exists(cls, name: str) -> bool:
        """Check if project exists (GCP equivalent of resource group)."""
        try:
            client = resourcemanager_v3.ProjectsClient()
            client.get_project(name=f"projects/{name}")
            return True
        except Exception:
            return False

    @classmethod
    def create_resource_group(cls, name: str, location: str) -> None:
        """Create a project (GCP equivalent of resource group).
        Note: In GCP, projects need to be created through console or with
        organization permissions.
        """
        raise RuntimeError(
            f"GCP projects cannot be created via CLI without organization "
            f"access. Please create project {name} manually if it doesn't "
            f"exist."
        )

    @classmethod
    def ensure_created_resource_group(cls, name: str, location: str):
        """Ensure project exists."""
        if cls.resource_group_exists(name):
            logger.info(f"Project {name} already exists")
        else:
            logger.warning(
                f"Project {name} does not exist. "
                f"Please create it manually in the GCP console."
            )

    @classmethod
    def create_public_ip(cls, name: str, resource_group: str) -> str:
        """Create a static public IP address and return it."""
        logger.info(f"Creating static public IP address: {name}")

        address_client = compute_v1.AddressesClient()

        address = compute_v1.Address()
        address.name = name
        address.network_tier = DEFAULT_NETWORK_TIER

        operation = address_client.insert(
            project=resource_group,
            region=DEFAULT_REGION,
            address_resource=address,
        )

        wait_for_extended_operation(operation, "IP address creation")

        # Get the IP address
        address_obj = address_client.get(
            project=resource_group,
            region=DEFAULT_REGION,
            address=name,
        )
        return address_obj.address

    @classmethod
    def get_existing_public_ip(
        cls,
        name: str,
        resource_group: str,
    ) -> str | None:
        """Get existing IP address if it exists."""
        try:
            address_client = compute_v1.AddressesClient()
            address = address_client.get(
                project=resource_group,
                region=DEFAULT_REGION,
                address=name,
            )
            return address.address if address.address else None
        except Exception:
            return None

    @classmethod
    def get_existing_dns_ips(cls, config: DeployConfigs) -> list[str]:
        """Get existing DNS A record IPs.
        Note: This assumes Azure DNS is still being used for DNS management.
        """
        # For now, we'll use Azure DNS even for GCP deployments
        # This can be changed to Cloud DNS later if needed
        return AzureApi.get_existing_dns_ips(config)

    @classmethod
    def remove_dns_ip(cls, config: DeployConfigs, ip_address: str) -> None:
        """Remove IP from DNS A record."""
        # For now, we'll use Azure DNS even for GCP deployments
        AzureApi.remove_dns_ip(config, ip_address)

    @classmethod
    def add_dns_ip(cls, config: DeployConfigs, ip_address: str) -> None:
        """Add IP to DNS A record."""
        # For now, we'll use Azure DNS even for GCP deployments
        AzureApi.add_dns_ip(config, ip_address)

    @classmethod
    def update_dns_record(
        cls,
        config: DeployConfigs,
        ip_address: str,
        remove_old: bool = True,
    ) -> None:
        """Update DNS A record with new IP address."""
        if remove_old:
            previous_ips = cls.get_existing_dns_ips(config)
            for prev_ip in previous_ips:
                if prev_ip:
                    cls.remove_dns_ip(config, prev_ip)

        cls.add_dns_ip(config, ip_address)

    @classmethod
    def disk_exists(cls, config: DeployConfigs, image_path: Path) -> bool:
        """Check if disk exists."""
        disk_name = config.vm.disk_name(image_path)
        try:
            disk_client = compute_v1.DisksClient()
            disk_client.get(
                project=config.vm.resource_group,
                zone=config.vm.location,
                disk=disk_name,
            )
            return True
        except Exception:
            return False

    @classmethod
    def create_disk(cls, config: DeployConfigs, image_path: Path) -> None:
        """Create a managed disk from image.
        This uploads the image to Cloud Storage, creates a GCP image, then
        creates a disk.
        """
        disk_name = config.vm.disk_name(image_path)
        logger.info(f"Creating disk {disk_name}")

        # Setup
        bucket_name = f"{config.vm.resource_group}-images"
        image_name = f"{config.vm.name}-{image_path.stem}".replace(".", "-")
        blob_name = image_path.name

        # Step 1: Upload to Cloud Storage
        logger.info(f"Uploading {image_path.name} to gs://{bucket_name}/{blob_name}")
        cls._upload_to_gcs(
            image_path=image_path,
            project=config.vm.resource_group,
            bucket_name=bucket_name,
            blob_name=blob_name,
        )

        # Step 2: Create image from Cloud Storage
        logger.info(f"Creating image {image_name} from Cloud Storage")
        cls._create_image_from_gcs(
            project=config.vm.resource_group,
            image_name=image_name,
            bucket_name=bucket_name,
            blob_name=blob_name,
        )

        # Step 3: Create disk from image
        logger.info(f"Creating disk {disk_name} from image")
        cls._create_disk_from_image(
            project=config.vm.resource_group,
            zone=config.vm.location,
            disk_name=disk_name,
            image_name=image_name,
            disk_type=DEFAULT_DISK_TYPE,
        )

    @classmethod
    def grant_disk_access(cls, config: DeployConfigs, image_path: Path) -> str:
        """Grant access to disk and return access URI.
        Note: Not needed for GCP workflow.
        """
        raise NotImplementedError("grant_disk_access not needed for GCP")

    @classmethod
    def delete_disk(
        cls, resource_group: str, vm_name: str, artifact: str, zone: str
    ):
        """Delete a disk."""
        disk_name = VmConfigs.get_disk_name(vm_name, artifact)
        logger.info(f"Deleting disk {disk_name} from project {resource_group}")

        disk_client = compute_v1.DisksClient()
        operation = disk_client.delete(
            project=resource_group,
            zone=zone,
            disk=disk_name,
        )

        wait_for_extended_operation(operation, f"disk deletion for {disk_name}")
        logger.info(f"Disk {disk_name} deleted successfully")

    @classmethod
    def copy_disk(
        cls,
        image_path: Path,
        sas_uri: str,
        show_logs: bool = False,
    ) -> None:
        """Copy disk to cloud storage.
        Note: Not needed for GCP workflow.
        """
        raise NotImplementedError("copy_disk not needed for GCP")

    @classmethod
    def revoke_disk_access(cls, config: DeployConfigs, image_path: Path) -> None:
        """Revoke access to disk.
        Note: Not needed for GCP workflow.
        """
        raise NotImplementedError("revoke_disk_access not needed for GCP")

    @classmethod
    def upload_disk(cls, config: DeployConfigs, image_path: Path) -> None:
        """Upload disk image to GCP.
        Note: This is handled in create_disk for GCP.
        """
        logger.info("Disk upload is handled during disk creation for GCP")

    @classmethod
    def create_nsg(cls, config: DeployConfigs) -> None:
        """Create network security group (firewall rules in GCP)."""
        logger.info("Creating firewall rules")
        # GCP uses VPC firewall rules instead of NSGs
        # We'll create them in create_standard_nsg_rules

    @classmethod
    def add_nsg_rule(
        cls,
        config: DeployConfigs,
        name: str,
        priority: str,
        port: str,
        protocol: str,
        source: str,
    ) -> None:
        """Add a single firewall rule."""
        rule_name = f"{config.vm.name}-{name.lower()}"
        protocol_lower = protocol.lower()

        firewall_client = compute_v1.FirewallsClient()

        firewall = compute_v1.Firewall()
        firewall.name = rule_name
        firewall.direction = "INGRESS"
        firewall.priority = int(priority)
        firewall.network = (
            f"projects/{config.vm.resource_group}/global/networks/default"
        )

        # Configure allowed rules
        allowed = compute_v1.Allowed()
        if protocol_lower == "*" or protocol_lower == "all":
            allowed.I_p_protocol = "all"
        else:
            allowed.I_p_protocol = protocol_lower
            if port:
                allowed.ports = [port]

        firewall.allowed = [allowed]
        firewall.source_ranges = [source if source != "*" else "0.0.0.0/0"]

        try:
            operation = firewall_client.insert(
                project=config.vm.resource_group,
                firewall_resource=firewall,
            )
            wait_for_extended_operation(operation, f"firewall rule {rule_name}")
        except Exception as e:
            logger.warning(f"Firewall rule {rule_name} may already exist: {e}")

    @classmethod
    def create_standard_nsg_rules(cls, config: DeployConfigs) -> None:
        """Add all standard security rules."""
        rules = [
            ("AllowSSH", "100", "22", "tcp", config.source_ip, "SSH rule"),
            ("AllowAnyHTTPInbound", "101", "80", "tcp", "*", "HTTP rule (TCP 80)"),
            ("AllowAnyHTTPSInbound", "102", "443", "tcp", "*", "HTTPS rule (TCP 443)"),
            ("TCP7878", "115", "7878", "tcp", "*", "TCP 7878 rule"),
            ("TCP7936", "116", "7936", "tcp", "*", "TCP 7936 rule"),
            ("TCP8545", "110", "8545", "tcp", "*", "TCP 8545 rule"),
            ("TCP8551", "111", "8551", "tcp", "*", "TCP 8551 rule"),
            ("TCP8645", "112", "8645", "tcp", "*", "TCP 8645 rule"),
            ("TCP8745", "113", "8745", "tcp", "*", "TCP 8745 rule"),
            (
                f"ANY{CONSENSUS_PORT}",
                "114",
                f"{CONSENSUS_PORT}",
                "all",
                "*",
                "Any 18551 rule",
            ),
        ]

        for name, priority, port, protocol, source, description in rules:
            logger.info(f"Creating {description}")
            cls.add_nsg_rule(config, name, priority, port, protocol, source)

    @classmethod
    def create_data_disk(
        cls,
        resource_group: str,
        disk_name: str,
        location: str,
        size_gb: int,
        sku: str = "pd-ssd",
        show_logs: bool = False,
    ) -> None:
        """Create a data disk for persistent storage.

        Args:
            location: For GCP, this should be the zone (e.g., 'us-central1-a')
        """
        logger.info(f"Creating data disk: {disk_name} ({size_gb}GB)")

        disk_client = compute_v1.DisksClient()

        disk = compute_v1.Disk()
        disk.name = disk_name
        disk.size_gb = size_gb
        disk.type_ = f"projects/{resource_group}/zones/{location}/diskTypes/{sku}"

        operation = disk_client.insert(
            project=resource_group,
            zone=location,
            disk_resource=disk,
        )

        wait_for_extended_operation(operation, f"data disk creation for {disk_name}")
        logger.info(f"Data disk {disk_name} created successfully")

    @classmethod
    def attach_data_disk(
        cls,
        resource_group: str,
        vm_name: str,
        disk_name: str,
        zone: str,
        lun: int = 10,
        show_logs: bool = False,
    ) -> None:
        """Attach a data disk to a VM.

        Args:
            zone: For GCP, the zone where the VM and disk are located.
        """
        logger.info(f"Attaching data disk {disk_name} to {vm_name}")

        instance_client = compute_v1.InstancesClient()

        attached_disk = compute_v1.AttachedDisk()
        disk_path = f"projects/{resource_group}/zones/{zone}/disks/"
        attached_disk.source = f"{disk_path}{disk_name}"
        attached_disk.auto_delete = False

        operation = instance_client.attach_disk(
            project=resource_group,
            zone=zone,
            instance=vm_name,
            attached_disk_resource=attached_disk,
        )

        wait_for_extended_operation(operation, f"disk attachment for {disk_name}")
        logger.info(f"Disk {disk_name} attached to {vm_name} successfully")

    @classmethod
    def create_user_data_file(cls, config: DeployConfigs) -> str:
        """Create temporary user data file."""
        fd, temp_file = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(f'CERTBOT_EMAIL="{config.email}"\n')
                f.write(f'RECORD_NAME="{config.domain.record}"\n')
                f.write(f'DOMAIN="{config.domain.name}"\n')

            logger.info(f"Created temporary user-data file: {temp_file}")
            with open(temp_file) as f:
                logger.info(f.read())

            return temp_file
        except:
            os.close(fd)
            raise

    @classmethod
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
        """Create a confidential VM without user-data.

        Args:
            location: For GCP, this should be the zone (e.g., 'us-central1-a')
        """
        logger.info("Creating TDX-enabled confidential VM...")

        instance_client = compute_v1.InstancesClient()

        # Configure network interface
        network_interface = compute_v1.NetworkInterface()
        network_interface.network = (
            f"projects/{resource_group}/global/networks/default"
        )
        network_interface.stack_type = "IPV4_ONLY"
        network_interface.nic_type = DEFAULT_NIC_TYPE

        # Configure attached disk
        attached_disk = compute_v1.AttachedDisk()
        attached_disk.boot = True
        attached_disk.auto_delete = True
        attached_disk.mode = "READ_WRITE"
        attached_disk.device_name = vm_name
        attached_disk.source = (
            f"projects/{resource_group}/zones/{location}/disks/{os_disk_name}"
        )

        # Configure shielded instance config
        shielded_config = compute_v1.ShieldedInstanceConfig()
        shielded_config.enable_secure_boot = False
        shielded_config.enable_vtpm = True
        shielded_config.enable_integrity_monitoring = True

        # Configure confidential instance config
        confidential_config = compute_v1.ConfidentialInstanceConfig()
        confidential_config.confidential_instance_type = "TDX"

        # Configure scheduling
        scheduling = compute_v1.Scheduling()
        scheduling.on_host_maintenance = "TERMINATE"
        scheduling.provisioning_model = DEFAULT_PROVISIONING_MODEL

        # Create instance
        instance = compute_v1.Instance()
        instance.name = vm_name
        instance.machine_type = f"zones/{location}/machineTypes/{vm_size}"
        instance.network_interfaces = [network_interface]
        instance.disks = [attached_disk]
        instance.shielded_instance_config = shielded_config
        instance.confidential_instance_config = confidential_config
        instance.scheduling = scheduling

        operation = instance_client.insert(
            project=resource_group,
            zone=location,
            instance_resource=instance,
        )

        wait_for_extended_operation(operation, "VM creation")
        logger.info(f"VM {vm_name} created successfully")

    @classmethod
    def create_vm(cls, config: DeployConfigs, image_path: Path, ip_name: str) -> None:
        """Create the virtual machine with user-data."""
        user_data_file = cls.create_user_data_file(config)

        try:
            logger.info("Booting VM...")

            instance_client = compute_v1.InstancesClient()

            # Read user data content
            with open(user_data_file) as f:
                user_data_content = f.read()

            # Configure network interface
            network_interface = compute_v1.NetworkInterface()
            network_interface.network = (
                f"projects/{config.vm.resource_group}/global/networks/default"
            )
            network_interface.stack_type = "IPV4_ONLY"
            network_interface.nic_type = DEFAULT_NIC_TYPE

            # Configure attached disk
            attached_disk = compute_v1.AttachedDisk()
            attached_disk.boot = True
            attached_disk.auto_delete = True
            attached_disk.mode = "READ_WRITE"
            attached_disk.device_name = config.vm.name
            disk_name = config.vm.disk_name(image_path)
            attached_disk.source = (
                f"projects/{config.vm.resource_group}/zones/"
                f"{config.vm.location}/disks/{disk_name}"
            )

            # Configure shielded instance config
            shielded_config = compute_v1.ShieldedInstanceConfig()
            shielded_config.enable_secure_boot = False
            shielded_config.enable_vtpm = True
            shielded_config.enable_integrity_monitoring = True

            # Configure confidential instance config
            confidential_config = compute_v1.ConfidentialInstanceConfig()
            confidential_config.confidential_instance_type = "TDX"

            # Configure scheduling
            scheduling = compute_v1.Scheduling()
            scheduling.on_host_maintenance = "TERMINATE"
            scheduling.provisioning_model = DEFAULT_PROVISIONING_MODEL

            # Configure metadata with user-data
            metadata = compute_v1.Metadata()
            metadata_item = compute_v1.Items()
            metadata_item.key = "user-data"
            metadata_item.value = user_data_content
            metadata.items = [metadata_item]

            # Create instance
            instance = compute_v1.Instance()
            instance.name = config.vm.name
            instance.machine_type = (
                f"zones/{config.vm.location}/machineTypes/{config.vm.size}"
            )
            instance.network_interfaces = [network_interface]
            instance.disks = [attached_disk]
            instance.shielded_instance_config = shielded_config
            instance.confidential_instance_config = confidential_config
            instance.scheduling = scheduling
            instance.metadata = metadata

            operation = instance_client.insert(
                project=config.vm.resource_group,
                zone=config.vm.location,
                instance_resource=instance,
            )

            wait_for_extended_operation(operation, "VM creation")
            logger.info(f"VM {config.vm.name} created successfully")
        finally:
            os.unlink(user_data_file)
            logger.info(f"Deleted temporary user-data file: {user_data_file}")


