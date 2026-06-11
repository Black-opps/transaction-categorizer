"""
RabbitMQ Event Bus - Async messaging for pipeline services
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

import aio_pika
from aio_pika import DeliveryMode, Message

logger = logging.getLogger(__name__)

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "transactions.topic"
PREFETCH_COUNT = 10


class EventBus:
    """RabbitMQ event bus for async pipeline communication"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self._consuming_tasks = []

    async def connect(self):
        """Connect to RabbitMQ and declare exchange"""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=PREFETCH_COUNT)

            self.exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info(f"✅ Connected to RabbitMQ at {RABBITMQ_URL}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False

    async def publish(
        self, routing_key: str, payload: Dict[str, Any], trace_id: str = None
    ) -> Dict[str, Any]:
        """Publish event to exchange"""
        event = {
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id or str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            **payload,
        }

        message = Message(
            body=json.dumps(event).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=event["event_id"],
        )

        await self.exchange.publish(message, routing_key=routing_key)
        logger.info(f"📤 Published to {routing_key} | trace_id={event['trace_id']}")
        return event

    async def consume(
        self,
        queue_name: str,
        routing_key: str,
        handler: Callable[[Dict], Awaitable[None]],
    ):
        """Subscribe to events and process them"""
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.bind(self.exchange, routing_key)

        logger.info(f"📥 Subscribed {queue_name} -> {routing_key}")

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    body = message.body.decode()
                    event = json.loads(body)
                    logger.info(
                        f"🔄 Processing {routing_key} | event_id={event.get('event_id')}"
                    )
                    await handler(event)
                    logger.info(
                        f"✅ Processed {routing_key} | event_id={event.get('event_id')}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Handler failed for {routing_key}: {e}", exc_info=True
                    )
                    raise

        await queue.consume(on_message)

    async def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("🔌 Disconnected from RabbitMQ")
