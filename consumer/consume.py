import asyncio
import json
import logging
import os
from typing import Dict, Any
from aio_pika import connect, connect_robust, Message, IncomingMessage, Exchange, ExchangeType
from models import User
from db import get_db
from crud import create_user, get_user_by_username, get_user_by_id


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host = os.getenv("RABBITMQ_HOST", "rabbitmq")
port = os.getenv("RABBITMQ_PORT", "5672")
user = os.getenv("RABBITMQ_DEFAULT_USER", "guest")
password = os.getenv("RABBITMQ_DEFAULT_PASS", "guest")
RABBITMQ_URL = f"amqp://{user}:{password}@{host}:{port}/"
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "default_exchange")

async def process_register(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    user_data = message["data"]
    try:
        existing_user = await get_user_by_username(db, user_data["username"])
        if existing_user:
            return {"error": "User with this username already exists"}
        new_user = User(
            username=user_data["username"],
            password=user_data["password"],
            role=user_data.get("role"),
        )
        await create_user(db, new_user)
    finally:
        db.close()
    return {"success": "User registered successfully"}

async def process_login(message: Dict[str, Any]) -> Dict[str, Any]:
    db_gen = get_db()
    db = next(db_gen)
    username = message["data"]["username"]
    try:
        logger.info(f"Processing login request for user: {username}")
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            logger.info(f"User found in database: {existing_user.as_dict()}")
            return existing_user.as_dict()
        else:
            logger.error(f"User not found: {username}")
            return {"error": "User not found"} 
    finally:
        db.close()
    
async def process_message(message: IncomingMessage, exchange: Exchange):
    try:
        async with message.process():
            logger.info(f"Received message with correlation_id: {message.correlation_id}")
            request_data = json.loads(message.body.decode())
            action = request_data.get("action")
            response = {}

            # Log the received action and routing key
            logger.info(f"Processing action: {action} with routing key: {message.routing_key}")

            # Request processing
            match action:
                case "register_user":
                    logger.info("Processing register request...")
                    response = await process_register(request_data)
                case "get_user_by_username":
                    logger.info("Processing login request...")
                    response = await process_login(request_data)
                case _:
                    logger.warning(f"Unknown action received: {action}")
                    response = {"error": f"Unknown action: {action}"}


            if message.reply_to:
                logger.info(f"Sending response to {message.reply_to}")
                response_message = Message(
                    body=json.dumps(response).encode(),
                    correlation_id=message.correlation_id
                )
                await exchange.publish(
                    response_message,
                    routing_key=message.reply_to
                )
                logger.info(f"Response sent for correlation_id: {message.correlation_id}")
            else:
                logger.warning("No reply_to in message, response not sent")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        if not message.processed:
            await message.reject(requeue=False)
        await send_error_response(message, exchange, "Invalid message format")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        if not message.processed:
            await message.reject(requeue=False)
        await send_error_response(message, exchange, str(e))

async def send_error_response(message: IncomingMessage, exchange: Exchange, error_msg: str):
    if message.reply_to:
        error_response = {"error": error_msg}
        error_message = Message(
            body=json.dumps(error_response).encode(),
            correlation_id=message.correlation_id
        )
        try:
            await exchange.publish(
                error_message,
                routing_key=message.reply_to
            )
            logger.error(f"Error response sent for correlation_id: {message.correlation_id}")
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

async def main():
    connection = await connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.DIRECT,
            durable=True
        )

        queue = await channel.declare_queue(
            "messages",
            durable=True,
            auto_delete=False
        )
       
        routing_keys = [
            "user.register",
            "user.login",
        ]
        
        for key in routing_keys:
            await queue.bind(exchange, routing_key=key)
            logger.info(f"Queue bound to exchange with routing key: {key}")

        async with queue.iterator() as queue_iter:
            message: IncomingMessage
            async for message in queue_iter:
                await process_message(message, exchange)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        raise