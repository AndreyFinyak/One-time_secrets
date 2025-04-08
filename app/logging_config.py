from loguru import logger

logger.add("logs/debug.log", rotation="1 MB", retention="10 days", level="DEBUG")
