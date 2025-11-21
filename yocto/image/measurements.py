import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from yocto.utils.paths import BuildPaths

logger = logging.getLogger(__name__)

Measurements = dict[str, Any]


def write_measurements_tmpfile(measurements: Measurements) -> Path:
    measurements_tmpfile = Path(tempfile.mktemp())
    with open(measurements_tmpfile, "w+") as f:
        json.dump([measurements], f)
    return measurements_tmpfile


def generate_measurements(image_path: Path, home: str) -> Measurements:
    """Generate measurements for TDX boot process using make measure"""

    paths = BuildPaths(home)
    if not image_path.exists():
        raise FileNotFoundError(f"Image path not found: {image_path}")

    # For mkosi builds, we need the .efi file for measurements, not .vhd
    efi_path = image_path
    if image_path.suffix in [".vhd", ".tar.gz"]:
        # Look for the corresponding .efi file
        # Pattern: seismic-dev-azure-TIMESTAMP.vhd ->
        # seismic-dev-azure-TIMESTAMP.efi
        efi_path = image_path.with_suffix(".efi")
        if not efi_path.exists():
            raise FileNotFoundError(
                f"EFI file not found for {image_path.name}. "
                f"Expected: {efi_path}"
            )

    if not paths.flashbots_images.exists():
        raise FileNotFoundError(
            f"flashbots-images path not found: {paths.flashbots_images}"
        )

    logger.info(f"Generating measurements for: {efi_path.name}")
    logger.info(f"  EFI path: {efi_path.absolute()}")

    # Extract image name from path (e.g., seismic from seismic-dev-azure-*.efi)
    image_name = efi_path.name.split("-")[0]

    # Use the same command as make measure, but with our specific EFI file
    # This is what make measure does internally:
    #   $(WRAPPER) measured-boot "$$EFI_FILE" build/measurements.json
    #   --direct-uki
    #
    # Important: env_wrapper.sh runs in Lima VM where flashbots-images is
    # mounted at ~/mnt. So we need to use relative paths from
    # flashbots-images root
    wrapper_script = paths.flashbots_images / "scripts" / "env_wrapper.sh"

    # Get relative path from flashbots-images root
    # (e.g., "build/seismic-dev-azure-*.efi")
    efi_relative = efi_path.relative_to(paths.flashbots_images)
    measurements_relative = "build/measurements.json"

    measure_cmd = (
        f"cd {paths.flashbots_images} && "
        f"IMAGE={image_name} {wrapper_script} measured-boot "
        f'"{efi_relative}" {measurements_relative} --direct-uki'
    )

    result = subprocess.run(
        measure_cmd, shell=True, capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"measured-boot failed: {result.stderr.strip()}"
        )

    # Read the generated measurements.json
    measurements_output = paths.flashbots_images / measurements_relative
    if not measurements_output.exists():
        raise FileNotFoundError(
            f"Measurements file not generated: {measurements_output}"
        )

    with open(measurements_output) as f:
        raw_measurements = json.load(f)

    # Format to match expected structure
    measurements = {
        "measurement_id": image_path.name,
        "attestation_type": "azure-tdx",
        "measurements": raw_measurements.get("measurements", raw_measurements),
    }

    logger.info("Measurements generated successfully")
    return measurements
