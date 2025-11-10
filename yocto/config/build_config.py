"""Build configuration dataclass."""

import argparse
from dataclasses import dataclass
from typing import Any

from yocto.image.git import GitConfigs


@dataclass
class BuildConfigs:
    git: GitConfigs
    cloud: str | None = None
    dev: bool = False

    @staticmethod
    def from_args(args: argparse.Namespace) -> "BuildConfigs":
        return BuildConfigs(
            git=GitConfigs.from_args(args),
            cloud=args.cloud if hasattr(args, 'cloud') else None,
            dev=args.dev if hasattr(args, 'dev') else False,
        )

    @staticmethod
    def default() -> "BuildConfigs":
        return BuildConfigs(
            git=GitConfigs.default(),
            cloud=None,
            dev=False,
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "git": self.git.to_dict(),
            "dev": self.dev,
        }
        if self.cloud:
            result["cloud"] = self.cloud
        return result
