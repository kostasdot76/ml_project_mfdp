import pika
import json
import time
from services.service import UnitOfWork, UpdatePredictionTask
from models.schemas import PredictionTask
from database.config import get_settings
from database.database import get_session2
from services.service.RabbitMQClient import RabbitMQClient
from sqlmodel import Session
from fastapi import Depends
from services.logging.logging import get_logger
from services.service.build_prompt_enhancer_model import build_prompt_enhancer_model
from services.service.build_image_generator_model import build_image_generator_model

logging = get_logger(logger_name=__name__)

settings = get_settings()

# Инициализация модели при запуске воркера
# ["prompt_enhancer", "image_generator"]
model_prompt_enhancer = build_prompt_enhancer_model()
model_image_generator = build_image_generator_model()
logging.info("PromptEnhancerModel initialized")


def process_task(ch, method, properties, body):
    try:
        logging.info(f"body {body}")
        # decoded_body = body.decode().strip('"').replace('\\"', '"')
        task = json.loads(body)

        logging.info(f"Load task {task}")
        session = get_session2()
        with UnitOfWork(session=session) as uow:
            logging.info(f" found task {task['prediction_id']}")
            model = (
                model_prompt_enhancer
                if task["model_type"] == "prompt_enhancer"
                else model_image_generator
            )
            logging.info(f" task {task["prediction_id"]}  + model for {task['model_type']} asigned as  {model}")
            service = UpdatePredictionTask(uow, task["prediction_id"], model=model)

            try:
                logging.info(f"try process for Task {task['prediction_id']}")
                if service.process():
                    logging.info(f"Task {task['prediction_id']} completed")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logging.info(f"Task {task['prediction_id']} process failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.info(f"Error processing task: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
            finally:
                service.close()
    except (json.JSONDecodeError, KeyError) as e:
        logging.info(f"Invalid task format: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.info(f"Critical error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)


def main():
    rmq_client = RabbitMQClient()
    rmq_client.connect()

    channel = rmq_client.connection.channel()
    channel.queue_declare(queue=rmq_client.config.RABBITMQ_QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=rmq_client.config.RABBITMQ_QUEUE_NAME, on_message_callback=process_task
    )

    logging.info("Worker started. Waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
