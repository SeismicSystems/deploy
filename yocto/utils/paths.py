from dataclasses import dataclass
from pathlib import Path

if __name__ != "__main__":
    from yocto.cloud.cloud_config import CloudProvider


@dataclass
class BuildPaths:
    def __init__(self, home: str):
        self.home = Path(home)

    @property
    def seismic_images(self) -> Path:
        return self.home / "seismic-images"

    @property
    def artifacts(self) -> Path:
        return self.seismic_images / "build"

    @staticmethod
    def artifact_pattern(cloud: "CloudProvider", dev: bool = False) -> str:
        """Get artifact pattern for the given cloud and dev flag.

        Args:
            cloud: CloudProvider enum (AZURE, GCP, or OVH)
            dev: Whether this is a dev build

        Returns:
            Glob pattern like "azure/seismic-dev-azure-*.vhd" or
            "gcp/seismic-gcp-*.tar.gz"
        """
        prefix = "seismic-dev" if dev else "seismic"

        if cloud == CloudProvider.AZURE:
            # Dev builds use "seismic-dev" prefix
            # e.g., azure/seismic-dev-azure-timestamp.vhd or
            # azure/seismic-azure-timestamp.vhd
            return f"{prefix}-azure-*.vhd"
        elif cloud == CloudProvider.GCP:
            return f"{prefix}-gcp-*.tar.gz"
        else:
            # OVH uses baremetal profile (no PROFILE in build)
            return f"{prefix}-baremetal-*.efi"

    @staticmethod
    def artifact_prefix() -> str:
        """Legacy method for backward compatibility."""
        return "cvm-image-azure-tdx.rootfs"

    @property
    def repo_root(self) -> Path:
        return self.home / "deploy"

    @property
    def deploy_metadata(self) -> Path:
        return self.repo_root / "deploy_metadata.json"

    @property
    def proxy_client(self) -> Path:
        return self.home / "cvm-reverse-proxy/build/proxy-client"
