# user_service/apps/users/events.py
import json
import logging

import pika
from django.conf import settings

logger = logging.getLogger(__name__)


def publish_event(exchange: str, routing_key: str, payload: dict):
    """Generic event publisher"""
    try:
        with pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL)) as connection:
            channel = connection.channel()

            channel.exchange_declare(
                exchange=exchange,
                exchange_type='topic',
                durable=True,
            )

            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                )
            )

        logger.info(f"Published {routing_key}: {payload}")

    except Exception as e:
        logger.error(f"Failed to publish event: {e}")


def publish_user_created(user):
    publish_event(
        exchange='user_events',
        routing_key='user.created',
        payload={
            'event': 'user.created',
            'user_id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
        }
    )