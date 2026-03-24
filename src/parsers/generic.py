import json


class GenericParser:
    def parse(self, payload: dict, headers: dict, endpoint_name: str) -> dict:
        body_lines = []
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            body_lines.append(f"**{key}**: {value}")
        return {
            "title": f"Webhook received from {endpoint_name}",
            "body": "\n".join(body_lines) if body_lines else "Empty payload",
        }
