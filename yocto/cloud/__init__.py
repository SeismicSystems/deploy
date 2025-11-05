"""Cloud provider abstraction and implementations."""

from yocto.cloud.cloud_api import CloudApi
from yocto.cloud.cloud_config import (
    AZURE_REGIONS,
    GCP_ZONES,
    CloudProvider,
    get_cloud_api,
    get_default_region,
    get_default_resource_group,
    get_default_vm_size,
    validate_region,
)
from yocto.cloud.cloud_parser import (
    confirm,
    create_cloud_parser,
    parse_cloud_args,
    validate_and_apply_defaults,
)

__all__ = [
    # Cloud API
    "CloudApi",
    # Cloud Config
    "CloudProvider",
    "AZURE_REGIONS",
    "GCP_ZONES",
    "validate_region",
    "get_default_region",
    "get_default_resource_group",
    "get_default_vm_size",
    "get_cloud_api",
    # Cloud Parser
    "create_cloud_parser",
    "validate_and_apply_defaults",
    "parse_cloud_args",
    "confirm",
]
