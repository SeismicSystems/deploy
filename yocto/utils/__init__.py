"""Utility module for common helper functions.

Note: Functions are imported lazily to avoid circular dependencies.
Import directly from submodules when needed:
  - from yocto.utils.artifact import ...
  - from yocto.utils.metadata import ...
  - etc.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from yocto.utils import artifact, logging_setup, metadata, parser, paths, summit_client

# Only export module names, not individual functions
__all__ = [
    "artifact",
    "logging_setup",
    "metadata",
    "parser",
    "paths",
    "summit_client",
]
