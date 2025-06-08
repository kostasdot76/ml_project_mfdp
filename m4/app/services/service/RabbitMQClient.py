import pika
from pika.adapters.blocking_connection import BlockingChannel
from database.config import get_settings
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


class RabbitMQClient:
    def __init__(self):
        self.config = get_settings()
        self.connection = None
        self.channel = None

    def connect(self):
        # Параметры подключения
        connection_params = pika.ConnectionParameters(
            host=self.config.RABBITMQ_HOST,
            port=self.config.RABBITMQ_PORT,
            virtual_host="/",
            credentials=pika.PlainCredentials(
                username=self.config.RABBITMQ_USER, password=self.config.RABBITMQ_PASS
            ),
            heartbeat=30,
            blocked_connection_timeout=2,
        )
        logging.info(
            f"rabbitMQ config {self.config.RABBITMQ_HOST} {self.config.RABBITMQ_PORT} {self.config.RABBITMQ_USER} {self.config.RABBITMQ_PASS} {self.config.RABBITMQ_QUEUE_NAME}"
        )
        self.connection = pika.BlockingConnection(connection_params)
        logging.info(f"self.connection.channel()")
        self.channel = self.connection.channel()

        logging.info(f"self.channel.queue_declare")

        self.channel.queue_declare(queue=self.config.RABBITMQ_QUEUE_NAME, durable=True)

    def close(self):
        if self.connection:
            self.connection.close()
