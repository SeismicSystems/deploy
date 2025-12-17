import argparse
import json
import tempfile
from pathlib import Path

from yocto.cloud.azure import CONSENSUS_PORT
from yocto.cloud.cloud_api import CloudApi
from yocto.cloud.cloud_config import CloudProvider
from yocto.config import get_domain_record_prefix, get_genesis_vm_prefix
from yocto.utils.metadata import load_metadata
from yocto.utils.summit_client import SummitClient


_ANVIL_ADDRESSES = [
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
    "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
    "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
    "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
    "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
    "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720"
]


def _genesis_vm_name(node: int, cloud: CloudProvider) -> str:
    """Get genesis VM name for the given node and cloud provider."""
    prefix = get_genesis_vm_prefix(cloud)
    return f"{prefix}-{node}"


def _genesis_client(node: int, cloud: CloudProvider) -> SummitClient:
    """Create a genesis client for the given node and cloud provider."""
    prefix = get_domain_record_prefix(cloud)
    return SummitClient(
        f"https://{prefix}-{node}.seismictest.net/summit"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nodes", type=int, default=4)
    parser.add_argument(
        "--node",
        nargs="*",
        type=int,
        help="Specific node numbers (e.g., --node 23 24 25). Overrides -n/--nodes if provided.",
    )
    parser.add_argument(
        "--code-path",
        default="",
        type=str,
        help="path to code relative to $HOME",
    )
    parser.add_argument(
        "--cloud",
        type=str,
        default="azure",
        choices=["azure", "gcp"],
        help="Cloud provider (azure or gcp)",
    )
    parser.add_argument(
        "-g", "--genesis-hash",
        type=str,
        default=None,
        help="Eth genesis hash",
    )
    return parser.parse_args()


def _get_pubkeys(
    home: Path,
    node_clients: list[tuple[int, SummitClient]],
    cloud: str,
    cloud_provider: CloudProvider,
) -> tuple[list[dict[str, str]], dict[int, str]]:
    metadata = load_metadata(str(home))
    cloud_resources = metadata["resources"].get(cloud, {})

    validators = []
    node_to_pubkey = {}
    for i, (node, client) in enumerate(node_clients):
        vm_name = _genesis_vm_name(node, cloud_provider)
        if vm_name not in cloud_resources:
            raise ValueError(f"VM {vm_name} not found in {cloud} metadata")

        meta = cloud_resources[vm_name]
        ip_address = meta["public_ip"]
        try:
            pubkeys = client.get_public_keys()
            validators.append(
                {
                    "node_public_key": pubkeys.node,
                    "consensus_public_key": pubkeys.consensus,
                    "ip_address": f"{ip_address}:{CONSENSUS_PORT}",
                    "withdrawal_credentials": _ANVIL_ADDRESSES[i % len(_ANVIL_ADDRESSES)],
                }
            )
            node_to_pubkey[node] = pubkeys.node
        except Exception as e:
            print(f"Error: {e}")
            raise e
    return validators, node_to_pubkey

def main():
    args = _parse_args()
    genesis_arg = ["-g", args.genesis_hash] if args.genesis_hash else []
    cloud = CloudProvider(args.cloud)

    # Use --node if provided, otherwise use range from --nodes
    if args.node:
        node_numbers = args.node
    elif args.nodes == 0:
        raise ValueError(f'Must provide --node <n1> <n2> or --nodes <COUNT>')
    else:
        node_numbers = list(range(1, args.nodes + 1))

    node_clients = [
        (n, _genesis_client(n, cloud)) for n in node_numbers
    ]

    tmpdir = tempfile.mkdtemp()
    home = Path.home() if not args.code_path else Path.home() / args.code_path

    summit_path = str(home / "summit")
    summit_genesis_target = f"{summit_path}/target/debug/genesis"
    summit_example_genesis = f"{summit_path}/example_genesis.toml"

    validators, node_to_pubkey = _get_pubkeys(
        home, node_clients, args.cloud, cloud
    )

    tmp_validators = f"{tmpdir}/validators.json"
    with open(tmp_validators, "w+") as f:
        print(f"Wrote validators to {tmp_validators}")
        json.dump(validators, f, indent=2)

    CloudApi.run_command(
        cmd=[
            summit_genesis_target,
            "-o",
            f"{tmpdir}",
            "-i",
            summit_example_genesis,
            "-v",
            tmp_validators,
            *genesis_arg,
        ],
        show_logs=True,
    )
    
    for _, client in node_clients:
        client.post_genesis_filepath(f"{tmpdir}/genesis.toml")


if __name__ == "__main__":
    main()
