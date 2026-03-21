"""
Kafka consumer for processing transactions asynchronously.
"""
import json
import logging
from aiokafka import AIOKafkaConsumer

from ..core.config import settings
from ..services.categorizer import TransactionCategorizer
from ..models.transaction import Transaction

logger = logging.getLogger(__name__)


class TransactionConsumer:
    """Kafka consumer for raw transactions."""
    
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            "raw-transactions",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="transaction-categorizer",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.categorizer = TransactionCategorizer()
        self.running = False
    
    async def start(self):
        """Start consuming messages."""
        await self.consumer.start()
        self.running = True
        logger.info("Transaction consumer started")
        
        try:
            async for msg in self.consumer:
                await self.process_transaction(msg.value)
        finally:
            await self.consumer.stop()
    
    async def stop(self):
        """Stop consuming messages."""
        self.running = False
    
    async def process_transaction(self, data: dict):
        """Process a single transaction."""
        try:
            transaction = Transaction(**data)
            categorized = await self.categorizer.categorize_transaction(transaction)
            
            # TODO: Publish to Kafka topic for next service
            # await producer.send("categorized-transactions", categorized.dict())
            
            logger.info(f"Categorized transaction {transaction.id} as {categorized.category}")
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")