"""
Default values for GCP deployments.

Note on regions/zones:
- In GCP, a zone is a deployment area within a region (e.g., us-central1-a)
- For compatibility with Azure's location field, we use DEFAULT_ZONE as the
  default value for config.vm.location
- DEFAULT_REGION is used for regional resources (like IP addresses, buckets)
"""

# Resource groups / Projects
DEFAULT_PROJECT = "testnet-477314"
DEFAULT_DOMAIN_RESOURCE_GROUP = "yocto-testnet"  # For compatibility with Azure DNS

# Domain configuration
DEFAULT_DOMAIN_NAME = "seismictest.net"
DEFAULT_CERTBOT_EMAIL = "c@seismic.systems"

# VM configuration
DEFAULT_REGION = "us-central1"  # Used for regional resources (IPs, buckets)
DEFAULT_ZONE = "us-central1-a"  # Used for zonal resources (VMs, disks)
# TDX-enabled VM for attestation
DEFAULT_VM_TYPE = "c3-standard-4"

# Network ports
CONSENSUS_PORT = 18551

# GCP-specific settings
DEFAULT_NETWORK_TIER = "PREMIUM"
DEFAULT_NIC_TYPE = "GVNIC"
DEFAULT_PROVISIONING_MODEL = "STANDARD"
DEFAULT_DISK_TYPE = "pd-balanced"
DEFAULT_DISK_SIZE_GB = 32
