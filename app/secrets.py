from loguru import logger
from datetime import datetime
from fastapi import Request

# ...existing code...

def create_secret(db, secret_data, ttl_seconds, request: Request):
    # ...existing code for creating a secret...
    secret_id = "generated_secret_id"  # Replace with actual secret ID logic
    creation_time = datetime.utcnow()
    client_ip = request.client.host

    logger.info(
        f"Secret created: ID={secret_id}, Time={creation_time}, IP={client_ip}, TTL={ttl_seconds}"
    )

    # ...existing code...