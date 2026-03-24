from typing import Protocol


class BaseParser(Protocol):
    def parse(self, payload: dict, headers: dict, endpoint_name: str) -> dict:
        """Parse webhook payload, return {"title": str, "body": str}."""
        ...
