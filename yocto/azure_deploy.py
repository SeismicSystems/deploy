#!/usr/bin/env python3
"""
Azure VM Deployment Tool

A modular Python replacement for deploy.sh that handles Azure VM deployment.
"""

from yocto.cloud.azure import AzureApi
from yocto.cloud.base_parser import create_base_parser
from yocto.cloud.cloud_config import CloudProvider
from yocto.config import DeploymentConfig


def deploy_vm(config: DeploymentConfig) -> None:
    """Execute full VM deployment pipeline."""
    print("Starting Azure VM deployment...")

    # Check dependencies
    AzureApi.check_dependencies()

    # Create resource group
    AzureApi.create_resource_group(config.resource_group, config.region)

    # Create and configure IP address
    ip_address = AzureApi.create_public_ip(config.resource_group, config.resource_group)
    AzureApi.update_dns_record(config, ip_address)

    # Create and upload disk
    AzureApi.create_disk(config)
    AzureApi.upload_disk(config)

    # Create network security group and rules
    AzureApi.create_nsg(config)
    AzureApi.create_standard_nsg_rules(config)

    # Create VM
    AzureApi.create_vm(config)

    print("Deployment completed.")


def main():
    """Main entry point."""
    try:
        parser = create_base_parser("Azure VM Deployment Tool", cloud=CloudProvider.AZURE)
        parser.add_argument(
            "--node",
            type=int,
            required=True,
            help="Node number. Will deploy at node-<node>.<ip-address>",
        )
        args = parser.parse_args()
        config = DeploymentConfig.from_deploy_args(args)
        deploy_vm(config)
    except Exception as e:
        print(f"Deployment failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
