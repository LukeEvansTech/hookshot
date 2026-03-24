import hashlib
import hmac
import json
import pytest
from src.parsers import get_parser
from src.parsers.generic import GenericParser
from src.parsers.ebay import EbayDeletionParser
from src.parsers.github import GithubParser
from src.parsers.template import TemplateParser


def test_generic_parser():
    parser = GenericParser()
    result = parser.parse(
        payload={"action": "completed", "repo": "hookshot"},
        headers={},
        endpoint_name="Test",
    )
    assert result["title"] == "Webhook received from Test"
    assert "action" in result["body"]
    assert "completed" in result["body"]


def test_ebay_deletion_parse():
    parser = EbayDeletionParser()
    result = parser.parse(
        payload={"metadata": {"topic": "MARKETPLACE_ACCOUNT_DELETION"}, "notification": {"data": {"username": "testuser", "userId": "abc123"}}},
        headers={},
        endpoint_name="eBay",
    )
    assert "testuser" in result["body"] or "abc123" in result["body"]
    assert "deletion" in result["title"].lower() or "account" in result["title"].lower()


def test_ebay_verification_challenge():
    parser = EbayDeletionParser()
    secret = "my-verification-token"
    challenge_code = "test-challenge-123"
    result = parser.verify(challenge_code=challenge_code, secret=secret)
    expected_hash = hashlib.sha256(
        challenge_code.encode() + secret.encode()
    ).hexdigest()
    assert result["challengeResponse"] == expected_hash


def test_github_parser_push():
    parser = GithubParser()
    result = parser.parse(
        payload={"repository": {"full_name": "user/repo"}, "pusher": {"name": "luke"}, "ref": "refs/heads/main", "commits": [{"message": "fix bug"}]},
        headers={"x-github-event": "push"},
        endpoint_name="GitHub",
    )
    assert "user/repo" in result["title"]
    assert "push" in result["title"].lower()


def test_github_parser_signature_valid():
    parser = GithubParser()
    payload = json.dumps({"action": "opened"}).encode()
    secret = "github-secret"
    sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert parser.verify_signature(payload=payload, signature=sig, secret=secret) is True


def test_github_parser_signature_invalid():
    parser = GithubParser()
    assert parser.verify_signature(payload=b"data", signature="sha256=wrong", secret="secret") is False


def test_template_parser():
    template_str = "title: Deploy {{ data.status }} — {{ data.app }}\nbody: {{ data.message }}"
    parser = TemplateParser(template_str)
    result = parser.parse(
        payload={"status": "success", "app": "hookshot", "message": "Deployed v1.0"},
        headers={},
        endpoint_name="Deploy",
    )
    assert result["title"] == "Deploy success — hookshot"
    assert result["body"] == "Deployed v1.0"


def test_get_parser_builtin():
    parser = get_parser(parser_type="builtin", parser_name="ebay_deletion")
    assert isinstance(parser, EbayDeletionParser)


def test_get_parser_generic():
    parser = get_parser(parser_type="generic", parser_name="")
    assert isinstance(parser, GenericParser)


def test_get_parser_template():
    parser = get_parser(parser_type="template", parser_name="title: hi\nbody: there")
    assert isinstance(parser, TemplateParser)
