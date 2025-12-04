import logging
import subprocess
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from yocto.utils.paths import BuildPaths

logger = logging.getLogger(__name__)

GitCommit = str | None


def commit_from_args(args: Namespace, repo: str) -> GitCommit:
    values = vars(args)
    return values[f"{repo}_commit"]


@dataclass
class GitConfigs:
    enclave: GitCommit
    sreth: GitCommit
    summit: GitCommit

    @staticmethod
    def from_args(args: Namespace) -> "GitConfigs":
        return GitConfigs(
            enclave=commit_from_args(args, "enclave"),
            sreth=commit_from_args(args, "sreth"),
            summit=commit_from_args(args, "summit"),
        )

    def to_dict(self):
        return {
            "enclave": self.enclave,
            "sreth": self.sreth,
            "summit": self.summit,
        }


def run_command(
    cmd: str, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr.strip()}")

    return result


def _extract(cmd: str, field: str) -> str:
    process = subprocess.Popen(
        args=cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        return stdout.strip()
    else:
        raise Exception(f"Failed to get {field}: {stderr}")


def _extract_commit_from_mkosi(build_file: Path, package_name: str) -> str:
    """Extract commit hash from mkosi.build file for a given package.

    Args:
        build_file: Path to mkosi.build file
        package_name: Package name (e.g., "summit", "seismic-reth",
            "seismic-enclave-server")

    Returns:
        The commit hash as a string

    The format in mkosi.build is:
        RETH_COMMIT="e0ebd6a8d2c4d160867f213ad39482d1095195a4"
    """
    # Map package names to variable prefixes
    package_var_map = {
        "seismic-reth": "RETH",
        "seismic-enclave-server": "ENCLAVE",
        "summit": "SUMMIT",
    }

    var_prefix = package_var_map.get(package_name)
    if not var_prefix:
        raise ValueError(f"Unknown package name: {package_name}")

    commit_var = f"{var_prefix}_COMMIT"
    cmd = f"""grep '^{commit_var}=' {build_file} | cut -d'"' -f2"""
    result = _extract(cmd, f"{package_name} commit")
    if not result or len(result) != 40:
        raise ValueError(
            f"Failed to extract valid commit hash for {package_name}. "
            f"Got: '{result}'"
        )
    return result


def update_git_mkosi_batch(
    updates: dict[str, GitCommit],
    home: str,
    commit_message: str | None = None,
) -> dict[str, GitCommit]:
    """
    Update git commits for multiple packages in seismic/mkosi.build in a
    single commit.

    Args:
        updates: Dict mapping package name to commit hash
                 (e.g., {"summit": "3720ab4...",
                 "seismic-reth": "3720ab4..."})
        home: Home directory path
        commit_message: Optional custom commit message

    Returns:
        Dict mapping package names to their final commit hash
    """

    paths = BuildPaths(home)
    build_file = paths.flashbots_images / "seismic" / "mkosi.build"

    if not paths.flashbots_images.exists():
        raise FileNotFoundError(
            f"flashbots-images path not found: {paths.flashbots_images}"
        )

    if not build_file.exists():
        raise FileNotFoundError(f"{build_file} not found")

    # Map package names to variable prefixes
    package_var_map = {
        "seismic-reth": "RETH",
        "seismic-enclave-server": "ENCLAVE",
        "summit": "SUMMIT",
    }

    # Process each package
    results = {}
    packages_to_update = []

    for package_name, git_config in updates.items():
        if git_config is None:
            # No commit specified, use current
            current_commit = _extract_commit_from_mkosi(
                build_file=build_file,
                package_name=package_name,
            )
            logger.info(
                f"No git commit provided for {package_name}. "
                f"Using current git commit "
                f"{current_commit}"
            )
            results[package_name] = current_commit
        else:
            # Mark for update
            packages_to_update.append((package_name, git_config))
            results[package_name] = git_config

    # If nothing to update, return early
    if not packages_to_update:
        logger.info("No packages to update")
        return results

    logger.info(
        f"Updating {len(packages_to_update)} packages in "
        f"{build_file.name}..."
    )

    # Update all packages in one pass
    for package_name, git_commit in packages_to_update:
        logger.info(f"  - {package_name} @ {git_commit[:8]}")

        var_prefix = package_var_map.get(package_name)
        if not var_prefix:
            raise ValueError(f"Unknown package name: {package_name}")

        # Update commit variable (e.g., RETH_COMMIT="abc123...")
        commit_var = f"{var_prefix}_COMMIT"
        commit_update_cmd = (
            f"sed -i 's/^{commit_var}=.*$/{commit_var}="
            f'"{git_config.commit}"\' {build_file}'
        )
        run_command(commit_update_cmd, cwd=paths.flashbots_images)

    logger.info("All packages updated in file")

    # Stage the file
    run_command("git add seismic/mkosi.build", cwd=paths.flashbots_images)

    # Check if there are changes to commit
    status_result = run_command(
        cmd="git status --porcelain",
        cwd=paths.flashbots_images,
    )
    if status_result.stdout.strip():
        logger.info("Changes detected, committing...")
        if not commit_message:
            package_names = ", ".join([name for name, _ in packages_to_update])
            commit_message = f"Update commit hashes for {package_names}"
        run_command(
            f'git commit -m "{commit_message}"', cwd=paths.flashbots_images
        )
        logger.info("Committed changes")

        run_command("git push", cwd=paths.flashbots_images)
        logger.info("Successfully pushed changes")
    else:
        logger.info("No changes to commit")

    logger.info("Batch update completed successfully")
    return results


def update_git_mkosi(
    package_name: str,
    git_config: GitCommit,
    home: str,
    commit_message: str | None = None,
) -> GitCommit:
    """
    Update the git commit for a single package in seismic/mkosi.build.

    For batch updates of multiple packages, use update_git_mkosi_batch()
    instead.
    """
    results = update_git_mkosi_batch(
        {package_name: git_config},
        home,
        commit_message,
    )
    return results[package_name]
