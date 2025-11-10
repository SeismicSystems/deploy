from dataclasses import dataclass
from pathlib import Path

if __name__ != "__main__":
    from yocto.cloud.cloud_config import CloudProvider


@dataclass
class BuildPaths:
    def __init__(self, home: str):
        self.home = Path(home)

    @property
    def yocto_manifests(self) -> Path:
        return self.home / "yocto-manifests"

    @property
    def flashbots_images(self) -> Path:
        return self.home / "flashbots-images"

    @property
    def artifacts(self) -> Path:
        return self.flashbots_images / "build"

    @staticmethod
    def artifact_pattern(cloud: "CloudProvider", dev: bool = False) -> str:
        """Get artifact pattern for the given cloud and dev flag.

        Args:
            cloud: CloudProvider enum (AZURE, GCP, or OVH)
            dev: Whether this is a dev build

        Returns:
            Glob pattern like "seismic-dev-azure-*.vhd" or "seismic-gcp-*.tar.gz"
        """
        prefix = "seismic-dev" if dev else "seismic"

        if cloud == CloudProvider.AZURE:
            return f"{prefix}-azure-*.vhd"
        elif cloud == CloudProvider.GCP:
            return f"{prefix}-gcp-*.tar.gz"
        elif cloud == CloudProvider.OVH:
            # OVH uses baremetal profile (no PROFILE in build)
            return f"{prefix}-baremetal-*.efi"
        else:
            # Bare metal or unknown
            return f"{prefix}-baremetal-*.efi"

    @staticmethod
    def artifact_prefix() -> str:
        """Legacy method for backward compatibility."""
        return "cvm-image-azure-tdx.rootfs"

    @property
    def meta_seismic(self) -> Path:
        return self.home / "meta-seismic"

    @property
    def measured_boot(self) -> Path:
        return self.home / "measured-boot"

    @property
    def enclave_bb(self) -> str:
        return "recipes-nodes/enclave/enclave.bb"

    @property
    def sreth_bb(self) -> str:
        return "recipes-nodes/reth/reth.bb"

    @property
    def summit_bb(self) -> str:
        return "recipes-nodes/summit/summit.bb"

    @property
    def repo_root(self) -> Path:
        return self.home / "deploy"

    @property
    def deploy_script(self) -> Path:
        return self.repo_root / "deploy.sh"

    @property
    def deploy_metadata(self) -> Path:
        return self.repo_root / "deploy_metadata.json"

    @property
    def proxy_client(self) -> Path:
        return self.home / "cvm-reverse-proxy/build/proxy-client"

    @property
    def source_env(self) -> Path:
        return self.home / "yocto-manifests/build/srcs/poky"
