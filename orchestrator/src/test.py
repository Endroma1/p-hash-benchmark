import unittest
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.app import Component, LoadResponse
import httpx

class TestComponentStartIter(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.check_health_patcher = patch.object(Component, "check_health", new_callable=AsyncMock)
        self.mock_check_health = self.check_health_patcher.start()

        self.response_data = {"loads": [{"id": 1, "path": "/img.jpg", "user_id": 42}]}
        self.component = Component("http://test:8000", "/test/health",LoadResponse,"loads")

    def tearDown(self) -> None:
        self.check_health_patcher.stop()

    @patch("src.app.httpx.AsyncClient")
    async def test_success(self, MockAsyncClient):
        mock_client = MockAsyncClient.return_value
        mock_client.post = AsyncMock()
        mock_client.post.return_value.json = AsyncMock(return_value=self.response_data)


        results = []
        round = 0
        async for result in self.component.start_iter("/test/next"):
            results.append(result)
            round += 1
            if round >=2:
                break

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], LoadResponse)
        self.assertEqual(results[0].id, 1)
        self.assertEqual(results[0].path, "/img.jpg")
        self.assertEqual(results[0].user_id, 42)

        self.mock_check_health.assert_awaited_once()


    @patch("src.app.httpx.AsyncClient")
    async def test_connection_error(self, MockAsyncClient):
        mock_client = MockAsyncClient.return_value
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        async def run_once():
            async for result in self.component.start_iter("/test/next"):
                break

        await run_once()

        mock_client.post.assert_awaited()
        

