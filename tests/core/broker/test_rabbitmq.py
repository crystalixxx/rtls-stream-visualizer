import asyncio
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import RabbitMQConfig
from core.broker.rabbitmq import RabbitMQPublisher


def _config() -> RabbitMQConfig:
    return RabbitMQConfig(
        url="amqp://guest:guest@localhost:5672/",
        exchange="test-exchange",
        exchange_type="topic",
        queue="test-queue",
        routing_key="test.key",
    )


class TestRabbitMQPublisher:
    @patch("core.broker.rabbitmq.aio_pika")
    def test_publish_sends_message_to_exchange(self, mock_aio_pika):
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_aio_pika.connect_robust = AsyncMock(return_value=mock_connection)
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
        mock_aio_pika.ExchangeType = MagicMock(return_value="topic")

        captured_message = None

        async def capture_publish(msg, routing_key):
            nonlocal captured_message
            captured_message = msg

        mock_exchange.publish = capture_publish

        mock_aio_pika.Message = MagicMock()
        sentinel_msg = MagicMock()
        mock_aio_pika.Message.return_value = sentinel_msg

        publisher = RabbitMQPublisher(_config())

        body = b'{"test": true}'
        headers = {"origin": "ls-1000"}
        publisher.publish("test.key", body, headers=headers)

        mock_aio_pika.Message.assert_called_once_with(
            body=body,
            headers={"origin": "ls-1000"},
        )
        assert captured_message is sentinel_msg

        publisher.close()

    @patch("core.broker.rabbitmq.aio_pika")
    def test_publish_uses_topic_as_routing_key(self, mock_aio_pika):
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_aio_pika.connect_robust = AsyncMock(return_value=mock_connection)
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
        mock_aio_pika.ExchangeType = MagicMock(return_value="topic")
        mock_aio_pika.Message = MagicMock()

        captured_routing_key = None

        async def capture_publish(msg, routing_key):
            nonlocal captured_routing_key
            captured_routing_key = routing_key

        mock_exchange.publish = capture_publish

        publisher = RabbitMQPublisher(_config())
        publisher.publish("custom.routing.key", b"data")

        assert captured_routing_key == "custom.routing.key"

        publisher.close()

    @patch("core.broker.rabbitmq.aio_pika")
    def test_publish_with_none_headers(self, mock_aio_pika):
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_aio_pika.connect_robust = AsyncMock(return_value=mock_connection)
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
        mock_aio_pika.ExchangeType = MagicMock(return_value="topic")
        mock_aio_pika.Message = MagicMock()

        async def noop_publish(msg, routing_key):
            pass

        mock_exchange.publish = noop_publish

        publisher = RabbitMQPublisher(_config())
        publisher.publish("key", b"data", headers=None)

        mock_aio_pika.Message.assert_called_once_with(body=b"data", headers=None)

        publisher.close()

    @patch("core.broker.rabbitmq.aio_pika")
    def test_close_shuts_down_connection(self, mock_aio_pika):
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_aio_pika.connect_robust = AsyncMock(return_value=mock_connection)
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
        mock_aio_pika.ExchangeType = MagicMock(return_value="topic")

        publisher = RabbitMQPublisher(_config())
        publisher.close()

        mock_channel.close.assert_awaited_once()
        mock_connection.close.assert_awaited_once()
