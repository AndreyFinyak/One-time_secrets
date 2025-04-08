from loguru import logger

logger.add("logs/secrets.log", rotation="1 MB", retention="10 days", level="INFO")
