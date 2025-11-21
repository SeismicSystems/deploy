import datetime
import glob
import logging
import os
import re

from yocto.utils.metadata import load_metadata, remove_artifact_from_metadata
from yocto.utils.paths import BuildPaths

logger = logging.getLogger(__name__)


def _extract_timestamp(artifact: str):
    """
    Extract timestamp from artifact filename
        Old format: 'cvm-image-azure-tdx.rootfs-20241202202935.wic.vhd'
        New format: 'seismic-dev-azure-20250110120000.vhd'
    Returns the timestamp if found, None otherwise
    """

    pattern = r".*?(\d{14}).*"
    match = re.search(pattern, artifact)
    if not match:
        example_old = "cvm-image-azure-tdx.rootfs-20241202202935.wic.vhd"
        example_new = "seismic-dev-azure-20250110120000.vhd"
        msg = (
            f"Invalid artifact name: {artifact}. "
            f'Should be like "{example_old}" or "{example_new}"'
        )
        raise ValueError(msg)
    return match.group(1)


def artifact_timestamp(artifact: str) -> int:
    """
    Extract timestamp from artifact filename
        e.g. 'cvm-image-azure-tdx.rootfs-20241202202935.wic.vhd'
    Returns the timestamp if found, None otherwise
    """
    ts_string = _extract_timestamp(artifact)
    if not ts_string:
        raise ValueError(f"Invalid artifact name: {artifact}")
    dt = datetime.datetime.strptime(ts_string, "%Y%m%d%H%M%S")
    return int(dt.timestamp())


def _artifact_from_timestamp(
    timestamp: str, home: str, dev: bool = False
) -> str | None:
    """Find artifact file by timestamp.

    Searches the artifacts directory for files matching the timestamp.
    Returns the filename if found, or constructs a legacy name as fallback.

    Args:
        timestamp: 14-digit timestamp string
        home: Home directory path
        dev: If True, prefer dev artifacts (seismic-dev-*), else prefer non-dev

    Returns:
        Artifact filename
    """
    artifacts_path = BuildPaths(home).artifacts

    # Search for any file with this timestamp
    matches = list(glob.glob(f"{artifacts_path}/*{timestamp}*"))
    if matches:
        # Filter by dev preference
        if dev:
            dev_matches = [m for m in matches if "-dev-" in os.path.basename(m)]
            if dev_matches:
                matches = dev_matches
        else:
            non_dev_matches = [
                m for m in matches if "-dev-" not in os.path.basename(m)
            ]
            if non_dev_matches:
                matches = non_dev_matches

        # Return the basename of the first match (preferring .vhd, .tar.gz, or .efi)
        for ext in [".vhd", ".tar.gz", ".efi"]:
            for match in matches:
                if match.endswith(ext):
                    return os.path.basename(match)
        # If no preferred extension, just return first match
        return os.path.basename(matches[0])

    # Fallback to legacy format
    return f"{BuildPaths.artifact_prefix()}-{timestamp}.wic.vhd"


def parse_artifact(
    artifact_arg: str | None, home: str | None = None, dev: bool = False
) -> str | None:
    if not artifact_arg:
        return None

    if len(artifact_arg) == 14:
        if all(a.isdigit() for a in artifact_arg):
            if home is None:
                raise ValueError("home parameter required when parsing timestamp")
            return _artifact_from_timestamp(artifact_arg, home, dev)

    # Validate that it's correctly named
    timestamp = _extract_timestamp(artifact_arg)

    # If full artifact name provided, just return it
    # (it already has the correct format - either old or new)
    return artifact_arg


def expect_artifact(artifact_arg: str, home: str, dev: bool = False) -> str:
    artifact = parse_artifact(artifact_arg, home, dev)
    if artifact is None:
        raise ValueError("Empty --artifact")
    return artifact


def delete_artifact(artifact: str, home: str):
    resources = load_metadata(home).get("resources", {})

    # Iterate over clouds and VMs to find where artifact is deployed
    deployed_to = []
    for cloud, cloud_resources in resources.items():
        for vm_name, resource in cloud_resources.items():
            if resource.get("artifact") == artifact:
                deployed_to.append(f"{vm_name} ({cloud})")

    if deployed_to:
        confirm = input(
            f'\nThe artifact "{artifact}" is deployed to '
            f"{len(deployed_to)} VM(s):"
            f"\n - {'\n - '.join(deployed_to)}\n\n"
            "Are you really sure you want to delete it? "
            "This will not delete the resources (y/n): "
        )
        if confirm.strip().lower() != "y":
            logger.info(f"Not deleting artifact {artifact}")
            return

    timestamp = _extract_timestamp(artifact)
    artifacts_path = BuildPaths(home).artifacts
    files_deleted = 0
    for filepath in glob.glob(f"{artifacts_path}/*{timestamp}*"):
        os.remove(filepath)
        files_deleted += 1

    if not files_deleted:
        logger.warning("Found no files associated with this artifact")
        return

    logger.info(
        f"Deleted {files_deleted} files associated with artifact {artifact}"
    )
    remove_artifact_from_metadata(artifact, home)
