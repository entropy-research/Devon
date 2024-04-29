import logging
import sys

LOGGER_NAME = "devon"

logger = logging.getLogger(LOGGER_NAME)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)

logger.setLevel(logging.DEBUG)

