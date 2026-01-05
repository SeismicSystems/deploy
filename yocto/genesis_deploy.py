#!/usr/bin/env python3
"""
Genesis Azure VM Deployment Tool

Genesis mode deployment with persistent IP addresses and
node-specific allocation.
"""
import copy
import json
import logging
from pathlib import Path

from yocto.cloud.azure.api import AzureApi
from yocto.cloud.base_parser import create_base_parser
from yocto.cloud.cloud_api import CloudApi
from yocto.cloud.cloud_factory import get_cloud_api
from yocto.cloud.cloud_parser import confirm
from yocto.config import DeploymentConfig
from yocto.deployment.deploy import Deployer
from yocto.image.build import maybe_build
from yocto.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


class GenesisIPManager:
    """Manages persistent IP addresses for genesis nodes."""

    def __init__(self, cloud_api: CloudApi, ip_rg: str):
        self.cloud_api = cloud_api
        self.ip_rg = ip_rg

    def ensure_genesis_resource_group(self, region: str) -> None:
        self.cloud_api.ensure_created_resource_group(self.ip_rg, region)

    def get_or_create_node_ip(
        self, node_number: int, region: str
    ) -> tuple[str, str]:
        """Get or create persistent IP for a specific node number."""
        self.ensure_genesis_resource_group(region)

        ip_name = f"genesis-node-{node_number}"

        # Check if IP already exists
        existing_ip = self.cloud_api.get_existing_public_ip(ip_name, self.ip_rg)
        if existing_ip:
            logger.info(
                f"Using existing IP {existing_ip} for node {node_number}"
            )
            return (existing_ip, ip_name)

        # Create new IP
        logger.info(f"Creating new IP for node {node_number}")
        confirm(f"create new IP for node {node_number} @ {ip_name}")
        ip_address = self.cloud_api.create_public_ip(
            ip_name, self.ip_rg, region
        )
        logger.info(f"Created IP {ip_address} for node {node_number}")
        return (ip_address, ip_name)


def deploy_genesis_vm(args: DeploymentConfig) -> None:
    """Execute genesis VM deployment pipeline."""
    logger.info("Starting Genesis Azure VM deployment...")

    if not args.artifact and not args.ip_only:
        raise ValueError("Missing --artifact arg")

    node = args.node
    cfg = args.to_configs()
    deploy_cfg = cfg.deploy
    print(f"Config:\n{json.dumps(cfg.to_dict(), indent=2)}")

    # Prepare enclave args based on peers
    if hasattr(args, 'peers') and args.peers:
        # Format peers as space-separated list of URLs
        peer_urls = ' '.join([f"http://{ip.strip()}:7878" for ip in args.peers])
        enclave_args = f"--peers {peer_urls}"
    else:
        enclave_args = "--genesis-node"

    cloud_api = get_cloud_api(deploy_cfg.vm.cloud)
    genesis_ip_manager = GenesisIPManager(cloud_api, args.resource_group)

    # Check dependencies
    cloud_api.check_dependencies()

    # Create resource group
    cloud_api.ensure_created_resource_group(
        name=deploy_cfg.vm.resource_group,
        location=deploy_cfg.vm.location,
    )

    if node is None:
        raise ValueError("Genesis deploy ran without --node arg")

    # Handle IP address allocation
    (ip_address, ip_name) = genesis_ip_manager.get_or_create_node_ip(
        node_number=node,
        region=deploy_cfg.vm.location,
    )

    # NOTE: only use Azure for domain
    # Enable metrics at metrics.{domain}
    metrics_cfg = copy.deepcopy(deploy_cfg)
    metrics_cfg.domain.record = f"metrics.{deploy_cfg.domain.record}"

    AzureApi.update_dns_record(metrics_cfg, ip_address, remove_old=True)
    AzureApi.update_dns_record(deploy_cfg, ip_address, remove_old=True)

    if args.ip_only:
        logger.info("Not creating machines (used --ip-only flag)")
        return

    image_path, measurements = maybe_build(cfg)
    deployer = Deployer(
        configs=cfg.deploy,
        image_path=image_path,
        measurements=measurements,
        home=cfg.home,
        ip_name=ip_name,
        show_logs=cfg.show_logs,
    )
    deploy_output = deployer.deploy()
    deploy_output.update_deploy_metadata()

    logger.info("Genesis deployment completed.")

    # Read SSH public key
    ssh_key_path = Path.home() / ".ssh" / "id_ed25519.pub"
    try:
        ssh_key_content = ssh_key_path.read_text().strip()
        # Extract just the key part (second field)
        ssh_key = ssh_key_content.split()[1]
    except (FileNotFoundError, IndexError) as e:
        logger.warning(f"Could not read SSH key from {ssh_key_path}: {e}")
        ssh_key = "YOUR_SSH_KEY_HERE"

    # Prepare the JSON payload
    payload = {
        "ssh_keys": [ssh_key],
        "domain": {
            "email": args.certbot_email,
            "name": f"{deploy_cfg.domain.record}.{deploy_cfg.domain.name}"
        },
        "log": {
            "enclave": "debug",
            "summit": "debug",
            "reth": "debug"
        },
        "args": {
            "enclave": enclave_args,
            "reth": "",
            "summit": ""
        }
    }
    payload_json = json.dumps(payload)

    # Print setup instructions
    print("\n" + "=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"\nNode: {node}")
    print(f"IP Address: {ip_address}")
    print(f"Domain: {deploy_cfg.domain.record}.{deploy_cfg.domain.name}")
    print("\nNext steps:")
    print("1. Register SSH key and domain config (port 8080):")
    print(
        f"   curl -X POST http://{ip_address}:8080 "
        f"-H 'Content-Type: application/json' -d '{payload_json}'"
    )
    print("\n2. Nginx with SSL will automatically set up after initialization")
    print("   Endpoints will be available at:")
    print(f"     https://{deploy_cfg.domain.record}.{deploy_cfg.domain.name}/rpc")
    print(f"     https://{deploy_cfg.domain.record}.{deploy_cfg.domain.name}/ws")
    print(f"     https://{deploy_cfg.domain.record}.{deploy_cfg.domain.name}/summit")
    if args.dev:
        print("\n3. SSH access uses dropbear (from bob-common) on port 22")
        print("   NOTE: Seismic uses bob-common's SSH setup:")
        print("   - Production: key-only auth, no root, no password")
        print("\n   ⚠️  DEV MODE - SSH Root Access Enabled:")
        print(f"   ssh root@{ip_address}")
        print("   Password: dqSPjo4p")
        print("   (Dev builds have debugging tools enabled)")
    print("\n" + "=" * 80 + "\n")


def parse_genesis_args():
    """Parse genesis-specific command line arguments."""
    parser = create_base_parser("Seismic Genesis VM Deployment Tool")
    # Genesis-specific node arguments (mutually exclusive)
    node_group = parser.add_mutually_exclusive_group(required=True)
    node_group.add_argument(
        "-c",
        "--count",
        type=int,
        help="Number of nodes to deploy",
    )
    node_group.add_argument(
        "-n",
        "--node",
        type=int,
        help="Specific node number to deploy",
    )
    parser.add_argument(
        "--name",
        type=str,
        help=(
            "Manual VM name override "
            "(default: cloud-specific prefix + node number)"
        ),
    )
    parser.add_argument(
        "--peers",
        type=str,
        nargs='+',
        help="List of peer IP addresses (will be formatted as http://{ip}:7878)",
    )
    return parser.parse_args()


def main():
    setup_logging()
    args = parse_genesis_args()
    if args.node:
        configs = [DeploymentConfig.from_genesis_args(args, args.node)]
    elif args.count:
        configs = [
            DeploymentConfig.from_genesis_args(args, n)
            for n in range(1, args.count + 1)
        ]

    for config in configs:
        logger.info(f"Deploying genesis node {config.node}...")
        deploy_genesis_vm(config)


if __name__ == "__main__":
    main()
