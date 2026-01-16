import logging
import tomllib
from pathlib import Path
from typing import Any, Dict, List
import requests
from dataclasses import dataclass
from pathlib import Path
logger = logging.getLogger(__name__)

GenesisText = str
Json = Any

@dataclass
class PublicKeys:
    node: str
    consensus: str


class SummitClient:

    def __init__(self, url: str):
        self.url = url
        self._request_id = 0
        print(f"{self._request_id}")



    def _rpc_call(self, path: str, params: dict[str, Any] | list | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": path,
            "params": params or [],
            "id": self._request_id + 1
        }
        self._request_id += 1
        
        response = requests.post(
            self.url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            raise Exception(f"RPC Error {error.get('code')}: {error.get('message')}")
        
        return result.get("result")



    def _call(self, path: str, params: List|Dict | None = None) -> Any:
        # response = requests.get(f"{self.url}/{path}")
        return self._rpc_call(path, params)
    

    def _post_text(self, path: str, body: str) -> str:
        response = requests.post(
            f"{self.url}/{path}",
            data=body,
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()
        return response.text

    def health(self) -> str:
        return self._call("health")

    def get_public_keys(self) -> PublicKeys:
        keys = self._call("getPublicKeys", [])
        return PublicKeys(node=keys['node'], consensus=keys['consensus'])

   
    def send_genesis(self, genesis: GenesisText) -> str:
        self.validate_genesis_text(genesis)
        return self._call("sendGenesis", [genesis])

    def post_genesis_filepath(self, path: Path):
        text = self.load_genesis_file(path)
        self.send_genesis(text)

    @staticmethod
    def load_genesis_file(path: Path) -> GenesisText:
        with open(path) as f:
            return f.read()

    @staticmethod
    def validate_genesis_text(genesis: GenesisText) -> dict[str, Any]:
        try:
            return tomllib.loads(genesis)
        except tomllib.TOMLDecodeError as e:
            logger.error(
                "\n".join(
                    [
                        f"Failed to parse genesis as toml: {e}",
                        "File contents:",
                        genesis,
                    ]
                )
            )
            raise e

    @classmethod
    def load_genesis_toml(cls, path: Path) -> dict[str, Any]:
        text = cls.load_genesis_file(path)
        return cls.validate_genesis_text(text)
