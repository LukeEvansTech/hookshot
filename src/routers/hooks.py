import json
from fastapi import APIRouter, Request, Response
from src.database import get_endpoint
from src.parsers import get_parser
from src.parsers.ebay import EbayDeletionParser
from src.parsers.github import GithubParser
from src.services.apprise import send_notification
from src.services.activity import log_activity, prune_activity
from src.config import settings

router = APIRouter()


@router.get("/hook/{endpoint_id}")
async def webhook_verify(endpoint_id: str, request: Request):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return Response(status_code=404, content="Not found")

    challenge_code = request.query_params.get("challenge_code")
    if challenge_code and endpoint["parser_name"] == "ebay_deletion":
        parser = EbayDeletionParser()
        result = parser.verify(challenge_code=challenge_code, secret=endpoint.get("secret", ""))
        return result

    return {"status": "ok"}


@router.post("/hook/{endpoint_id}")
async def webhook_receive(endpoint_id: str, request: Request):
    db = request.app.state.db
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        return Response(status_code=404, content="Not found")

    source_ip = request.client.host if request.client else ""
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        payload = {"raw": raw_body.decode(errors="replace")}

    if not endpoint["enabled"]:
        await log_activity(db, endpoint_id=endpoint_id, source_ip=source_ip, payload=json.dumps(payload), notification_title="", notification_body="", status="skipped", apprise_response="Endpoint disabled")
        return {"status": "skipped"}

    # Signature verification for GitHub
    parser = get_parser(endpoint["parser_type"], endpoint["parser_name"])
    if isinstance(parser, GithubParser) and endpoint.get("secret"):
        signature = request.headers.get("x-hub-signature-256", "")
        if signature and not parser.verify_signature(payload=raw_body, signature=signature, secret=endpoint["secret"]):
            await log_activity(db, endpoint_id=endpoint_id, source_ip=source_ip, payload=json.dumps(payload), notification_title="", notification_body="", status="failed", apprise_response="Invalid signature")
            return Response(status_code=401, content="Invalid signature")

    headers = dict(request.headers)
    try:
        result = parser.parse(payload=payload, headers=headers, endpoint_name=endpoint["name"])
    except Exception:
        from src.parsers.generic import GenericParser
        result = GenericParser().parse(payload=payload, headers=headers, endpoint_name=endpoint["name"])

    apprise_result = await send_notification(
        apprise_url=settings.apprise_url,
        apprise_key=settings.apprise_key,
        title=result["title"],
        body=result["body"],
        tag=endpoint["apprise_tag"],
    )

    await log_activity(
        db, endpoint_id=endpoint_id, source_ip=source_ip, payload=json.dumps(payload),
        notification_title=result["title"], notification_body=result["body"],
        status=apprise_result["status"], apprise_response=apprise_result["response"],
    )

    await prune_activity(db, max_entries=settings.activity_retention)

    return {"status": "received"}
