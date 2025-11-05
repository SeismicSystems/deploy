"""Domain configuration dataclass."""

import argparse
from dataclasses import dataclass


@dataclass
class DomainConfig:
    record: str = "yocto-0"
    resource_group: str = "devnet2"
    name: str = "seismicdev.net"

    @staticmethod
    def from_args(args: argparse.Namespace) -> "DomainConfig":
        if not args.domain_record:
            raise ValueError(
                "If passing in --deploy, you must also provide a --domain-record"
            )
        return DomainConfig(
            record=args.domain_record,
            resource_group=args.domain_resource_group,
            name=args.domain_name,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "url": f"https://{self.record}.{self.name}",
            "record": self.record,
            "name": self.name,
            "resource_group": self.resource_group,
        }
