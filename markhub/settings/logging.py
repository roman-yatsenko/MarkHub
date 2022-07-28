import sys

from loguru import logger

from .django import DEBUG

ERROR_LOG_FILENAME = "logs/errors.log"

logger.remove()
logger.add(ERROR_LOG_FILENAME, level="ERROR", retention="7 days")

if DEBUG:
    logger.add(sys.stdout)
