import pytest
import httpx
from unittest.mock import AsyncMock, patch
from src.services.apprise import send_notification


@pytest.mark.asyncio
async def test_send_notification_success():
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "ok"

    with patch("src.services.apprise.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await send_notification(
            apprise_url="http://apprise:8000",
            apprise_key="testkey",
            title="Test",
            body="Hello",
            tag="all",
        )
        assert result["status"] == "success"
        assert result["response"] == "ok"


@pytest.mark.asyncio
async def test_send_notification_failure():
    with patch("src.services.apprise.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client_cls.return_value = mock_client

        result = await send_notification(
            apprise_url="http://apprise:8000",
            apprise_key="testkey",
            title="Test",
            body="Hello",
            tag="all",
        )
        assert result["status"] == "failed"
