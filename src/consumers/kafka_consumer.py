"""
Kafka consumer for processing raw transactions.
"""
import asyncio
import json
import logging
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

# Try to import Kafka, but don't fail if not available
try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("Kafka libraries not available. Running without Kafka support.")


class TransactionConsumer:
    """Consumes raw transactions from Kafka and publishes categorized ones."""
    
    def __init__(self):
        self.consumer = None
        self.producer = None
        self.running = False
        self.categorizer = None
        self.processed_count = 0
    
    async def start(self):
        """Start the Kafka consumer."""
        if not KAFKA_AVAILABLE:
            logger.info("Kafka not available - running in standalone mode")
            return
        
        try:
            from ..services.categorizer import TransactionCategorizer
            self.categorizer = TransactionCategorizer()
            
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_RAW_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                max_poll_records=100
            )
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            await self.consumer.start()
            await self.producer.start()
            self.running = True
            
            logger.info(f"Kafka consumer started. Listening to: {settings.KAFKA_RAW_TOPIC}")
            
            async for msg in self.consumer:
                if not self.running:
                    break
                await self.process_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.running = False
        finally:
            if self.consumer:
                await self.consumer.stop()
            if self.producer:
                await self.producer.stop()
            if self.categorizer:
                pass
    
    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        logger.info("Kafka consumer stopped")
    
    async def process_message(self, msg):
        """Process a single Kafka message."""
        try:
            transaction = msg.value
            self.processed_count += 1
            
            logger.debug(f"Processing transaction #{self.processed_count}")
            
            categorized = self.categorizer.categorize_transaction(transaction)
            await self.producer.send(settings.KAFKA_CATEGORIZED_TOPIC, categorized)
            await self.consumer.commit()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")


# Global consumer instance
consumer = TransactionConsumer()