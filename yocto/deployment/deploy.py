import glob
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from yocto.cloud.cloud_config import CloudProvider
from yocto.cloud.cloud_factory import get_cloud_api
from yocto.config import DeployConfigs
from yocto.deployment.proxy import ProxyClient
from yocto.image.measurements import Measurements, write_measurements_tmpfile
from yocto.utils.metadata import load_metadata, write_metadata
from yocto.utils.paths import BuildPaths

logger = logging.getLogger(__name__)


def delete_vm(vm_name: str, home: str) -> bool:
    """
    Delete existing VM using cloud-specific API.
    Returns True if successful, False otherwise.
    """
    metadata = load_metadata(home)
    resources = metadata.get("resources", {})

    # Search for VM in all clouds
    meta = None
    for _, cloud_resources in resources.items():
        if vm_name in cloud_resources:
            meta = cloud_resources[vm_name]
            break

    if not meta:
        logger.error(f"VM {vm_name} not found in metadata")
        return False

    resource_group = meta["vm"]["resourceGroup"]
    region = meta["vm"]["region"]
    artifact = meta["artifact"]
    cloud_provider = CloudProvider(meta["vm"]["cloud"])

    cloud_api = get_cloud_api(cloud_provider)
    return cloud_api.delete_vm(vm_name, resource_group, region, artifact, home)


def deploy_image(
    image_path: Path,
    configs: DeployConfigs,
    ip_name: str,
) -> tuple[str, str]:
    """Deploy image and return (public_ip, data_disk_name).

    Raises an error if deployment fails.
    """
    cloud_api = get_cloud_api(configs.vm.cloud)

    # Check if image_path exists
    if not image_path.exists():
        raise FileNotFoundError(f"Image path not found: {image_path}")

    # Disk
    if cloud_api.disk_exists(configs, image_path):
        logger.warning(
            f"Disk for artifact {image_path.name} already exists for "
            f"{configs.vm.name}, skipping creation"
        )
        # Get the disk name without creating it (for passing to create_vm)
        disk_name = cloud_api.get_disk_name(configs, image_path)
    else:
        disk_name = cloud_api.create_disk(configs, image_path)
    cloud_api.upload_disk(configs, image_path)

    # Security groups
    cloud_api.create_nsg(configs)
    cloud_api.create_standard_nsg_rules(configs)

    # Create and attach persistent data disk at LUN 10 (required by tdx-init)
    data_disk_name = f"{configs.vm.name}-persistent"
    logger.info(f"Creating persistent data disk: {data_disk_name}")
    cloud_api.create_data_disk(
        resource_group=configs.vm.resource_group,
        disk_name=data_disk_name,
        location=configs.vm.location,
        size_gb=1024,  # 1TB default
        show_logs=configs.show_logs,
    )

    # Actually create the VM
    if configs.vm.cloud == CloudProvider.GCP:
        # For GCP, attach the data disk at creation to avoid hot-plug issues
        cloud_api.create_vm(configs, image_path, ip_name, disk_name, data_disk_name)
    else:
        # For Azure, create the VM and then attach the disk
        cloud_api.create_vm(configs, image_path, ip_name, disk_name)
        cloud_api.attach_data_disk(
            resource_group=configs.vm.resource_group,
            vm_name=configs.vm.name,
            disk_name=data_disk_name,
            zone=configs.vm.location,  # Not used by Azure but required by API
            lun=10,  # MUST be LUN 10 for tdx-init
            show_logs=configs.show_logs,
        )

    # Get the VM's IP address
    public_ip = cloud_api.get_vm_ip(
        vm_name=configs.vm.name,
        resource_group=configs.vm.resource_group,
        location=configs.vm.location,
    )
    return (public_ip, data_disk_name)


@dataclass
class DeployOutput:
    configs: DeployConfigs
    artifact: str
    public_ip: str
    home: str
    data_disk_name: str | None = None

    def update_deploy_metadata(self):
        metadata = load_metadata(self.home)
        if "resources" not in metadata:
            metadata["resources"] = {"azure": {}, "gcp": {}}

        cloud = self.configs.vm.cloud
        if cloud not in metadata["resources"]:
            metadata["resources"][cloud] = {}

        vm_metadata = {
            "artifact": self.artifact,
            "public_ip": self.public_ip,
            "domain": self.configs.domain.to_dict(),
            "vm": self.configs.vm.to_dict(),
        }

        # Track data disk if it exists
        if self.data_disk_name:
            vm_metadata["data_disk"] = self.data_disk_name

        metadata["resources"][cloud][self.configs.vm.name] = vm_metadata
        write_metadata(metadata, self.home)


class Deployer:
    def __init__(
        self,
        configs: DeployConfigs,
        image_path: Path,
        measurements: Measurements,
        ip_name: str,
        home: str,
        show_logs: bool = True,
    ):
        self.configs = configs
        self.image_path = image_path
        self.ip_name = ip_name
        self.home = home
        self.show_logs = show_logs

        self.measurements_file = write_measurements_tmpfile(measurements)
        self.proxy: ProxyClient | None = None

    def deploy(self) -> DeployOutput:
        public_ip, data_disk_name = deploy_image(
            image_path=self.image_path,
            configs=self.configs,
            ip_name=self.ip_name,
        )
        if not public_ip:
            raise RuntimeError("Failed to obtain public IP during deployment")

        return DeployOutput(
            configs=self.configs,
            artifact=self.image_path.name,
            public_ip=public_ip,
            home=self.home,
            data_disk_name=data_disk_name,
        )

    def start_proxy_server(self, public_ip: str) -> None:
        # Give 5 seconds to let the VM boot up
        time.sleep(5)
        self.proxy = ProxyClient(public_ip, self.measurements_file, self.home)
        if not self.proxy.start():
            raise RuntimeError("Failed to start proxy server")

    def find_latest_image(self, cloud: str, dev: bool = False) -> Path:
        """Find the most recently built image for the given cloud.

        Args:
            cloud: Cloud provider ("azure", "gcp", etc.)
            dev: Whether to search for dev builds

        Returns:
            Path to the most recent image
        """
        from yocto.cloud.cloud_config import CloudProvider

        cloud_provider = CloudProvider(cloud)
        artifact_pattern = BuildPaths.artifact_pattern(cloud_provider, dev)
        pattern = str(BuildPaths(self.home).artifacts / artifact_pattern)

        image_files = glob.glob(pattern)
        if not image_files:
            raise FileNotFoundError(
                f"No images found matching pattern: {pattern}"
            )

        latest_image = max(image_files, key=lambda x: Path(x).stat().st_mtime)
        logger.info(f"Found latest image: {latest_image}")
        return Path(latest_image)

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.proxy:
            self.proxy.stop()
        if self.measurements_file.exists():
            os.remove(self.measurements_file)
