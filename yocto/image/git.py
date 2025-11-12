import logging
import subprocess
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from yocto.utils.paths import BuildPaths

logger = logging.getLogger(__name__)


@dataclass
class GitConfig:
    commit: str | None
    branch: str

    @staticmethod
    def from_args(args: Namespace, repo: str) -> "GitConfig":
        values = vars(args)
        return GitConfig(
            commit=values[f"{repo}_commit"], branch=values[f"{repo}_branch"]
        )

    def to_dict(self) -> dict[str, str]:
        # if not self.commit:
        #     raise ValueError(
        #         "Cannot call to_dict() on GitConfig without commit"
        #     )
        return {
            "branch": self.branch,
            "commit": self.commit,
        }

    @staticmethod
    def branch_only(branch: str) -> "GitConfig":
        return GitConfig(commit=None, branch=branch)


@dataclass
class GitConfigs:
    enclave: GitConfig
    sreth: GitConfig
    summit: GitConfig

    @staticmethod
    def from_args(args: Namespace) -> "GitConfigs":
        return GitConfigs(
            enclave=GitConfig.from_args(args, "enclave"),
            sreth=GitConfig.from_args(args, "sreth"),
            summit=GitConfig.from_args(args, "summit"),
        )

    def to_dict(self):
        return {
            "enclave": self.enclave.to_dict(),
            "sreth": self.sreth.to_dict(),
            "summit": self.summit.to_dict(),
        }

    @staticmethod
    def default() -> "GitConfigs":
        return GitConfigs(
            enclave=GitConfig.branch_only("seismic"),
            sreth=GitConfig.branch_only("seismic"),
            summit=GitConfig.branch_only("main"),
        )


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
        package_name: Package name (e.g., "summit", "seismic-reth", "seismic-enclave-server")

    Returns:
        The commit hash as a string

    The format in mkosi.build is:
        make_git_package \
            "summit" \
            "2022223a75f7e9e6d008638501ad95d1662d5ebc" \
    """
    # TODO: remove this
    return ""
    # Find the line with the package name, get the next line (commit), extract the quoted string
    cmd = f"""grep -A 1 '"{package_name}"' {build_file} | tail -1 | grep -o '"[^"]*"' | tr -d '"'"""
    result = _extract(cmd, f"{package_name} commit")
    if not result or len(result) != 40:
        raise ValueError(
            f"Failed to extract valid commit hash for {package_name}. "
            f"Got: '{result}'"
        )
    return result


def _extract_branch(bb_path: Path) -> str:
    """Legacy function - branches are not stored in mkosi.build."""
    # For mkosi builds, we don't track branches separately
    # The commit hash is what matters
    return "main"


def update_git_mkosi_batch(
    updates: dict[str, GitConfig],
    home: str,
    commit_message: str | None = None,
) -> dict[str, GitConfig]:
    """
    Update git commits for multiple packages in seismic/mkosi.build in a single commit.

    Args:
        updates: Dict mapping package name to GitConfig
                 (e.g., {"summit": GitConfig(...), "seismic-reth": GitConfig(...)})
        home: Home directory path
        commit_message: Optional custom commit message

    Returns:
        Dict mapping package names to their final GitConfig
    """

    paths = BuildPaths(home)
    build_file = paths.flashbots_images / "seismic" / "mkosi.build"

    if not paths.flashbots_images.exists():
        raise FileNotFoundError(
            f"flashbots-images path not found: {paths.flashbots_images}"
        )

    if not build_file.exists():
        raise FileNotFoundError(f"{build_file} not found")

    # Process each package
    results = {}
    packages_to_update = []

    for package_name, git_config in updates.items():
        if git_config.commit is None:
            # No commit specified, use current
            current_commit = _extract_commit_from_mkosi(build_file, package_name)
            current_git = GitConfig(
                commit=current_commit,
                branch=git_config.branch or "main",
            )
            logger.info(
                f"No git commit provided for {package_name}. "
                f"Using current git state {current_git.branch}#{current_git.commit}"
            )
            results[package_name] = current_git
        else:
            # Mark for update
            packages_to_update.append((package_name, git_config))
            results[package_name] = git_config

    # If nothing to update, return early
    if not packages_to_update:
        logger.info("No packages to update")
        return results

    logger.info(f"Updating {len(packages_to_update)} packages in {build_file.name}...")

    # Update all packages in one pass
    for package_name, git_config in packages_to_update:
        logger.info(f"  - {package_name} → {git_config.commit[:8]}")
        update_cmd = f"""
            awk -v pkg="{package_name}" -v commit="{git_config.commit}" '
            BEGIN {{ in_pkg=0; line_count=0 }}
            /make_git_package/ {{
                if ($0 ~ "\\"" pkg "\\"") {{
                    in_pkg=1
                    line_count=0
                }}
            }}
            {{
                if (in_pkg && line_count == 1) {{
                    sub(/"[^"]*"/, "\\"" commit "\\"")
                    in_pkg=0
                }}
                if (in_pkg) line_count++
                print
            }}
            ' {build_file} > {build_file}.tmp && mv {build_file}.tmp {build_file}
        """
        run_command(update_cmd, cwd=paths.flashbots_images)

    logger.info("All packages updated in file")

    # Stage the file
    run_command(f"git add seismic/mkosi.build", cwd=paths.flashbots_images)

    # Check if there are changes to commit
    status_result = run_command(
        "git status --porcelain", cwd=paths.flashbots_images
    )
    if status_result.stdout.strip():
        logger.info("Changes detected, committing...")
        if not commit_message:
            package_names = ", ".join([name for name, _ in packages_to_update])
            commit_message = f"Update commit hashes for {package_names}"
        run_command(f'git commit -m "{commit_message}"', cwd=paths.flashbots_images)
        logger.info("Committed changes")

        run_command("git push", cwd=paths.flashbots_images)
        logger.info("Successfully pushed changes")
    else:
        logger.info("No changes to commit")

    logger.info("Batch update completed successfully")
    return results


def update_git_mkosi(
    package_name: str,
    git_config: GitConfig,
    home: str,
    commit_message: str | None = None,
) -> GitConfig:
    """
    Update the git commit for a single package in seismic/mkosi.build.

    For batch updates of multiple packages, use update_git_mkosi_batch() instead.
    """
    results = update_git_mkosi_batch(
        {package_name: git_config},
        home,
        commit_message,
    )
    return results[package_name]


# Keep old function name for backwards compatibility, but delegate to new one
def update_git_bb(
    bb_pathname: str,
    git_config: GitConfig,
    home: str,
    commit_message: str | None = None,
) -> GitConfig:
    """Legacy wrapper for update_git_mkosi.

    Maps old bb_pathname to package names:
    - recipes-nodes/enclave/enclave.bb -> seismic-enclave-server
    - recipes-nodes/reth/reth.bb -> seismic-reth
    - recipes-nodes/summit/summit.bb -> summit
    """
    package_map = {
        "recipes-nodes/enclave/enclave.bb": "seismic-enclave-server",
        "recipes-nodes/reth/reth.bb": "seismic-reth",
        "recipes-nodes/summit/summit.bb": "summit",
    }

    package_name = package_map.get(bb_pathname)
    if not package_name:
        raise ValueError(f"Unknown bb_pathname: {bb_pathname}")

    return update_git_mkosi(package_name, git_config, home, commit_message)
