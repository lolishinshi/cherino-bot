import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger.opt(depth=6, exception=record.exc_info).log(
            record.levelname, record.getMessage()
        )


def setup_logging():
    logger.remove()
    logger.add(sys.stderr, colorize=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(InterceptHandler())
