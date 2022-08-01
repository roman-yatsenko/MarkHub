import sys

from loguru import logger

from django.http import Http404

from .django import DEBUG

ERROR_LOG_FILENAME = "logs/errors.log"


logger.remove()
logger.add(ERROR_LOG_FILENAME, level="ERROR", retention="7 days")

if DEBUG:
    logger.add(sys.stdout)

def log_error_with_404(message: str) -> None:
    """Log error message and raise Http404 exception

    Args:
        message (str): _description_
    """
    logger.error(message)
    raise Http404(message)
