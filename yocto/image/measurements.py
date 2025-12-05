#!/usr/bin/env python3
import argparse
import json
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from yocto.utils.paths import BuildPaths
from yocto.cloud.cloud_config import CloudProvider

logger = logging.getLogger(__name__)

Measurements = dict[str, Any]


def write_measurements_tmpfile(measurements: Measurements) -> Path:
    measurements_tmpfile = Path(tempfile.mktemp())
    with open(measurements_tmpfile, "w+") as f:
        json.dump([measurements], f)
    return measurements_tmpfile


def parse_gcp_measurements(measurements_output: Path, result: subprocess.CompletedProcess):
    # Parse stdout and extract only the JSON part (first valid JSON object)
    stdout = result.stdout.strip()

    # Try to parse as JSON directly first (in case output is clean)
    try:
        measurements_data = json.loads(stdout)
        json_str = json.dumps(measurements_data, indent=2)
    except json.JSONDecodeError:
        # If that fails, extract JSON by tracking brace balance
        # This handles cases where Lima VM messages are mixed with output
        json_lines = []
        brace_count = 0
        in_json = False

        for line in stdout.split('\n'):
            stripped = line.strip()
            # Look for the start of a JSON object
            if not in_json and '{' in stripped:
                in_json = True
                # Find where the brace starts and slice from there
                brace_pos = line.index('{')
                line = line[brace_pos:]

            if in_json:
                json_lines.append(line)
                # Count braces on this line
                brace_count += line.count('{') - line.count('}')

                # If brace count is 0, we've completed the JSON object
                if brace_count == 0:
                    break

        if not json_lines:
            raise RuntimeError(
                f"Could not find JSON in dstack-mr output:\n{stdout}"
            )

        json_str = '\n'.join(json_lines)
        # Validate it's valid JSON
        try:
            json.loads(json_str)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Extracted invalid JSON from dstack-mr output:\n{json_str}\n\nError: {e}"
            )

    measurements_output.parent.mkdir(parents=True, exist_ok=True)
    measurements_output.write_text(json_str)


def generate_measurements(image_path: Path, home: str) -> Measurements:
    """Generate measurements for TDX boot process using make measure"""

    paths = BuildPaths(home)

    # Resolve to absolute path
    image_path = image_path.resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"Image path not found: {image_path}")

    # For mkosi builds, we need the .efi file for measurements, not .vhd/.tar.gz
    efi_path = image_path
    if image_path.suffix == ".vhd" or image_path.name.endswith(".tar.gz"):
        # Look for the corresponding .efi file
        # Pattern: seismic-dev-azure-TIMESTAMP.vhd -> seismic-dev-azure-TIMESTAMP.efi
        # Pattern: seismic-dev-gcp-TIMESTAMP.tar.gz -> seismic-dev-gcp-TIMESTAMP.efi
        if image_path.name.endswith(".tar.gz"):
            efi_path = Path(str(image_path)[:-7] + ".efi")  # Remove .tar.gz, add .efi
        else:
            efi_path = image_path.with_suffix(".efi")

        if not efi_path.exists():
            raise FileNotFoundError(
                f"EFI file not found for {image_path.name}. "
                f"Expected: {efi_path}"
            )

    if not paths.seismic_images.exists():
        raise FileNotFoundError(
            f"flashbots-images path not found: {paths.seismic_images}"
        )

    logger.info(f"Generating measurements for: {efi_path.name}")
    logger.info(f"  EFI path: {efi_path.absolute()}")

    # Extract image name from path (e.g., seismic from seismic-dev-azure-*.efi)
    image_name = efi_path.name.split("-")[0]

    # Detect cloud provider from filename (e.g., seismic-dev-gcp-*.efi)
    cloud_provider = CloudProvider.from_string(efi_path.name)

    # Important: env_wrapper.sh runs in Lima VM where flashbots-images is
    # mounted at ~/mnt. So we need to use relative paths from
    # flashbots-images root
    wrapper_script = paths.seismic_images / "scripts" / "env_wrapper.sh"

    # Get relative path from flashbots-images root
    # (e.g., "build/gcp/seismic-dev-gcp-*.efi" or "build/seismic-dev-azure-*.efi")
    efi_relative = efi_path.relative_to(paths.seismic_images)

    # Generate timestamped output filename
    # Extract timestamp from filename (e.g., 20251204212823 from seismic-dev-gcp-20251204212823.efi)
    timestamp_match = re.search(r'-(\d{14})\.', efi_path.name)
    timestamp = timestamp_match.group(1) if timestamp_match else "latest"

    if cloud_provider.is_gcp():
        measurements_relative = f"build/gcp/measurements-{timestamp}.json"
        # GCP uses dstack-mr which outputs to stdout
        # We need to capture only stdout (not the Lima message), so we'll handle this differently
        measure_cmd = (
            f"cd {paths.seismic_images} && "
            f"IMAGE={image_name} {wrapper_script} dstack-mr "
            f'-uki "{efi_relative}" -json'
        )
    else:
        measurements_relative = f"build/{cloud_provider.value}/measurements-{timestamp}.json"
        # Azure uses measured-boot which writes to a file
        measure_cmd = (
            f"cd {paths.seismic_images} && "
            f"IMAGE={image_name} {wrapper_script} measured-boot "
            f'"{efi_relative}" {measurements_relative} --direct-uki'
        )

    logger.info(f"Running measurement tool for {cloud_provider.value.upper()}")
    logger.info(f"Output: {measurements_relative}")

    result = subprocess.run(
        measure_cmd, shell=True, capture_output=True, text=True
    )

    if result.returncode != 0:
        tool_name = "dstack-mr" if cloud_provider.is_gcp() else "measured-boot"
        raise RuntimeError(
            f"{tool_name} failed:\n"
            f"{result.stderr.strip()}\n"
            f"Command:\n{measure_cmd}"
        )

    # For GCP, we need to manually write the stdout to file (filtering out non-JSON)
    measurements_output = paths.seismic_images / measurements_relative
    if cloud_provider.is_gcp():
        parse_gcp_measurements(measurements_output, result)
    else:
        # measured-boot writes directly to file
        if not measurements_output.exists():
            raise FileNotFoundError(
                f"Measurements file not generated: {measurements_output}"
            )

    with open(measurements_output) as f:
        raw_measurements = json.load(f)

    # Format to match expected structure
    attestation_type = f"{cloud_provider}-tdx"
    measurements = {
        "measurement_id": image_path.name,
        "attestation_type": attestation_type,
        "measurements": raw_measurements.get("measurements", raw_measurements),
    }

    logger.info("Measurements generated successfully")
    return measurements


def main():
    """CLI entry point for standalone measurement generation."""
    parser = argparse.ArgumentParser(
        description="Generate TDX measurements from UKI EFI files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate measurements for a GCP image
  %(prog)s build/gcp/seismic-dev-gcp-20251204212823.tar.gz --home /home/azureuser

  # Generate measurements for an Azure image with explicit EFI path
  %(prog)s build/azure/seismic-dev-azure-20251204212823.efi --home /home/azureuser

  # Override cloud provider detection
  %(prog)s build/seismic.efi --home /home/azureuser --cloud gcp

  # Specify custom output path
  %(prog)s build/seismic.efi --home /home/azureuser --output custom-measurements.json
        """,
    )
    parser.add_argument(
        "image_path",
        type=Path,
        help="Path to image file (.efi, .vhd, or .tar.gz)",
    )
    parser.add_argument(
        "--home",
        type=str,
        default="/home/azureuser",
        help="Home directory path (required for BuildPaths)",
    )
    parser.add_argument(
        "--cloud",
        choices=["auto", "gcp", "azure"],
        default="auto",
        help="Cloud provider (default: auto-detect from filename)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Custom output path (default: auto-generated with timestamp)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Generate measurements
        measurements = generate_measurements(args.image_path, args.home)

        # If custom output specified, also write there
        if args.output:
            logger.info(f"Writing measurements to custom path: {args.output}")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(measurements, f, indent=2)

        logger.info(f"✓ Measurements generated successfully")
        logger.info(f"  Measurement ID: {measurements['measurement_id']}")
        logger.info(f"  Attestation Type: {measurements['attestation_type']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Measurement generation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
