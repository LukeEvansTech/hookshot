import hashlib


class EbayDeletionParser:
    def parse(self, payload: dict, headers: dict, endpoint_name: str) -> dict:
        notification = payload.get("notification", {})
        data = notification.get("data", {})
        username = data.get("username", "unknown")
        user_id = data.get("userId", "unknown")
        return {
            "title": "eBay Account Deletion Notification",
            "body": f"User **{username}** (ID: {user_id}) has requested account deletion.",
        }

    def verify(self, challenge_code: str, secret: str) -> dict:
        hash_value = hashlib.sha256(
            challenge_code.encode() + secret.encode()
        ).hexdigest()
        return {"challengeResponse": hash_value}
