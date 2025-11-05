"""
Default values for Azure deployments.
"""

# Resource groups
DEFAULT_DOMAIN_RESOURCE_GROUP = "yocto-testnet"
DEFAULT_RESOURCE_GROUP = "tdx-testnet"

# Domain configuration
DEFAULT_DOMAIN_NAME = "seismictest.net"
DEFAULT_CERTBOT_EMAIL = "c@seismic.systems"

# VM configuration
DEFAULT_REGION = "eastus2"
# TDX-enabled VM for attestation
# Also works: Standard_EC4es_v6
DEFAULT_VM_SIZE = "Standard_DC4es_v6"

# Network ports
CONSENSUS_PORT = 18551
