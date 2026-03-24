import hashlib
import hmac


class GithubParser:
    def parse(self, payload: dict, headers: dict, endpoint_name: str) -> dict:
        event = headers.get("x-github-event", "unknown")
        repo = payload.get("repository", {}).get("full_name", "unknown")
        action = payload.get("action", "")
        actor = payload.get("sender", {}).get("login", "")

        title = f"[{repo}] {event}"
        if action:
            title += f": {action}"

        body_parts = []
        if actor:
            body_parts.append(f"**Actor**: {actor}")

        if event == "push":
            pusher = payload.get("pusher", {}).get("name", "unknown")
            ref = payload.get("ref", "")
            commits = payload.get("commits", [])
            body_parts.append(f"**Pushed by**: {pusher}")
            body_parts.append(f"**Ref**: {ref}")
            body_parts.append(f"**Commits**: {len(commits)}")
            for commit in commits[:5]:
                body_parts.append(f"- {commit.get('message', '')}")
        elif event == "pull_request":
            pr = payload.get("pull_request", {})
            body_parts.append(f"**PR**: #{pr.get('number', '')} {pr.get('title', '')}")
            body_parts.append(f"**URL**: {pr.get('html_url', '')}")

        return {
            "title": title,
            "body": "\n".join(body_parts) if body_parts else f"GitHub {event} event received",
        }

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
