import httpx


async def send_notification(*, apprise_url: str, apprise_key: str, title: str, body: str, tag: str = "") -> dict:
    url = f"{apprise_url.rstrip('/')}/notify/{apprise_key}"
    payload = {"title": title, "body": body, "type": "info"}
    if tag:
        payload["tag"] = tag
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "response": response.text,
            }
    except Exception as e:
        return {"status": "failed", "response": str(e)}
